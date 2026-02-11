# Swine Monitor - macOS ビルドガイド

このガイドでは、macOSでSwine Monitorアプリケーションをビルドする方法を説明します。

## 📋 前提条件

1. **Python 3.10以上** がインストールされていること
2. **Homebrew** がインストールされていること（推奨）
3. プロジェクトの仮想環境が設定されていること

## 🚀 クイックビルド（推奨）

ビルドスクリプトを使った最も簡単な方法：

```bash
# プロジェクトルートに移動
cd /path/to/for_BIRC_Monitor

# ビルドスクリプトを実行
./scripts/build_mac.sh
```

これだけで以下が自動的に行われます：
- PyInstallerのインストール/更新
- 以前のビルドのクリーンアップ
- アプリケーションのビルド
- 必要なファイルのコピー

## 📦 手動ビルド

ビルドスクリプトを使わない場合：

### 1. 仮想環境を有効化

```bash
source .venv/bin/activate
```

### 2. PyInstallerをインストール

```bash
pip install pyinstaller
```

### 3. ビルドを実行

```bash
# --noconfirm で確認プロンプトをスキップ
pyinstaller build.spec --clean --noconfirm
```

### 4. 設定ファイルをコピー

```bash
# 設定ファイルをdistフォルダにコピー
cp config.yaml.template dist/SwineMonitor/config.yaml
cp .env.template dist/SwineMonitor/.env

# 必要なディレクトリを作成
mkdir -p dist/SwineMonitor/models
mkdir -p dist/SwineMonitor/data
mkdir -p dist/SwineMonitor/detections

# モデルファイルをコピー（存在する場合）
cp models/yolo11s_best.pt dist/SwineMonitor/models/
```

## ▶️ ビルド済みアプリの実行

```bash
# ターミナルから実行
./dist/SwineMonitor/SwineMonitor

# または Finder から
# dist/SwineMonitor/ フォルダを開き、SwineMonitor をダブルクリック
```

## 📁 ビルド成果物の構成

```
dist/SwineMonitor/
├── SwineMonitor          # 実行ファイル
├── config.yaml           # 設定ファイル
├── .env                  # 環境変数ファイル
├── models/
│   └── yolo11s_best.pt   # YOLOモデル
├── data/                 # データベース保存先
├── detections/           # 検出画像保存先
└── _internal/            # 依存ライブラリ
```

## ⚠️ よくある問題と解決方法

### 1. `pyinstaller: command not found`

仮想環境が有効になっていない可能性があります：

```bash
source .venv/bin/activate
```

### 2. ビルド中に確認プロンプトが表示される

`--noconfirm` オプションを使用：

```bash
pyinstaller build.spec --clean --noconfirm
```

### 3. scipy関連の警告が表示される

これは警告であり、ビルドには影響しません。アプリは正常に動作します。

### 4. コード署名の警告

```
WARNING: Found one or more binaries with invalid or incompatible macOS SDK version
```

開発/テスト用途では無視できます。配布する場合は、Apple Developer IDでの署名が必要です。

### 5. アプリが起動しない

ターミナルから実行してエラーメッセージを確認：

```bash
./dist/SwineMonitor/SwineMonitor
```

よくある原因：
- `.env` ファイルがない → テンプレートからコピー
- `config.yaml` がない → テンプレートからコピー
- モデルファイルがない → `models/` にコピー

## 🔧 build.specのカスタマイズ

### アイコンを追加する場合

`build.spec` の `EXE` セクションで：

```python
exe = EXE(
    ...
    icon='path/to/icon.icns',  # macOSは .icns 形式
)
```

### 追加のデータファイルを含める場合

`build.spec` の `datas` に追加：

```python
datas=[
    ('config.yaml.template', '.'),
    ('.env.template', '.'),
    ('models/*.pt', 'models'),  # 追加例
],
```

## 📤 配布方法

### 1. フォルダごと配布

`dist/SwineMonitor/` フォルダをzipで圧縮して配布：

```bash
cd dist
zip -r SwineMonitor-mac.zip SwineMonitor/
```

### 2. DMGファイルの作成（オプション）

```bash
# create-dmg をインストール
brew install create-dmg

# DMGを作成
create-dmg \
  --volname "Swine Monitor" \
  --window-size 400 300 \
  --icon-size 100 \
  "SwineMonitor.dmg" \
  "dist/SwineMonitor/"
```

## 🖥️ Intel Mac vs Apple Silicon Mac

現在のビルドは、ビルドを実行したMacのアーキテクチャ用に生成されます：

- **Apple Silicon Mac (M1/M2/M3)** でビルド → arm64
- **Intel Mac** でビルド → x86_64

ユニバーサルバイナリ（両方対応）を作成するには、追加の設定が必要です。

---

## 📝 補足

- ビルドには数分かかることがあります
- 初回ビルドは特に時間がかかります（依存関係の解析）
- ビルドサイズは約500MB〜1GB程度になります（YOLOモデル含む）

何か問題があれば、`build/build/warn-build.txt` でビルド警告を確認してください。
