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

GENRE_VALUES = (
    "MTG",
    "ポケカ",
    "遊戯王",
    "デュエマ",
    "ワンピースカード",
    "その他",
)

RARITY_VALUES = (
    "C",
    "U",
    "R",
    "M",
    "UC",
    "RR",
    "RRR",
    "SR",
    "UR",
    "SAR",
    "SEC",
)

LANGUAGE_VALUES = (
    "jp",
    "en",
    "ja",
)

CONDITION_VALUES = (
    "NM",
    "EX",
    "PLD",
    "MP",
    "HP",
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
    "selected",
    "inventory_id",
    "genre",
    "card_name",
    "note",
    "quantity",
    "sale_price",
    "last_checked_date",
    "status",
    "price_links",
)

EDIT_FIELDS = (
    "note",
    "quantity",
    "sale_price",
    "last_checked_date",
    "status",
)

PURCHASE_MODE_EDIT_FIELDS = (
    *EDIT_FIELDS,
    "card_name",
    "rarity",
    "set_name",
    "collector_number",
    "condition",
    "purchase_price",
    "memo",
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

DISPLAYABLE_COLUMNS = (
    "inventory_id",
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
    "registered_date",
    "last_checked_date",
    "updated_date",
    "memo",
    "price_links",
)

DEFAULT_VISIBLE_COLUMNS = (
    "genre",
    "card_name",
    "note",
    "quantity",
    "sale_price",
    "last_checked_date",
    "status",
    "price_links",
)

WORK_MODES = {
    "management": {
        "label": "管理モード",
        "default_status": "販売中",
        "default_columns": DEFAULT_VISIBLE_COLUMNS,
    },
    "purchase": {
        "label": "買取モード",
        "default_status": "準備中",
        "default_columns": (
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
            "memo",
            "status",
            "price_links",
        ),
    },
    "review": {
        "label": "価格見直しモード",
        "default_status": "販売中",
        "default_columns": (
            "genre",
            "card_name",
            "note",
            "quantity",
            "sale_price",
            "purchase_price",
            "last_checked_date",
            "updated_date",
            "status",
            "price_links",
        ),
    },
}

VIRTUAL_FIELD_LABELS = {
    "selected": "選択",
    "price_links": "価格検索リンク",
    "actions": "操作",
}

SORT_FIELDS = (
    "genre",
    "card_name",
    "rarity",
    "set_name",
    "language",
    "condition",
    "quantity",
    "purchase_price",
    "sale_price",
    "registered_date",
    "last_checked_date",
    "updated_date",
    "status",
)

PRICE_LINK_VARIABLES = (
    "genre",
    "card_name",
    "set",
    "language",
    "collector_number",
    "condition",
    "note",
    "query",
)
