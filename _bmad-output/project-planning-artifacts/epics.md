---
stepsCompleted: [1, 2, 3, 4]
status: 'complete'
completedAt: '2025-12-27'
inputDocuments:
  - '_bmad-output/prd.md'
  - '_bmad-output/architecture.md'
workflowType: 'epics-and-stories'
project_name: 'local-voice-assistant-claude-bmad'
user_name: 'y'
date: '2025-12-27'
---

# local-voice-assistant-claude-bmad - Epic Breakdown

## Overview

This document provides the complete epic and story breakdown for local-voice-assistant-claude-bmad, decomposing the requirements from the PRD and Architecture into implementable stories.

## Requirements Inventory

### Functional Requirements

**音声入力（STT）**
- FR1: ユーザーはマイクを通じて日本語音声を入力できる
- FR2: システムはVADにより発話の開始と終了を自動検出できる
- FR3: システムは音声をリアルタイムでテキストに変換できる
- FR4: ユーザーは認識されたテキストを画面上で確認できる

**LLM対話**
- FR5: ユーザーはテキスト化された発話に対してLLMからの応答を受け取れる
- FR6: システムは会話コンテキストを維持して応答を生成できる
- FR7: システムはOpenAI API互換インターフェースを通じて複数のLLMプロバイダーに接続できる
- FR8: ユーザーはLLMプロバイダー（Ollama/OpenAI/Groq）を設定で切り替えられる

**音声出力（TTS）**
- FR9: システムはLLM応答をStyle-BERT-VITS2を使用して音声に変換できる
- FR10: ユーザーは音声応答をスピーカーで聴くことができる
- FR11: ユーザーは音声出力中にテキストも同時に確認できる

**Web UI**
- FR12: ユーザーはブラウザでチャット形式のUIにアクセスできる
- FR13: ユーザーはマイクボタンで録音を開始/停止できる
- FR14: ユーザーは会話履歴をスクロールして閲覧できる
- FR15: ユーザーは現在の録音状態（待機/録音中/処理中）を視覚的に確認できる

**会話履歴管理**
- FR16: システムは会話履歴をローカルデータベースに保存できる
- FR17: ユーザーは過去の会話履歴を閲覧できる
- FR18: ユーザーは会話履歴を削除できる

**設定管理**
- FR19: ユーザーはLLMプロバイダーの接続設定を構成できる
- FR20: ユーザーはLLM APIのレート制限を設定できる
- FR21: システムは設定をローカルファイルで永続化できる

**評価・ログ機能**
- FR22: システムはSTT処理のレイテンシを記録できる
- FR23: システムはLLM応答のレイテンシを記録できる
- FR24: システムはTTS処理のレイテンシを記録できる
- FR25: システムは評価ログをJSON形式で出力できる
- FR26: ユーザーはログデータを分析用にエクスポートできる

**リアルタイム通信**
- FR27: システムはWebSocketを通じてフロントエンドとバックエンド間でリアルタイム通信できる
- FR28: システムは接続断時に自動再接続を試行できる
- FR29: システムはエラー発生時にユーザーに通知できる

**システム起動・ヘルスチェック**
- FR30: ユーザーは`uv run`コマンドでシステムを起動できる
- FR31: システムはヘルスチェックAPIを提供できる
- FR32: システムはバックエンドサービスの状態を報告できる

### NonFunctional Requirements

**Performance**
- NFR-P1: 音声認識（STT）は発話終了から2秒以内に完了する（STTレイテンシ < 2000ms）
- NFR-P2: LLM応答は最初のトークンが1秒以内に到着する（TTFT < 1000ms）
- NFR-P3: TTS音声生成は1秒以内に開始する（TTS開始レイテンシ < 1000ms）
- NFR-P4: E2E応答遅延は2秒以内に収まる（発話終了→TTS再生開始 < 2000ms）
- NFR-P5: Web UIの初回ロードは3秒以内に完了する（Lighthouse > 80）
- NFR-P6: WebSocket接続確立は500ms以内に完了する

**Integration**
- NFR-I1: OpenAI API互換インターフェースを提供する
- NFR-I2: Style-BERT-VITS2をインプロセスで呼び出せる
- NFR-I3: 設定ファイルはYAML/JSON形式で管理する

