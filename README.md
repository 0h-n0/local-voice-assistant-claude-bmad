# Local Voice Assistant

日本語特化ローカル音声対話アシスタント - ブラウザベースの音声インターフェースで AI と自然に会話できます。

[![Release](https://img.shields.io/github/v/release/0h-n0/local-voice-assistant-claude-bmad)](https://github.com/0h-n0/local-voice-assistant-claude-bmad/releases)
[![License](https://img.shields.io/badge/license-AGPL--3.0-blue.svg)](LICENSE)

## 概要

Local Voice Assistant は、日本語音声認識 (STT)、大規模言語モデル (LLM)、音声合成 (TTS) を組み合わせた音声対話システムです。ブラウザ上で動作し、マイクからの音声入力をリアルタイムで処理します。

### 主な特徴

- **日本語特化 STT**: ReazonSpeech NeMo v2 による高精度な日本語音声認識
- **柔軟な LLM 対応**: OpenAI API、Ollama など OpenAI 互換 API に対応
- **自然な音声合成**: Style-BERT-VITS2 による感情豊かな日本語音声
- **ブラウザ VAD**: Voice Activity Detection でハンズフリー操作
- **会話履歴管理**: SQLite による永続化、一覧・詳細・削除機能
- **リアルタイム通信**: WebSocket によるストリーミング処理

## アーキテクチャ

```
┌─────────────────────────────────────────────────────────────────┐
│                        Browser (Frontend)                        │
│  ┌─────────────┐  ┌─────────────┐  ┌─────────────────────────┐  │
│  │  VAD        │  │  WebSocket  │  │  Audio Player           │  │
│  │  (ONNX)     │──│  Client     │──│  (Web Audio API)        │  │
│  └─────────────┘  └──────┬──────┘  └─────────────────────────┘  │
└──────────────────────────┼──────────────────────────────────────┘
                           │ WebSocket
┌──────────────────────────┼──────────────────────────────────────┐
│                     Backend (FastAPI)                            │
│  ┌─────────────┐  ┌──────┴──────┐  ┌─────────────────────────┐  │
│  │  STT        │  │  WebSocket  │  │  TTS                    │  │
│  │  ReazonSpeech│──│  Handler    │──│  Style-BERT-VITS2       │  │
│  └─────────────┘  └──────┬──────┘  └─────────────────────────┘  │
│                          │                                       │
│                   ┌──────┴──────┐                               │
│                   │  LLM        │                               │
│                   │  OpenAI API │                               │
│                   └──────┬──────┘                               │
│                          │                                       │
│                   ┌──────┴──────┐                               │
│                   │  SQLite DB  │                               │
│                   │  (会話履歴)  │                               │
│                   └─────────────┘                               │
└─────────────────────────────────────────────────────────────────┘
```

## 必要要件

### システム要件

- **OS**: Linux (Ubuntu 22.04+), macOS, Windows (WSL2)
- **Python**: 3.12+
- **Node.js**: 20+
- **GPU** (推奨): NVIDIA GPU with CUDA 12.1+ (STT/TTS 高速化)

### 依存ツール

- [uv](https://github.com/astral-sh/uv) - Python パッケージマネージャー
- [npm](https://www.npmjs.com/) - Node.js パッケージマネージャー
- [git](https://git-scm.com/) - バージョン管理

## インストール

### 1. リポジトリのクローン

```bash
git clone https://github.com/0h-n0/local-voice-assistant-claude-bmad.git
cd local-voice-assistant-claude-bmad
```

### 2. バックエンドのセットアップ

```bash
cd backend
uv sync
```

### 3. フロントエンドのセットアップ

```bash
cd frontend
npm install
```

### 4. TTS モデルのダウンロード

Style-BERT-VITS2 モデルをダウンロードします：

```bash
mkdir -p models/tts
cd models/tts

# jvnv-F1-jp モデル (女性音声) をダウンロード
curl -L -o config.json "https://huggingface.co/litagin/style_bert_vits2_jvnv/resolve/main/jvnv-F1-jp/config.json"
curl -L -o style_vectors.npy "https://huggingface.co/litagin/style_bert_vits2_jvnv/resolve/main/jvnv-F1-jp/style_vectors.npy"
curl -L -o jvnv-F1-jp.safetensors "https://huggingface.co/litagin/style_bert_vits2_jvnv/resolve/main/jvnv-F1-jp/jvnv-F1-jp_e160_s14000.safetensors"
```

他の音声モデル:
- `jvnv-F2-jp` - 女性音声 2
- `jvnv-M1-jp` - 男性音声 1
- `jvnv-M2-jp` - 男性音声 2

## 設定

### 環境変数

```bash
# OpenAI API を使用する場合
export OPENAI_API_KEY="your-api-key"
export OPENAI_BASE_URL="https://api.openai.com/v1"
export LLM_MODEL="gpt-4o-mini"

# Ollama を使用する場合
export OPENAI_BASE_URL="http://localhost:11434/v1"
export LLM_MODEL="llama3.2"
```

### 設定ファイル (オプション)

`config/config.yaml` を作成してカスタマイズできます：

```yaml
llm:
  provider: openai
  model: gpt-4o-mini
  base_url: https://api.openai.com/v1

stt:
  model: reazon-nemo-v2
  device: auto  # cuda, cpu, auto

tts:
  model: style-bert-vits2
  device: auto

server:
  host: "0.0.0.0"
  port: 8000
  cors_origins:
    - "http://localhost:3000"
```

## 使用方法

### 開発サーバーの起動

```bash
# プロジェクトルートから
make dev
```

または個別に起動：

```bash
# バックエンド (ターミナル 1)
cd backend
OPENAI_API_KEY="your-key" OPENAI_BASE_URL="https://api.openai.com/v1" LLM_MODEL="gpt-4o-mini" \
  uv run uvicorn voice_assistant.main:app --host 0.0.0.0 --port 8000

# フロントエンド (ターミナル 2)
cd frontend
npm run dev
```

### アクセス

ブラウザで http://localhost:3000 を開きます。

### 操作方法

1. **接続**: 画面中央の接続ボタンをクリック
2. **録音開始**: マイクボタンをクリックして VAD を有効化
3. **会話**: マイクに向かって話すと自動で認識・応答
4. **履歴**: サイドバーで過去の会話を確認・削除

## プロジェクト構成

```
local-voice-assistant-claude-bmad/
├── backend/                    # FastAPI バックエンド
│   ├── src/voice_assistant/
│   │   ├── api/               # API エンドポイント
│   │   │   ├── websocket.py   # WebSocket ハンドラー
│   │   │   └── ...
│   │   ├── db/                # データベース層
│   │   ├── llm/               # LLM サービス
│   │   ├── stt/               # 音声認識サービス
│   │   ├── tts/               # 音声合成サービス
│   │   └── main.py            # アプリケーションエントリ
│   ├── tests/                 # テスト
│   └── pyproject.toml         # Python 依存関係
│
├── frontend/                   # Next.js フロントエンド
│   ├── src/
│   │   ├── app/               # Next.js App Router
│   │   ├── components/        # React コンポーネント
│   │   ├── core/              # コアロジック
│   │   ├── hooks/             # カスタムフック
│   │   ├── lib/               # ユーティリティ
│   │   └── stores/            # Zustand ストア
│   └── package.json           # Node.js 依存関係
│
├── config/                     # 設定ファイル
│   └── config.example.yaml
│
├── models/                     # モデルファイル (gitignore)
│   └── tts/                   # TTS モデル
│
├── data/                       # データファイル (gitignore)
│   └── voice_assistant.db     # SQLite データベース
│
└── Makefile                    # 開発タスク
```

## 開発

### Makefile コマンド

```bash
make dev          # 開発サーバー起動
make lint         # リンター実行
make lint-fix     # リンター自動修正
make test         # テスト実行
make setup        # 初期セットアップ
make clean        # ビルド成果物削除
```

### テスト

```bash
# バックエンドテスト
cd backend
uv run pytest

# フロントエンドリント
cd frontend
npm run lint
```

## API リファレンス

### REST API

| エンドポイント | メソッド | 説明 |
|--------------|--------|------|
| `/api/v1/health` | GET | ヘルスチェック |
| `/api/v1/conversations` | GET | 会話一覧取得 |
| `/api/v1/conversations/{id}` | GET | 会話詳細取得 |
| `/api/v1/conversations/{id}` | DELETE | 会話削除 |

### WebSocket API

エンドポイント: `/api/v1/ws/chat`

#### クライアント → サーバー

| イベント | 説明 |
|---------|------|
| `vad.start` | 音声検出開始 |
| `vad.audio` | 音声データ送信 (バイナリ) |
| `vad.end` | 音声検出終了 |

#### サーバー → クライアント

| イベント | 説明 |
|---------|------|
| `stt.partial` | STT 中間結果 |
| `stt.final` | STT 最終結果 |
| `llm.start` | LLM 処理開始 |
| `llm.chunk` | LLM ストリーミングチャンク |
| `llm.end` | LLM 処理完了 |
| `tts.chunk` | TTS 音声チャンク (Base64 PCM16) |
| `tts.end` | TTS 処理完了 |
| `error` | エラー通知 |

## トラブルシューティング

### VAD が動作しない (404 エラー)

WASM ファイルが不足している可能性があります：

```bash
cd frontend
npm run postinstall
```

### TTS が動作しない

モデルファイルが正しくダウンロードされているか確認：

```bash
ls -la models/tts/
# config.json, *.safetensors, style_vectors.npy が必要
```

### LLM 接続エラー

環境変数を確認：

```bash
echo $OPENAI_API_KEY
echo $OPENAI_BASE_URL
echo $LLM_MODEL
```

### GPU が使用されない

CUDA が利用可能か確認：

```python
import torch
print(torch.cuda.is_available())
```

## ライセンス

**AGPL-3.0 License**

このプロジェクトは [Style-BERT-VITS2](https://github.com/litagin02/Style-Bert-VITS2) を使用しているため、AGPL-3.0 ライセンスが適用されます。

- ソースコードの公開が必要
- ネットワーク経由で使用する場合もソース公開が必要
- 派生作品も AGPL-3.0 でライセンスする必要あり

## 謝辞

- [ReazonSpeech](https://github.com/reazon-research/ReazonSpeech) - 日本語音声認識
- [Style-BERT-VITS2](https://github.com/litagin02/Style-Bert-VITS2) - 日本語音声合成
- [@ricky0123/vad](https://github.com/ricky0123/vad) - ブラウザ VAD
- [FastAPI](https://fastapi.tiangolo.com/) - Python Web フレームワーク
- [Next.js](https://nextjs.org/) - React フレームワーク
