"use client";

/**
 * Custom hook for voice recording with VAD (Voice Activity Detection)
 * Uses @ricky0123/vad-react for speech detection
 */

import { useCallback, useEffect, useRef } from "react";
import { useMicVAD } from "@ricky0123/vad-react";
import { useVoiceStore } from "@/stores/voice-store";
import { RecordingState, serializeEvent } from "@/core/events";

export interface UseVoiceResult {
  recordingState: RecordingState;
  isVadLoading: boolean;
  isVadError: boolean;
  isListening: boolean;
  startListening: () => void;
  stopListening: () => void;
}

export function useVoice(): UseVoiceResult {
  const { connectionState, wsClient, recordingState, setRecordingState } = useVoiceStore();
  // Track previous connection state to detect disconnection
  const prevConnectionRef = useRef(connectionState);

  const vad = useMicVAD({
    startOnLoad: false,
    baseAssetPath: "/",
    model: "v5",
    onSpeechStart: () => {
      setRecordingState("recording");
      if (wsClient) {
        wsClient.send(
          serializeEvent({ type: "vad.start", timestamp: Date.now() })
        );
      }
    },
    onVADMisfire: () => {
      // False positive detection - ignore and stay in listening mode
      setRecordingState("idle");
    },
    onSpeechEnd: (audio: Float32Array) => {
      if (!wsClient) {
        setRecordingState("idle");
        return;
      }

      setRecordingState("processing");

      // Send audio data as binary
      // Note: slice() can return SharedArrayBuffer, cast to ArrayBuffer for our protocol
      const audioBuffer = audio.buffer.slice(
        audio.byteOffset,
        audio.byteOffset + audio.byteLength
      ) as ArrayBuffer;
      const audioSent = wsClient.send(
        serializeEvent({
          type: "vad.audio",
          audio: audioBuffer,
          sampleRate: 16000,
        })
      );

      if (!audioSent) {
        // Connection lost during send - reset state
        setRecordingState("idle");
        return;
      }

      // Send end event
      wsClient.send(
        serializeEvent({ type: "vad.end", timestamp: Date.now() })
      );

      // State will be reset to "idle" by voice-store when stt.final is received
    },
  });

  const startListening = useCallback(() => {
    if (connectionState === "connected" && !vad.listening) {
      vad.start();
      setRecordingState("idle");
    }
  }, [connectionState, vad, setRecordingState]);

  const stopListening = useCallback(() => {
    vad.pause();
    setRecordingState("idle");
  }, [vad, setRecordingState]);

  // Stop VAD when connection drops
  useEffect(() => {
    const wasConnected = prevConnectionRef.current === "connected";
    const isDisconnected = connectionState !== "connected";
    prevConnectionRef.current = connectionState;

    if (wasConnected && isDisconnected && vad.listening) {
      vad.pause();
    }
  }, [connectionState, vad]);

  // Cleanup on unmount - ensures VAD is paused (React Strict Mode safety)
  useEffect(() => {
    return () => {
      vad.pause();
      setRecordingState("idle");
    };
  }, [vad, setRecordingState]);

  return {
    recordingState,
    isVadLoading: vad.loading,
    isVadError: !!vad.errored,
    isListening: vad.listening,
    startListening,
    stopListening,
  };
}
