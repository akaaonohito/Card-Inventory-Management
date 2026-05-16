# カード在庫管理 Phase 1

Windows向けのローカル在庫管理アプリです。

Phase 1では、SQLiteを使った基本的な在庫管理、商品追加、一覧上のクイック編集、詳細編集、通常CSVのインポート/エクスポートを実装しています。

## 起動方法

1. Python 3.11以降をインストールします。
2. このフォルダで `run_app.bat` をダブルクリックします。

コマンドラインから起動する場合は以下を実行してください。

```powershell
python -m app.main
```

## Phase 1でできること

- SQLiteへの在庫データ保存
- 在庫一覧の表示
- 商品追加
- 一覧上のクイック編集（Enterキーで保存、Escキーでキャンセル）
- 詳細編集
- 販売価格更新時の最終確認日自動更新
- 選択商品の最終確認日を今日にする操作
- ステータス管理
- 通常CSVのインポート
- CSVエクスポート
- CSVインポート前のDBバックアップ
- トランザクションによるCSV一括登録

## ファイル構成

- `app/main.py`: Tkinter GUI本体
- `app/database.py`: SQLite接続、テーブル作成、登録、更新
- `app/validation.py`: 入力値とCSV値の検証
- `app/csv_io.py`: 通常CSVのインポート/エクスポート
- `app/constants.py`: 項目名、ステータス、CSVヘッダー定義
- `run_app.bat`: Windows用起動ファイル
- `sample_inventory.csv`: 通常CSVサンプル
- `data/inventory.sqlite3`: 起動後に作成されるSQLite DB
- `data/backups/`: CSVインポート前のDBバックアップ保存先

## CSV仕様

通常CSVの列は以下です。

```csv
在庫ID,ジャンル,カード名,レア,セット,言語,コレクター番号,補足,カード状態,枚数,買取価格,販売価格,在庫ステータス,登録日,最終確認日,更新日,メモ
```

CSVインポート時、CSV内の在庫IDは取り込まず、アプリ側で新しい在庫IDを採番します。

## 注意

SQLiteのDBファイルをGoogle Drive、OneDrive、Dropboxなどの同期フォルダに置いて、複数PCから同時に編集する運用は推奨しません。

複数PCで使う場合は、CSVまたはバックアップで受け渡し、同時編集は避けてください。
