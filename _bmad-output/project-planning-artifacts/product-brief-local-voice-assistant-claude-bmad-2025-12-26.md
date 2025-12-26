---
stepsCompleted: [1, 2, 3, 4, 5]
inputDocuments:
  - '_bmad-output/project-planning-artifacts/research/technical-voice-assistant-research-2025-12-26.md'
  - '_bmad-output/analysis/brainstorming-session-2025-12-26.md'
workflowType: 'product-brief'
lastStep: 5
project_name: 'local-voice-assistant-claude-bmad'
user_name: 'y'
date: '2025-12-26'
---

# Product Brief: local-voice-assistant-claude-bmad

## Executive Summary

**local-voice-assistant-claude-bmad** は、日本語に特化したローカル音声対話アシスタントです。

**核心的な価値提案:**
- **日本語特化の高精度認識**: ReazonSpeech NeMo v2による Whisper を超える日本語認識精度
- **コスト最適化アーキテクチャ**: STT/TTSはローカル処理、LLMは用途に応じて選択可能
- **ベンダーロックインからの解放**: OpenAI API互換インターフェースで任意のLLMに切り替え
- **自然な対話体験**: VAD自動検出とストリーミング応答による低遅延対話
- **開発者にとっての使いやすさ**: FastAPI + Next.js + TypeScriptによるモダンな技術スタック

研究・検証から実用まで、一つのベースで対応できる柔軟なプラットフォームを提供します。

---

## Core Vision

### Problem Statement

クラウドベースの音声アシスタント（Alexa、Google Assistant、Siri等）は便利だが、以下の課題があります：

1. **プライバシーの懸念**: 音声データがクラウドに送信され、どのように利用されるか不透明
2. **ベンダーロックイン**: 特定のエコシステムに依存し、切り替えが困難
3. **従量課金のコスト**: APIコールごとの課金が積み重なると高額に
4. **日本語対応の限界**: 汎用モデルは日本語特有の表現やアクセントに弱い
5. **カスタマイズの制限**: 用途に応じた調整が難しい

### Problem Impact

- 開発者・研究者が音声対話システムを試す際、毎回クラウドAPI費用が発生
- 機密性の高い会話（業務内容等）をクラウドに送信することへの抵抗
- 日本語音声認識の誤認識によるユーザー体験の低下
- 特定ベンダーのAPI変更・終了リスク

### Why Existing Solutions Fall Short

| ソリューション | 課題 |
|--------------|------|
| Whisper (OpenAI) | 日本語特化ではない、API利用は従量課金 |
| Google Speech-to-Text | 高精度だが従量課金、データがクラウドへ |
| Azure Speech | 同上 |
| Amazon Transcribe | 同上 |
| ローカルWhisper | 日本語精度がReazonSpeechに劣る |

### Proposed Solution

**ハイブリッドアーキテクチャによる最適化:**

```
[Frontend: Next.js + VAD]
         ↓ WebSocket
[Backend: FastAPI]
    ├── STT: ReazonSpeech NeMo v2 (ローカル)
    ├── LLM: OpenAI API互換 (Ollama/OpenAI/Groq 切り替え可能)
    └── TTS: VOICEVOX/Style-BERT-VITS2/Piper (ローカル)
```

- **STT/TTS**: 完全ローカル処理でプライバシー保護・コスト削減
- **LLM**: OpenAI API互換インターフェースで柔軟に選択
  - ローカル: Ollama (Qwen 2.5等)
  - クラウド: OpenAI / Groq (高速・低コスト)
- **VAD**: フロントエンドで自動音声検出、自然な対話体験

### Key Differentiators

1. **日本語特化の高精度STT**: ReazonSpeech NeMo v2は Whisper large-v3 を超える日本語認識精度
2. **真のコスト最適化**: STT/TTSはローカル無料、LLMは用途に応じて最適な選択
3. **ベンダー非依存**: OpenAI API互換で将来のモデル変更に柔軟対応
4. **開発者フレンドリー**: モダンな技術スタック、明確なAPI設計
5. **研究から実用まで**: 単一コードベースで検証・本番両方に対応

---

## Target Users

### Primary Users

#### 1. 個人ユーザー（優先度: 最高）

**ペルソナ: 田中 健太（32歳）**
- **役割**: ソフトウェアエンジニア（Web系企業勤務）
- **背景**: プライバシーを重視し、自宅の作業環境を最適化したい。ChatGPTは便利だが、音声でのやり取りをしたい時にクラウドに音声データを送ることに抵抗がある
- **動機**: 自分だけのローカルAIアシスタントで、気軽に日本語で会話したい
- **現状の課題**: Alexaは便利だが、会話の自由度が低い。ChatGPTの音声機能は高品質だが、プライバシーが気になる
- **成功の姿**: 「Hey Siri」のように自然に話しかけて、プログラミングの質問や雑談ができる環境

#### 2. 開発者/エンジニア（優先度: 高）

