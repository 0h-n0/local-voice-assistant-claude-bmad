---
stepsCompleted: [1, 2, 3, 4, 5, 6, 7]
inputDocuments:
  - '_bmad-output/prd.md'
  - '_bmad-output/project-planning-artifacts/research/technical-voice-assistant-research-2025-12-26.md'
workflowType: 'architecture'
project_name: 'local-voice-assistant-claude-bmad'
user_name: 'y'
date: '2025-12-27'
hasProjectContext: false
---

# Architecture Decision Document

_This document builds collaboratively through step-by-step discovery. Sections are appended as we work through each architectural decision together._

## Project Context Analysis

### 要件概要

**Functional Requirements (32件):**

| カテゴリ | FR数 | アーキテクチャ上の含意 |
|---------|------|----------------------|
| 音声入力（STT） | 4 | フロントエンドVAD、バックエンドSTTエンジン統合 |
| LLM対話 | 4 | OpenAI API互換アダプター、プロバイダー切り替え機構 |
| 音声出力（TTS） | 3 | Style-BERT-VITS2 インプロセス統合 |
| Web UI | 4 | React/Next.jsコンポーネント、状態管理 |
| 会話履歴管理 | 3 | SQLiteデータ層、CRUD操作 |
| 設定管理 | 3 | 設定ファイル永続化、バリデーション |
| 評価・ログ | 5 | 構造化ログ、レイテンシ計測インフラ |
| リアルタイム通信 | 3 | WebSocketサーバー/クライアント |
| システム起動 | 3 | ヘルスチェック、プロセス管理 |

**Non-Functional Requirements:**

| カテゴリ | 主要NFR | アーキテクチャへの影響 |
|---------|---------|---------------------|
| Performance | E2E < 2秒（GPU環境）、CPU環境は超過許容 | 非同期処理、ストリーミング |
| Integration | OpenAI API互換 | アダプターパターン |
| Reliability | 自動再接続、永続化 | 状態管理、エラーハンドリング |

### 技術的決定事項（確定）

#### TTS採用決定

| 項目 | 決定 |
|-----|------|
| MVP TTS | Style-BERT-VITS2（インプロセス） |
| 統合方式 | Python直接呼び出し |
| GPU要件 | 推奨（CPU動作可だが低速） |

#### ストリーミング戦略

| フェーズ | 方式 | 詳細 |
|---------|------|------|
| STT部分認識 | UI表示のみ | 確定テキストのみLLM送信 |
| LLMストリーミング | デルタ送信 | トークン単位でクライアントへ |
| TTSチャンク | 文単位生成 | 先行再生で体感レイテンシ低減 |

#### WebSocketイベント契約

**Client → Server:**
- `vad.start` - 発話開始
- `vad.audio` + ArrayBuffer - 音声チャンク
- `vad.end` - 発話終了
- `cancel` - キャンセル

**Server → Client:**
- `stt.partial` + text - 部分認識（UI表示用）
- `stt.final` + text + latency - 確定認識
- `llm.start` - LLM処理開始
- `llm.delta` + text - LLMトークン
- `llm.end` + latency - LLM完了
- `tts.chunk` + audio - TTSチャンク
- `tts.end` + latency - TTS完了
- `error` + code + message - エラー

#### GPU/CPUフォールバック

| 環境 | STT | E2E目標 |
|-----|-----|---------|
| GPU ≥4GB | ReazonSpeech NeMo v2 | < 2秒 |
| GPU 2-4GB | ReazonSpeech（量子化） | < 2秒 |
| CPU | Whisper small/medium | 超過許容 |

#### 永続化設計

| データ種別 | 保存 | フォーマット |
|-----------|------|-------------|
| 会話メタデータ | Yes | SQLite |
| メッセージ | Yes | SQLite |
| レイテンシログ | Yes | JSONL |
| 設定 | Yes | YAML |
| 音声ファイル | No | 保存しない |

### クロスカッティング・コンサーン

1. **レイテンシ計測**: 全コンポーネントで統一計測（STT/LLM/TTS各レイテンシ記録）
2. **エラーハンドリング**: 状態機械に基づくエラー伝播とIDLEへのリカバリ
3. **設定管理**: YAML設定ファイルによる一元管理
4. **ログ構造**: JSONL形式での評価ログ出力

## Starter Template Evaluation

### プライマリ技術ドメイン

**Full-Stack Hybrid** - Next.js (TypeScript) + FastAPI (Python) モノレポ構成

### 技術スタック確定