**Reliability**
- NFR-R1: WebSocket切断時に自動再接続を試行する（最大3回、指数バックオフ）
- NFR-R2: バックエンドサービス起動時にヘルスチェックを実施する
- NFR-R3: エラー発生時にユーザーに分かりやすいメッセージを表示する
- NFR-R4: 会話履歴はローカルDBに永続化され、再起動後も保持される

**Maintainability**
- NFR-M1: コードはRuff/ESLintでリント検証に合格する
- NFR-M2: 評価ログはJSON形式で構造化される
- NFR-M3: 依存関係はuv/npm lockfileで固定される

### Additional Requirements

**アーキテクチャ由来の技術要件:**

1. **プロジェクト構成**
   - カスタムモノレポ構成（frontend/ + backend/）
   - Python 3.12 + Node.js 20 LTS
   - Tailwind CSS スタイリング

2. **初期化手順**
   - Frontend: `npx create-next-app@latest` + `@ricky0123/vad-web`
   - Backend: `uv init --package` + FastAPI + SQLModel

3. **データベース設計**
   - SQLModel ORM（Conversation, Message モデル）
   - SQLite ローカル永続化
   - レイテンシ計測カラム（stt/llm/tts_latency_ms）

4. **WebSocketイベント契約**
   - Client→Server: vad.start, vad.audio, vad.end, cancel
   - Server→Client: stt.partial, stt.final, llm.start, llm.delta, llm.end, tts.chunk, tts.end, error

5. **状態機械設計**
   - IDLE → RECORDING → STT → LLM → TTS → IDLE
   - エラー時はIDLEへリカバリ

6. **フロントエンド設計**
   - Zustand 状態管理（VoiceStore）
   - TanStack Query（REST API キャッシュ）
   - framework-agnostic core層（websocket-client, state-machine, events, audio-utils）

7. **開発環境**
   - Makefile による開発タスク管理
   - structlog JSONL ログ出力
   - Vitest (Frontend) / pytest (Backend) テスト

8. **セキュリティ**
   - 認証なし（MVP、ローカル個人利用）
   - CORS localhost許可
   - Pydantic 入力検証

### FR Coverage Map

| FR | Epic | 説明 |
|----|------|------|
| FR1 | Epic 2 | マイク音声入力 |
| FR2 | Epic 2 | VAD自動検出 |
| FR3 | Epic 2 | リアルタイムSTT |
| FR4 | Epic 2 | 認識テキスト表示 |
| FR5 | Epic 2 | LLM応答受信 |
| FR6 | Epic 2 | コンテキスト維持 |
| FR7 | Epic 2 | OpenAI API互換接続 |
| FR8 | Epic 4 | LLMプロバイダー切り替え |
| FR9 | Epic 2 | Style-BERT-VITS2 TTS |
| FR10 | Epic 2 | 音声再生 |
| FR11 | Epic 2 | テキスト同時表示 |
| FR12 | Epic 2 | チャットUI |
| FR13 | Epic 2 | マイクボタン |
| FR14 | Epic 3 | 履歴スクロール |
| FR15 | Epic 2 | 録音状態表示 |
| FR16 | Epic 3 | 履歴DB保存 |
| FR17 | Epic 3 | 履歴閲覧 |
| FR18 | Epic 3 | 履歴削除 |
| FR19 | Epic 4 | LLM接続設定 |
| FR20 | Epic 4 | レート制限設定 |
| FR21 | Epic 4 | 設定永続化 |
| FR22 | Epic 5 | STTレイテンシ記録 |
| FR23 | Epic 5 | LLMレイテンシ記録 |
| FR24 | Epic 5 | TTSレイテンシ記録 |
| FR25 | Epic 5 | JSON評価ログ出力 |
| FR26 | Epic 5 | ログエクスポート |
| FR27 | Epic 2 | WebSocket通信 |
| FR28 | Epic 5 | 自動再接続 |
| FR29 | Epic 5 | エラー通知 |
| FR30 | Epic 1 | uv run起動 |
| FR31 | Epic 5 | ヘルスチェックAPI |
| FR32 | Epic 5 | サービス状態報告 |

## Epic List

### Epic 1: プロジェクト基盤構築

モノレポ構造の初期化、開発環境のセットアップにより、開発者が`uv run`でシステムを起動できる状態を実現。

**FRs covered:** FR30
**技術要件:** カスタムモノレポ構成、Makefile、基本ディレクトリ構造

---

