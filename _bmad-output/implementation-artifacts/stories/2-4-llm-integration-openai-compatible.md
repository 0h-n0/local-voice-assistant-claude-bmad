# Story 2.4: LLM統合（OpenAI互換）

Status: done

## Story

As a **ユーザー**,
I want **認識されたテキストに対してLLMが応答する**,
so that **AIとの対話ができる** (FR5, FR6, FR7).

## Acceptance Criteria

1. **Given** `stt.final`で認識テキストが確定した
   **When** Backend側でOpenAI互換APIにリクエストする
   **Then** `llm.start`イベントが送信される

2. **And** LLM応答がストリーミングで`llm.delta`として送信される

3. **And** 応答完了時に`llm.end`（レイテンシ付き）が送信される

4. **And** 会話コンテキスト（直近のやり取り）が維持される

5. **And** Frontendで応答テキストがリアルタイム表示される

## Tasks / Subtasks

- [x] Task 1: OpenAI Python SDK インストールと依存関係設定 (AC: #1)
  - [x] `backend/pyproject.toml` に `openai` パッケージ追加
  - [x] `httpx` パッケージ追加（非同期HTTPクライアント）
  - [x] 環境変数/設定ファイルでAPIキー・ベースURL管理

- [x] Task 2: LLMサービス層実装 (AC: #1, #2, #3, #4)
  - [x] `backend/src/voice_assistant/llm/base.py` LLM抽象基底クラス
  - [x] `backend/src/voice_assistant/llm/openai_compat.py` OpenAI互換実装
  - [x] ストリーミング対応（async generator）
  - [x] 会話コンテキスト管理（直近N件のメッセージ保持）
  - [x] レイテンシ計測（TTFT + 総時間）

- [x] Task 3: WebSocketイベント送信実装 (AC: #1, #2, #3)
  - [x] `backend/src/voice_assistant/api/websocket.py` 更新
  - [x] `stt.final` 受信後にLLM処理を開始
  - [x] `llm.start` イベント送信
  - [x] `llm.delta` イベント送信（トークン単位）
  - [x] `llm.end` イベント送信（latency_ms, ttft_ms）

- [x] Task 4: Frontendイベント受信処理 (AC: #5)
  - [x] `frontend/src/core/events.ts` LLMイベント型追加
  - [x] `frontend/src/stores/voice-store.ts` LLM応答状態管理
  - [x] `frontend/src/app/page.tsx` リアルタイムテキスト表示

- [x] Task 5: 統合テスト (AC: #1-5)
  - [x] pytest LLMサービステスト（モック使用）
  - [x] WebSocket統合テスト（LLMイベントフロー）
  - [x] E2E動作確認（実際のLLM APIを使用）

## Dev Notes

### アーキテクチャ準拠事項

**WebSocketイベント契約（Architecture.md準拠）:**

```
Server → Client:
- llm.start     # LLM処理開始
- llm.delta     # LLMトークン（ストリーミング）
- llm.end       # LLM完了（latency_ms, ttft_ms）
```

**イベントペイロード設計:**

```typescript
// Server → Client Events
export interface LlmStartEvent {
  type: 'llm.start';
}

export interface LlmDeltaEvent {
  type: 'llm.delta';
  text: string;  // トークン単位のテキスト
}

export interface LlmEndEvent {
  type: 'llm.end';
  latency_ms: number;   // 総処理時間
  ttft_ms: number;      // Time To First Token
}
```

**状態機械遷移（Architecture.md準拠）:**

```
IDLE → RECORDING → STT → LLM → TTS → IDLE
                          ↑
                    このStoryで実装
```

### 技術仕様

**OpenAI Python SDK（v1.x）:**
- 公式SDK: `openai>=1.0.0`
- 非同期クライアント: `AsyncOpenAI`
- ストリーミング: `stream=True` で `AsyncIterator[ChatCompletionChunk]`
- 自動リトライ: 429, 500+ エラーは2回まで自動リトライ

**OpenAI互換API対応:**
- Ollama: `base_url="http://localhost:11434/v1"`
- Groq: `base_url="https://api.groq.com/openai/v1"`
- OpenAI: デフォルト

**ストリーミングコード例:**

```python
from openai import AsyncOpenAI

client = AsyncOpenAI(
    api_key=api_key,
    base_url=base_url,  # OpenAI互換エンドポイント
)

async def stream_completion(messages: list[dict]) -> AsyncIterator[str]:
    stream = await client.chat.completions.create(
        model=model,
        messages=messages,
        stream=True,
    )
    async for chunk in stream:
        if chunk.choices[0].delta.content:
            yield chunk.choices[0].delta.content
```

**会話コンテキスト管理:**

```python
class ConversationContext:
    def __init__(self, max_messages: int = 10):
        self.messages: list[dict] = []
        self.max_messages = max_messages

    def add_user_message(self, text: str) -> None:
        self.messages.append({"role": "user", "content": text})
        self._trim()

    def add_assistant_message(self, text: str) -> None:
        self.messages.append({"role": "assistant", "content": text})
        self._trim()

    def get_messages(self) -> list[dict]:
        return [
            {"role": "system", "content": "あなたは親切な日本語アシスタントです。"},
            *self.messages
        ]

    def _trim(self) -> None:
        if len(self.messages) > self.max_messages:
            self.messages = self.messages[-self.max_messages:]
```

### LLMサービス実装

**base.py:**

```python
from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import AsyncIterator

@dataclass
class LLMResponse:
    text: str
    latency_ms: float
    ttft_ms: float  # Time To First Token

class BaseLLM(ABC):
    @abstractmethod
    async def stream_completion(
        self,
        messages: list[dict],
    ) -> AsyncIterator[str]:
        """Stream completion tokens."""
        pass
```

**openai_compat.py:**

```python
import time
from openai import AsyncOpenAI
from voice_assistant.llm.base import BaseLLM
from voice_assistant.core.logging import get_logger

logger = get_logger(__name__)

class OpenAICompatLLM(BaseLLM):
    def __init__(
        self,
        api_key: str | None = None,
        base_url: str | None = None,
        model: str = "gpt-4o-mini",
    ):
        self.client = AsyncOpenAI(
            api_key=api_key or "ollama",  # Ollama doesn't need real key
            base_url=base_url,
        )
        self.model = model

    async def stream_completion(
        self,
        messages: list[dict],
    ) -> AsyncIterator[str]:
        logger.info("llm_stream_start", model=self.model, message_count=len(messages))

        stream = await self.client.chat.completions.create(
            model=self.model,
            messages=messages,
            stream=True,
        )

        async for chunk in stream:
            content = chunk.choices[0].delta.content
            if content:
                yield content
```

### WebSocket統合

**websocket.py 更新:**

```python
async def handle_stt_final(
    websocket: WebSocket,
    text: str,
    llm_service: OpenAICompatLLM,
    context: ConversationContext,
) -> None:
    # Add user message to context
    context.add_user_message(text)

    # Send llm.start
    await websocket.send_json({"type": "llm.start"})

    start_time = time.perf_counter()
    ttft: float | None = None
    full_response = ""

    async for token in llm_service.stream_completion(context.get_messages()):
        if ttft is None:
            ttft = (time.perf_counter() - start_time) * 1000

        full_response += token
        await websocket.send_json({
            "type": "llm.delta",
            "text": token,
        })

    latency_ms = (time.perf_counter() - start_time) * 1000

    # Add assistant response to context
    context.add_assistant_message(full_response)

    # Send llm.end
    await websocket.send_json({
        "type": "llm.end",
        "latency_ms": round(latency_ms, 2),
        "ttft_ms": round(ttft or 0, 2),
    })

    logger.info(
        "llm_completed",
        response_length=len(full_response),
        latency_ms=round(latency_ms, 2),
        ttft_ms=round(ttft or 0, 2),
    )
```

### Frontend実装

**events.ts 追加:**

```typescript
export interface LlmStartEvent {
  type: 'llm.start';
}

export interface LlmDeltaEvent {
  type: 'llm.delta';
  text: string;
}

export interface LlmEndEvent {
  type: 'llm.end';
  latency_ms: number;
  ttft_ms: number;
}

export type ServerEvent =
  | SttPartialEvent
  | SttFinalEvent
  | LlmStartEvent
  | LlmDeltaEvent
  | LlmEndEvent
  | ErrorEvent;
```

**voice-store.ts 追加:**

```typescript
interface VoiceState {
  // ... existing state
  llmResponse: string;       // 累積LLM応答テキスト
  isLlmStreaming: boolean;   // LLMストリーミング中フラグ
  llmLatency: number | null; // 最終LLMレイテンシ
}

// Reducer cases
case 'llm.start':
  set({ llmResponse: '', isLlmStreaming: true });
  break;

case 'llm.delta':
  set((state) => ({
    llmResponse: state.llmResponse + event.text,
  }));
  break;

case 'llm.end':
  set({
    isLlmStreaming: false,
    llmLatency: event.latency_ms,
  });
  break;
```

### ディレクトリ構造

```
backend/
├── src/voice_assistant/
│   ├── llm/                        # ← 新規作成
│   │   ├── __init__.py
│   │   ├── base.py                 # LLM抽象基底クラス
│   │   └── openai_compat.py        # OpenAI互換クライアント
│   └── api/
│       └── websocket.py            # ← 更新（LLM統合）

frontend/
├── src/
│   ├── core/
│   │   └── events.ts               # ← 更新（LLMイベント型）
│   ├── stores/
│   │   └── voice-store.ts          # ← 更新（llmResponse, isLlmStreaming）
│   └── app/
│       └── page.tsx                # ← 更新（LLM応答表示）
```

### 環境変数/設定

```yaml
# config/config.yaml
llm:
  provider: "ollama"  # ollama | openai | groq
  model: "llama3.2"   # or "gpt-4o-mini", "llama-3.1-70b-versatile"
  base_url: "http://localhost:11434/v1"  # Ollama default
  api_key: ""  # OpenAI/Groq requires key
  max_context_messages: 10
```

```python
# Environment variable fallbacks
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY", "")
OPENAI_BASE_URL = os.getenv("OPENAI_BASE_URL", "http://localhost:11434/v1")
LLM_MODEL = os.getenv("LLM_MODEL", "llama3.2")
```

### 命名規則（Architecture準拠）

| 対象 | パターン | 例 |
|------|---------|-----|
| サービスクラス | PascalCase + 種別 | `OpenAICompatLLM` |
| データクラス | PascalCase | `LLMResponse` |
| イベント型 | PascalCase + Event | `LlmDeltaEvent` |
| モジュール | snake_case | `openai_compat.py` |

### 依存関係

**前提条件:**
- Story 2.3 完了（STT統合）
- `stt.final` イベントで認識テキスト受信
- WebSocket双方向通信が機能

**後続Story:**
- Story 2.5 (TTS統合) - `llm.delta` のテキストをTTSに送信
- Story 2.6 (E2Eパイプライン) - 全フローの統合

### Previous Story Learnings

**Story 2.3 から:**
- サービス層の抽象基底クラスパターン（BaseSTT）→ BaseLLM に適用
- asyncio.to_thread for blocking operations（LLMはAsyncOpenAIで不要）
- スレッドセーフなサービス初期化（threading.Lock + double-check locking）
- WebSocket JSON送信パターン: `websocket.send_json({"type": "...", ...})`
- レイテンシ計測: `time.perf_counter()` でミリ秒精度

**Story 2.2 から:**
- Zustand ストア更新パターン
- イベントタイプの Union 型定義
- parseServerEvent() でイベントパース

**Story 2.1 から:**
- structlog で構造化ログ出力
- WebSocket接続状態管理

### テスト基準

1. LLMサービスがOpenAI互換APIにリクエストできる
2. ストリーミングでトークンが順次返される
3. `llm.start` → `llm.delta`(複数) → `llm.end` のイベント順序
4. `llm.end` に `latency_ms` と `ttft_ms` が含まれる
5. 会話コンテキストが維持される（直近10件）
6. Frontendでリアルタイムにテキストが表示される
7. Ollama/OpenAI/Groq の切り替えが設定で可能

### NFR考慮事項

**パフォーマンス (NFR-P2):**
- 目標: TTFT < 1000ms
- 計測: time.perf_counter() でTTFTと総時間を記録
- ストリーミングで体感レイテンシを低減

**信頼性 (NFR-R3):**
- エラー時はerrorイベントでユーザーに通知
- 接続エラーは自動リトライ（SDK組み込み）

**ロギング (NFR-M2):**
- structlog で `llm_completed` イベント
- response_length, latency_ms, ttft_ms を記録

### エラーハンドリング

```python
from openai import APIError, RateLimitError, AuthenticationError

async def safe_stream_completion(
    websocket: WebSocket,
    llm_service: OpenAICompatLLM,
    messages: list[dict],
) -> None:
    try:
        async for token in llm_service.stream_completion(messages):
            await websocket.send_json({"type": "llm.delta", "text": token})
    except RateLimitError:
        await websocket.send_json({
            "type": "error",
            "code": "LLM_RATE_LIMIT",
            "message": "APIレート制限に達しました。しばらく待ってから再試行してください。",
        })
    except AuthenticationError:
        await websocket.send_json({
            "type": "error",
            "code": "LLM_AUTH_ERROR",
            "message": "LLM APIの認証に失敗しました。APIキーを確認してください。",
        })
    except APIError as e:
        await websocket.send_json({
            "type": "error",
            "code": "LLM_API_ERROR",
            "message": f"LLM APIエラー: {str(e)}",
        })
```

### 追加インストール

**Backend:**
```bash
cd backend
uv add openai httpx
```

**Ollama セットアップ（開発用）:**
```bash
# Ollama インストール
curl -fsSL https://ollama.com/install.sh | sh

# 日本語対応モデル取得
ollama pull llama3.2
# または
ollama pull qwen2.5:7b
```

### References

- [Source: _bmad-output/architecture.md#WebSocketイベント契約]
- [Source: _bmad-output/architecture.md#API-Communication-Patterns]
- [Source: _bmad-output/architecture.md#Project-Structure]
- [Source: _bmad-output/project-planning-artifacts/epics.md#Story-2.4]
- [OpenAI Python SDK - GitHub](https://github.com/openai/openai-python)
- [OpenAI Streaming API Guide](https://platform.openai.com/docs/guides/streaming-responses)
- [Chat Completions API Reference](https://platform.openai.com/docs/api-reference/chat/)

## Dev Agent Record

### Agent Model Used

Claude Opus 4.5 (claude-opus-4-5-20251101)

### Debug Log References

- All 47 backend tests passing
- Frontend lint and build successful

### Completion Notes List

1. Implemented OpenAI-compatible LLM client with streaming support
2. Added ConversationContext for maintaining chat history (max 10 messages)
3. Integrated LLM processing into WebSocket flow after STT
4. Added comprehensive error handling for OpenAI API errors
5. Updated frontend to display conversation with streaming LLM responses
6. All acceptance criteria verified through integration tests

### File List

**Backend (New):**
- `backend/src/voice_assistant/llm/__init__.py` - Module exports
- `backend/src/voice_assistant/llm/base.py` - ConversationContext, BaseLLM
- `backend/src/voice_assistant/llm/openai_compat.py` - OpenAICompatLLM
- `backend/tests/unit/test_llm.py` - 12 unit tests

**Backend (Modified):**
- `backend/pyproject.toml` - Added openai, httpx dependencies
- `backend/src/voice_assistant/api/websocket.py` - LLM integration
- `backend/tests/integration/test_websocket.py` - 4 new LLM tests

**Frontend (Modified):**
- `frontend/src/core/events.ts` - LLM event types
- `frontend/src/stores/voice-store.ts` - LLM state management
- `frontend/src/app/page.tsx` - Conversation display

