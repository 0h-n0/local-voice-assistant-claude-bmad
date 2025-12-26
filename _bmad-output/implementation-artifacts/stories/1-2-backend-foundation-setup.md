# Story 1.2: Backend基盤セットアップ

Status: done

## Story

As a **開発者**,
I want **FastAPIバックエンドの基盤が構築されている**,
so that **APIエンドポイントの開発を開始できる**.

## Acceptance Criteria

1. **Given** モノレポ構造が初期化済み（Story 1.1完了）
   **When** `cd backend && uv sync`を実行する
   **Then** FastAPI、uvicorn、pydantic等の依存関係がインストールされる

2. **And** `backend/src/voice_assistant/main.py`にFastAPIアプリが作成される

3. **And** `/api/v1/health`エンドポイントが`{"status": "ok"}`を返す

4. **And** `uv run uvicorn voice_assistant.main:app`で起動できる

## Tasks / Subtasks

- [x] Task 1: backend/pyproject.toml の作成 (AC: #1)
  - [x] パッケージメタデータ定義（name: voice-assistant）
  - [x] 依存関係追加: fastapi, uvicorn[standard], pydantic, pyyaml
  - [x] 依存関係追加: sqlmodel (DB用、後続Story準備)
  - [x] 依存関係追加: structlog (ログ用)
  - [x] 開発依存関係: pytest, pytest-asyncio, httpx

- [x] Task 2: Pythonパッケージ構造の作成 (AC: #2)
  - [x] `backend/src/voice_assistant/__init__.py` 作成
  - [x] `backend/src/voice_assistant/main.py` 作成（FastAPIアプリ）
  - [x] `backend/src/voice_assistant/api/__init__.py` 作成
  - [x] `backend/src/voice_assistant/core/__init__.py` 作成
  - [x] `backend/src/voice_assistant/core/config.py` 作成（設定管理）
  - [x] `backend/src/voice_assistant/core/logging.py` 作成（structlog設定）

- [x] Task 3: Health Check API の実装 (AC: #3)
  - [x] `GET /api/v1/health` エンドポイント実装
  - [x] レスポンス: `{"status": "ok"}`
  - [x] CORS設定（localhost:3000許可）

- [x] Task 4: 起動確認とテスト (AC: #4)
  - [x] `uv sync` で依存関係インストール確認
  - [x] `uv run uvicorn voice_assistant.main:app --reload` で起動確認
  - [x] `/api/v1/health` エンドポイントの動作確認
  - [x] 基本的なユニットテスト作成

## Dev Notes

### アーキテクチャ準拠事項

**ディレクトリ構造（Architecture.md準拠）:**
```
backend/
├── src/
│   └── voice_assistant/
│       ├── __init__.py
│       ├── main.py                 # FastAPI エントリーポイント
│       ├── api/                    # API層
│       │   └── __init__.py
│       └── core/                   # 共通基盤
│           ├── __init__.py
│           ├── config.py           # 設定管理
│           └── logging.py          # structlog設定
├── tests/
│   ├── __init__.py
│   └── test_health.py
├── pyproject.toml
└── uv.lock
```

### 技術仕様

**backend/pyproject.toml:**
```toml
[project]
name = "voice-assistant"
version = "0.1.0"
description = "日本語特化ローカル音声対話アシスタント - Backend"
requires-python = ">=3.12"
dependencies = [
    "fastapi>=0.115.0",
    "uvicorn[standard]>=0.32.0",
    "pydantic>=2.10.0",
    "pydantic-settings>=2.6.0",
    "pyyaml>=6.0",
    "sqlmodel>=0.0.22",
    "structlog>=24.4.0",
]

[project.optional-dependencies]
dev = [
    "pytest>=8.3.0",
    "pytest-asyncio>=0.24.0",
    "httpx>=0.28.0",
]

[build-system]
requires = ["hatchling"]
build-backend = "hatchling.build"

[tool.hatch.build.targets.wheel]
packages = ["src/voice_assistant"]
```

**main.py エントリーポイント:**
```python
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

app = FastAPI(
    title="Voice Assistant API",
    version="0.1.0",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.get("/api/v1/health")
async def health_check():
    return {"status": "ok"}
```

**config.py 設定管理:**
```python
from pydantic_settings import BaseSettings
from pathlib import Path

class Settings(BaseSettings):
    # Server
    host: str = "0.0.0.0"
    port: int = 8000
    cors_origins: list[str] = ["http://localhost:3000"]

    # Logging
    log_level: str = "INFO"
    eval_log_path: Path = Path("logs/eval.jsonl")

    class Config:
        env_file = ".env"
        env_prefix = "VOICE_ASSISTANT_"

settings = Settings()
```

**logging.py structlog設定:**
```python
import structlog
from voice_assistant.core.config import settings

def configure_logging():
    structlog.configure(
        processors=[
            structlog.stdlib.filter_by_level,
            structlog.stdlib.add_logger_name,
            structlog.stdlib.add_log_level,
            structlog.processors.TimeStamper(fmt="iso"),
            structlog.processors.JSONRenderer()
        ],
        wrapper_class=structlog.stdlib.BoundLogger,
        context_class=dict,
        logger_factory=structlog.stdlib.LoggerFactory(),
    )
```

### 命名規則（Architecture準拠）

| 対象 | パターン | 例 |
|------|---------|-----|
| 変数/関数 | snake_case | `get_settings()` |
| クラス | PascalCase | `Settings` |
| モジュール | snake_case | `config.py` |
| エンドポイント | kebab-case | `/api/v1/health` |

### API レスポンスパターン

**成功レスポンス:**
```json
{
  "status": "ok"
}
```

**エラーレスポンス（後続Storyで実装）:**
```json
{
  "error": {
    "code": "ERROR_CODE",
    "message": "Human readable message"
  }
}
```

### 依存関係

- **前提条件:** Story 1.1 完了（モノレポ構造、ルート pyproject.toml）
- **後続Story:**
  - Story 1.3 (Frontend基盤) - 並行開発可能
  - Story 1.4 (統合開発環境) - Backend/Frontend両方必要
  - Story 2.1 (WebSocket基盤) - このStoryの基盤を利用

### テスト基準

1. `uv sync` が正常完了する
2. `uv run uvicorn voice_assistant.main:app` で起動する
3. `curl http://localhost:8000/api/v1/health` が `{"status":"ok"}` を返す
4. `uv run pytest` でテストが通過する

### Previous Story Learnings

Story 1.1 から:
- ルート `pyproject.toml` に `[tool.uv.workspace] members = ["backend"]` 設定済み
- `scripts/setup.sh` で `backend/pyproject.toml` 存在チェック追加済み
- Makefile の `dev-backend` ターゲットは `uv run uvicorn voice_assistant.main:app --reload --host 0.0.0.0 --port 8000` を期待

### References

- [Source: _bmad-output/architecture.md#Project-Structure]
- [Source: _bmad-output/architecture.md#Core-Architectural-Decisions]
- [Source: _bmad-output/architecture.md#Implementation-Patterns]
- [Source: _bmad-output/project-planning-artifacts/epics.md#Story-1.2]

## Dev Agent Record

### Agent Model Used

Claude Opus 4.5 (claude-opus-4-5-20251101)

### Debug Log References

N/A

### Completion Notes List

- Task 1: backend/pyproject.toml作成完了 - FastAPI 0.127.1, uvicorn 0.40.0, pydantic 2.12.5, sqlmodel 0.0.30, structlog 25.5.0
- Task 2: Pythonパッケージ構造作成完了 - src/voice_assistant/ 配下に main.py, api/, core/ を配置
- Task 3: Health Check API実装完了 - GET /api/v1/health → {"status": "ok"}, CORS設定済み
- Task 4: 起動確認・テスト完了 - uv sync成功、uvicorn起動確認、pytest 2テスト合格

### File List

**Created:**
- `backend/pyproject.toml`
- `backend/src/voice_assistant/__init__.py`
- `backend/src/voice_assistant/main.py`
- `backend/src/voice_assistant/api/__init__.py`
- `backend/src/voice_assistant/core/__init__.py`
- `backend/src/voice_assistant/core/config.py`
- `backend/src/voice_assistant/core/logging.py`
- `backend/tests/__init__.py`
- `backend/tests/test_health.py`

**Generated:**
- `backend/uv.lock`

## Senior Developer Review

### Review Summary

**Reviewer:** Senior Developer (Adversarial Review)
**Review Date:** 2025-12-27
**Result:** PASS (after auto-fix)
**Issues Found:** 6 (2 HIGH, 3 MEDIUM, 1 LOW)
**Issues Fixed:** 6/6

### Issues Fixed

| Severity | Issue | Fix Applied |
|----------|-------|-------------|
| HIGH | CORS configuration too permissive | Changed to explicit methods/headers with dev note |
| HIGH | Invalid log_level causes unhandled exception | Added Pydantic field_validator with fallback to INFO |
| MEDIUM | Settings module-level instantiation blocks testing | Added lru_cache factory function get_settings() |
| MEDIUM | Missing error path tests | Added tests for 405 and 404 responses |
| MEDIUM | configure_logging() called at import time | Moved to lifespan context manager |
| LOW | Inconsistent pytest config location | Consolidated to root pyproject.toml |

### Files Modified in Review

- `backend/src/voice_assistant/main.py` - CORS + lifespan
- `backend/src/voice_assistant/core/config.py` - Validation + lru_cache
- `backend/tests/test_health.py` - Added 2 error path tests
- `pyproject.toml` (root) - Added asyncio_mode
- `backend/pyproject.toml` - Removed duplicate pytest config

### Test Results After Fix

```
4 passed in 0.27s
- test_health_check_returns_ok
- test_health_check_content_type
- test_health_check_method_not_allowed
- test_nonexistent_endpoint_returns_404
```

## Change Log

- 2025-12-27: Code review完了 - 6件の問題を修正、テスト4件合格
- 2025-12-27: Story 1.2 実装完了 - Backend基盤セットアップ（全4タスク完了）
- 2025-12-27: Story 1.2 created via create-story workflow
