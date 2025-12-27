/**
 * Zustand store for voice assistant state management
 */

import { create } from "zustand";
import {
  ConnectionState,
  WebSocketClient,
} from "@/core/websocket-client";
import { RecordingState, parseServerEvent } from "@/core/events";
import { getAudioPlayer } from "@/core/audio-player";
import { fetchConversation, type MessageResponse } from "@/lib/api-client";

// WebSocket URL - configurable via environment variable
const getWebSocketUrl = (): string => {
  const host = process.env.NEXT_PUBLIC_API_HOST || "localhost:8000";
  const protocol = process.env.NEXT_PUBLIC_API_PROTOCOL === "wss" ? "wss" : "ws";
  return `${protocol}://${host}/api/v1/ws/chat`;
};

/** Represents a recognized text from STT */
export interface SttResult {
  text: string;
  latency_ms: number;
  timestamp: number;
}

/** Represents an LLM response (Story 2.4) */
export interface LlmResult {
  text: string;
  latency_ms: number;
  ttft_ms: number;
  timestamp: number;
}

/** Processing state for LLM (Story 2.4) */
export type LlmState = "idle" | "processing" | "streaming";

/** Processing state for TTS (Story 2.5) */
export type TtsState = "idle" | "playing";

interface VoiceStore {
  // State
  connectionState: ConnectionState;
  recordingState: RecordingState;
  wsClient: WebSocketClient | null;

  // STT results
  partialText: string;
  sttResults: SttResult[];
  lastError: { code: string; message: string } | null;

  // LLM state (Story 2.4)
  llmState: LlmState;
  llmStreamingText: string;
  llmResults: LlmResult[];

  // TTS state (Story 2.5)
  ttsState: TtsState;
  ttsLatencyMs: number | null;

  // Conversation selection state (Story 3.4)
  selectedConversationId: string | null;
  historicalMessages: MessageResponse[];
  isLoadingConversation: boolean;
  conversationError: string | null;

  // Actions
  connect: () => void;
  disconnect: () => void;
  setConnectionState: (state: ConnectionState) => void;
  setRecordingState: (state: RecordingState) => void;
  clearSttResults: () => void;
  clearLlmResults: () => void;
  stopTts: () => void;
  selectConversation: (id: string) => Promise<void>;
  clearSelection: () => void;
}

export const useVoiceStore = create<VoiceStore>((set, get) => ({
  // Initial state
  connectionState: "disconnected",
  recordingState: "idle",
  wsClient: null,
  partialText: "",
  sttResults: [],
  lastError: null,

  // LLM initial state (Story 2.4)
  llmState: "idle",
  llmStreamingText: "",
  llmResults: [],

  // TTS initial state (Story 2.5)
  ttsState: "idle",
  ttsLatencyMs: null,

  // Conversation selection initial state (Story 3.4)
  selectedConversationId: null,
  historicalMessages: [],
  isLoadingConversation: false,
  conversationError: null,

  // Actions
  setConnectionState: (state: ConnectionState) => {
    set({ connectionState: state });
  },

  setRecordingState: (state: RecordingState) => {
    set({ recordingState: state });
  },

  clearSttResults: () => {
    set({ sttResults: [], partialText: "", lastError: null });
  },

  clearLlmResults: () => {
    set({ llmResults: [], llmStreamingText: "", llmState: "idle" });
  },

  stopTts: () => {
    const audioPlayer = getAudioPlayer();
    audioPlayer.stop();
    set({ ttsState: "idle" });
  },

  connect: () => {
    const existing = get().wsClient;

    // Prevent duplicate connections
    if (existing?.isConnected()) {
      return;
    }

    // Clean up existing client
    if (existing) {
      existing.disconnect();
    }

    const client = new WebSocketClient({
      url: getWebSocketUrl(),
      onStateChange: (state: ConnectionState) => {
        set({ connectionState: state });
      },
      onMessage: (data: unknown) => {
        const event = parseServerEvent(data);
        if (!event) return;

        switch (event.type) {
          case "stt.partial":
            set({ partialText: event.text });
            break;

          case "stt.final":
            set((state) => ({
              partialText: "",
              recordingState: "idle",
              lastError: null, // Clear previous error on successful recognition
              sttResults: [
                ...state.sttResults,
                {
                  text: event.text,
                  latency_ms: event.latency_ms,
                  timestamp: Date.now(),
                },
              ],
            }));
            break;

          case "error":
            set({
              lastError: { code: event.code, message: event.message },
              recordingState: "idle",
              llmState: "idle",
            });
            break;

          // LLM events (Story 2.4)
          case "llm.start":
            set({ llmState: "processing", llmStreamingText: "" });
            break;

          case "llm.delta":
            set((state) => ({
              llmState: "streaming",
              llmStreamingText: state.llmStreamingText + event.text,
            }));
            break;

          case "llm.end":
            set((state) => ({
              llmState: "idle",
              llmResults: [
                ...state.llmResults,
                {
                  text: state.llmStreamingText,
                  latency_ms: event.latency_ms,
                  ttft_ms: event.ttft_ms,
                  timestamp: Date.now(),
                },
              ],
              llmStreamingText: "",
            }));
            break;

          // TTS events (Story 2.5)
          case "tts.chunk": {
            const audioPlayer = getAudioPlayer();
            // Resume AudioContext if suspended (browser autoplay policy)
            audioPlayer.resume().catch(() => {
              // Ignore resume errors
            });
            // Set callback to update state when all audio finishes playing
            audioPlayer.onPlaybackComplete(() => {
              set({ ttsState: "idle" });
            });
            // Enqueue audio chunk for playback
            audioPlayer.enqueue(event.audio, event.sampleRate).catch(() => {
              // Ignore decode errors
            });
            set({ ttsState: "playing" });
            break;
          }

          case "tts.end":
            // Only store latency - ttsState will be set to idle by AudioPlayer callback
            set({ ttsLatencyMs: event.latency_ms });
            break;
        }
      },
      onError: () => {
        // WebSocket errors trigger onclose which handles cleanup
        // Error details are logged at the WebSocket layer if needed
      },
    });

    set({ wsClient: client });
    client.connect();
  },

  disconnect: () => {
    const client = get().wsClient;
    if (client) {
      client.disconnect();
    }
    set({ wsClient: null, connectionState: "disconnected" });
  },

  // Conversation selection actions (Story 3.4)
  selectConversation: async (id: string) => {
    set({
      selectedConversationId: id,
      isLoadingConversation: true,
      conversationError: null,
      // Clear real-time messages when switching to historical view
      sttResults: [],
      llmResults: [],
      llmStreamingText: "",
      partialText: "",
    });

    try {
      const conversation = await fetchConversation(id);
      set({
        historicalMessages: conversation.messages,
        isLoadingConversation: false,
      });
    } catch (error) {
      set({
        conversationError:
          error instanceof Error ? error.message : "会話の読み込みに失敗しました",
        isLoadingConversation: false,
        historicalMessages: [],
      });
    }
  },

  clearSelection: () => {
    set({
      selectedConversationId: null,
      historicalMessages: [],
      isLoadingConversation: false,
      conversationError: null,
    });
  },
}));