| カテゴリ | 技術 |
|---------|------|
| 構成 | モノレポ（frontend/ + backend/） |
| Python | 3.12 |
| Node.js | 20 LTS |
| CSS | Tailwind CSS |

### 推奨アプローチ: カスタムモノレポ構成

汎用スターターではなく、最小限のボイラープレートから構築：

```
local-voice-assistant-claude-bmad/
├── frontend/                    # Next.js アプリ
│   ├── src/
│   │   ├── app/                # App Router
│   │   ├── components/         # React コンポーネント
│   │   ├── hooks/              # カスタムフック (VAD等)
│   │   └── lib/                # ユーティリティ
│   ├── package.json
│   ├── tsconfig.json
│   └── tailwind.config.ts
├── backend/                     # FastAPI アプリ
│   ├── src/
│   │   └── voice_assistant/
│   │       ├── api/            # WebSocket + REST
│   │       ├── stt/            # ReazonSpeech統合
│   │       ├── llm/            # OpenAI互換アダプター
│   │       ├── tts/            # Style-BERT-VITS2統合
│   │       ├── db/             # SQLite操作
│   │       └── core/           # 設定、ログ
│   ├── pyproject.toml          # uv管理
│   └── uv.lock
├── shared/                      # 共有定義（オプション）
│   └── types/                  # WebSocketイベント型定義
├── scripts/                     # 起動・開発スクリプト
│   ├── dev.sh                  # 開発環境起動
│   └── start.sh                # 本番起動
├── config/                      # 設定ファイル
│   └── config.yaml
├── logs/                        # 評価ログ出力先
├── data/                        # SQLite DB
└── pyproject.toml              # ルートuv（ワークスペース）
```

### 初期化コマンド

**Frontend (Next.js + Tailwind):**
```bash
cd frontend
npx create-next-app@latest . --typescript --tailwind --eslint --app --src-dir --import-alias "@/*"
npm install @ricky0123/vad-web
```

**Backend (FastAPI + uv):**
```bash
cd backend
uv init --package voice-assistant
uv add fastapi uvicorn websockets pydantic pyyaml
uv add torch nemo-toolkit  # STT用
uv add openai httpx        # LLM用
```

### アーキテクチャ決定（スターター由来）

| カテゴリ | 決定 |
|---------|------|
| 言語・ランタイム | TypeScript (Frontend), Python 3.12 (Backend) |
| スタイリング | Tailwind CSS |
| ビルドツール | Next.js (Turbopack), uv |
| テスト | Vitest (Frontend), pytest (Backend) |
| リンター | ESLint + Prettier, Ruff |
| コード構成 | App Router, src/ディレクトリ構造 |

## Core Architectural Decisions

### Decision Priority Analysis

**Critical Decisions (実装ブロック):**
- STT: ReazonSpeech NeMo v2
- TTS: Style-BERT-VITS2
- LLM: OpenAI API互換インターフェース
- 通信: WebSocket（イベント契約確定）

**Important Decisions (アーキテクチャ形成):**
- ORM: SQLModel
- 状態管理: Zustand
- ログ: structlog

**Deferred Decisions (Post-MVP):**
- STT/TTS切り替えUI
- 複数会話セッション管理
- Docker/コンテナ化

### Data Architecture

| 決定 | 選択 | バージョン | 理由 |
|-----|------|-----------|------|
| ORM | SQLModel | 0.0.22+ | Pydantic統合、型安全、FastAPI親和性 |
| DB | SQLite | 3.x | ローカル永続化、セットアップ不要 |
| マイグレーション | SQLModel自動 | - | MVP段階では手動スキーマ管理 |

**スキーマ設計:**
```python
class Conversation(SQLModel, table=True):
    id: str = Field(primary_key=True)
    title: str | None = None
    created_at: datetime
    updated_at: datetime

class Message(SQLModel, table=True):
    id: str = Field(primary_key=True)
    conversation_id: str = Field(foreign_key="conversation.id")
    role: Literal["user", "assistant"]
    content: str
    stt_latency_ms: int | None = None
    llm_latency_ms: int | None = None
    tts_latency_ms: int | None = None
    created_at: datetime
```

### Authentication & Security

| 決定 | 選択 | 理由 |
|-----|------|------|
| 認証 | なし（MVP） | ローカル個人利用前提 |
| CORS | localhost許可 | 開発環境対応 |
| 入力検証 | Pydantic | FastAPI標準 |

### API & Communication Patterns

