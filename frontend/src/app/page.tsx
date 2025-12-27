"use client";

import { useVoiceStore } from "@/stores/voice-store";

export default function Home() {
  const { connectionState, connect, disconnect } = useVoiceStore();

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

      {/* チャットUIは Story 2.7 で実装 */}
    </main>
  );
}