### Epic 2: リアルタイム音声対話

ユーザーがマイクで日本語を話し、AIが音声で応答する完全なE2E対話パイプラインを実現。**これがMVPの核心。**

**FRs covered:** FR1-4, FR5-7, FR9-11, FR12-13, FR15, FR27
**ユーザー成果:** 「声で話しかけて、声で返事が来る」

---

### Epic 3: 会話体験の完成

会話履歴のスクロール表示、ローカルDB永続化、会話管理機能により、継続的な対話体験を提供。

**FRs covered:** FR14, FR16-18
**ユーザー成果:** 「過去の会話を見返せる、履歴が保存される」

---

### Epic 4: 設定とカスタマイズ

LLMプロバイダーの切り替え、レート制限、設定永続化により、ユーザーがシステムをカスタマイズできる。

**FRs covered:** FR8, FR19-21
**ユーザー成果:** 「Ollama/OpenAI/Groqを自由に切り替えられる」

---

### Epic 5: 評価・運用基盤

レイテンシログ出力、ヘルスチェック、自動再接続、エラー通知により、研究用途と安定運用を実現。

**FRs covered:** FR22-26, FR28-29, FR31-32
**ユーザー成果:** 「パフォーマンス計測ができる、エラーに強い」

---

## Epic 1: プロジェクト基盤構築

モノレポ構造の初期化、開発環境のセットアップにより、開発者が`uv run`でシステムを起動できる状態を実現。

### Story 1.1: モノレポ構造の初期化

As a **開発者**,
I want **プロジェクトのモノレポ構造が初期化されている**,
So that **frontend/backend両方の開発を統一された環境で開始できる**.

**Acceptance Criteria:**

**Given** 空のプロジェクトディレクトリ
**When** 初期化スクリプトを実行する
**Then** 以下のディレクトリ構造が作成される:
- `frontend/` (Next.js用)
- `backend/` (FastAPI用)
- `config/` (設定ファイル)
- `scripts/` (起動スクリプト)
- `Makefile` (開発タスク)
**And** ルートの`pyproject.toml`が作成される
**And** `.gitignore`が適切に設定される

---

### Story 1.2: Backend基盤セットアップ

As a **開発者**,
I want **FastAPIバックエンドの基盤が構築されている**,
So that **APIエンドポイントの開発を開始できる**.

**Acceptance Criteria:**

**Given** モノレポ構造が初期化済み
**When** `cd backend && uv sync`を実行する
**Then** FastAPI、uvicorn、pydantic等の依存関係がインストールされる
**And** `backend/src/voice_assistant/main.py`にFastAPIアプリが作成される
**And** `/api/v1/health`エンドポイントが`{"status": "ok"}`を返す
**And** `uv run uvicorn voice_assistant.main:app`で起動できる

---

### Story 1.3: Frontend基盤セットアップ

As a **開発者**,
I want **Next.jsフロントエンドの基盤が構築されている**,
So that **UIコンポーネントの開発を開始できる**.

**Acceptance Criteria:**

**Given** モノレポ構造が初期化済み
**When** `cd frontend && npm install`を実行する
**Then** Next.js、TypeScript、Tailwind CSS等の依存関係がインストールされる
**And** `frontend/src/app/page.tsx`に基本ページが作成される
**And** `npm run dev`でhttp://localhost:3000が起動する
**And** Tailwind CSSが適用されている

---

### Story 1.4: 統合開発環境

As a **開発者**,
I want **`make dev`で frontend/backend 両方が起動する**,
So that **ワンコマンドで開発環境を立ち上げられる** (FR30).

**Acceptance Criteria:**

**Given** Frontend/Backendの基盤が構築済み
**When** プロジェクトルートで`make dev`を実行する
**Then** BackendがPort 8000で起動する
**And** FrontendがPort 3000で起動する
**And** Frontend→Backend間のCORS設定が有効になる
**And** `make dev`の終了で両プロセスが停止する

---

## Epic 2: リアルタイム音声対話

ユーザーがマイクで日本語を話し、AIが音声で応答する完全なE2E対話パイプラインを実現。**MVPの核心。**

### Story 2.1: WebSocket基盤

As a **システム**,
I want **Frontend/Backend間のWebSocket接続が確立できる**,
So that **リアルタイム双方向通信の基盤ができる** (FR27).

**Acceptance Criteria:**