| 決定 | 選択 | 理由 |
|-----|------|------|
| リアルタイム | WebSocket | 双方向ストリーミング必須 |
| REST API | FastAPI標準 | 会話履歴・設定管理用 |
| シリアライゼーション | msgpack (audio) / JSON (text) | 音声データ効率化 |
| エラーハンドリング | 統一エラーイベント | `error` + code + message |

**REST エンドポイント:**
```
GET    /api/v1/health              # ヘルスチェック
GET    /api/v1/conversations       # 会話一覧
POST   /api/v1/conversations       # 新規会話
GET    /api/v1/conversations/{id}  # 会話詳細
DELETE /api/v1/conversations/{id}  # 会話削除
GET    /api/v1/config              # 設定取得
PUT    /api/v1/config              # 設定更新
WS     /api/v1/ws/chat             # 音声対話
```

### Frontend Architecture

| 決定 | 選択 | バージョン | 理由 |
|-----|------|-----------|------|
| 状態管理 | Zustand | 5.x | 軽量、WebSocket状態に最適 |
| フェッチ | TanStack Query | 5.x | REST API用キャッシュ |
| フォーム | React Hook Form | 7.x | 設定画面用 |

**Zustand Store設計:**
```typescript
interface VoiceStore {
  // 状態
  connectionState: 'disconnected' | 'connecting' | 'connected'
  recordingState: 'idle' | 'recording' | 'processing'
  partialText: string
  messages: Message[]

  // アクション
  connect: () => void
  disconnect: () => void
  startRecording: () => void
  stopRecording: () => void
}
```

### Infrastructure & Deployment

| 決定 | 選択 | 理由 |
|-----|------|------|
| 開発起動 | Makefile | シンプル、広くサポート |
| ログ | structlog | 構造化JSONL出力 |
| 設定 | YAML + Pydantic Settings | 型安全な設定管理 |
| ホスティング | ローカル | MVP段階 |

**Makefile例:**
```makefile
.PHONY: dev dev-frontend dev-backend

dev:
	make -j2 dev-frontend dev-backend

dev-frontend:
	cd frontend && npm run dev

dev-backend:
	cd backend && uv run uvicorn voice_assistant.main:app --reload
```

### Decision Impact Analysis

**実装順序:**
1. プロジェクト初期化（モノレポ構造）
2. Backend基盤（FastAPI + WebSocket + SQLite）
3. STT統合（ReazonSpeech）
4. LLM統合（OpenAI互換）
5. TTS統合（Style-BERT-VITS2）
6. Frontend基盤（Next.js + Zustand）
7. VAD統合（@ricky0123/vad）
8. E2E結合テスト

**コンポーネント間依存:**
```
Frontend (Zustand) ←→ WebSocket ←→ Backend (FastAPI)
                                      ├── STT (ReazonSpeech)
                                      ├── LLM (OpenAI互換)
                                      ├── TTS (Style-BERT-VITS2)
                                      └── DB (SQLite/SQLModel)
```

## Implementation Patterns & Consistency Rules

### Naming Patterns

#### Database Naming
| 対象 | パターン | 例 |
|-----|---------|-----|
| テーブル名 | snake_case 複数形 | `conversations`, `messages` |
| カラム名 | snake_case | `created_at`, `conversation_id` |
| 外部キー | `{テーブル単数}_id` | `conversation_id` |

#### API Naming
| 対象 | パターン | 例 |
|-----|---------|-----|
| エンドポイント | kebab-case 複数形 | `/api/v1/conversations` |
| クエリパラメータ | snake_case | `?page_size=20` |

#### Code Naming
| 言語 | 対象 | パターン | 例 |
|-----|------|---------|-----|
| Python | 変数/関数 | snake_case | `get_conversation()` |
| Python | クラス | PascalCase | `ConversationService` |
| TypeScript | 変数/関数 | camelCase | `getConversation()` |
| TypeScript | 型/インターフェース | PascalCase | `Conversation` |
| React | コンポーネント | PascalCase | `ChatMessage` |

#### File Naming
| 領域 | パターン | 例 |
|-----|---------|-----|
| Frontend コンポーネント | PascalCase.tsx | `ChatMessage.tsx` |
| Frontend hooks | kebab-case.ts | `use-voice.ts` |
| Frontend utils | kebab-case.ts | `websocket-client.ts` |
| Backend モジュール | snake_case.py | `conversation_service.py` |

### API Response Patterns

**成功レスポンス:**
```json
{
  "data": { ... }
}
```

