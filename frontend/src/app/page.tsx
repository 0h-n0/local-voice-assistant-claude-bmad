"use client";

import { VoiceInput } from "@/components/VoiceInput";
import { ConversationList } from "@/components/ConversationList";
import { useVoiceStore } from "@/stores/voice-store";
import { useCallback, useEffect, useRef, useState } from "react";
import { useQueryClient } from "@tanstack/react-query";

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
    // Conversation selection (Story 3.4)
    selectedConversationId,
    historicalMessages,
    isLoadingConversation,
    conversationError,
    selectConversation,
    clearSelection,
  } = useVoiceStore();

  const queryClient = useQueryClient();
  const chatAreaRef = useRef<HTMLDivElement>(null);
  const [isUserAtBottom, setIsUserAtBottom] = useState(true);
  const scrollThrottleRef = useRef<NodeJS.Timeout | null>(null);
  const [sidebarOpen, setSidebarOpen] = useState(true);

  // Check if scroll position is near the bottom
  const isNearBottom = (element: HTMLElement, threshold = 100): boolean => {
    return element.scrollHeight - element.scrollTop - element.clientHeight < threshold;
  };

  // Handle scroll events to track user position (throttled for performance)
  const handleScroll = useCallback(() => {
    if (scrollThrottleRef.current) return;

    scrollThrottleRef.current = setTimeout(() => {
      scrollThrottleRef.current = null;
      if (chatAreaRef.current) {
        setIsUserAtBottom(isNearBottom(chatAreaRef.current));
      }
    }, 100);
  }, []);

  // Scroll to bottom helper with smooth animation
  const scrollToBottom = useCallback(() => {
    if (chatAreaRef.current) {
      chatAreaRef.current.scrollTo({
        top: chatAreaRef.current.scrollHeight,
        behavior: "smooth",
      });
      setIsUserAtBottom(true);
    }
  }, []);

  // Check actual scroll position on initial mount
  useEffect(() => {
    if (chatAreaRef.current) {
      setIsUserAtBottom(isNearBottom(chatAreaRef.current));
    }
  }, []);

  // Auto-scroll to bottom when new messages arrive (only if user is at bottom)
  useEffect(() => {
    if (isUserAtBottom && chatAreaRef.current) {
      chatAreaRef.current.scrollTo({
        top: chatAreaRef.current.scrollHeight,
        behavior: "smooth",
      });
    }
  }, [sttResults, llmResults, llmStreamingText, partialText, historicalMessages, isUserAtBottom]);

  // Handle window resize to maintain scroll position
  useEffect(() => {
    const handleResize = () => {
      if (chatAreaRef.current) {
        const atBottom = isNearBottom(chatAreaRef.current);
        setIsUserAtBottom(atBottom);
        if (atBottom) {
          chatAreaRef.current.scrollTop = chatAreaRef.current.scrollHeight;
        }
      }
    };

    window.addEventListener("resize", handleResize);
    return () => window.removeEventListener("resize", handleResize);
  }, []);

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

  // Handle new conversation button
  const handleNewConversation = useCallback(() => {
    clearSelection();
    // Invalidate conversation list to refresh after new messages
    queryClient.invalidateQueries({ queryKey: ["conversations", "list"] });
  }, [clearSelection, queryClient]);

  // Handle conversation selection
  const handleSelectConversation = useCallback(
    (id: string) => {
      selectConversation(id);
    },
    [selectConversation]
  );

  // Determine which messages to display
  const isHistoricalView = selectedConversationId !== null;

  // Build real-time message list (for live conversation)
  const realtimeMessages = [
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

  // Convert historical messages for display
  const displayMessages = isHistoricalView
    ? historicalMessages.map((msg) => ({
        key: msg.id,
        role: msg.role,
        text: msg.content,
        latency_ms:
          msg.role === "user"
            ? msg.stt_latency_ms ?? 0
            : msg.llm_latency_ms ?? 0,
        timestamp: new Date(msg.created_at).getTime(),
        ttft_ms: msg.role === "assistant" ? 0 : undefined,
      }))
    : realtimeMessages;

  return (
    <div className="flex flex-col h-screen bg-gray-50">
      {/* Header */}
      <header className="flex-shrink-0 bg-white border-b border-gray-200 px-4 py-3">
        <div className="flex items-center justify-between">
          <div className="flex items-center gap-4">
            {/* Mobile sidebar toggle */}
            <button
              onClick={() => setSidebarOpen(!sidebarOpen)}
              className="lg:hidden p-2 text-gray-600 hover:text-gray-800"
              aria-label="メニュー"
            >
              <svg className="w-6 h-6" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M4 6h16M4 12h16M4 18h16" />
              </svg>
            </button>
            <div>
              <h1 className="text-xl font-bold text-gray-800">Voice Assistant</h1>
              <p className="text-sm text-gray-500">日本語音声対話アシスタント</p>
            </div>
          </div>
          <div className="flex items-center gap-4">
            {/* Show mode indicator */}
            {isHistoricalView && (
              <span className="text-sm text-gray-500 bg-gray-100 px-2 py-1 rounded">
                履歴表示中
              </span>
            )}
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

      {/* Main content with sidebar */}
      <div className="flex-1 flex overflow-hidden">
        {/* Sidebar */}
        <aside
          className={`${
            sidebarOpen ? "w-64" : "w-0"
          } flex-shrink-0 transition-all duration-300 overflow-hidden lg:w-64`}
        >
          <ConversationList
            onSelect={handleSelectConversation}
            selectedId={selectedConversationId}
            onNewConversation={handleNewConversation}
          />
        </aside>

        {/* Chat Area */}
        <main className="flex-1 flex flex-col overflow-hidden relative">
          <div
            ref={chatAreaRef}
            onScroll={handleScroll}
            className="flex-1 overflow-y-auto px-4 py-6"
          >
            <div className="max-w-4xl mx-auto space-y-4">
              {/* Error Display */}
              {(lastError || conversationError) && (
                <div className="p-4 bg-red-50 border border-red-200 rounded-lg">
                  <p className="text-sm text-red-600">
                    {conversationError
                      ? `エラー: ${conversationError}`
                      : lastError
                      ? `エラー [${lastError.code}]: ${lastError.message}`
                      : null}
                  </p>
                </div>
              )}

              {/* Loading indicator for historical messages */}
              {isLoadingConversation && (
                <div className="flex items-center justify-center py-20">
                  <div className="animate-spin w-8 h-8 border-2 border-blue-500 border-t-transparent rounded-full" />
                </div>
              )}

              {/* Empty State */}
              {!isLoadingConversation &&
                displayMessages.length === 0 &&
                !partialText &&
                llmState === "idle" && (
                  <div className="flex flex-col items-center justify-center py-20 text-gray-400">
                    <svg
                      className="w-16 h-16 mb-4"
                      fill="none"
                      stroke="currentColor"
                      viewBox="0 0 24 24"
                    >
                      <path
                        strokeLinecap="round"
                        strokeLinejoin="round"
                        strokeWidth={1.5}
                        d="M19 11a7 7 0 01-7 7m0 0a7 7 0 01-7-7m7 7v4m0 0H8m4 0h4m-4-8a3 3 0 01-3-3V5a3 3 0 116 0v6a3 3 0 01-3 3z"
                      />
                    </svg>
                    <p className="text-lg">
                      {isHistoricalView
                        ? "この会話にはメッセージがありません"
                        : "マイクボタンを押して話しかけてください"}
                    </p>
                  </div>
                )}

              {/* Message Bubbles */}
              {!isLoadingConversation &&
                displayMessages.map((msg) => (
                  <div
                    key={msg.key}
                    className={`flex ${
                      msg.role === "user" ? "justify-end" : "justify-start"
                    }`}
                  >
                    <div
                      className={`max-w-[80%] rounded-2xl px-4 py-3 ${
                        msg.role === "user"
                          ? "bg-blue-500 text-white"
                          : "bg-white border border-gray-200 text-gray-800"
                      }`}
                    >
                      <p className="whitespace-pre-wrap">{msg.text}</p>
                      <p
                        className={`text-xs mt-2 ${
                          msg.role === "user" ? "text-blue-100" : "text-gray-400"
                        }`}
                      >
                        {msg.latency_ms > 0 && `${msg.latency_ms.toFixed(0)}ms`}
                        {msg.role === "assistant" &&
                          "ttft_ms" in msg &&
                          msg.ttft_ms !== undefined &&
                          msg.ttft_ms > 0 && (
                            <span> (TTFT: {msg.ttft_ms.toFixed(0)}ms)</span>
                          )}
                      </p>
                    </div>
                  </div>
                ))}

              {/* Partial STT Text (user is speaking) - only in live mode */}
              {!isHistoricalView && partialText && (
                <div className="flex justify-end">
                  <div className="max-w-[80%] rounded-2xl px-4 py-3 bg-blue-300 text-white opacity-80">
                    <p className="whitespace-pre-wrap italic">{partialText}</p>
                    <p className="text-xs mt-1 text-blue-100">認識中...</p>
                  </div>
                </div>
              )}

              {/* LLM Streaming Response - only in live mode */}
              {!isHistoricalView &&
                (llmState === "processing" || llmState === "streaming") && (
                  <div className="flex justify-start">
                    <div className="max-w-[80%] rounded-2xl px-4 py-3 bg-white border border-gray-200 text-gray-800">
                      {llmStreamingText ? (
                        <p className="whitespace-pre-wrap">{llmStreamingText}</p>
                      ) : (
                        <div className="flex items-center gap-1">
                          <span
                            className="w-2 h-2 bg-gray-400 rounded-full animate-bounce"
                            style={{ animationDelay: "0ms" }}
                          />
                          <span
                            className="w-2 h-2 bg-gray-400 rounded-full animate-bounce"
                            style={{ animationDelay: "150ms" }}
                          />
                          <span
                            className="w-2 h-2 bg-gray-400 rounded-full animate-bounce"
                            style={{ animationDelay: "300ms" }}
                          />
                        </div>
                      )}
                      <p className="text-xs mt-2 text-gray-400">
                        {llmState === "processing" ? "考え中..." : "応答中..."}
                      </p>
                    </div>
                  </div>
                )}
            </div>
          </div>

          {/* Scroll to Bottom Button */}
          {!isUserAtBottom && displayMessages.length > 0 && (
            <button
              onClick={scrollToBottom}
              className="absolute bottom-24 right-6 w-10 h-10 bg-blue-500 text-white rounded-full shadow-lg hover:bg-blue-600 transition-colors flex items-center justify-center z-10"
              aria-label="最新メッセージへスクロール"
            >
              <svg
                className="w-5 h-5"
                fill="none"
                stroke="currentColor"
                viewBox="0 0 24 24"
              >
                <path
                  strokeLinecap="round"
                  strokeLinejoin="round"
                  strokeWidth={2}
                  d="M19 14l-7 7m0 0l-7-7m7 7V3"
                />
              </svg>
            </button>
          )}

          {/* Footer */}
          <footer className="flex-shrink-0 bg-white border-t border-gray-200 px-4 py-4">
            <div className="max-w-4xl mx-auto flex flex-col items-center gap-2">
              {/* Historical view return button */}
              {isHistoricalView && (
                <button
                  onClick={handleNewConversation}
                  className="mb-2 px-4 py-2 text-sm text-blue-500 bg-blue-50 rounded-lg hover:bg-blue-100 transition-colors"
                >
                  新規会話を開始
                </button>
              )}

              {/* TTS Playing Indicator */}
              {ttsState === "playing" && (
                <div className="flex items-center gap-3 text-sm text-gray-600 mb-2">
                  <div className="flex items-center gap-1">
                    <span
                      className="w-1.5 h-1.5 bg-blue-500 rounded-full animate-bounce"
                      style={{ animationDelay: "0ms" }}
                    />
                    <span
                      className="w-1.5 h-1.5 bg-blue-500 rounded-full animate-bounce"
                      style={{ animationDelay: "150ms" }}
                    />
                    <span
                      className="w-1.5 h-1.5 bg-blue-500 rounded-full animate-bounce"
                      style={{ animationDelay: "300ms" }}
                    />
                  </div>
                  <span>音声再生中</span>
                  <button
                    onClick={stopTts}
                    className="px-2 py-0.5 text-xs bg-gray-200 hover:bg-gray-300 rounded transition-colors"
                  >
                    停止
                  </button>
                  {ttsLatencyMs !== null && (
                    <span className="text-xs text-gray-400">
                      ({ttsLatencyMs.toFixed(0)}ms)
                    </span>
                  )}
                </div>
              )}

              {/* Mic Button - disabled in historical view */}
              <VoiceInput disabled={isHistoricalView} />
            </div>
          </footer>
        </main>
      </div>
    </div>
  );
}
