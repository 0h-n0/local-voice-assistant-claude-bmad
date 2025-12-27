# Story 3.5: 会話履歴削除

Status: done

## Story

As a **ユーザー**,
I want **会話履歴を削除できる**,
so that **不要な履歴を整理できる** (FR18).

## Acceptance Criteria

1. **Given** 会話一覧が表示されている
   **When** 削除ボタンをクリックする
   **Then** 確認ダイアログが表示される

2. **And** 確認後、`DELETE /api/v1/conversations/{id}`が呼び出される

3. **And** 会話と関連メッセージがDBから削除される

4. **And** UI上から会話が消える

## Tasks / Subtasks

- [x] Task 1: Backend DELETE APIエンドポイント追加 (AC: #2, #3)
  - [x] `DELETE /api/v1/conversations/{id}` エンドポイント作成
  - [x] 404エラーハンドリング
  - [x] 統合テスト追加

- [x] Task 2: Frontend API クライアント拡張 (AC: #2)
  - [x] `api-client.ts` に `deleteConversation(id)` 追加
  - [x] エラーハンドリング

- [x] Task 3: 削除ボタンUI実装 (AC: #1, #4)
  - [x] `ConversationList.tsx` に削除ボタン追加
  - [x] ホバー時に表示するデザイン
  - [x] アクセシビリティ対応 (aria-label)

- [x] Task 4: 確認ダイアログ実装 (AC: #1)
  - [x] 確認モーダル/ダイアログ作成
  - [x] キャンセル/確認ボタン
  - [x] キーボード操作対応 (Escape でキャンセル)

- [x] Task 5: 削除処理とUI更新 (AC: #2, #4)
  - [x] 削除API呼び出し
  - [x] TanStack Query キャッシュ更新 (invalidateQueries)
  - [x] 選択中の会話が削除された場合のハンドリング
  - [x] 削除中のローディング状態

- [x] Task 6: ビルド確認 (AC: #1-4)
  - [x] npm run lint 合格
  - [x] npm run build 合格
  - [x] uv run pytest 合格

## Dev Notes

### 重要: Repository層は実装済み

**Story 3.2 で実装済みの削除メソッド:**

```python
# backend/src/voice_assistant/db/repository.py (lines 190-211)
def delete(self, conversation_id: str) -> bool:
    """Delete a conversation and all its messages."""
    conversation = self.get(conversation_id)
    if conversation is None:
        return False

    # Delete all messages first (cascade)
    statement = select(Message).where(Message.conversation_id == conversation_id)
    messages = self.session.exec(statement).all()
    for message in messages:
        self.session.delete(message)

    self.session.delete(conversation)
    self.session.commit()
    return True
```

### 新規APIエンドポイント

```python
# backend/src/voice_assistant/main.py に追加
@app.delete("/api/v1/conversations/{conversation_id}")
async def delete_conversation(conversation_id: str) -> dict:
    """Delete a conversation and all its messages."""
    with Session(engine) as session:
        repo = ConversationRepository(session)
        deleted = repo.delete(conversation_id)
        if not deleted:
            raise HTTPException(status_code=404, detail="Conversation not found")
        return {"deleted": True}
```

### Frontend API クライアント

```typescript
// frontend/src/lib/api-client.ts に追加
export async function deleteConversation(id: string): Promise<void> {
  const res = await fetch(`${API_BASE}/api/v1/conversations/${id}`, {
    method: "DELETE",
  });
  if (!res.ok) {
    if (res.status === 404) {
      throw new Error("Conversation not found");
    }
    throw new Error("Failed to delete conversation");
  }
}
```

### UI設計

**削除ボタン配置:**
```
┌────────────────────────────────────┐
│ 会話タイトル              [🗑️] │  ← ホバー時に表示
│ 3時間前                          │
└────────────────────────────────────┘
```

**確認ダイアログ:**
```
┌─────────────────────────────────────┐
│ 会話を削除しますか？                 │
│                                     │
│ この操作は取り消せません。           │
│                                     │
│     [キャンセル]  [削除する]        │
└─────────────────────────────────────┘
```

### 状態管理考慮事項

1. **選択中の会話が削除された場合:**
   - `clearSelection()` を呼び出してリアルタイムモードに戻る
   - または次の会話を自動選択

2. **削除中の状態:**
   - 削除ボタンを無効化
   - ローディングインジケーター表示

3. **キャッシュ更新:**
   - `queryClient.invalidateQueries({ queryKey: ["conversations", "list"] })`

### Previous Story Learnings

**Story 3.4 から:**
- TanStack Query の `invalidateQueries` でキャッシュ更新
- `useQueryClient()` でキャッシュアクセス
- `clearSelection()` で選択解除

**Story 3.3 から:**
- 一覧APIは `/api/v1/conversations?limit=20&offset=0`
- レスポンスは `{ data: [], meta: { total, limit, offset } }`

### テスト基準

1. 削除ボタンクリックで確認ダイアログが表示される
2. キャンセルで何も起きない
3. 確認で DELETE API が呼ばれる
4. 削除後、一覧から消える
5. 選択中の会話が削除されたらリアルタイムモードに戻る
6. 存在しない会話の削除は 404 エラー

### NFR考慮事項

**UX:**
- 誤削除防止のための確認ダイアログ
- 削除中はボタン無効化
- 削除後の即座のUI更新

**パフォーマンス:**
- Optimistic update は不要（確認ダイアログがあるため）
- キャッシュ無効化で最新データ取得

### References

- [Source: _bmad-output/architecture.md#API Design]
- [Source: backend/src/voice_assistant/db/repository.py#delete]
- [Source: frontend/src/lib/api-client.ts]
- [Source: frontend/src/components/ConversationList.tsx]

## Dev Agent Record

### Agent Model Used

Claude Opus 4.5 (claude-opus-4-5-20251101)

### Debug Log References

N/A

### Completion Notes List

- Backend DELETE endpoint added with 404 handling
- Frontend deleteConversation API client function
- Delete button with hover-visible design
- Confirmation dialog with keyboard support (Escape)
- Cache invalidation on delete
- Selected conversation clear on delete
- All tests passing (20 tests)

**Code Review Fixes:**
- Added deleteError state to show user-facing error messages
- Added dialog focus management (auto-focus cancel button on open)
- Error messages now displayed in dialog instead of console only

### File List

**Created:**
- `_bmad-output/implementation-artifacts/stories/3-5-conversation-history-delete.md`

**Modified:**
- `backend/src/voice_assistant/main.py` - Added DELETE endpoint
- `backend/tests/integration/test_conversation_api.py` - Added delete tests
- `frontend/src/lib/api-client.ts` - Added deleteConversation function
- `frontend/src/components/ConversationList.tsx` - Delete button and confirmation dialog
- `_bmad-output/implementation-artifacts/sprint-status.yaml` - Updated story status

## Change Log

- 2025-12-27: Story 3.5 created - Conversation history deletion implementation
- 2025-12-27: Implementation complete - All tasks done
