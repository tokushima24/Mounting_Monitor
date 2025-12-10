# 🐷 Swine Breeding Behavior Detection System (Desktop Client)

![Python](https://img.shields.io/badge/Python-3.10%2B-blue?logo=python&logoColor=white)
![PyQt6](https://img.shields.io/badge/GUI-PyQt6-green?logo=qt&logoColor=white)
![YOLOv8](https://img.shields.io/badge/AI-YOLOv8-purple)
![Status](https://img.shields.io/badge/Status-Beta-orange)

豚舎の監視カメラ映像からAI (YOLO) を用いて豚の交配行動 (Mounting Behavior) を自動検出し、管理者へ通知するデスクトップアプリケーションです。

## ✨ 実装済み機能 (Features)

### 1. 監視・検知機能
* **リアルタイム監視**: RTSP接続により、ネットワークカメラの映像を遅延なく表示します。
* **AI自動検知**: YOLOv8 モデルを使用し、豚の交配行動をリアルタイムで認識します。
* **自動復旧 (Watchdog)**: 通信断や映像フリーズが発生しても、自動で再接続を行い監視を継続します。
* **安定通信**: RTSP over TCP を採用し、パケットロスによる映像乱れを最小限に抑えています。

### 2. 通知・記録機能
* **Discord通知**: 検知時、画像付きのアラートをDiscordチャンネルへ非同期で送信します（監視を止めません）。
* **画像保存**: 検知の瞬間を画像（枠付き）としてローカルストレージに保存します。
* **データベース記録**: 検知日時、信頼度、豚舎IDなどをSQLiteデータベースに記録します。

### 3. 管理・操作機能
* **GUI操作**: 直感的な操作パネルで、監視対象の豚舎（Barn 1〜7）を切り替えられます。
* **管理者設定**: アプリ上で検知感度や通知クールダウン時間を変更・保存できます（要パスワード）。

## 🚧 今後のロードマップ (Todo / Roadmap)

現在、以下の機能が開発予定（未実装）です。

* [ ] **検知結果の確認機能 (History Viewer)** * 過去の検知ログをカレンダーやリストから検索・閲覧する機能。
    * 保存された画像をアプリ上でプレビューする機能。
* [ ] **ストレージ容量警告**
    * ディスク残量が少なくなった際に警告を出す機能。
* [ ] **データ自動クリーンアップ**
    * 古い画像やログを定期的に削除し、容量を確保する機能。
* [ ] **インストーラー作成 (exe化)**
    * Windows環境向けに、Python不要で動作する配布用パッケージの作成。

## 📂 ディレクトリ構成 (Structure)

```text
mounting_monitor/
├── config.yaml          # [設定] 動作パラメータ (GUIから変更可能)
├── .env                 # [機密] パスワード・URL・Webhook
├── src/                 # ソースコード
│   ├── gui/             # GUI関連
│   │   ├── main_window.py    # メイン画面
│   │   ├── settings_window.py # 設定画面
│   │   └── video_thread.py   # 映像取得・自動復旧ロジック
│   ├── detector.py      # YOLO検知ロジック
│   ├── notification.py  # Discord通知ロジック
│   ├── database.py      # データベース操作
│   └── ...
├── data/                # データ保存先
│   ├── images/          # 検知画像
│   └── breeding_logs.db # ログデータベース
└── models/              # AIモデル格納場所
````

## 🚀 セットアップ (Installation)

### 1\. 前提条件

  * Python 3.10 以上
  * [uv](https://github.com/astral-sh/uv) パッケージマネージャー

### 2\. インストール

```bash
# リポジトリのクローン
git clone [https://github.com/tokushima24/mounting_monitor.git](https://github.com/tokushima24/mounting_monitor.git)
cd mounting_monitor

# 依存ライブラリの同期
uv sync
```

### 3\. 設定ファイルの準備

ルートディレクトリに `.env` ファイルを作成し、以下の情報を記述してください。

```ini
# .env
# 各豚舎のRTSP URL
RTSP_URL_1=rtsp://admin:pass@192.168.1.10:558/LiveChannel/0/media.smp
RTSP_URL_2=rtsp://admin:pass@192.168.1.11:558/LiveChannel/0/media.smp
# ... (RTSP_URL_7 まで)

# Discord Webhook URL
DISCORD_WEBHOOK_URL=[https://discord.com/api/webhooks/xxxx/xxxx](https://discord.com/api/webhooks/xxxx/xxxx)

# 管理者パスワード (設定画面用)
ADMIN_PASSWORD=admin123
```

## 🏃‍♂️ 実行方法 (Usage)

以下のコマンドでアプリケーションを起動します。

```bash
uv run python -m src.gui.main
```

1.  左側のパネルから「豚舎」を選択します。
2.  **「Start Monitoring」** を押すと監視を開始します。
3.  設定を変更する場合は **「Settings (Admin)」** を押し、パスワードを入力してください。

## 🛠️ 開発者向け情報

  * **コードフォーマット**: `uv run black src/`
  * **静的解析**: `uv run flake8 src/`

## 📝 License

This project is licensed under the MIT License.

```

---

### 次のアクションのご相談

READMEを更新し、現状を整理しました。
ご指摘の通り、**「検知結果確認機能（履歴ビューア）」は運用上必須の機能** です。

以前コード (`history_window.py`) は提示しましたが、まだ `main_window.py` との結合や動作確認が終わっていない状態です。

exe化（ビルド）に進む前に、この **「履歴機能の実装」を完了させますか？**
それとも、一旦今の機能だけでビルドのテストを行いますか？

（必須とのことですので、**実装してからビルドに進む** ことを強く推奨します）
```