**Given** Backend/Frontendが起動している
**When** Frontendが`/api/v1/ws/chat`に接続する
**Then** WebSocket接続が確立される
**And** Backend側で接続イベントがログ出力される
**And** Frontend側で接続状態が`connected`になる
**And** 接続断時にFrontendで`disconnected`状態になる

---

### Story 2.2: Frontend音声キャプチャとVAD

As a **ユーザー**,
I want **マイクボタンを押すと発話を自動検出して録音される**,
So that **自然に話しかけるだけで音声入力ができる** (FR1, FR2, FR13).

**Acceptance Criteria:**

**Given** WebSocket接続が確立されている
**When** マイクボタンをクリックする
**Then** マイク使用許可ダイアログが表示される（初回）
**And** VAD（@ricky0123/vad）が発話開始を検出すると録音状態になる
**And** `vad.start`イベントがWebSocketで送信される
**And** 発話中は音声チャンクが`vad.audio`で送信される
**And** 発話終了が検出されると`vad.end`が送信される
**And** 録音状態がUIに表示される (FR15)

---

### Story 2.3: STT統合（ReazonSpeech）

As a **ユーザー**,
I want **話した日本語が高精度でテキストに変換される**,
So that **自分の発話内容を正確に確認できる** (FR3, FR4).

**Acceptance Criteria:**

**Given** `vad.end`イベントを受信した
**When** Backend側でReazonSpeech NeMo v2を実行する
**Then** 音声がテキストに変換される
**And** 部分認識結果が`stt.partial`でストリーミング送信される
**And** 最終認識結果が`stt.final`で送信される
**And** `stt.final`にはレイテンシ（ms）が含まれる
**And** FrontendでテキストがUIに表示される

---

### Story 2.4: LLM統合（OpenAI互換）

As a **ユーザー**,
I want **認識されたテキストに対してLLMが応答する**,
So that **AIとの対話ができる** (FR5, FR6, FR7).

**Acceptance Criteria:**

**Given** `stt.final`で認識テキストが確定した
**When** Backend側でOpenAI互換APIにリクエストする
**Then** `llm.start`イベントが送信される
**And** LLM応答がストリーミングで`llm.delta`として送信される
**And** 応答完了時に`llm.end`（レイテンシ付き）が送信される
**And** 会話コンテキスト（直近のやり取り）が維持される
**And** Frontendで応答テキストがリアルタイム表示される

---

### Story 2.5: TTS統合（Style-BERT-VITS2）

As a **ユーザー**,
I want **LLM応答が日本語音声で読み上げられる**,
So that **声でAIの応答を聴くことができる** (FR9, FR10).

**Acceptance Criteria:**

**Given** `llm.delta`でテキストチャンクを受信している
**When** 文単位でTTS処理を実行する
**Then** Style-BERT-VITS2で音声が生成される
**And** 音声チャンクが`tts.chunk`（audio data）で送信される
**And** 全音声送信完了時に`tts.end`（レイテンシ付き）が送信される
**And** Frontendで音声がWeb Audio APIで再生される

---

### Story 2.6: E2Eパイプライン統合

As a **ユーザー**,
I want **話しかけてから音声応答が返るまでの一連の流れが動作する**,
So that **声で話しかけて声で返事が来る体験ができる** (FR11).

**Acceptance Criteria:**

**Given** 全コンポーネント（STT/LLM/TTS）が統合されている
**When** ユーザーがマイクに向かって日本語で話しかける
**Then** 発話が自動検出され録音される
**And** 音声がテキストに変換される（画面表示）
**And** LLMが応答を生成する（テキストストリーミング表示）
**And** 応答が音声で再生される
**And** テキストと音声が同時に確認できる (FR11)
**And** E2E遅延が測定可能（ログ出力）

---

### Story 2.7: チャットUI基本実装

As a **ユーザー**,
I want **ChatGPTライクなチャット画面で対話できる**,
So that **馴染みのあるUIで音声対話ができる** (FR12, FR15).

**Acceptance Criteria:**

**Given** E2Eパイプラインが動作している
**When** ブラウザでアプリにアクセスする
**Then** チャット形式のUIが表示される (FR12)
**And** マイクボタンが画面下部に配置される
**And** 録音状態（待機/録音中/処理中）がアイコン/色で視覚的に表示される (FR15)
**And** ユーザー発話と AI応答がメッセージバブルで表示される
**And** Zustand storeで状態管理される

