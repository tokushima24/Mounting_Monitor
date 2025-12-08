# 🐷 Swine Breeding Behavior Detection System

![Python](https://img.shields.io/badge/Python-3.10%2B-blue?logo=python&logoColor=white)
![uv](https://img.shields.io/badge/Manage_with-uv-purple)
![License](https://img.shields.io/badge/License-MIT-green)
![Status](https://img.shields.io/badge/Status-Development-orange)

豚舎の監視カメラ映像からAI (YOLO) を用いて豚の交配行動 (Mounting Behavior) を自動検出し、管理者へリアルタイムで通知するシステムです。

## ✨ 特徴 (Features)

* **リアルタイム検出**: YOLOv8 (または OpenVINO) を使用した高速な行動認識
* **RTSP対応**: ネットワークカメラ (NVR) からのストリーミング映像を直接解析
* **即時通知**: 交配行動を検知すると、Discord (Webhook) へ画像付きでアラートを送信
* **データ蓄積**: 検知ログと画像を自動で保存・データベース化 (SQLite)
* **ダッシュボード**: 保存されたログと画像を閲覧できるWebアプリ (Streamlit) 付属
* **モダンな開発環境**: `uv` による高速で再現性の高い環境構築

## 📂 ディレクトリ構成 (Structure)

```text
mounting_monitor/
├── src/                 # ソースコード
│   ├── app.py           # ダッシュボード (Streamlit)
│   ├── detector.py      # 検知ロジック (YOLO)
│   ├── main.py          # 実行エントリーポイント
│   └── ...
├── config.yaml          # [設定] 動作パラメータ (Git管理対象)
├── .env                 # [機密] パスワード・URL (Git管理外)
├── pyproject.toml       # プロジェクト定義
├── uv.lock              # 依存関係ロックファイル
├── logs/                # 実行ログ出力先
└── data/                # データ保存先 (画像・DB)
````

## 🚀 セットアップ (Installation)

このプロジェクトはパッケージマネージャー **[uv](https://github.com/astral-sh/uv)** を使用しています。

### 1\. 前提条件

  * Python 3.10 以上
  * uv がインストールされていること
      * Mac/Linux: `curl -LsSf https://astral.sh/uv/install.sh | sh`
      * Windows: `powershell -c "irm https://astral.sh/uv/install.ps1 | iex"`

### 2\. クローンと同期

リポジトリをクローンし、依存ライブラリを同期します。

```bash
git clone [https://github.com/tokushima24/mounting_monitor.git](https://github.com/tokushima24/mounting_monitor.git)
cd mounting_monitor
uv sync
```

### 3\. 設定ファイルの作成

**① 環境変数ファイル (`.env`)**
プロジェクトルートに `.env` ファイルを作成し、機密情報を記述します。

```ini
# .env
# カメラのRTSPアドレス (ユーザー名:パスワード@IP:ポート)
RTSP_URL=rtsp://admin:password123@192.168.1.100:558/LiveChannel/0/media.smp

# 通知用 Discord Webhook URL
WEBHOOK_URL=[https://discord.com/api/webhooks/xxxxxxxx/xxxxxxxx](https://discord.com/api/webhooks/xxxxxxxx/xxxxxxxx)
```

**② 設定ファイル (`config.yaml`)**
必要に応じて `config.yaml` のパラメータ（検知感度や保存設定）を調整してください。

## 🏃‍♂️ 実行方法 (Usage)

`uv run` コマンドを使用することで、仮想環境を意識せずに実行できます。

### 監視システムの起動

カメラ接続と検知を開始します。

```bash
uv run python -m src.main
```

  * 停止するにはコンソールで `Ctrl + C` を押します。
  * ログは画面および `logs/system.log` に出力されます。

### ダッシュボードの起動

検知履歴を確認するWebアプリを起動します。

```bash
uv run streamlit run src/app.py
```

ブラウザが自動的に開き、`http://localhost:8501` でアクセスできます。

## 🛠️ 開発 (Development)

### コード品質管理

以下のツールでコードのフォーマットと静的解析を行います。

```bash
# コードの自動整形 (Black)
uv run black src/

# コードのチェック (Flake8)
uv run flake8 src/
```

## 📝 License

This project is licensed under the MIT License.