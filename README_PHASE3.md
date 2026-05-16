# カード在庫管理 Phase 3

Phase 3では、外部CSV連携と表示設定、今後の拡張準備を追加しました。

## 追加したこと

- 通常CSV / Manabox CSVの自動判別インポート
- Manabox CSVから在庫データへの変換
- CSV取り込み前の形式表示とエラー確認
- CSV日付のゆらぎ変換
- メイン画面右上の作業モード切り替え
- モード別の一覧表示列
- モード別の初期表示ステータス
- 設定タブでのモード別表示設定
- 買取モード専用のクイック編集項目拡張
- 将来のタグ候補挿入、買取見積書機能、exe化に向けた方針整理

## Manabox CSVインポート

以下の列があるCSVはManabox CSVとして自動判別します。

- `Name`
- `Set code`
- `Collector number`
- `Foil`
- `Rarity`
- `Quantity`
- `Language`

主な変換内容は以下です。

- `Name` -> カード名
- `Set code` -> セット
- `Collector number` -> コレクター番号
- `Foil` -> 補足
- `Rarity` -> レア
- `Quantity` -> 枚数
- `Language` -> 言語
- ジャンルは `MTG`
- 販売価格は `0`
- 在庫ステータスは `準備中`
- 登録日、最終確認日、更新日は取り込み日

`Foil` は `foil` を `#Foil`、`normal` を空欄へ変換します。
`Rarity` は `common/uncommon/rare/mythic` を `C/U/R/M` へ変換します。
`Language` は `ja` を `jp` へ変換します。

## 日付変換

通常CSVの日付は以下の形式を受け付け、保存時は `YYYY-MM-DD` に統一します。

- `YYYY-MM-DD`
- `YYYY/MM/DD`
- `MM/DD`
- `M月D日`

年がない形式は、取り込み時点の年を使います。

## 作業モード

- 管理モード
  - 初期ステータス: 販売中
  - 日常の在庫管理向けの標準列
- 買取モード
  - 初期ステータス: 準備中
  - レア、セット、言語、状態、買取価格、メモを確認しやすい列
  - カード名、レア、セット、コレクター番号、カード状態、買取価格、メモもクイック編集可能
- 価格見直しモード
  - 初期ステータス: 販売中
  - 販売価格、買取価格、最終確認日、更新日を確認しやすい列

設定はSQLiteの `app_meta` に保存されるため、次回起動時も維持されます。

## 将来拡張メモ

補足欄は通常の文字列として保存し、`#Foil` などのタグも同じ欄に保持します。
タグ候補挿入UIを追加する場合も、保存形式やCSV形式は変えず、入力補助として追加してください。

買取見積書機能は、一覧のチェック済み在庫を対象に、買取価格、枚数、小計、合計を扱う構成で追加する想定です。
ステータス追加が必要な場合は、絞り込み、CSV、初期表示、一括操作への影響を確認してください。

## exe化メモ

PyInstallerを使う場合の想定手順です。

```powershell
python -m pip install pyinstaller
python -m PyInstaller --noconsole --name CardInventory --add-data "app;app" app\main.py
```

配布前に、`data\inventory.sqlite3` を同梱するか、初回起動時に空DBを作成する運用にするかを決めてください。
