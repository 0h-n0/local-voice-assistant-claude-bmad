---
stepsCompleted: []
inputDocuments: []
workflowType: 'research'
lastStep: 1
research_type: 'technical'
research_topic: 'ローカル日本語音声対話アシスタント技術スタック'
research_goals: '実装可能性、性能比較、統合パターン、ベストプラクティス'
user_name: 'y'
date: '2025-12-26'
web_research_enabled: true
source_verification: true
---

# Technical Research Report: ローカル日本語音声対話アシスタント

**Date:** 2025-12-26
**Author:** y
**Research Type:** Technical Research

---

## Research Overview

### 調査目的

ローカル環境で動作する日本語音声対話アシスタントの実装に必要な技術スタックについて、最新の情報を収集し、実装可能性と最適な構成を評価する。

### 調査対象

1. **STT**: ReazonSpeech NeMo v2
2. **TTS**: VOICEVOX / Style-BERT-VITS2 / Piper
3. **通信**: WebSocket + FastAPI リアルタイムストリーミング
4. **LLM**: Ollama 日本語性能
5. **入力処理**: VAD（音声活動検出）実装パターン

### 調査基準

- 実装可能性と導入難易度
- 性能（レイテンシ、精度、リソース使用量）
- FastAPI/Next.js との統合パターン
- ベストプラクティスと注意点

---

## 1. ReazonSpeech NeMo v2（STT）

### 概要

| 項目 | 詳細 |
|------|------|
| **パラメータ数** | 619M |
| **アーキテクチャ** | Fast Conformer + RNN-T |
| **学習データ** | ReazonSpeech v2.0 (35,000時間) |
| **対応音声長** | 数時間まで（NeMo版）/ 約30秒（K2版） |
| **精度** | Whisper v1/v2/v3 より高精度 |
| **速度** | Whisper Tiny と同等速度 |
| **ライセンス** | Apache License 2.0 |

### 実装例

```python
from reazonspeech.nemo.asr import load_model, transcribe, audio_from_path

audio = audio_from_path("speech.wav")
model = load_model()
ret = transcribe(model, audio)
print(ret.text)
```

### FastAPI統合例

```python
from fastapi import FastAPI, UploadFile, File
from reazonspeech.nemo.asr import load_model, transcribe, audio_from_path
import tempfile

app = FastAPI()
model = load_model()  # 起動時に1回ロード

@app.post("/transcribe")
async def transcribe_audio(file: UploadFile = File(...)):
    with tempfile.NamedTemporaryFile(suffix=".wav", delete=False) as tmp:
        content = await file.read()
        tmp.write(content)
        tmp_path = tmp.name

    audio = audio_from_path(tmp_path)
    result = transcribe(model, audio)
    return {"text": result.text}
```

### Sources