**エラーレスポンス:**
```json
{
  "error": {
    "code": "VALIDATION_ERROR",
    "message": "Invalid input",
    "details": []
  }
}
```

**リストレスポンス:**
```json
{
  "data": [...],
  "meta": { "total": 100, "page": 1, "limit": 20 }
}
```

### Test Location Patterns

| 領域 | パターン | 場所 |
|-----|---------|------|
| Frontend Unit | co-located | `*.test.tsx` |
| Frontend E2E | 別ディレクトリ | `frontend/e2e/` |
| Backend Unit | 別ディレクトリ | `backend/tests/unit/` |
| Backend Integration | 別ディレクトリ | `backend/tests/integration/` |

### Error Handling Patterns

**Backend (Python):**
```python
class AppError(Exception):
    def __init__(self, code: str, message: str, status_code: int = 400):
        self.code = code
        self.message = message
        self.status_code = status_code
```

**Frontend (TypeScript):**
```typescript
interface AppError {
  code: string
  message: string
  details?: unknown
}
```

### Logging Patterns

**structlog 形式:**
```python
logger.info("stt_completed",
    text="こんにちは",
    latency_ms=450,
    model="reazon-nemo-v2"
)
```

**JSONL 出力:**
```json
{"event": "stt_completed", "text": "...", "latency_ms": 450, "timestamp": "..."}
```

### Enforcement Guidelines

**All AI Agents MUST:**
- 上記の命名規則に従う
- APIレスポンス形式を統一する
- エラーは AppError クラス/インターフェースを使用する
- ログは structlog の構造化形式で出力する

## Project Structure

### ディレクトリ構造

```
local-voice-assistant-claude-bmad/
├── frontend/                           # Next.js アプリケーション
│   ├── src/
│   │   ├── app/                        # App Router
│   │   │   ├── layout.tsx              # ルートレイアウト
│   │   │   ├── page.tsx                # チャット画面
│   │   │   └── globals.css             # グローバルスタイル
│   │   ├── core/                       # Framework-agnostic コア
│   │   │   ├── websocket-client.ts     # WebSocketクライアント
│   │   │   ├── state-machine.ts        # 対話状態機械
│   │   │   ├── events.ts               # WebSocketイベント型定義
│   │   │   └── audio-utils.ts          # 音声ユーティリティ
│   │   ├── components/                 # React コンポーネント
│   │   │   ├── ChatContainer.tsx       # チャットコンテナ
│   │   │   ├── ChatMessage.tsx         # メッセージ表示
│   │   │   ├── VoiceInput.tsx          # 音声入力UI
│   │   │   └── RecordingIndicator.tsx  # 録音状態表示
│   │   ├── hooks/                      # React カスタムフック
│   │   │   ├── use-voice.ts            # VAD + WebSocket統合
│   │   │   └── use-conversation.ts     # 会話状態管理
│   │   ├── stores/                     # Zustand ストア
│   │   │   └── voice-store.ts          # 音声対話状態
│   │   └── lib/                        # ユーティリティ
│   │       └── api-client.ts           # REST APIクライアント
│   ├── e2e/                            # E2Eテスト
│   │   └── chat.spec.ts
│   ├── public/                         # 静的ファイル
│   ├── package.json
│   ├── tsconfig.json
│   ├── tailwind.config.ts
│   ├── next.config.ts
│   └── eslint.config.mjs
│
├── backend/                            # FastAPI アプリケーション
│   ├── src/
│   │   └── voice_assistant/
│   │       ├── __init__.py
│   │       ├── main.py                 # FastAPI エントリーポイント
│   │       ├── api/                    # API層
│   │       │   ├── __init__.py
│   │       │   ├── websocket.py        # /api/v1/ws/chat ハンドラ
│   │       │   ├── conversations.py    # 会話 CRUD
│   │       │   └── config.py           # 設定 API
│   │       ├── stt/                    # 音声認識
│   │       │   ├── __init__.py
│   │       │   ├── base.py             # STT抽象基底
│   │       │   └── reazon_speech.py    # ReazonSpeech NeMo v2
│   │       ├── llm/                    # LLM統合
│   │       │   ├── __init__.py
│   │       │   ├── base.py             # LLM抽象基底
│   │       │   └── openai_compat.py    # OpenAI API互換クライアント
│   │       ├── tts/                    # 音声合成
│   │       │   ├── __init__.py
│   │       │   ├── base.py             # TTS抽象基底
│   │       │   └── style_bert_vits2.py # Style-BERT-VITS2統合
│   │       ├── db/                     # データベース層
│   │       │   ├── __init__.py
│   │       │   ├── models.py           # SQLModelモデル
│   │       │   └── repository.py       # CRUD操作
│   │       └── core/                   # 共通基盤
│   │           ├── __init__.py
│   │           ├── config.py           # 設定管理
│   │           ├── logging.py          # structlog設定
│   │           └── errors.py           # エラー定義
│   ├── tests/
│   │   ├── unit/                       # ユニットテスト
│   │   │   ├── test_stt.py
│   │   │   ├── test_llm.py
│   │   │   └── test_tts.py
│   │   └── integration/                # 統合テスト
│   │       └── test_websocket.py
│   ├── pyproject.toml
│   └── uv.lock
│
├── config/                             # 設定ファイル
│   ├── config.yaml                     # メイン設定
│   └── config.example.yaml             # 設定例
│
├── data/                               # データ永続化
│   └── voice_assistant.db              # SQLite DB
│
├── logs/                               # ログ出力
│   └── eval.jsonl                      # 評価ログ
│
├── scripts/                            # 起動スクリプト
│   ├── dev.sh                          # 開発環境起動
│   └── setup.sh                        # 初期セットアップ
│
├── Makefile                            # 開発タスク
├── pyproject.toml                      # ルートuv設定
├── README.md
└── .gitignore
```

