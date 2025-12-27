"use client";

import { useState, useCallback, useRef, useEffect } from "react";
import { useQueryClient } from "@tanstack/react-query";
import { useConversationList } from "@/hooks/use-conversations";
import { deleteConversation } from "@/lib/api-client";

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
  const queryClient = useQueryClient();

  // Delete confirmation state
  const [deleteTarget, setDeleteTarget] = useState<{
    id: string;
    title: string | null;
  } | null>(null);
  const [isDeleting, setIsDeleting] = useState(false);
  const [deleteError, setDeleteError] = useState<string | null>(null);

  // Dialog focus management
  const cancelButtonRef = useRef<HTMLButtonElement>(null);

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

  // Focus cancel button when dialog opens
  useEffect(() => {
    if (deleteTarget && cancelButtonRef.current) {
      cancelButtonRef.current.focus();
    }
  }, [deleteTarget]);

  // Handle delete button click (show confirmation)
  const handleDeleteClick = useCallback(
    (e: React.MouseEvent, id: string, title: string | null) => {
      e.stopPropagation(); // Prevent selecting the conversation
      setDeleteError(null); // Clear previous error
      setDeleteTarget({ id, title });
    },
    []
  );

  // Handle delete confirmation
  const handleConfirmDelete = useCallback(async () => {
    if (!deleteTarget) return;

    setIsDeleting(true);
    setDeleteError(null);
    try {
      await deleteConversation(deleteTarget.id);
      // Invalidate cache to refresh list
      queryClient.invalidateQueries({ queryKey: ["conversations", "list"] });
      // If deleted conversation was selected, clear selection
      if (selectedId === deleteTarget.id) {
        onNewConversation();
      }
      setDeleteTarget(null);
    } catch (err) {
      const message =
        err instanceof Error ? err.message : "削除に失敗しました";
      setDeleteError(message);
      // Keep dialog open to show error
    } finally {
      setIsDeleting(false);
    }
  }, [deleteTarget, queryClient, selectedId, onNewConversation]);

  // Handle cancel delete
  const handleCancelDelete = useCallback(() => {
    setDeleteTarget(null);
  }, []);

  // Handle keyboard for dialog
  const handleDialogKeyDown = useCallback(
    (e: React.KeyboardEvent) => {
      if (e.key === "Escape") {
        handleCancelDelete();
      }
    },
    [handleCancelDelete]
  );

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
              <li key={conv.id} className="group relative">
                <button
                  onClick={() => onSelect(conv.id)}
                  className={`w-full px-4 py-3 text-left hover:bg-gray-50 transition-colors pr-10 ${
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
                {/* Delete button - visible on hover */}
                <button
                  onClick={(e) => handleDeleteClick(e, conv.id, conv.title)}
                  className="absolute right-2 top-1/2 -translate-y-1/2 p-1.5 text-gray-400 hover:text-red-500 opacity-0 group-hover:opacity-100 transition-opacity rounded hover:bg-red-50"
                  aria-label="会話を削除"
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
                      d="M19 7l-.867 12.142A2 2 0 0116.138 21H7.862a2 2 0 01-1.995-1.858L5 7m5 4v6m4-6v6m1-10V4a1 1 0 00-1-1h-4a1 1 0 00-1 1v3M4 7h16"
                    />
                  </svg>
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

      {/* Delete Confirmation Dialog */}
      {deleteTarget && (
        <div
          className="fixed inset-0 bg-black/50 flex items-center justify-center z-50"
          onClick={handleCancelDelete}
          onKeyDown={handleDialogKeyDown}
          role="dialog"
          aria-modal="true"
          aria-labelledby="delete-dialog-title"
        >
          <div
            className="bg-white rounded-lg shadow-xl p-6 max-w-sm mx-4"
            onClick={(e) => e.stopPropagation()}
          >
            <h2
              id="delete-dialog-title"
              className="text-lg font-semibold text-gray-800 mb-2"
            >
              会話を削除しますか？
            </h2>
            <p className="text-sm text-gray-600 mb-4">
              「{deleteTarget.title || "無題の会話"}」を削除します。
              <br />
              この操作は取り消せません。
            </p>
            {deleteError && (
              <p className="text-sm text-red-500 mb-4">{deleteError}</p>
            )}
            <div className="flex justify-end gap-3">
              <button
                ref={cancelButtonRef}
                onClick={handleCancelDelete}
                disabled={isDeleting}
                className="px-4 py-2 text-sm text-gray-600 hover:text-gray-800 transition-colors disabled:opacity-50"
              >
                キャンセル
              </button>
              <button
                onClick={handleConfirmDelete}
                disabled={isDeleting}
                className="px-4 py-2 text-sm text-white bg-red-500 rounded-lg hover:bg-red-600 transition-colors disabled:opacity-50 flex items-center gap-2"
              >
                {isDeleting && (
                  <div className="animate-spin w-4 h-4 border-2 border-white border-t-transparent rounded-full" />
                )}
                削除する
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}
