"use client";

import { useConversationList } from "@/hooks/use-conversations";

interface ConversationListProps {
  onSelect: (id: string) => void;
  selectedId: string | null;
  onNewConversation: () => void;
}

/**
 * Sidebar component displaying list of conversations
 */
export function ConversationList({
  onSelect,
  selectedId,
  onNewConversation,
}: ConversationListProps) {
  const { data, isLoading, isError, error, refetch } = useConversationList();

  // Format relative time for display
  const formatRelativeTime = (dateString: string): string => {
    const date = new Date(dateString);
    const now = new Date();
    const diffMs = now.getTime() - date.getTime();
    const diffMins = Math.floor(diffMs / 60000);
    const diffHours = Math.floor(diffMs / 3600000);
    const diffDays = Math.floor(diffMs / 86400000);

    if (diffMins < 1) return "たった今";
    if (diffMins < 60) return `${diffMins}分前`;
    if (diffHours < 24) return `${diffHours}時間前`;
    if (diffDays < 7) return `${diffDays}日前`;
    return date.toLocaleDateString("ja-JP");
  };

  return (
    <div className="flex flex-col h-full bg-gray-100 border-r border-gray-200">
      {/* Header */}
      <div className="flex-shrink-0 p-3 border-b border-gray-200 bg-white">
        <button
          onClick={onNewConversation}
          className="w-full px-4 py-2 text-sm font-medium text-white bg-blue-500 rounded-lg hover:bg-blue-600 transition-colors flex items-center justify-center gap-2"
        >
          <svg
            className="w-4 h-4"
            fill="none"
            stroke="currentColor"
            viewBox="0 0 24 24"
          >
            <path
              strokeLinecap="round"
              strokeLinejoin="round"
              strokeWidth={2}
              d="M12 4v16m8-8H4"
            />
          </svg>
          新規会話
        </button>
      </div>

      {/* List */}
      <div className="flex-1 overflow-y-auto">
        {isLoading && (
          <div className="flex items-center justify-center py-8">
            <div className="animate-spin w-6 h-6 border-2 border-blue-500 border-t-transparent rounded-full" />
          </div>
        )}

        {isError && (
          <div className="p-4 text-center">
            <p className="text-sm text-red-500 mb-2">
              {error instanceof Error ? error.message : "読み込みエラー"}
            </p>
            <button
              onClick={() => refetch()}
              className="px-3 py-1 text-sm text-blue-500 hover:text-blue-600"
            >
              再試行
            </button>
          </div>
        )}

        {data && data.data.length === 0 && (
          <div className="p-4 text-center text-gray-400 text-sm">
            会話履歴がありません
          </div>
        )}

        {data && data.data.length > 0 && (
          <ul className="divide-y divide-gray-200">
            {data.data.map((conv) => (
              <li key={conv.id}>
                <button
                  onClick={() => onSelect(conv.id)}
                  className={`w-full px-4 py-3 text-left hover:bg-gray-50 transition-colors ${
                    selectedId === conv.id
                      ? "bg-blue-50 border-l-4 border-blue-500"
                      : ""
                  }`}
                >
                  <p
                    className={`text-sm font-medium truncate ${
                      selectedId === conv.id ? "text-blue-700" : "text-gray-800"
                    }`}
                  >
                    {conv.title || "無題の会話"}
                  </p>
                  <p className="text-xs text-gray-400 mt-1">
                    {formatRelativeTime(conv.updated_at)}
                  </p>
                </button>
              </li>
            ))}
          </ul>
        )}
      </div>

      {/* Footer with count */}
      {data && (
        <div className="flex-shrink-0 p-2 border-t border-gray-200 bg-white text-center text-xs text-gray-400">
          {data.meta.total}件の会話
        </div>
      )}
    </div>
  );
}