**ペルソナ: 佐藤 美咲（28歳）**
- **役割**: フルスタックエンジニア（スタートアップ勤務）
- **背景**: 自社プロダクトに音声対話機能を追加したいが、クラウドAPIのコストが懸念
- **動機**: 低コストで日本語音声対話を実装し、プロトタイプを素早く作りたい
- **現状の課題**: Google/AzureのAPIは高精度だが従量課金が怖い。Whisperは日本語が微妙
- **成功の姿**: 自社サービスに音声対話を組み込み、ユーザー体験を向上させる

#### 3. 研究者（優先度: 中）

**ペルソナ: 山田 教授（45歳）**
- **役割**: 大学の情報工学科准教授
- **背景**: 音声対話システムの研究で、日本語特化のベースラインが必要
- **動機**: 論文用の実験環境として、再現性のあるローカル環境が欲しい
- **現状の課題**: 既存ツールは設定が複雑、または英語中心
- **成功の姿**: 学生が簡単にセットアップでき、実験に集中できる環境

### Secondary Users

N/A（現時点では想定なし）

### User Journey

**田中さん（個人ユーザー）の典型的なジャーニー:**

1. **Discovery**: GitHubで「日本語 音声アシスタント ローカル」を検索し発見
2. **Onboarding**: READMEを見て `uv run` でセットアップ、5分で起動
3. **Core Usage**: 朝のコーディング中に「この関数のリファクタリング案を教えて」と話しかける
4. **Aha! Moment**: 「クラウドに送らずにこの品質で認識できるんだ！」と実感
5. **Long-term**: 毎日の作業パートナーとして定着、カスタマイズも楽しむ

---

## Success Metrics

### User Success Metrics

| 指標 | 成功基準 | 測定方法 |
|-----|---------|---------|
| **認識精度** | 日本語発話が正確にテキスト化される | STT出力の正確性を体感で確認 |
| **応答速度** | 発話終了から音声応答開始まで自然な間 | 体感レイテンシ（ストレスを感じない） |
| **日常利用** | 毎日使いたくなる体験 | 継続的な利用習慣の形成 |

### Business Objectives

このプロジェクトは個人プロジェクトのため、ビジネス目標は以下に置き換え：

| 目標 | 定義 |
|-----|------|
| **自己利用** | 開発者自身が毎日の作業で活用できる |
| **完成度** | 研究・検証ではなく、実用レベルの品質 |

### Key Performance Indicators

| KPI | 目標値 | 優先度 |
|-----|-------|-------|
| **STT認識精度** | > 95% | 高 |
| **応答遅延（End-to-End）** | < 2秒 | 高 |
| **セットアップ時間** | < 5分（uv run で起動） | 中 |

**測定ポイント:**
- STT認識精度: ReazonSpeech NeMo v2のベンチマーク値（CER）で確認
- 応答遅延: 発話終了検出 → TTS音声再生開始までの時間

---

## MVP Scope

### Core Features

| 機能 | MVP実装 | 説明 |
|-----|--------|------|
| **音声入力（STT）** | ReazonSpeech NeMo v2（ローカル） | 日本語特化の高精度認識 |
| **音声検出（VAD）** | @ricky0123/vad（フロントエンド） | 自動発話検出 |
| **LLM応答** | OpenAI API互換 | Ollama/OpenAI/Groq切り替え可能 |
| **音声出力（TTS）** | VOICEVOX（ローカル） | 日本語自然音声 |
| **Web UI** | Next.js + TypeScript | チャット画面 + 録音状態表示 |
| **通信** | WebSocket | リアルタイム双方向通信 |
| **会話履歴** | SQLite | ローカル保存 |

### Out of Scope for MVP

| 機能 | 理由 | 将来バージョン |
|-----|------|--------------|
| **STTクラウド切り替え** | MVP後に追加 | v2.0 |
| **TTS切り替え（Style-BERT-VITS2/Piper）** | MVP後に追加 | v2.0 |
| **TTSクラウド切り替え** | MVP後に追加 | v2.0 |
| **複数会話セッション管理** | シンプルさ優先 | v2.0 |
| **ウェイクワード検出** | 複雑性回避 | v3.0 |
| **マルチユーザー対応** | 個人利用前提 | 将来検討 |

### MVP Success Criteria

| 基準 | 達成条件 |
|-----|---------|
| **End-to-End動作** | 音声入力→LLM→音声出力が一貫して動作 |
| **認識精度** | STT > 95% |
| **応答遅延** | < 2秒 |
| **セットアップ** | `uv run` で5分以内に起動 |
| **日常利用** | 開発者自身が毎日使える品質 |

### Future Vision

**v2.0: コンポーネント切り替え対応**
- STT: ローカル（ReazonSpeech） ⇔ クラウド（Whisper API/Google）
- TTS: VOICEVOX ⇔ Style-BERT-VITS2 ⇔ Piper ⇔ クラウド
- 設定画面でのモデル切り替えUI

**v3.0: 高度な対話機能**
- ウェイクワード検出（常時待機モード）
- 会話コンテキスト管理の強化
- プラグイン/拡張機能システム

**長期ビジョン**
- 他の開発者が自分のプロジェクトに組み込めるライブラリ化
- Docker/コンテナでのワンクリックデプロイ

