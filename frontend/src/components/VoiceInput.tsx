"use client";

/**
 * VoiceInput component - Microphone button with VAD integration
 * Shows recording state through colors and animation
 */

import { useVoice } from "@/hooks/use-voice";
import { useVoiceStore } from "@/stores/voice-store";

export function VoiceInput() {
  const { connectionState } = useVoiceStore();
  const { recordingState, isVadLoading, isVadError, isListening, startListening, stopListening } = useVoice();

  const isConnected = connectionState === "connected";
  const showStopButton = isListening || recordingState !== "idle" || isVadLoading;

  const getButtonStyles = () => {
    if (isVadError) {
      return "bg-red-700 cursor-not-allowed";
    }
    if (!isConnected) {
      return "bg-gray-400 cursor-not-allowed";
    }
    switch (recordingState) {
      case "recording":
        return "bg-red-500 animate-pulse";
      case "processing":
        return "bg-yellow-500";
      default:
        return isVadLoading ? "bg-gray-500 animate-pulse" : "bg-gray-500 hover:bg-gray-600";
    }
  };

  const getStatusText = () => {
    if (isVadError) return "VAD Error";
    if (!isConnected) return "Not connected";
    if (isVadLoading) return "Loading VAD...";
    switch (recordingState) {
      case "recording":
        return "Recording...";
      case "processing":
        return "Processing...";
      default:
        return "Click to start";
    }
  };

  const handleClick = () => {
    if (!isConnected || isVadError) return;

    if (!showStopButton) {
      startListening();
    } else {
      stopListening();
    }
  };

  return (
    <div className="flex flex-col items-center gap-3">
      <button
        onClick={handleClick}
        disabled={!isConnected || isVadError}
        className={`
          w-20 h-20 rounded-full
          flex items-center justify-center
          text-white text-3xl
          transition-all duration-200
          focus:outline-none focus:ring-4 focus:ring-blue-300
          disabled:opacity-50
          ${getButtonStyles()}
        `}
        aria-label={showStopButton ? "Stop recording" : "Start recording"}
      >
        {showStopButton ? (
          <svg className="w-8 h-8" fill="currentColor" viewBox="0 0 24 24">
            <rect x="6" y="6" width="12" height="12" rx="2" />
          </svg>
        ) : (
          <svg className="w-8 h-8" fill="currentColor" viewBox="0 0 24 24">
            <path d="M12 14c1.66 0 3-1.34 3-3V5c0-1.66-1.34-3-3-3S9 3.34 9 5v6c0 1.66 1.34 3 3 3z" />
            <path d="M17 11c0 2.76-2.24 5-5 5s-5-2.24-5-5H5c0 3.53 2.61 6.43 6 6.92V21h2v-3.08c3.39-.49 6-3.39 6-6.92h-2z" />
          </svg>
        )}
      </button>
      <span className="text-sm text-gray-600 dark:text-gray-400">
        {getStatusText()}
      </span>
    </div>
  );
}
