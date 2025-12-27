/**
 * Zustand store for voice assistant state management
 */

import { create } from "zustand";
import {
  ConnectionState,
  WebSocketClient,
} from "@/core/websocket-client";
import { RecordingState, parseServerEvent } from "@/core/events";

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

interface VoiceStore {
  // State
  connectionState: ConnectionState;
  recordingState: RecordingState;
  wsClient: WebSocketClient | null;

  // STT results
  partialText: string;
  sttResults: SttResult[];
  lastError: { code: string; message: string } | null;

  // Actions
  connect: () => void;
  disconnect: () => void;
  setConnectionState: (state: ConnectionState) => void;
  setRecordingState: (state: RecordingState) => void;
  clearSttResults: () => void;
}

export const useVoiceStore = create<VoiceStore>((set, get) => ({
  // Initial state
  connectionState: "disconnected",
  recordingState: "idle",
  wsClient: null,
  partialText: "",
  sttResults: [],
  lastError: null,

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
            });
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
}));