- [Hugging Face - reazonspeech-nemo-v2](https://huggingface.co/reazon-research/reazonspeech-nemo-v2)
- [ReazonSpeech v2.1 公式ブログ](https://research.reazon.jp/blog/2024-08-01-ReazonSpeech.html)
- [GitHub - ReazonSpeech](https://github.com/reazon-research/ReazonSpeech)
- [ReazonSpeech クイックスタート](https://research.reazon.jp/projects/ReazonSpeech/quickstart.html)

---

## 2. TTS エンジン比較

### VOICEVOX

| 項目 | 詳細 |
|------|------|
| **アーキテクチャ** | FastAPI ベースの RESTful API |
| **インターフェース** | REST API (localhost:50021) |
| **認証** | デフォルトなし（CORS設定で制御） |
| **Python クライアント** | `voicevox-client` (非公式) |
| **特徴** | 多数のキャラクター、感情表現 |

**使用例:**

```python
from vvclient import Client
import asyncio

async def main():
    async with Client() as client:
        audio_query = await client.create_audio_query("こんにちは！", speaker=1)
        with open("voice.wav", "wb") as f:
            f.write(await audio_query.synthesis(speaker=1))

asyncio.run(main())
```

### Style-BERT-VITS2

| 項目 | 詳細 |
|------|------|
| **ベース** | Bert-VITS2 v2.1 + JP-Extra |
| **学習データ** | 約800時間（日本語特化） |
| **特徴** | 感情・スタイル制御、SDP/DP比率調整 |
| **インストール** | `pip install style-bert-vits2` |
| **GPU** | 推奨（CPUでも動作可） |

### Piper TTS

| 項目 | 詳細 |
|------|------|
| **速度** | 最速クラス（1秒未満） |
| **日本語対応** | 限定的（OpenJTalk連携で改善） |
| **拡張** | `piper-tts-plus` で日本語強化 |
| **特徴** | 超軽量、ローカル完結、50+言語 |

### TTS比較まとめ

| TTS | 日本語品質 | 速度 | 導入難度 | 推奨用途 |
|-----|-----------|------|---------|---------|
| **VOICEVOX** | ◎ | ○ | 低 | 標準利用、キャラ重視 |
| **Style-BERT-VITS2** | ◎ | △ | 中 | 感情表現、カスタム音声 |
| **Piper** | △〜○ | ◎ | 低 | 軽量環境、高速応答 |

### Sources

- [VOICEVOX Engine API Reference](https://deepwiki.com/VOICEVOX/voicevox_engine/4-api-reference)
- [voicevox-client Python](https://github.com/voicevox-client/python)
- [Style-BERT-VITS2 GitHub](https://github.com/litagin02/Style-Bert-VITS2)
- [Piper GitHub](https://github.com/rhasspy/piper)

---

## 3. WebSocket + FastAPI リアルタイムストリーミング

### 基本実装パターン

```python
from fastapi import FastAPI, WebSocket
import asyncio

app = FastAPI()

@app.websocket("/ws/audio")
async def websocket_endpoint(websocket: WebSocket):
    await websocket.accept()
    audio_queue = asyncio.Queue()

    try:
        while True:
            # バイナリ音声データ受信
            audio_data = await websocket.receive_bytes()
            # 処理後、音声データ送信
            processed_audio = await process_audio(audio_data)
            await websocket.send_bytes(processed_audio)
    except Exception as e:
        print(f"Error: {e}")
    finally:
        await websocket.close()
```

### ベストプラクティス

| 項目 | 推奨 |
|------|------|
| **音声フォーマット** | WebM (ブラウザ) → WAV/PCM (処理) |
| **サンプリングレート** | 16kHz (STT最適) |
| **チャンネル** | モノラル (channelCount: 1) |
| **バッファリング** | `asyncio.Queue()` で非同期処理 |
| **レート制御** | 時間ベースで送信（長さベースではNG） |

### クライアント側 (JavaScript)

```javascript
const constraints = {
  audio: {
    channelCount: 1,
    sampleRate: 16000,
    sampleSize: 16
  }
}

const stream = await navigator.mediaDevices.getUserMedia(constraints)
const ws = new WebSocket("ws://localhost:8000/ws/audio")

ws.onopen = () => {
  // MediaRecorder で音声チャンクを送信
}
```

### Sources

- [FastAPI WebSockets 公式ドキュメント](https://fastapi.tiangolo.com/advanced/websockets/)
- [Real-Time Audio Processing with FastAPI & Whisper 2024](https://trinesis.com/blog/articles-1/real-time-audio-processing-with-fastapi-whisper-complete-guide-2024-70)
- [whisper_streaming_web GitHub](https://github.com/ScienceIO/whisper_streaming_web)

---

## 4. Ollama 日本語性能

### 日本語対応モデル比較

| モデル | サイズ | 日本語対応 | 特徴 |
|--------|--------|-----------|------|
| **Qwen 2.5** | 0.5B〜72B | ◎ | 29言語対応、アジア言語強い |
| **Gemma-2-JPN** | 2B | ◎ | 日本語ファインチューン済み |
| **Suzume-Llama3** | 8B | ○ | Llama3日本語ファインチューン |
| **Mistral Small 3** | 22B | ○ | 多言語対応（日本語含む） |

### 用途別推奨モデル

| 用途 | 推奨モデル |
|------|-----------|
| **軽量・高速** | Qwen 2.5 (3B/7B) |
| **日本語特化** | Gemma-2-JPN (2B), Suzume-Llama3 (8B) |
| **高品質応答** | Qwen 2.5 (14B/32B) |
| **クラウド併用** | OpenAI GPT-4o-mini, Claude Haiku |

### OpenAI API互換設定

```bash
# Ollama サーバー起動
ollama serve

# モデル実行
ollama run qwen2.5:7b
```

```python
from openai import OpenAI

client = OpenAI(
    base_url="http://localhost:11434/v1",
    api_key="ollama"  # 任意
)

response = client.chat.completions.create(
    model="qwen2.5:7b",
    messages=[{"role": "user", "content": "こんにちは"}]
)
```

### Sources

- [Qwen2.5 公式ブログ](https://qwenlm.github.io/blog/qwen2.5/)
- [Ollama Suzume-Llama3](https://ollama.com/microai/suzume-llama3)
- [Ollama Gemma-2-JPN](https://ollama.com/schroneko/gemma-2-2b-jpn-it)
- [Best Ollama Models 2025](https://collabnix.com/best-ollama-models-in-2025-complete-performance-comparison/)

---

## 5. VAD（音声活動検出）実装パターン

### フロントエンド (JavaScript)

| ライブラリ | 特徴 | 実装難度 |
|-----------|------|---------|
| **@ricky0123/vad** | Silero VAD + ONNX Runtime、React対応 | 低 |
| **Picovoice Cobra** | 軽量、プライバシー重視 | 中 |
| **voixen-vad** | WebRTC ベース | 中 |

**@ricky0123/vad 使用例:**

```javascript
import { MicVAD } from "@ricky0123/vad-web"

const myvad = await MicVAD.new({
  onSpeechStart: () => {
    console.log("Speech start")
  },
  onSpeechEnd: (audio) => {
    sendToServer(audio)
  }
})

myvad.start()
```

### バックエンド (Python)

| ライブラリ | サイズ | 速度 | 言語対応 |
|-----------|--------|------|---------|
| **Silero VAD** | 1.8MB | <1ms/chunk | 6000+言語 |
| **pysilero-vad** | 軽量 | 高速 | 同上 |

**Silero VAD 使用例:**

```python
import torch
torch.set_num_threads(1)

model, utils = torch.hub.load('snakers4/silero-vad', 'silero_vad')
get_speech_timestamps, _, read_audio, _, _ = utils

wav = read_audio('audio.wav', sampling_rate=16000)
speech_timestamps = get_speech_timestamps(wav, model, sampling_rate=16000)
```

### 推奨アーキテクチャ

```
[マイク] → [WebAudio API] → [@ricky0123/vad] → [発話検出]
                                    ↓
                           [WebSocket送信] → [FastAPI]
```

### Sources

- [ricky0123/vad GitHub](https://github.com/ricky0123/vad)
- [Silero VAD GitHub](https://github.com/snakers4/silero-vad)
- [Silero VAD PyTorch Hub](https://pytorch.org/hub/snakers4_silero-vad_vad/)

---

## 推奨技術スタック

### 最終推奨構成

| コンポーネント | 技術 | 理由 |
|---------------|------|------|
| **STT** | ReazonSpeech NeMo v2 | 日本語最高精度、高速 |
| **LLM (ローカル)** | Qwen 2.5 (7B/14B) | 日本語強い、OpenAI互換 |
| **LLM (クラウド)** | OpenAI GPT-4o-mini | コスパ良い |
| **TTS (標準)** | VOICEVOX | 導入簡単、キャラ豊富 |
| **TTS (研究)** | Style-BERT-VITS2 | カスタム音声可能 |
| **TTS (軽量)** | Piper | 最速 |
| **VAD (フロント)** | @ricky0123/vad | React対応、簡単 |
| **通信** | WebSocket | 双方向リアルタイム |

---

## Research Completed: 2025-12-26