### FR → ディレクトリマッピング

| FR | ディレクトリ | 主要ファイル |
|----|------------|-------------|
| 音声入力（STT） | `backend/src/voice_assistant/stt/` | `reazon_speech.py` |
| LLM対話 | `backend/src/voice_assistant/llm/` | `openai_compat.py` |
| 音声出力（TTS） | `backend/src/voice_assistant/tts/` | `style_bert_vits2.py` |
| Web UI | `frontend/src/components/` | `ChatContainer.tsx` |
| 会話履歴管理 | `backend/src/voice_assistant/db/` | `repository.py` |
| 設定管理 | `backend/src/voice_assistant/core/` | `config.py` |
| 評価・ログ | `backend/src/voice_assistant/core/` | `logging.py` |
| リアルタイム通信 | `backend/src/voice_assistant/api/` | `websocket.py` |
| VAD | `frontend/src/hooks/` | `use-voice.ts` |
| 状態管理 | `frontend/src/stores/` | `voice-store.ts` |
| WebSocket状態機械 | `frontend/src/core/` | `state-machine.ts` |

### core/ ディレクトリ設計

`frontend/src/core/` はフレームワーク非依存のコア機能を集約：

| ファイル | 責務 |
|---------|------|
| `websocket-client.ts` | WebSocket接続管理、再接続、メッセージ送受信 |
| `state-machine.ts` | IDLE→RECORDING→STT→LLM→TTS→IDLE 状態遷移 |
| `events.ts` | WebSocketイベント型定義（`VadStartEvent`, `SttFinalEvent` 等） |
| `audio-utils.ts` | 音声データ変換、再生キュー管理 |

**設計原則:**
- React/Next.js への依存なし
- テスト容易性を確保（純粋関数・クラス）
- hooks/ がcore/を利用してReact統合を提供

## Architecture Validation Results

### Coherence Validation ✅

**Decision Compatibility:**
- Next.js 15 + React 19 + TypeScript → 互換性確認済み
- FastAPI + Python 3.12 + SQLModel + structlog → 互換性確認済み
- Zustand 5.x + TanStack Query 5.x → 相互補完（状態管理とキャッシュ分離）
- WebSocket (`/api/v1/ws/chat`) + REST API (`/api/v1/*`) → 同一バージョン境界で整合

**Pattern Consistency:**
- 命名規則: Python(snake_case) / TypeScript(camelCase) / React(PascalCase) → 明確に分離
- API応答パターン: `{ data: {...} }` / `{ error: {...} }` → 統一
- ファイル命名: Frontend(PascalCase.tsx / kebab-case.ts) / Backend(snake_case.py) → 一貫性あり

**Structure Alignment:**
- `frontend/src/core/` がframework-agnostic機能を集約 → hooks/がReact統合を担当
- `backend/src/voice_assistant/{stt,llm,tts}/` が各コンポーネント分離 → モジュラー設計実現
- テスト配置: Frontend(co-located) / Backend(tests/分離) → 各エコシステムのベストプラクティス準拠

### Requirements Coverage Validation ✅