---

## Epic 3: 会話体験の完成

会話履歴のスクロール表示、ローカルDB永続化、会話管理機能により、継続的な対話体験を提供。

### Story 3.1: 会話履歴スクロール表示

As a **ユーザー**,
I want **会話履歴をスクロールして閲覧できる**,
So that **過去のやり取りを確認できる** (FR14).

**Acceptance Criteria:**

**Given** 複数のメッセージが存在する
**When** チャット画面をスクロールする
**Then** 過去のメッセージが表示される
**And** 新しいメッセージ受信時に自動スクロールする
**And** 手動スクロール中は自動スクロールを停止する
**And** スクロール位置が適切に維持される

---

### Story 3.2: 会話履歴のDB永続化

As a **ユーザー**,
I want **会話履歴がローカルDBに保存される**,
So that **アプリ再起動後も会話が保持される** (FR16).

**Acceptance Criteria:**

**Given** E2E音声対話が動作している
**When** ユーザーとAIがメッセージを交換する
**Then** 各メッセージがSQLite DBに保存される
**And** Conversationレコードが作成/更新される
**And** Messageレコードにrole（user/assistant）が記録される
**And** レイテンシ情報（stt/llm/tts_latency_ms）が記録される
**And** アプリ再起動後も履歴が復元される

---

### Story 3.3: 会話履歴一覧API

As a **ユーザー**,
I want **過去の会話一覧を取得できる**,
So that **以前の会話を選択して閲覧できる** (FR17).

**Acceptance Criteria:**

**Given** 複数の会話がDBに保存されている
**When** `GET /api/v1/conversations`を呼び出す
**Then** 会話一覧がJSON形式で返される
**And** 各会話にid、title、created_at、updated_atが含まれる
**And** 新しい順にソートされる
**And** ページネーション対応（limit/offset）

---

### Story 3.4: 会話詳細表示

As a **ユーザー**,
I want **特定の会話の詳細を表示できる**,
So that **過去の対話内容を確認できる** (FR17).

**Acceptance Criteria:**

**Given** 会話IDが指定されている
**When** `GET /api/v1/conversations/{id}`を呼び出す
**Then** 会話のメタデータとメッセージ一覧が返される
**And** メッセージは時系列順で返される
**And** Frontendで選択した会話が表示される

---

### Story 3.5: 会話履歴削除

As a **ユーザー**,
I want **会話履歴を削除できる**,
So that **不要な履歴を整理できる** (FR18).

**Acceptance Criteria:**

**Given** 会話一覧が表示されている
**When** 削除ボタンをクリックする
**Then** 確認ダイアログが表示される
**And** 確認後、`DELETE /api/v1/conversations/{id}`が呼び出される
**And** 会話と関連メッセージがDBから削除される
**And** UI上から会話が消える

---

## Epic 4: 設定とカスタマイズ

LLMプロバイダーの切り替え、レート制限、設定永続化により、ユーザーがシステムをカスタマイズできる。

### Story 4.1: 設定ファイル基盤

As a **開発者**,
I want **YAML設定ファイルで設定が管理される**,
So that **設定を永続化し、起動時に読み込める** (FR21).

**Acceptance Criteria:**

**Given** `config/config.yaml`が存在する
**When** Backendが起動する
**Then** 設定ファイルが読み込まれる
**And** Pydantic Settingsで型安全に検証される
**And** 設定がない場合はデフォルト値が使用される
**And** `config/config.example.yaml`がサンプルとして存在する

---

### Story 4.2: LLMプロバイダー設定

As a **ユーザー**,
I want **LLMプロバイダー（Ollama/OpenAI/Groq）を設定できる**,
So that **好みのLLMを使用できる** (FR8, FR19).

**Acceptance Criteria:**

**Given** 設定ファイルが読み込まれている
**When** 設定でprovider=ollama/openai/groqを指定する
**Then** 指定されたプロバイダーに接続される
**And** 各プロバイダー用の設定（api_key, base_url, model）が適用される
**And** 設定変更後、再起動で反映される

---

### Story 4.3: 設定取得API

As a **ユーザー**,
I want **現在の設定をAPIで取得できる**,
So that **UIで設定状態を確認できる** (FR19).

**Acceptance Criteria:**

