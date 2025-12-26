# Story 1.3: Frontend基盤セットアップ

Status: done

## Story

As a **開発者**,
I want **Next.jsフロントエンドの基盤が構築されている**,
so that **UIコンポーネントの開発を開始できる**.

## Acceptance Criteria

1. **Given** モノレポ構造が初期化済み（Story 1.1完了）
   **When** `cd frontend && npm install`を実行する
   **Then** Next.js、TypeScript、Tailwind CSS等の依存関係がインストールされる

2. **And** `frontend/src/app/page.tsx`に基本ページが作成される

3. **And** `npm run dev`でhttp://localhost:3000が起動する

4. **And** Tailwind CSSが適用されている

## Tasks / Subtasks

- [x] Task 1: Next.jsプロジェクトの初期化 (AC: #1)
  - [x] `npx create-next-app@latest frontend --typescript --tailwind --eslint --app --src-dir --import-alias "@/*"` 実行
  - [x] 不要な初期ファイル削除（boilerplate整理）
  - [x] package.json にプロジェクト名設定

- [x] Task 2: ディレクトリ構造の作成 (AC: #2)
  - [x] `frontend/src/components/` ディレクトリ作成
  - [x] `frontend/src/hooks/` ディレクトリ作成
  - [x] `frontend/src/lib/` ディレクトリ作成
  - [x] `frontend/src/core/` ディレクトリ作成（framework-agnostic層）
  - [x] `frontend/src/stores/` ディレクトリ作成（Zustand用）
  - [x] 各ディレクトリに `.gitkeep` または `index.ts` 作成

- [x] Task 3: 基本ページの作成 (AC: #2)
  - [x] `frontend/src/app/page.tsx` 編集 - 基本的なチャットUI placeholder
  - [x] `frontend/src/app/layout.tsx` 編集 - メタデータ設定
  - [x] `frontend/src/app/globals.css` 確認 - Tailwindディレクティブ

- [x] Task 4: 起動確認とテスト (AC: #3, #4)
  - [x] `npm install` で依存関係インストール確認
  - [x] `npm run dev` で http://localhost:3000 起動確認
  - [x] Tailwind CSSスタイルが適用されていることを確認
  - [x] ESLint (`npm run lint`) 実行確認

## Dev Notes

### アーキテクチャ準拠事項

**ディレクトリ構造（Architecture.md準拠）:**
```
frontend/
├── src/
│   ├── app/                        # App Router
│   │   ├── layout.tsx              # ルートレイアウト
│   │   ├── page.tsx                # チャット画面（placeholder）
│   │   └── globals.css             # グローバルスタイル
│   ├── core/                       # Framework-agnostic コア（後続Story用）
│   │   └── index.ts
│   ├── components/                 # React コンポーネント（後続Story用）
│   │   └── index.ts
│   ├── hooks/                      # React カスタムフック（後続Story用）
│   │   └── index.ts
│   ├── stores/                     # Zustand ストア（後続Story用）
│   │   └── index.ts
│   └── lib/                        # ユーティリティ（後続Story用）
│       └── index.ts
├── public/                         # 静的ファイル
├── package.json
├── tsconfig.json
├── postcss.config.mjs              # Tailwind CSS v4 (PostCSS経由)
├── next.config.ts
└── eslint.config.mjs
```

### 技術仕様

**初期化コマンド:**
```bash
cd frontend
npx create-next-app@latest . --typescript --tailwind --eslint --app --src-dir --import-alias "@/*"
```

**package.json 設定（実際の実装）:**
```json
{
  "name": "voice-assistant-frontend",
  "version": "0.1.0",
  "private": true,
  "scripts": {
    "dev": "next dev",
    "build": "next build",
    "start": "next start",
    "lint": "eslint"
  },
  "dependencies": {
    "next": "16.1.1",
    "react": "19.2.3",
    "react-dom": "19.2.3"
  },
  "devDependencies": {
    "@tailwindcss/postcss": "^4",
    "tailwindcss": "^4",
    "typescript": "^5",
    "eslint": "^9",
    "eslint-config-next": "16.1.1"
  }
}
```

**page.tsx 基本実装:**
```tsx
export default function Home() {
  return (
    <main className="flex min-h-screen flex-col items-center justify-center p-24">
      <h1 className="text-4xl font-bold text-center">
        Voice Assistant
      </h1>
      <p className="mt-4 text-gray-600">
        日本語特化ローカル音声対話アシスタント
      </p>
      {/* チャットUIは Story 2.7 で実装 */}
    </main>
  );
}
```

**layout.tsx 基本実装:**
```tsx
import type { Metadata } from "next";
import { Inter } from "next/font/google";
import "./globals.css";

const inter = Inter({ subsets: ["latin"] });

export const metadata: Metadata = {
  title: "Voice Assistant",
  description: "日本語特化ローカル音声対話アシスタント",
};

export default function RootLayout({
  children,
}: Readonly<{
  children: React.ReactNode;
}>) {
  return (
    <html lang="ja">
      <body className={inter.className}>{children}</body>
    </html>
  );
}
```

### 命名規則（Architecture準拠）

| 対象 | パターン | 例 |
|------|---------|-----|
| コンポーネント | PascalCase.tsx | `ChatMessage.tsx` |
| hooks | kebab-case.ts | `use-voice.ts` |
| utils | kebab-case.ts | `websocket-client.ts` |
| ストア | kebab-case.ts | `voice-store.ts` |
| TypeScript型 | PascalCase | `Message`, `VoiceStore` |

### 依存関係

**前提条件:**
- Story 1.1 完了（モノレポ構造）
- Story 1.2 完了（Backend基盤 - CORS設定済み）

**後続Story:**
- Story 1.4 (統合開発環境) - `make dev`でfrontend/backend同時起動
- Story 2.2 (Frontend音声キャプチャとVAD) - @ricky0123/vad-web追加
- Story 2.7 (チャットUI基本実装) - Zustand、コンポーネント実装

### テスト基準

1. `npm install` が正常完了する
2. `npm run dev` で http://localhost:3000 が起動する
3. ブラウザで「Voice Assistant」テキストが表示される
4. Tailwind CSSスタイル（text-4xl, font-bold等）が適用されている
5. `npm run lint` がエラーなしで完了する

### Previous Story Learnings

**Story 1.2 から:**
- Backend `/api/v1/health` が http://localhost:8000 で動作確認済み
- CORS設定で `http://localhost:3000` が許可済み
- lifespan context managerパターンで起動時処理を管理
- lru_cache パターンで設定のテスト容易性を確保

**Story 1.1 から:**
- ルート `Makefile` に `dev-frontend` ターゲット準備済み: `cd frontend && npm run dev`
- `scripts/setup.sh` で `frontend/package.json` 存在チェック追加済み
- `.gitignore` に `node_modules/`, `.next/` 設定済み

### 注意事項

**create-next-app の対話形式について:**
- `--typescript`, `--tailwind`, `--eslint`, `--app`, `--src-dir` フラグで対話をスキップ
- 既存ディレクトリ `frontend/` がある場合、`.` で現在位置に作成

**Boilerplate整理:**
- 不要な `page.tsx` のサンプルコード削除
- `favicon.ico` 等のデフォルトアセットは残す
- Vercel関連の設定は削除不要（影響なし）

### References

- [Source: _bmad-output/architecture.md#Project-Structure]
- [Source: _bmad-output/architecture.md#Starter-Template-Evaluation]
- [Source: _bmad-output/architecture.md#Frontend-Architecture]
- [Source: _bmad-output/project-planning-artifacts/epics.md#Story-1.3]

## Dev Agent Record

### Agent Model Used

Claude Opus 4.5 (claude-opus-4-5-20251101)

### Debug Log References

N/A

### Completion Notes List

- Task 1: Next.js 16.1.1プロジェクト初期化完了 - React 19.2.3, TypeScript 5, Tailwind CSS 4
- Task 2: ディレクトリ構造作成完了 - components/, hooks/, lib/, core/, stores/ に index.ts 配置
- Task 3: 基本ページ作成完了 - page.tsx (Voice Assistant placeholder), layout.tsx (lang="ja", Inter font), 不要SVG削除
- Task 4: 起動確認完了 - npm run dev で localhost:3000 起動、ESLint エラーなし、Tailwind スタイル適用確認

### File List

**Created:**
- `frontend/package.json` (voice-assistant-frontend)
- `frontend/src/app/page.tsx`
- `frontend/src/app/layout.tsx`
- `frontend/src/app/globals.css`
- `frontend/src/app/favicon.ico`
- `frontend/src/components/index.ts`
- `frontend/src/hooks/index.ts`
- `frontend/src/lib/index.ts`
- `frontend/src/core/index.ts`
- `frontend/src/stores/index.ts`
- `frontend/public/.gitkeep`
- `frontend/tsconfig.json`
- `frontend/next.config.ts`
- `frontend/eslint.config.mjs`
- `frontend/postcss.config.mjs`

**Removed (boilerplate):**
- `frontend/public/file.svg`
- `frontend/public/globe.svg`
- `frontend/public/next.svg`
- `frontend/public/vercel.svg`
- `frontend/public/window.svg`

**Generated:**
- `frontend/package-lock.json`
- `frontend/node_modules/`
- `frontend/.next/`

## Senior Developer Review

### Review Summary

**Reviewer:** Senior Developer (Adversarial Review)
**Review Date:** 2025-12-27
**Result:** PASS (after auto-fix)
**Issues Found:** 6 (1 HIGH, 3 MEDIUM, 2 LOW)
**Issues Fixed:** 4/6

### Issues Fixed

| Severity | Issue | Fix Applied |
|----------|-------|-------------|
| HIGH | globals.css に未使用の Geist font 変数 | 削除、body の font-family ハードコードも削除 |
| MEDIUM | favicon.ico が File List に記載なし | File List に追加 |
| MEDIUM | body の font-family がハードコード | globals.css から削除（Inter は className 経由で適用） |
| LOW | public ディレクトリが空 | .gitkeep 追加 |

### Issues Not Fixed (Acceptable)

| Severity | Issue | Reason |
|----------|-------|--------|
| MEDIUM | npm run lint が "eslint" | Dev Notes の "実際の実装" セクションで正しく記載済み |
| LOW | index.ts のコンベンションコメント | 後続開発者へのガイダンスとして有用 |

### Files Modified in Review

- `frontend/src/app/globals.css` - Geist font 変数削除、body font-family 削除
- `frontend/public/.gitkeep` - 新規追加
- `_bmad-output/implementation-artifacts/stories/1-3-frontend-foundation-setup.md` - File List 更新

## Change Log

- 2025-12-27: Code review完了 - 4件の問題を修正
- 2025-12-27: Story 1.3 実装完了 - Frontend基盤セットアップ（全4タスク完了）
- 2025-12-27: Story 1.3 created via create-story workflow
