/**
 * Zustand store for voice assistant state management
 */

import { create } from "zustand";
import {
  ConnectionState,
  WebSocketClient,
} from "@/core/websocket-client";
import { RecordingState } from "@/core/events";

// WebSocket URL - configurable via environment variable
const getWebSocketUrl = (): string => {
  const host = process.env.NEXT_PUBLIC_API_HOST || "localhost:8000";
  const protocol = process.env.NEXT_PUBLIC_API_PROTOCOL === "wss" ? "wss" : "ws";
  return `${protocol}://${host}/api/v1/ws/chat`;
};

interface VoiceStore {
  // State
  connectionState: ConnectionState;
  recordingState: RecordingState;
  wsClient: WebSocketClient | null;

  // Actions
  connect: () => void;
  disconnect: () => void;
  setConnectionState: (state: ConnectionState) => void;
  setRecordingState: (state: RecordingState) => void;
}

export const useVoiceStore = create<VoiceStore>((set, get) => ({
  // Initial state
  connectionState: "disconnected",
  recordingState: "idle",
  wsClient: null,

  // Actions
  setConnectionState: (state: ConnectionState) => {
    set({ connectionState: state });
  },

  setRecordingState: (state: RecordingState) => {
    set({ recordingState: state });
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
      onMessage: () => {
        // Message handling will be added in Story 2.3+
        // Events: stt.partial, stt.final, llm.start, llm.delta, llm.end, tts.chunk, tts.end, error
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
