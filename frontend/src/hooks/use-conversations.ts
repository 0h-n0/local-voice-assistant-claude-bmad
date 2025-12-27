/**
 * TanStack Query hooks for conversation data fetching
 */

import { useQuery } from "@tanstack/react-query";
import {
  fetchConversations,
  type ConversationListResponse,
} from "@/lib/api-client";

/**
 * Hook to fetch paginated conversation list
 */
export function useConversationList(limit = 20, offset = 0) {
  return useQuery<ConversationListResponse>({
    queryKey: ["conversations", "list", limit, offset],
    queryFn: () => fetchConversations(limit, offset),
    staleTime: 30 * 1000, // 30 seconds
    refetchOnWindowFocus: true,
  });
}
