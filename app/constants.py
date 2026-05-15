from __future__ import annotations

APP_NAME = "カード在庫管理"

DATA_DIR = "data"
BACKUP_DIR = "backups"
DB_FILENAME = "inventory.sqlite3"

STATUS_VALUES = (
    "販売中",
    "準備中",
    "売却済み",
    "取置中",
    "販売停止",
    "削除済み",
)

CSV_HEADERS = (
    "在庫ID",
    "ジャンル",
    "カード名",
    "レア",
    "セット",
    "言語",
    "コレクター番号",
    "補足",
    "カード状態",
    "枚数",
    "買取価格",
    "販売価格",
    "在庫ステータス",
    "登録日",
    "最終確認日",
    "更新日",
    "メモ",
)

FIELD_TO_HEADER = {
    "inventory_id": "在庫ID",
    "genre": "ジャンル",
    "card_name": "カード名",
    "rarity": "レア",
    "set_name": "セット",
    "language": "言語",
    "collector_number": "コレクター番号",
    "note": "補足",
    "condition": "カード状態",
    "quantity": "枚数",
    "purchase_price": "買取価格",
    "sale_price": "販売価格",
    "status": "在庫ステータス",
    "registered_date": "登録日",
    "last_checked_date": "最終確認日",
    "updated_date": "更新日",
    "memo": "メモ",
}

HEADER_TO_FIELD = {header: field for field, header in FIELD_TO_HEADER.items()}

LIST_COLUMNS = (
    "inventory_id",
    "genre",
    "card_name",
    "note",
    "quantity",
    "sale_price",
    "last_checked_date",
    "status",
)

EDIT_FIELDS = (
    "note",
    "quantity",
    "sale_price",
    "last_checked_date",
    "status",
)

DETAIL_EDIT_FIELDS = (
    "genre",
    "card_name",
    "rarity",
    "set_name",
    "language",
    "collector_number",
    "note",
    "condition",
    "quantity",
    "purchase_price",
    "sale_price",
    "status",
    "last_checked_date",
    "memo",
)