**Given** Backendが起動している
**When** `GET /api/v1/config`を呼び出す
**Then** 現在の設定がJSON形式で返される
**And** 機密情報（api_key）はマスクされる
**And** LLMプロバイダー、モデル名、レート制限が含まれる

---

### Story 4.4: 設定更新API

As a **ユーザー**,
I want **設定をAPIで更新できる**,
So that **再起動なしで設定を変更できる** (FR19, FR20).

**Acceptance Criteria:**

**Given** 有効な設定値がある
**When** `PUT /api/v1/config`で設定を送信する
**Then** 設定が検証される
**And** 有効な場合、設定ファイルが更新される
**And** ランタイム設定が即座に反映される
**And** 無効な場合、エラーメッセージが返される

---

### Story 4.5: レート制限設定

As a **ユーザー**,
I want **LLM APIのレート制限を設定できる**,
So that **クラウドLLM利用時のコストを管理できる** (FR20).

**Acceptance Criteria:**

**Given** 設定画面が表示されている
**When** レート制限（requests_per_minute）を設定する
**Then** 設定が保存される
**And** 制限を超えるリクエストは遅延またはエラーになる
**And** 現在の利用状況が確認できる

---

## Epic 5: 評価・運用基盤

レイテンシログ出力、ヘルスチェック、自動再接続、エラー通知により、研究用途と安定運用を実現。

### Story 5.1: レイテンシログ記録

As a **研究者**,
I want **各コンポーネントのレイテンシが記録される**,
So that **パフォーマンスを分析できる** (FR22-24).

**Acceptance Criteria:**

**Given** E2E音声対話が動作している
**When** 各処理が完了する
**Then** STTレイテンシ（ms）がログに記録される (FR22)
**And** LLMレイテンシ（TTFT, 総時間）がログに記録される (FR23)
**And** TTSレイテンシ（ms）がログに記録される (FR24)
**And** structlog形式で構造化される

---

### Story 5.2: 評価ログJSON出力

As a **研究者**,
I want **評価ログがJSON形式で出力される**,
So that **データ分析ツールで処理できる** (FR25).

**Acceptance Criteria:**

**Given** レイテンシが記録されている
**When** ログファイルに出力する
**Then** `logs/eval.jsonl`にJSONL形式で保存される
**And** 各行にtimestamp, event_type, latency_ms等が含まれる
**And** ファイルローテーションが設定される

---

### Story 5.3: ログエクスポート機能

As a **研究者**,
I want **ログデータをエクスポートできる**,
So that **外部ツールで分析できる** (FR26).

**Acceptance Criteria:**

**Given** 評価ログが蓄積されている
**When** エクスポートを実行する
**Then** 指定期間のログがダウンロードできる
**And** JSON/CSV形式で出力できる
**And** フィルタリング（日付、イベント種別）が可能

---

### Story 5.4: WebSocket自動再接続

As a **ユーザー**,
I want **接続断時に自動で再接続される**,
So that **一時的な切断でも対話を継続できる** (FR28).

**Acceptance Criteria:**

**Given** WebSocket接続が確立されている
**When** 接続が切断される
**Then** 自動再接続が試行される
**And** 最大3回まで指数バックオフでリトライする
**And** 再接続成功時にUIが`connected`状態に戻る
**And** 再接続失敗時にユーザーに通知される

---

### Story 5.5: エラー通知

As a **ユーザー**,
I want **エラー発生時に分かりやすく通知される**,
So that **問題を認識して対処できる** (FR29).

**Acceptance Criteria:**

**Given** システムが動作している
**When** エラーが発生する
**Then** UIにエラーメッセージが表示される
**And** メッセージは日本語で分かりやすい
**And** エラー種別（接続エラー、STTエラー等）が識別できる
**And** 回復可能な場合は回復方法が案内される

---

### Story 5.6: ヘルスチェックAPI拡張

As a **システム管理者**,
I want **詳細なヘルスチェックができる**,
So that **各コンポーネントの状態を監視できる** (FR31, FR32).

**Acceptance Criteria:**

**Given** Backendが起動している
**When** `GET /api/v1/health`を呼び出す
**Then** 全体のステータス（healthy/degraded/unhealthy）が返される
**And** 各コンポーネント（STT/LLM/TTS/DB）の状態が含まれる
**And** レスポンスタイムが含まれる
**And** 詳細モード（?detail=true）で追加情報が取得できる
