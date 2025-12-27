# Story 2.1: WebSocket基盤

Status: done

## Story

As a **システム**,
I want **Frontend/Backend間のWebSocket接続が確立できる**,
so that **リアルタイム双方向通信の基盤ができる** (FR27).

## Acceptance Criteria

1. **Given** Backend/Frontendが起動している
   **When** Frontendが`/api/v1/ws/chat`に接続する
   **Then** WebSocket接続が確立される

2. **And** Backend側で接続イベントがログ出力される

3. **And** Frontend側で接続状態が`connected`になる

4. **And** 接続断時にFrontendで`disconnected`状態になる

## Tasks / Subtasks

- [x] Task 1: Backend WebSocketエンドポイント実装 (AC: #1, #2)
  - [x] `backend/src/voice_assistant/api/websocket.py` 作成
  - [x] `GET /api/v1/ws/chat` WebSocketエンドポイント実装
  - [x] 接続時のstructlogログ出力
  - [x] 切断時のログ出力
  - [x] main.pyにルーター登録

- [x] Task 2: Frontend WebSocketクライアント実装 (AC: #1, #3, #4)
  - [x] `frontend/src/core/websocket-client.ts` 作成
  - [x] WebSocketManager クラス実装
  - [x] 接続状態管理（'disconnected' | 'connecting' | 'connected'）
  - [x] 接続・切断メソッド

- [x] Task 3: Frontend状態ストア実装 (AC: #3, #4)
  - [x] `frontend/src/stores/voice-store.ts` 作成
  - [x] Zustand ストア実装
  - [x] connectionState の管理
  - [x] WebSocketクライアントとの連携

- [x] Task 4: UIコンポーネント更新 (AC: #3, #4)
  - [x] `frontend/src/app/page.tsx` 更新
  - [x] 接続状態インジケーター表示
  - [x] 接続/切断ボタン

- [x] Task 5: 統合テスト (AC: #1-4)
  - [x] `make dev` で両サーバー起動
  - [x] ブラウザでWebSocket接続確認
  - [x] Backend ログで接続イベント確認
  - [x] 接続断（ブラウザ閉じる）でdisconnected確認
  - [x] pytest テスト作成

## Dev Notes

### アーキテクチャ準拠事項

**WebSocketイベント契約（Architecture.md準拠）:**

今回のStoryでは接続/切断のみ。後続Storyで以下イベントを追加：

```
Client → Server:
- vad.start       # 発話開始 (Story 2.2)
- vad.audio       # 音声チャンク (Story 2.2)
- vad.end         # 発話終了 (Story 2.2)
- cancel          # キャンセル (Story 2.6)

Server → Client:
- stt.partial     # 部分認識 (Story 2.3)
- stt.final       # 確定認識 (Story 2.3)
- llm.start       # LLM開始 (Story 2.4)
- llm.delta       # LLMトークン (Story 2.4)
- llm.end         # LLM完了 (Story 2.4)
- tts.chunk       # TTSチャンク (Story 2.5)
- tts.end         # TTS完了 (Story 2.5)
- error           # エラー
```

**ディレクトリ構造:**
```
backend/
├── src/voice_assistant/
│   ├── api/
│   │   ├── __init__.py
│   │   └── websocket.py      # ← 新規作成
│   └── main.py               # ← ルーター登録追加

frontend/
├── src/
│   ├── core/
│   │   └── websocket-client.ts  # ← 新規作成
│   ├── stores/
│   │   └── voice-store.ts       # ← 新規作成
│   └── app/
│       └── page.tsx             # ← 更新
```

### 技術仕様

**Backend WebSocket実装:**

```python
# backend/src/voice_assistant/api/websocket.py
from fastapi import APIRouter, WebSocket, WebSocketDisconnect
from voice_assistant.core.logging import get_logger

router = APIRouter()
logger = get_logger(__name__)

@router.websocket("/api/v1/ws/chat")
async def websocket_chat(websocket: WebSocket) -> None:
    await websocket.accept()
    logger.info("websocket_connected", client=str(websocket.client))

    try:
        while True:
            # 将来のイベント処理用ループ
            data = await websocket.receive_text()
            # イベント処理は後続Storyで実装
    except WebSocketDisconnect:
        logger.info("websocket_disconnected", client=str(websocket.client))
```

**main.py 更新:**

```python
from voice_assistant.api.websocket import router as ws_router

app.include_router(ws_router)
```

**Frontend WebSocketクライアント:**

```typescript
// frontend/src/core/websocket-client.ts
export type ConnectionState = 'disconnected' | 'connecting' | 'connected';

export interface WebSocketClientOptions {
  url: string;
  onStateChange: (state: ConnectionState) => void;
  onMessage?: (data: unknown) => void;
}

export class WebSocketClient {
  private ws: WebSocket | null = null;
  private options: WebSocketClientOptions;

  constructor(options: WebSocketClientOptions) {
    this.options = options;
  }

  connect(): void {
    if (this.ws?.readyState === WebSocket.OPEN) return;

    this.options.onStateChange('connecting');
    this.ws = new WebSocket(this.options.url);

    this.ws.onopen = () => {
      this.options.onStateChange('connected');
    };

    this.ws.onclose = () => {
      this.options.onStateChange('disconnected');
      this.ws = null;
    };

    this.ws.onerror = () => {
      this.options.onStateChange('disconnected');
    };

    this.ws.onmessage = (event) => {
      this.options.onMessage?.(JSON.parse(event.data));
    };
  }

  disconnect(): void {
    this.ws?.close();
    this.ws = null;
  }

  send(data: unknown): void {
    if (this.ws?.readyState === WebSocket.OPEN) {
      this.ws.send(JSON.stringify(data));
    }
  }
}
```

**Zustand ストア:**

```typescript
// frontend/src/stores/voice-store.ts
import { create } from 'zustand';
import { ConnectionState, WebSocketClient } from '@/core/websocket-client';

interface VoiceStore {
  connectionState: ConnectionState;
  wsClient: WebSocketClient | null;

  connect: () => void;
  disconnect: () => void;
  setConnectionState: (state: ConnectionState) => void;
}

export const useVoiceStore = create<VoiceStore>((set, get) => ({
  connectionState: 'disconnected',
  wsClient: null,

  setConnectionState: (state) => set({ connectionState: state }),

  connect: () => {
    const existing = get().wsClient;
    if (existing) return;

    const client = new WebSocketClient({
      url: 'ws://localhost:8000/api/v1/ws/chat',
      onStateChange: (state) => set({ connectionState: state }),
    });

    set({ wsClient: client });
    client.connect();
  },

  disconnect: () => {
    const client = get().wsClient;
    client?.disconnect();
    set({ wsClient: null, connectionState: 'disconnected' });
  },
}));
```

### 命名規則（Architecture準拠）

| 対象 | パターン | 例 |
|------|---------|-----|
| Backend WebSocketルーター | snake_case | `websocket_chat()` |
| Frontend クラス | PascalCase | `WebSocketClient` |
| Frontend ストア | camelCase + usePrefix | `useVoiceStore` |
| 状態型 | PascalCase | `ConnectionState` |

### 依存関係

**前提条件:**
- Epic 1 完了（Story 1.1〜1.4）
- `make dev` で Frontend/Backend 両方起動可能
- Backend CORS設定済み（`http://localhost:3000`許可）

**後続Story:**
- Story 2.2 (Frontend音声キャプチャとVAD) - WebSocket接続を利用
- Story 2.3〜2.5 (STT/LLM/TTS統合) - WebSocketイベント追加
- Story 2.6 (E2Eパイプライン) - 全イベント統合

### テスト基準

1. `make dev` で両サーバーが起動する
2. ブラウザで http://localhost:3000 を開くと接続状態が表示される
3. 「接続」ボタンクリックで `connectionState` が `connected` になる
4. Backend ログに `websocket_connected` が出力される
5. ブラウザを閉じると `websocket_disconnected` がログ出力される
6. 「切断」ボタンクリックで `connectionState` が `disconnected` になる

### 追加インストール

**Frontend:**
```bash
cd frontend && npm install zustand
```

### Previous Story Learnings

**Epic 1 全体から:**
- FastAPI + uvicorn で Backend 起動済み（localhost:8000）
- Next.js 16.1.1 + React 19.2.3 で Frontend 起動済み（localhost:3000）
- CORS設定で `http://localhost:3000` 許可済み
- structlog でログ出力済み（`get_logger()` 関数）
- `make dev` で並列起動確認済み

**Story 1.2 から:**
- `backend/src/voice_assistant/main.py` に FastAPI app 定義
- `backend/src/voice_assistant/core/logging.py` に `get_logger()` 関数
- CORS設定: `allow_methods=["GET", "POST", "PUT", "DELETE", "OPTIONS"]`
- lifespan context manager パターン

**Story 1.3 から:**
- `frontend/src/stores/index.ts` ディレクトリ準備済み
- `frontend/src/core/index.ts` ディレクトリ準備済み
- Tailwind CSS でスタイリング

### References

- [Source: _bmad-output/architecture.md#API-Communication-Patterns]
- [Source: _bmad-output/architecture.md#WebSocketイベント契約]
- [Source: _bmad-output/architecture.md#Frontend-Architecture]
- [Source: _bmad-output/architecture.md#Project-Structure]
- [Source: _bmad-output/project-planning-artifacts/epics.md#Story-2.1]

## Dev Agent Record

### Agent Model Used

Claude Opus 4.5 (claude-opus-4-5-20251101)

### Debug Log References

N/A

### Completion Notes List

- Task 1: Backend WebSocketエンドポイント作成完了 - `/api/v1/ws/chat`エンドポイント、structlogでwebsocket_connected/disconnectedログ出力
- Task 2: Frontend WebSocketクライアント作成完了 - WebSocketClientクラス（connect/disconnect/send）、ConnectionState型定義
- Task 3: Zustand ストア作成完了 - useVoiceStore（connectionState, connect, disconnect）
- Task 4: UIコンポーネント更新完了 - 接続状態インジケーター（緑/黄/赤）、接続/切断ボタン
- Task 5: 統合テスト完了 - pytest 7件合格（WebSocket接続/エコー/切断）、make dev起動確認

### File List

**Created:**
- `backend/src/voice_assistant/api/websocket.py`
- `backend/tests/integration/__init__.py`
- `backend/tests/integration/test_websocket.py` (moved from tests/)
- `frontend/src/core/websocket-client.ts`
- `frontend/src/stores/voice-store.ts`

**Modified:**
- `backend/src/voice_assistant/main.py` - WebSocketルーター登録追加
- `backend/src/voice_assistant/api/__init__.py` - ws_router export追加
- `frontend/src/app/page.tsx` - 接続状態UI追加
- `frontend/package.json` - zustand依存追加

### Code Review Fixes Applied

**High Severity (Fixed):**
- H1: Fixed onerror handler race condition in websocket-client.ts - removed redundant state change, let onclose handle cleanup
- H2: Made WebSocket URL configurable via NEXT_PUBLIC_API_HOST and NEXT_PUBLIC_API_PROTOCOL env vars
- H3: Added ws_router export to api/__init__.py for consistent module structure

**Medium Severity (Fixed):**
- M1: Strengthened WebSocket tests with 7 comprehensive test cases (JSON, Unicode, multiple messages, empty message)
- M3: Removed console.log from voice-store.ts, replaced with comment placeholder for future event handling
- M4: Moved test file to backend/tests/integration/ per architecture.md

**Low Severity (Noted):**
- L1: TypeDoc for exported types - deferred to future iteration

## Change Log

- 2025-12-27: Code review完了 - 6件のissue修正（H1-H3, M1, M3-M4）、Status: done
- 2025-12-27: Story 2.1 実装完了 - WebSocket基盤（全5タスク完了）
- 2025-12-27: Story 2.1 created via create-story workflow
