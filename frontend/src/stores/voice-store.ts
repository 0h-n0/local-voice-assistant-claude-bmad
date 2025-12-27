/**
 * Zustand store for voice assistant state management
 */

import { create } from "zustand";
import {
  ConnectionState,
  WebSocketClient,
} from "@/core/websocket-client";

// WebSocket URL - configurable via environment variable
const getWebSocketUrl = (): string => {
  const host = process.env.NEXT_PUBLIC_API_HOST || "localhost:8000";
  const protocol = process.env.NEXT_PUBLIC_API_PROTOCOL === "wss" ? "wss" : "ws";
  return `${protocol}://${host}/api/v1/ws/chat`;
};

interface VoiceStore {
  // State
  connectionState: ConnectionState;
  wsClient: WebSocketClient | null;

  // Actions
  connect: () => void;
  disconnect: () => void;
  setConnectionState: (state: ConnectionState) => void;
}

export const useVoiceStore = create<VoiceStore>((set, get) => ({
  // Initial state
  connectionState: "disconnected",
  wsClient: null,

  // Actions
  setConnectionState: (state: ConnectionState) => {
    set({ connectionState: state });
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
      onMessage: (_data: unknown) => {
        // Message handling will be added in Story 2.2+
        // Events: stt.partial, stt.final, llm.start, llm.delta, llm.end, tts.chunk, tts.end, error
      },
      onError: (error: Event) => {
        console.error("WebSocket error:", error);
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
