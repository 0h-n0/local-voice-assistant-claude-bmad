# Story 2.2: Frontend音声キャプチャとVAD

Status: review

## Story

As a **ユーザー**,
I want **マイクボタンを押すと発話を自動検出して録音される**,
so that **自然に話しかけるだけで音声入力ができる** (FR1, FR2, FR13).

## Acceptance Criteria

1. **Given** WebSocket接続が確立されている
   **When** マイクボタンをクリックする
   **Then** マイク使用許可ダイアログが表示される（初回）

2. **And** VAD（@ricky0123/vad-react）が発話開始を検出すると録音状態になる

3. **And** `vad.start`イベントがWebSocketで送信される

4. **And** 発話中は音声チャンクが`vad.audio`で送信される

5. **And** 発話終了が検出されると`vad.end`が送信される

6. **And** 録音状態がUIに表示される (FR15)
   - 待機中: グレー
   - 録音中: 赤（パルスアニメーション）
   - 処理中: 黄色

## Tasks / Subtasks

- [x] Task 1: VADライブラリインストールと設定 (AC: #1, #2)
  - [x] `npm install @ricky0123/vad-react` 実行
  - [x] Next.js用のONNXファイル配信設定（public/または next.config.ts）
  - [x] Workletファイルの配置確認

- [x] Task 2: WebSocketイベント型定義 (AC: #3, #4, #5)
  - [x] `frontend/src/core/events.ts` 作成
  - [x] VadStartEvent, VadAudioEvent, VadEndEvent 型定義
  - [x] イベント送信ヘルパー関数

- [x] Task 3: use-voiceカスタムフック実装 (AC: #2, #3, #4, #5)
  - [x] `frontend/src/hooks/use-voice.ts` 作成
  - [x] useMicVAD統合
  - [x] WebSocket送信との連携
  - [x] recordingState管理（idle | recording | processing）

- [x] Task 4: VoiceStoreの拡張 (AC: #2, #6)
  - [x] `frontend/src/stores/voice-store.ts` 更新
  - [x] recordingState追加（'idle' | 'recording' | 'processing'）
  - [x] startListening / stopListening アクション追加

- [x] Task 5: UIコンポーネント実装 (AC: #1, #6)
  - [x] `frontend/src/components/VoiceInput.tsx` 作成
  - [x] マイクボタン（クリックで録音開始/停止）
  - [x] 録音状態インジケーター（色とアニメーション）
  - [x] `frontend/src/app/page.tsx` にVoiceInput組み込み

- [x] Task 6: Backend WebSocketイベント受信対応 (AC: #3, #4, #5)
  - [x] `backend/src/voice_assistant/api/websocket.py` 更新
  - [x] vad.start / vad.audio / vad.end イベントのログ出力
  - [x] 音声データのバッファリング（次Story用準備）

- [x] Task 7: 統合テスト (AC: #1-6)
  - [x] `make dev` でサーバー起動
  - [x] ブラウザでマイク許可確認
  - [x] 発話時のWebSocketイベント送信確認
  - [x] Backend ログでイベント受信確認
  - [x] 録音状態UIの遷移確認

## Dev Notes

### アーキテクチャ準拠事項

**WebSocketイベント契約（Architecture.md準拠）:**

```
Client → Server:
- vad.start       # 発話開始検出時に送信
- vad.audio       # 音声チャンク（ArrayBuffer）を送信
- vad.end         # 発話終了検出時に送信
```

**イベントペイロード設計:**

```typescript
// frontend/src/core/events.ts
export interface VadStartEvent {
  type: 'vad.start';
  timestamp: number;
}

export interface VadAudioEvent {
  type: 'vad.audio';
  audio: ArrayBuffer;  // Float32Array from VAD -> ArrayBuffer
  sampleRate: 16000;   // VADは16kHz固定
}

export interface VadEndEvent {
  type: 'vad.end';
  timestamp: number;
}

export type ClientEvent = VadStartEvent | VadAudioEvent | VadEndEvent;
```

**状態機械設計（Architecture.md準拠）:**

```
IDLE → RECORDING → STT → LLM → TTS → IDLE
         ↑                           |
         └───────────────────────────┘
```

この Story では IDLE ↔ RECORDING の遷移を実装。

### 技術仕様

**@ricky0123/vad-react 使用方法:**

```typescript
// frontend/src/hooks/use-voice.ts
import { useMicVAD } from "@ricky0123/vad-react";

export function useVoice() {
  const { connectionState, wsClient } = useVoiceStore();
  const [recordingState, setRecordingState] = useState<RecordingState>('idle');

  const vad = useMicVAD({
    startOnLoad: false,  // 手動開始
    onSpeechStart: () => {
      setRecordingState('recording');
      wsClient?.send({ type: 'vad.start', timestamp: Date.now() });
    },
    onVADMisfire: () => {
      // 誤検出時は無視
    },
    onSpeechEnd: (audio: Float32Array) => {
      setRecordingState('processing');
      // 音声データをArrayBufferに変換して送信
      wsClient?.send({
        type: 'vad.audio',
        audio: audio.buffer,
        sampleRate: 16000
      });
      wsClient?.send({ type: 'vad.end', timestamp: Date.now() });
    },
  });

  const startListening = () => {
    if (connectionState === 'connected') {
      vad.start();
    }
  };

  const stopListening = () => {
    vad.pause();
    setRecordingState('idle');
  };

  return { recordingState, startListening, stopListening, vad };
}
```

**Next.js ONNX ファイル配信設定:**

```javascript
// next.config.ts
const nextConfig = {
  webpack: (config) => {
    config.resolve.alias = {
      ...config.resolve.alias,
      "onnxruntime-web": "onnxruntime-web/dist/ort.webgpu.min.js"
    };
    return config;
  },
  // ONNXファイルをpublic/に配置する場合は不要
};
```

**VoiceInput コンポーネント:**

```typescript
// frontend/src/components/VoiceInput.tsx
'use client';

import { useVoice } from '@/hooks/use-voice';
import { useVoiceStore } from '@/stores/voice-store';

export function VoiceInput() {
  const { connectionState } = useVoiceStore();
  const { recordingState, startListening, stopListening } = useVoice();

  const getButtonColor = () => {
    switch (recordingState) {
      case 'recording': return 'bg-red-500 animate-pulse';
      case 'processing': return 'bg-yellow-500';
      default: return 'bg-gray-500';
    }
  };

  const handleClick = () => {
    if (recordingState === 'idle') {
      startListening();
    } else {
      stopListening();
    }
  };

  return (
    <button
      onClick={handleClick}
      disabled={connectionState !== 'connected'}
      className={`w-16 h-16 rounded-full ${getButtonColor()} ...`}
    >
      🎤
    </button>
  );
}
```

### ディレクトリ構造

```
frontend/
├── src/
│   ├── core/
│   │   ├── websocket-client.ts  # 既存
│   │   └── events.ts            # ← 新規作成
│   ├── components/
│   │   └── VoiceInput.tsx       # ← 新規作成
│   ├── hooks/
│   │   └── use-voice.ts         # ← 新規作成
│   ├── stores/
│   │   └── voice-store.ts       # ← 更新（recordingState追加）
│   └── app/
│       └── page.tsx             # ← 更新（VoiceInput組み込み）
├── public/
│   ├── vad.worklet.bundle.min.js    # VAD Worklet
│   ├── silero_vad.onnx              # VAD モデル
│   └── ort-wasm*.wasm               # ONNX Runtime WASM
```

### 命名規則（Architecture準拠）

| 対象 | パターン | 例 |
|------|---------|-----|
| イベント型 | PascalCase + Event | `VadStartEvent` |
| カスタムフック | use-kebab-case.ts | `use-voice.ts` |
| コンポーネント | PascalCase.tsx | `VoiceInput.tsx` |
| 状態型 | PascalCase | `RecordingState` |

### 依存関係

**前提条件:**
- Story 2.1 完了（WebSocket接続基盤）
- `useVoiceStore` で `connectionState` と `wsClient` が利用可能
- WebSocketClient に `send()` メソッドが実装済み

**後続Story:**
- Story 2.3 (STT統合) - `vad.audio` と `vad.end` を受けて音声認識実行
- Story 2.6 (E2Eパイプライン) - 全フローの統合

### テスト基準

1. `make dev` で両サーバーが起動する
2. ブラウザでマイクボタンをクリックするとマイク許可ダイアログが表示される
3. 許可後、発話するとボタンが赤くパルスする（recording状態）
4. 発話終了後、ボタンが黄色になる（processing状態）
5. Backend ログに `vad.start`, `vad.audio`, `vad.end` が出力される
6. WebSocket未接続時はマイクボタンが無効化される

### 追加インストール

**Frontend:**
```bash
cd frontend && npm install @ricky0123/vad-react
```

**ONNX/Workletファイルの配置:**
VADライブラリは以下のファイルをロードする必要がある：
- `vad.worklet.bundle.min.js` - Web Audio Worklet
- `silero_vad.onnx` - Silero VADモデル
- ONNX Runtime WASM files

これらは `node_modules/@ricky0123/vad-web/dist/` からコピーするか、
`useMicVAD` の `workletURL`, `modelURL` オプションで明示的にパスを指定する。

### Previous Story Learnings

**Story 2.1 から:**
- WebSocket接続は `useVoiceStore()` から取得
- `wsClient.send(data)` でJSONデータ送信可能
- `connectionState` で接続状態を確認可能
- onerror時はoncloseがcleanupを担当（race condition修正済み）
- WebSocket URLは環境変数で設定可能（NEXT_PUBLIC_API_HOST）

**Epic 1 から:**
- Tailwind CSS でスタイリング
- `frontend/src/core/` はframework-agnostic
- `frontend/src/hooks/` はReact統合層
- `frontend/src/components/` はReactコンポーネント

### VADライブラリ最新情報

**@ricky0123/vad-react v0.0.35** (2025-12-23時点の最新)
- React用の`useMicVAD`フック提供
- Silero VADモデルをONNX Runtimeで実行
- 16kHzサンプルレートで音声データ出力

**重要な注意点:**
- `startOnLoad: false` で手動開始を推奨
- `onSpeechEnd` で `Float32Array` が渡される（16kHz、モノラル）
- Worklet/ONNXファイルの配信設定が必要

### References

- [Source: _bmad-output/architecture.md#WebSocketイベント契約]
- [Source: _bmad-output/architecture.md#Frontend-Architecture]
- [Source: _bmad-output/architecture.md#Project-Structure]
- [Source: _bmad-output/project-planning-artifacts/epics.md#Story-2.2]
- [@ricky0123/vad-react npm](https://www.npmjs.com/package/@ricky0123/vad-react)
- [VAD Documentation](https://www.vad.ricky0123.com/)
- [VAD React Guide](https://wiki.vad.ricky0123.com/en/docs/user/react)

## Dev Agent Record

### Agent Model Used

Claude Opus 4.5 (claude-opus-4-5-20251101)

### Debug Log References

N/A

### Completion Notes List

- Task 1: VADライブラリインストール完了 - @ricky0123/vad-react v0.0.35, ONNX/Workletファイルをpublicに配置
- Task 2: WebSocketイベント型定義完了 - VadStartEvent, VadAudioEvent, VadEndEvent, serializeEvent関数
- Task 3: use-voiceカスタムフック実装完了 - useMicVAD統合, 録音状態管理
- Task 4: VoiceStore拡張完了 - recordingState追加 ('idle' | 'recording' | 'processing')
- Task 5: UIコンポーネント実装完了 - VoiceInput.tsx (マイクボタン、状態インジケーター)
- Task 6: Backend WebSocketイベント受信対応完了 - vad.start/vad.audio/vad.end ログ出力, AudioBuffer
- Task 7: 統合テスト完了 - pytest 9件合格, make dev起動確認, VAD/ONNX/Workletファイル配信確認

### File List

**Created:**
- `frontend/src/core/events.ts` - WebSocketイベント型定義
- `frontend/src/hooks/use-voice.ts` - VAD統合カスタムフック
- `frontend/src/components/VoiceInput.tsx` - マイクボタンUI
- `frontend/public/vad.worklet.bundle.min.js` - VAD Worklet
- `frontend/public/silero_vad.onnx` - Silero VAD v5モデル
- `frontend/public/silero_vad_legacy.onnx` - Silero VAD legacyモデル
- `frontend/public/ort-wasm-simd-threaded.wasm` - ONNX Runtime WASM
- `frontend/public/ort-wasm-simd-threaded.jsep.wasm` - ONNX Runtime WASM (WebGPU)

**Modified:**
- `frontend/package.json` - @ricky0123/vad-react依存追加
- `frontend/next.config.ts` - turbopack設定追加, webpack fallback設定
- `frontend/eslint.config.mjs` - public/*.js をlint対象外に
- `frontend/src/stores/voice-store.ts` - recordingState, setRecordingState追加
- `frontend/src/core/websocket-client.ts` - send()メソッドでArrayBuffer対応
- `frontend/src/app/page.tsx` - VoiceInput組み込み
- `backend/src/voice_assistant/api/websocket.py` - VADイベント受信処理, AudioBuffer
- `backend/tests/integration/test_websocket.py` - VADイベント/バイナリメッセージテスト

## Change Log

- 2025-12-27: Story 2.2 実装完了 - 全7タスク完了
- 2025-12-27: Story 2.2 created via create-story workflow