**FR Coverage (32件):**

| FR範囲 | 該当FR | アーキテクチャ対応 |
|--------|--------|------------------|
| 音声入力 | FR1-4 | `stt/reazon_speech.py`, `hooks/use-voice.ts` |
| LLM対話 | FR5-8 | `llm/openai_compat.py`, 設定でプロバイダー切り替え |
| 音声出力 | FR9-11 | `tts/style_bert_vits2.py` |
| Web UI | FR12-15 | `components/`, `stores/voice-store.ts` |
| 会話履歴 | FR16-18 | `db/models.py`, `db/repository.py` |
| 設定管理 | FR19-21 | `core/config.py`, `config/config.yaml` |
| 評価・ログ | FR22-26 | `core/logging.py`, JSONL出力 |
| リアルタイム通信 | FR27-29 | `api/websocket.py`, `core/websocket-client.ts` |
| システム起動 | FR30-32 | `main.py`, `/api/v1/health` |

**NFR Coverage:**

| NFR | 対応 |
|-----|------|
| NFR-P1〜P6 (Performance) | ストリーミング戦略、状態機械、WebSocketイベント契約 |
| NFR-I1〜I3 (Integration) | OpenAI互換アダプター、YAML設定 |
| NFR-R1〜R4 (Reliability) | 自動再接続、エラーハンドリングパターン |
| NFR-M1〜M3 (Maintainability) | Ruff/ESLint、structlog JSONL、uv/npm lock |

### Implementation Readiness Validation ✅

**Decision Completeness:**
- ✅ 全Critical決定（STT/TTS/LLM/通信）がバージョン付きで文書化
- ✅ SQLModelスキーマ設計が具体例付きで定義
- ✅ WebSocketイベント契約が完全定義（Client→Server / Server→Client）

**Structure Completeness:**
- ✅ 全ディレクトリ・主要ファイルが明示
- ✅ FR→ディレクトリマッピング表で追跡可能
- ✅ frontend/src/core/ のframework-agnostic分離が明確

**Pattern Completeness:**
- ✅ エラーハンドリング（AppError）パターン定義
- ✅ ログ形式（structlog JSONL）定義
- ✅ API応答パターン（成功/エラー/リスト）定義

### Gap Analysis Results

**Critical Gaps:** なし

**Important Gaps:** PRDのTTS記述更新済み（VOICEVOX → Style-BERT-VITS2）

**Nice-to-Have Gaps:**
- Docker構成（MVP後に追加予定 v2.0+）
- CI/CD定義（MVP後に追加予定）

### Architecture Completeness Checklist

**✅ Requirements Analysis**
- [x] Project context thoroughly analyzed
- [x] Scale and complexity assessed
- [x] Technical constraints identified (GPU/CPU fallback)
- [x] Cross-cutting concerns mapped

**✅ Architectural Decisions**
- [x] Critical decisions documented with versions
- [x] Technology stack fully specified
- [x] Integration patterns defined
- [x] Performance considerations addressed

**✅ Implementation Patterns**
- [x] Naming conventions established
- [x] Structure patterns defined
- [x] Communication patterns specified
- [x] Process patterns documented

**✅ Project Structure**
- [x] Complete directory structure defined
- [x] Component boundaries established
- [x] Integration points mapped
- [x] Requirements to structure mapping complete

### Architecture Readiness Assessment

**Overall Status:** READY FOR IMPLEMENTATION

**Confidence Level:** HIGH

**Key Strengths:**
- 日本語特化STT (ReazonSpeech) とTTS (Style-BERT-VITS2) の明確な統合設計
- WebSocketイベント契約と状態機械が完全定義
- framework-agnostic core層による将来の拡張性確保
- GPU/CPUフォールバック方針が明確

**Areas for Future Enhancement:**
- Docker/コンテナ化対応（v2.0+）
- CI/CDパイプライン構築

### Implementation Handoff

**AI Agent Guidelines:**
- Follow all architectural decisions exactly as documented
- Use implementation patterns consistently across all components
- Respect project structure and boundaries
- Refer to this document for all architectural questions

**First Implementation Priority:**
1. プロジェクト初期化（モノレポ構造）
2. Backend基盤（FastAPI + WebSocket + SQLite）
3. STT統合（ReazonSpeech）
4. LLM統合（OpenAI互換）
5. TTS統合（Style-BERT-VITS2）
6. Frontend基盤（Next.js + Zustand）
7. VAD統合（@ricky0123/vad）
8. E2E結合テスト

