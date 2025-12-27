"use client";

import { VoiceInput } from "@/components/VoiceInput";
import { useVoiceStore } from "@/stores/voice-store";
import { useEffect, useRef } from "react";

export default function Home() {
  const {
    connectionState,
    connect,
    disconnect,
    partialText,
    sttResults,
    lastError,
    llmState,
    llmStreamingText,
    llmResults,
    ttsState,
    ttsLatencyMs,
    stopTts,
  } = useVoiceStore();

  const chatAreaRef = useRef<HTMLDivElement>(null);

  // Auto-scroll to bottom when new messages arrive
  useEffect(() => {
    if (chatAreaRef.current) {
      chatAreaRef.current.scrollTop = chatAreaRef.current.scrollHeight;
    }
  }, [sttResults, llmResults, llmStreamingText, partialText]);

  const getStatusColor = () => {
    switch (connectionState) {
      case "connected":
        return "bg-green-500";
      case "connecting":
        return "bg-yellow-500";
      case "disconnected":
        return "bg-red-500";
    }
  };

  const getStatusText = () => {
    switch (connectionState) {
      case "connected":
        return "接続中";
      case "connecting":
        return "接続中...";
      case "disconnected":
        return "未接続";
    }
  };

  // Build sorted message list
  const messages = [
    ...sttResults.map((r, i) => ({
      ...r,
      role: "user" as const,
      key: `stt-${r.timestamp}-${i}`,
    })),
    ...llmResults.map((r, i) => ({
      ...r,
      role: "assistant" as const,
      key: `llm-${r.timestamp}-${i}`,
    })),
  ].sort((a, b) => a.timestamp - b.timestamp);

  return (
    <div className="flex flex-col h-screen bg-gray-50">
      {/* Header */}
      <header className="flex-shrink-0 bg-white border-b border-gray-200 px-4 py-3">
        <div className="max-w-4xl mx-auto flex items-center justify-between">
          <div>
            <h1 className="text-xl font-bold text-gray-800">Voice Assistant</h1>
            <p className="text-sm text-gray-500">日本語音声対話アシスタント</p>
          </div>
          <div className="flex items-center gap-4">
            <div className="flex items-center gap-2">
              <div className={`w-2.5 h-2.5 rounded-full ${getStatusColor()}`} />
              <span className="text-sm text-gray-600">{getStatusText()}</span>
            </div>
            {connectionState === "disconnected" ? (
              <button
                onClick={connect}
                className="px-4 py-1.5 text-sm bg-blue-500 text-white rounded-lg hover:bg-blue-600 transition-colors"
              >
                接続
              </button>
            ) : connectionState === "connected" ? (
              <button
                onClick={disconnect}
                className="px-4 py-1.5 text-sm bg-gray-200 text-gray-700 rounded-lg hover:bg-gray-300 transition-colors"
              >
                切断
              </button>
            ) : null}
          </div>
        </div>
      </header>

      {/* Chat Area */}
      <main
        ref={chatAreaRef}
        className="flex-1 overflow-y-auto px-4 py-6"
      >
        <div className="max-w-4xl mx-auto space-y-4">
          {/* Error Display */}
          {lastError && (
            <div className="p-4 bg-red-50 border border-red-200 rounded-lg">
              <p className="text-sm text-red-600">
                エラー [{lastError.code}]: {lastError.message}
              </p>
            </div>
          )}

          {/* Empty State */}
          {messages.length === 0 && !partialText && llmState === "idle" && (
            <div className="flex flex-col items-center justify-center py-20 text-gray-400">
              <svg className="w-16 h-16 mb-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={1.5} d="M19 11a7 7 0 01-7 7m0 0a7 7 0 01-7-7m7 7v4m0 0H8m4 0h4m-4-8a3 3 0 01-3-3V5a3 3 0 116 0v6a3 3 0 01-3 3z" />
              </svg>
              <p className="text-lg">マイクボタンを押して話しかけてください</p>
            </div>
          )}

          {/* Message Bubbles */}
          {messages.map((msg) => (
            <div
              key={msg.key}
              className={`flex ${msg.role === "user" ? "justify-end" : "justify-start"}`}
            >
              <div
                className={`max-w-[80%] rounded-2xl px-4 py-3 ${
                  msg.role === "user"
                    ? "bg-blue-500 text-white"
                    : "bg-white border border-gray-200 text-gray-800"
                }`}
              >
                <p className="whitespace-pre-wrap">{msg.text}</p>
                <p className={`text-xs mt-2 ${msg.role === "user" ? "text-blue-100" : "text-gray-400"}`}>
                  {msg.latency_ms.toFixed(0)}ms
                  {msg.role === "assistant" && "ttft_ms" in msg && (
                    <span> (TTFT: {(msg as { ttft_ms: number }).ttft_ms.toFixed(0)}ms)</span>
                  )}
                </p>
              </div>
            </div>
          ))}

          {/* Partial STT Text (user is speaking) */}
          {partialText && (
            <div className="flex justify-end">
              <div className="max-w-[80%] rounded-2xl px-4 py-3 bg-blue-300 text-white opacity-80">
                <p className="whitespace-pre-wrap italic">{partialText}</p>
                <p className="text-xs mt-1 text-blue-100">認識中...</p>
              </div>
            </div>
          )}

          {/* LLM Streaming Response */}
          {(llmState === "processing" || llmState === "streaming") && (
            <div className="flex justify-start">
              <div className="max-w-[80%] rounded-2xl px-4 py-3 bg-white border border-gray-200 text-gray-800">
                {llmStreamingText ? (
                  <p className="whitespace-pre-wrap">{llmStreamingText}</p>
                ) : (
                  <div className="flex items-center gap-1">
                    <span className="w-2 h-2 bg-gray-400 rounded-full animate-bounce" style={{ animationDelay: "0ms" }} />
                    <span className="w-2 h-2 bg-gray-400 rounded-full animate-bounce" style={{ animationDelay: "150ms" }} />
                    <span className="w-2 h-2 bg-gray-400 rounded-full animate-bounce" style={{ animationDelay: "300ms" }} />
                  </div>
                )}
                <p className="text-xs mt-2 text-gray-400">
                  {llmState === "processing" ? "考え中..." : "応答中..."}
                </p>
              </div>
            </div>
          )}
        </div>
      </main>

      {/* Footer */}
      <footer className="flex-shrink-0 bg-white border-t border-gray-200 px-4 py-4">
        <div className="max-w-4xl mx-auto flex flex-col items-center gap-2">
          {/* TTS Playing Indicator */}
          {ttsState === "playing" && (
            <div className="flex items-center gap-3 text-sm text-gray-600 mb-2">
              <div className="flex items-center gap-1">
                <span className="w-1.5 h-1.5 bg-blue-500 rounded-full animate-bounce" style={{ animationDelay: "0ms" }} />
                <span className="w-1.5 h-1.5 bg-blue-500 rounded-full animate-bounce" style={{ animationDelay: "150ms" }} />
                <span className="w-1.5 h-1.5 bg-blue-500 rounded-full animate-bounce" style={{ animationDelay: "300ms" }} />
              </div>
              <span>音声再生中</span>
              <button
                onClick={stopTts}
                className="px-2 py-0.5 text-xs bg-gray-200 hover:bg-gray-300 rounded transition-colors"
              >
                停止
              </button>
              {ttsLatencyMs !== null && (
                <span className="text-xs text-gray-400">({ttsLatencyMs.toFixed(0)}ms)</span>
              )}
            </div>
          )}

          {/* Mic Button */}
          <VoiceInput />
        </div>
      </footer>
    </div>
  );
}
