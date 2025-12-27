# Story 3.1: 会話履歴スクロール表示

Status: done

## Story

As a **ユーザー**,
I want **会話履歴をスクロールして閲覧できる**,
so that **過去のやり取りを確認できる** (FR14).

## Acceptance Criteria

1. **Given** 複数のメッセージが存在する
   **When** チャット画面をスクロールする
   **Then** 過去のメッセージが表示される

2. **And** 新しいメッセージ受信時に自動スクロールする

3. **And** 手動スクロール中は自動スクロールを停止する

4. **And** スクロール位置が適切に維持される

## Tasks / Subtasks

- [x] Task 1: スマートスクロール制御の実装 (AC: #2, #3, #4)
  - [x] ユーザーがスクロール位置を変更したかを検出（scroll event）
  - [x] 「ユーザーが下部にいるか」を追跡する状態を追加
  - [x] 自動スクロールはユーザーが下部にいる場合のみ実行

- [x] Task 2: 「下へスクロール」ボタンの実装 (AC: #3, #4)
  - [x] ユーザーが上にスクロールした場合にボタンを表示
  - [x] ボタンクリックで最新メッセージへスクロール
  - [x] 新着メッセージ数のバッジ表示（オプション） - スキップ（MVP外）

- [x] Task 3: スクロール位置の保持改善 (AC: #4)
  - [x] コンポーネント再レンダリング時のスクロール位置維持
  - [x] ウィンドウリサイズ時の適切なスクロール処理

- [x] Task 4: テストとビルド確認 (AC: #1-4)
  - [x] npm run lint 確認
  - [x] npm run build 確認
  - [x] 手動テスト：スクロール動作確認

### Review Follow-ups (AI)

- [ ] [AI-Review][MED] Set up frontend test framework (Jest/Vitest + React Testing Library) and add unit tests for scroll logic [frontend/]

## Dev Notes

### アーキテクチャ準拠事項

**既存実装の活用:**
- Story 2.7で構築されたChatGPTライクなレイアウト
- `page.tsx` の chatAreaRef による基本スクロール制御
- Zustand storeでの状態管理パターン

**変更範囲:**
- `frontend/src/app/page.tsx` - スクロール制御ロジック追加
- `frontend/src/hooks/use-scroll.ts` - スクロール制御用カスタムフック（新規）

### 技術仕様

**スマートスクロール実装方針:**

```typescript
// スクロール位置の追跡
const isNearBottom = (element: HTMLElement, threshold = 100) => {
  return element.scrollHeight - element.scrollTop - element.clientHeight < threshold;
};

// スクロールイベントハンドラ
const handleScroll = (e: React.UIEvent<HTMLDivElement>) => {
  const element = e.currentTarget;
  setIsUserAtBottom(isNearBottom(element));
};

// 自動スクロール（条件付き）
useEffect(() => {
  if (isUserAtBottom && chatAreaRef.current) {
    chatAreaRef.current.scrollTop = chatAreaRef.current.scrollHeight;
  }
}, [messages, isUserAtBottom]);
```

**「下へスクロール」ボタン:**

```typescript
// ボタン表示条件
{!isUserAtBottom && messages.length > 0 && (
  <button
    onClick={scrollToBottom}
    className="fixed bottom-24 right-6 w-10 h-10 bg-blue-500 text-white rounded-full shadow-lg"
  >
    ↓
  </button>
)}
```

### Previous Story Learnings

**Story 2.7 から:**
- 3セクションレイアウト（header/main/footer）が確立
- `chatAreaRef` で chat area への参照を保持
- 現在の自動スクロールは単純な `scrollTop = scrollHeight` 実装
- メッセージは `sttResults` と `llmResults` から構築

**現在のスクロール実装（page.tsx:26-30）:**
```typescript
useEffect(() => {
  if (chatAreaRef.current) {
    chatAreaRef.current.scrollTop = chatAreaRef.current.scrollHeight;
  }
}, [sttResults, llmResults, llmStreamingText, partialText]);
```

問題点: ユーザーが過去のメッセージを読んでいても強制的に下へスクロールしてしまう

### ディレクトリ構造

```
frontend/
└── src/
    ├── app/
    │   └── page.tsx           # ← スクロール制御ロジック追加
    └── hooks/
        └── use-scroll.ts      # ← 新規作成（オプション）
```

### テスト基準

1. 過去のメッセージをスクロールして閲覧できる
2. 新しいメッセージ到着時、下部にいる場合のみ自動スクロール
3. ユーザーが上にスクロールしている間は自動スクロールしない
4. 「下へスクロール」ボタンが適切に表示/非表示される
5. npm run lint / npm run build が成功する

### NFR考慮事項

**パフォーマンス (NFR-P5):**
- スクロールイベントのデバウンス/スロットリング考慮
- 不要な再レンダリングを防ぐ

**UI/UX:**
- スムーズなスクロールアニメーション
- ボタンの視認性とアクセシビリティ

### 実装例（参考）

**ChatGPTスタイルのスクロール挙動:**
1. ユーザーが下部にいる → 新しいメッセージで自動スクロール
2. ユーザーが上にスクロール → 自動スクロール停止
3. 下へスクロールボタン表示 → クリックで最下部へ

### References

- [Source: _bmad-output/architecture.md#フロントエンド設計]
- [Source: _bmad-output/project-planning-artifacts/epics.md#Story-3.1]
- [Source: frontend/src/app/page.tsx - 現在のスクロール実装]

## Dev Agent Record

### Agent Model Used

claude-opus-4-5-20251101

### Debug Log References

N/A - No debug issues encountered

### Completion Notes List

- **Task 1:** Implemented smart scroll control with `isUserAtBottom` state tracking and `isNearBottom()` helper function with 100px threshold. Added `handleScroll` event handler to detect user scroll position changes. Modified auto-scroll useEffect to only scroll when user is at bottom.

- **Task 2:** Added floating scroll-to-bottom button that appears when user scrolls up. Button positioned at `fixed bottom-24 right-6` with blue styling matching the app theme. Includes accessibility label and SVG arrow icon.

- **Task 3:** Added window resize handler to recalculate scroll position on resize. Uses `isNearBottom()` check after resize and maintains bottom position if user was already at bottom.

- **Task 4:** npm run lint passed with no errors. npm run build passed successfully. All 71 backend tests pass (no regressions).

**Implementation approach:** All scroll logic kept in `page.tsx` rather than creating a separate hook file, as the complexity didn't warrant extraction. Used `useCallback` for memoized functions to prevent unnecessary re-renders.

### File List

- `frontend/src/app/page.tsx` (modified) - Added smart scroll control, scroll-to-bottom button, and resize handler
- `_bmad-output/implementation-artifacts/sprint-status.yaml` (modified) - Story status tracking

## Change Log

- 2025-12-27: Story 3.1 implementation complete - Smart scroll control with conditional auto-scroll, scroll-to-bottom button, and resize handling
- 2025-12-27: Code review fixes applied - Added scroll throttling (100ms), smooth scroll animation, initial mount position check

## Senior Developer Review (AI)

**Date:** 2025-12-27
**Reviewer:** claude-opus-4-5-20251101
**Outcome:** Approve (with follow-up)

### Review Summary

All Acceptance Criteria implemented and verified. Code quality issues identified and fixed during review.

### Issues Found and Resolved

| Severity | Issue | Status |
|----------|-------|--------|
| MED | Missing scroll event throttling (NFR-P5) | ✅ Fixed |
| MED | Missing smooth scroll animation | ✅ Fixed |
| MED | Initial scroll state may be incorrect on mount | ✅ Fixed |
| MED | No frontend unit tests | ⏳ Action item created |
| LOW | Story File List incomplete | ✅ Fixed |

### Action Items

- [ ] [MED] Set up frontend test framework and add scroll logic tests
