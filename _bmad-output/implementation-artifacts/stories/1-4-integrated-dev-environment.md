# Story 1.4: 統合開発環境

Status: done

## Story

As a **開発者**,
I want **`make dev`で frontend/backend 両方が起動する**,
so that **ワンコマンドで開発環境を立ち上げられる** (FR30).

## Acceptance Criteria

1. **Given** Frontend/Backendの基盤が構築済み（Story 1.2, 1.3完了）
   **When** プロジェクトルートで`make dev`を実行する
   **Then** BackendがPort 8000で起動する

2. **And** FrontendがPort 3000で起動する

3. **And** Frontend→Backend間のCORS設定が有効になる

4. **And** `make dev`の終了（Ctrl+C）で両プロセスが停止する

## Tasks / Subtasks

- [x] Task 1: `make dev`の動作確認と修正 (AC: #1, #2, #4)
  - [x] 現在のMakefile `dev`ターゲットの動作確認
  - [x] `make -j2`でBackend/Frontendが同時起動することを確認
  - [x] Ctrl+Cで両プロセスが停止することを確認
  - [x] 問題があれば修正

- [x] Task 2: CORS設定の確認とテスト (AC: #3)
  - [x] Backend CORS設定で`http://localhost:3000`が許可されていることを確認
  - [x] Frontend→Backend APIアクセスが成功することをテスト
  - [x] 必要であれば追加のCORS設定

- [x] Task 3: 統合テストの実行 (AC: #1-4)
  - [x] `make dev`を実行し、両サーバーの起動を確認
  - [x] http://localhost:3000 でFrontendが表示されることを確認
  - [x] http://localhost:8000/api/v1/health がレスポンスを返すことを確認
  - [x] Frontend→Backend間の通信テスト（curl/fetch）
  - [x] Ctrl+Cで両プロセスが正常終了することを確認

## Dev Notes

### アーキテクチャ準拠事項

**現在のMakefile構成:**
```makefile
.PHONY: dev dev-frontend dev-backend

dev:
	@echo "Starting development servers..."
	make -j2 dev-frontend dev-backend

dev-frontend:
	cd frontend && npm run dev

dev-backend:
	cd backend && uv run uvicorn voice_assistant.main:app --reload --host 0.0.0.0 --port 8000
```

**Architecture.md記載のMakefile例:**
```makefile
.PHONY: dev dev-frontend dev-backend

dev:
	make -j2 dev-frontend dev-backend

dev-frontend:
	cd frontend && npm run dev

dev-backend:
	cd backend && uv run uvicorn voice_assistant.main:app --reload
```

**現在の構成とArchitecture.mdの差異:**
| 項目 | 現在の実装 | Architecture.md例 | 理由 |
|------|-----------|------------------|------|
| `--host 0.0.0.0` | あり | なし | LAN内の他デバイスからアクセス可能にするため（開発時便利） |
| `--port 8000` | 明示 | 暗黙（デフォルト） | 明示的な指定で混乱を防ぐ |
| `@echo` | あり | なし | 起動時のフィードバック表示 |

→ **結論**: 現在の構成はArchitecture.mdの意図に沿っており、開発利便性のための追加オプションのみ。変更不要。

### 技術仕様

**CORS設定（backend/src/voice_assistant/main.py、Story 1.2で実装済み）:**
```python
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins,  # ["http://localhost:3000"]
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "DELETE", "OPTIONS"],
    allow_headers=["Content-Type", "Authorization", "X-Request-ID"],
)
```

**設定（backend/src/voice_assistant/core/config.py）:**
```python
cors_origins: list[str] = ["http://localhost:3000"]
```

### プロセス管理

**`make -j2`の挙動:**
- `-j2`オプションで2つのジョブを並列実行
- 各ジョブはフォアグラウンドで実行される
- Ctrl+Cで両プロセスにSIGINTが送信される
- 正常終了時に両プロセスが停止する

**注意事項:**
- `make -j2`でターミナルが乱れる場合がある（出力が混在）
- 本格的な解決は trap/wait を使ったシェルスクリプトだが、MVPでは許容

### CORS テスト方法

**curl でのテスト:**
```bash
curl -X OPTIONS http://localhost:8000/api/v1/health \
  -H "Origin: http://localhost:3000" \
  -H "Access-Control-Request-Method: GET" \
  -v
```

**Frontend からのテスト（ブラウザコンソール）:**
```javascript
fetch('http://localhost:8000/api/v1/health')
  .then(res => res.json())
  .then(data => console.log(data));
```

### 依存関係

**前提条件:**
- Story 1.1 完了（モノレポ構造、Makefile）
- Story 1.2 完了（Backend基盤、CORS設定）
- Story 1.3 完了（Frontend基盤）

**後続Story:**
- Story 2.1 (WebSocket基盤) - 統合開発環境を前提
- Epic 2 全体 - 開発時は`make dev`を使用

### テスト基準

1. `make dev`で両サーバーが起動する
2. http://localhost:3000 でFrontendが表示される
3. http://localhost:8000/api/v1/health が`{"status":"ok"}`を返す
4. Frontend→Backend のCORS通信が成功する
5. Ctrl+Cで両プロセスが停止する

### Previous Story Learnings

**Story 1.3 から:**
- Next.js 16.1.1 + React 19.2.3 で http://localhost:3000 起動確認済み
- `npm run dev`で Turbopack 使用
- Cross origin request の警告が出る場合がある（next.config.ts で`allowedDevOrigins`設定可能）

**Story 1.2 から:**
- FastAPI + uvicorn で http://localhost:8000 起動確認済み
- CORS設定で`http://localhost:3000`許可済み
- `--reload`オプションでホットリロード有効
- lifespan context managerパターンで起動時処理を管理

**Story 1.1 から:**
- Makefile に `dev`, `dev-frontend`, `dev-backend` ターゲット定義済み
- `make -j2`で並列実行
- scripts/dev.sh は make dev を呼び出す

### References

- [Source: _bmad-output/architecture.md#Infrastructure-Deployment]
- [Source: _bmad-output/architecture.md#Project-Structure]
- [Source: _bmad-output/project-planning-artifacts/epics.md#Story-1.4]

## Dev Agent Record

### Agent Model Used

Claude Opus 4.5 (claude-opus-4-5-20251101)

### Debug Log References

N/A

### Completion Notes List

- Task 1: `make dev`動作確認完了 - `make -j2`でBackend/Frontendが並列起動、Ctrl+C（SIGINT）で両プロセス停止確認
- Task 2: CORS設定確認完了 - Preflight/GETリクエストで`access-control-allow-origin: http://localhost:3000`返却確認
- Task 3: 統合テスト完了 - Backend(8000)、Frontend(3000)起動確認、CORS通信成功、プロセス終了確認

### File List

**No files created or modified** - Story 1.4は既存設定の動作確認のみ

**検証済み設定ファイル:**
- `Makefile` - `dev`, `dev-frontend`, `dev-backend` ターゲット正常動作
- `backend/src/voice_assistant/main.py` - CORS設定正常
- `backend/src/voice_assistant/core/config.py` - `cors_origins: ["http://localhost:3000"]`

## Change Log

- 2025-12-27: Code review修正 - Makefile構成差異の説明テーブル追加
- 2025-12-27: Story 1.4 実装完了 - 統合開発環境（全3タスク完了、既存設定の動作確認のみ）
- 2025-12-27: Story 1.4 created via create-story workflow
