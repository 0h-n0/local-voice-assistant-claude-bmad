"use client";

import { VoiceInput } from "@/components/VoiceInput";
import { useVoiceStore } from "@/stores/voice-store";

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
  } = useVoiceStore();

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

  return (
    <main className="flex min-h-screen flex-col items-center justify-center p-24">
      <h1 className="text-4xl font-bold text-center">Voice Assistant</h1>
      <p className="mt-4 text-gray-600">
        日本語特化ローカル音声対話アシスタント
      </p>

      {/* Connection Status Indicator */}
      <div className="mt-8 flex items-center gap-3">
        <div className={`w-3 h-3 rounded-full ${getStatusColor()}`} />
        <span className="text-sm text-gray-600">{getStatusText()}</span>
      </div>

      {/* Connection Controls */}
      <div className="mt-6 flex gap-4">
        {connectionState === "disconnected" ? (
          <button
            onClick={connect}
            className="px-6 py-2 bg-blue-500 text-white rounded-lg hover:bg-blue-600 transition-colors"
          >
            接続
          </button>
        ) : connectionState === "connected" ? (
          <button
            onClick={disconnect}
            className="px-6 py-2 bg-gray-500 text-white rounded-lg hover:bg-gray-600 transition-colors"
          >
            切断
          </button>
        ) : (
          <button
            disabled
            className="px-6 py-2 bg-gray-300 text-gray-500 rounded-lg cursor-not-allowed"
          >
            接続中...
          </button>
        )}
      </div>

      {/* Voice Input - Story 2.2 */}
      <div className="mt-12">
        <VoiceInput />
      </div>

      {/* Conversation Display - Story 2.4 */}
      <div className="mt-8 w-full max-w-2xl">
        {/* Error Display */}
        {lastError && (
          <div className="p-4 bg-red-50 border border-red-200 rounded-lg mb-4">
            <p className="text-sm text-red-600">
              エラー [{lastError.code}]: {lastError.message}
            </p>
          </div>
        )}

        {/* Conversation History */}
        {(sttResults.length > 0 || llmResults.length > 0) && (
          <div className="space-y-4">
            <h2 className="text-lg font-semibold text-gray-700">会話</h2>
            {/* Interleave STT and LLM results based on timestamps */}
            {(() => {
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

              return messages.map((msg) => (
                <div
                  key={msg.key}
                  className={`p-4 rounded-lg shadow-sm ${
                    msg.role === "user"
                      ? "bg-blue-50 border border-blue-200 ml-8"
                      : "bg-green-50 border border-green-200 mr-8"
                  }`}
                >
                  <p className="text-xs text-gray-500 mb-1">
                    {msg.role === "user" ? "あなた" : "アシスタント"}
                  </p>
                  <p className="text-gray-800 whitespace-pre-wrap">{msg.text}</p>
                  <p className="text-xs text-gray-400 mt-2">
                    処理時間: {msg.latency_ms.toFixed(0)}ms
                    {msg.role === "assistant" && "ttft_ms" in msg && (
                      <span> (TTFT: {(msg as { ttft_ms: number }).ttft_ms.toFixed(0)}ms)</span>
                    )}
                  </p>
                </div>
              ));
            })()}
          </div>
        )}

        {/* Partial STT Text (streaming) */}
        {partialText && (
          <div className="p-4 bg-gray-100 rounded-lg mt-4 ml-8">
            <p className="text-xs text-gray-500 mb-1">認識中...</p>
            <p className="text-gray-700 italic">{partialText}</p>
          </div>
        )}

        {/* LLM Streaming Text */}
        {(llmState === "processing" || llmState === "streaming") && (
          <div className="p-4 bg-green-50 border border-green-200 rounded-lg mt-4 mr-8">
            <p className="text-xs text-gray-500 mb-1">
              {llmState === "processing" ? "考え中..." : "応答中..."}
            </p>
            {llmStreamingText && (
              <p className="text-gray-800 whitespace-pre-wrap">{llmStreamingText}</p>
            )}
            {llmState === "processing" && (
              <span className="inline-block w-2 h-4 bg-gray-400 animate-pulse" />
            )}
          </div>
        )}
      </div>
    </main>
  );
}
