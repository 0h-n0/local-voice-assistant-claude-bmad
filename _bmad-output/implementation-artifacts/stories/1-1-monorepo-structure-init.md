# Story 1.1: モノレポ構造の初期化

Status: done

## Story

As a **開発者**,
I want **プロジェクトのモノレポ構造が初期化されている**,
so that **frontend/backend両方の開発を統一された環境で開始できる**.

## Acceptance Criteria

1. **Given** 空のプロジェクトディレクトリ
   **When** 初期化スクリプトを実行する
   **Then** 以下のディレクトリ構造が作成される:
   - `frontend/` (Next.js用)
   - `backend/` (FastAPI用)
   - `config/` (設定ファイル)
   - `scripts/` (起動スクリプト)
   - `Makefile` (開発タスク)

2. **And** ルートの`pyproject.toml`が作成される

3. **And** `.gitignore`が適切に設定される

## Tasks / Subtasks

- [x] Task 1: ディレクトリ構造の作成 (AC: #1)
  - [x] `frontend/` ディレクトリ作成
  - [x] `backend/` ディレクトリ作成
  - [x] `config/` ディレクトリ作成
  - [x] `scripts/` ディレクトリ作成
  - [x] `data/` ディレクトリ作成（SQLite用）
  - [x] `logs/` ディレクトリ作成（評価ログ用）

- [x] Task 2: Makefile の作成 (AC: #1)
  - [x] `dev` ターゲット（frontend/backend並列起動）
  - [x] `dev-frontend` ターゲット
  - [x] `dev-backend` ターゲット
  - [x] `lint` ターゲット
  - [x] `test` ターゲット
  - [x] `clean` ターゲット

- [x] Task 3: ルートpyproject.toml の作成 (AC: #2)
  - [x] プロジェクトメタデータ定義
  - [x] uvワークスペース設定（backend/を参照）
  - [x] 開発依存関係（ruff, pytest等）

- [x] Task 4: .gitignore の設定 (AC: #3)
  - [x] Python関連（__pycache__, .venv, *.pyc）
  - [x] Node.js関連（node_modules/, .next/）
  - [x] 環境ファイル（.env*, config/config.yaml）
  - [x] データ/ログ（data/*.db, logs/*.jsonl）
  - [x] IDE設定（.vscode/, .idea/）

- [x] Task 5: 基本設定ファイル
  - [x] `config/config.example.yaml` 作成
  - [x] `scripts/dev.sh` 作成（開発環境起動スクリプト）
  - [x] `scripts/setup.sh` 作成（初期セットアップスクリプト）

## Dev Notes

### アーキテクチャ準拠事項

**プロジェクト構成:**
- カスタムモノレポ構成（frontend/ + backend/）
- Python 3.12 + Node.js 20 LTS
- Tailwind CSS スタイリング

**ディレクトリ構造（Architecture.md準拠）:**
```
local-voice-assistant-claude-bmad/
├── frontend/                    # Next.js アプリ（Story 1.3で初期化）
├── backend/                     # FastAPI アプリ（Story 1.2で初期化）
├── config/                      # 設定ファイル
│   └── config.example.yaml
├── data/                        # SQLite DB格納
├── logs/                        # 評価ログ出力
├── scripts/
│   ├── dev.sh
│   └── setup.sh
├── Makefile
├── pyproject.toml               # ルートuv設定
├── README.md
└── .gitignore
```

### Project Structure Notes

**このStoryで作成するファイル:**
- `Makefile` - 開発タスク管理
- `pyproject.toml` (ルート) - uvワークスペース設定
- `.gitignore` - バージョン管理除外設定
- `config/config.example.yaml` - 設定サンプル
- `scripts/dev.sh` - 開発環境起動
- `scripts/setup.sh` - 初期セットアップ

**このStoryでは作成しないファイル:**
- `frontend/` 内のファイル → Story 1.3
- `backend/` 内のファイル → Story 1.2
- `README.md` → ドキュメント要件がある場合のみ

### 技術仕様

**Makefile構成:**
```makefile
.PHONY: dev dev-frontend dev-backend lint test clean

dev:
	make -j2 dev-frontend dev-backend

dev-frontend:
	cd frontend && npm run dev

dev-backend:
	cd backend && uv run uvicorn voice_assistant.main:app --reload --port 8000

lint:
	cd backend && uv run ruff check .
	cd frontend && npm run lint

test:
	cd backend && uv run pytest
	cd frontend && npm test

clean:
	rm -rf frontend/.next frontend/node_modules
	rm -rf backend/.venv
```

**ルートpyproject.toml:**
```toml
[project]
name = "local-voice-assistant-claude-bmad"
version = "0.1.0"
description = "日本語特化ローカル音声対話アシスタント"
requires-python = ">=3.12"

[tool.uv.workspace]
members = ["backend"]

[tool.ruff]
line-length = 88
target-version = "py312"
```

**config/config.example.yaml:**
```yaml
# LLM設定
llm:
  provider: ollama  # ollama, openai, groq
  model: qwen2.5:7b
  base_url: http://localhost:11434/v1
  api_key: ""

# サーバー設定
server:
  host: "0.0.0.0"
  port: 8000
  cors_origins:
    - "http://localhost:3000"

# ログ設定
logging:
  level: INFO
  eval_log_path: logs/eval.jsonl
```

### 依存関係

- **前提条件:** なし（最初のStory）
- **後続Story:**
  - Story 1.2 (Backend基盤) - `backend/` 内のファイル作成
  - Story 1.3 (Frontend基盤) - `frontend/` 内のファイル作成
  - Story 1.4 (統合開発環境) - Makefileが動作する状態

### テスト基準

1. ディレクトリ構造が正しく作成されている
2. `make dev-frontend` と `make dev-backend` がエラーなく実行開始される（実際の起動はStory 1.2/1.3後）
3. `.gitignore` が適切にファイルを除外している
4. `config/config.example.yaml` が有効なYAMLとして読み込める

### References

- [Source: _bmad-output/architecture.md#Starter-Template-Evaluation]
- [Source: _bmad-output/architecture.md#Project-Structure]
- [Source: _bmad-output/prd.md#MVP-Scope]
- [Source: _bmad-output/project-planning-artifacts/epics.md#Story-1.1]

## Dev Agent Record

### Agent Model Used

Claude Opus 4.5 (claude-opus-4-5-20251101)

### Debug Log References

N/A - 基盤セットアップのため実行テストは後続Storyで実施

### Completion Notes List

- Task 1: 6ディレクトリ作成完了（frontend/, backend/, config/, scripts/, data/, logs/）
- Task 2: Makefile作成 - dev, dev-frontend, dev-backend, lint, lint-fix, test, test-backend, test-frontend, setup, clean ターゲット
- Task 3: pyproject.toml作成 - プロジェクトメタデータ、uvワークスペース設定、ruff設定、pytest設定
- Task 4: .gitignore作成 - Python, Node.js, 環境ファイル, データ/ログ, IDE設定, モデルファイルを除外
- Task 5: config/config.example.yaml, scripts/dev.sh, scripts/setup.sh 作成
- 全ACを満たすディレクトリ構造とファイルが作成された

### File List

**Created:**
- `frontend/` (directory)
- `backend/` (directory)
- `config/` (directory)
- `config/config.example.yaml`
- `scripts/` (directory)
- `scripts/dev.sh`
- `scripts/setup.sh`
- `data/` (directory)
- `logs/` (directory)
- `Makefile`
- `pyproject.toml`
- `.gitignore`

## Senior Developer Review

### Review Date
2025-12-27

### Issues Found
- **HIGH**: 0
- **MEDIUM**: 3 (all fixed)
- **LOW**: 1 (acknowledged, not fixed)

### Issues Fixed

1. **MEDIUM - scripts/setup.sh forward-compatibility**
   - Issue: Script would fail if `backend/pyproject.toml` doesn't exist (Story 1.2 not yet implemented)
   - Fix: Added existence check with skip message

2. **MEDIUM - scripts/setup.sh frontend check**
   - Issue: Script would fail if `frontend/package.json` doesn't exist (Story 1.3 not yet implemented)
   - Fix: Added existence check with skip message

3. **MEDIUM - scripts/dev.sh forward-compatibility**
   - Issue: Same issues as setup.sh - would fail without Story 1.2/1.3 files
   - Fix: Added existence checks with warning messages

### Issues Acknowledged (Not Fixed)

1. **LOW - .gitignore does not exclude _bmad-output/**
   - Rationale: Planning artifacts may be intentionally tracked in version control
   - Decision: Left as-is per project requirements

### Review Outcome
**PASS** - All blocking issues resolved, story approved for completion

## Change Log

- 2025-12-27: Code review completed - 3 MEDIUM issues fixed in scripts/setup.sh and scripts/dev.sh
- 2025-12-27: Story 1.1 実装完了 - モノレポ構造初期化（全5タスク完了）
