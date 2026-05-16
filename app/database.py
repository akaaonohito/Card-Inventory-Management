from __future__ import annotations

import shutil
import sqlite3
from contextlib import contextmanager
from datetime import date, datetime
from pathlib import Path
from typing import Iterable

from .constants import BACKUP_DIR, DATA_DIR, DB_FILENAME


ROOT_DIR = Path(__file__).resolve().parent.parent
DATA_PATH = ROOT_DIR / DATA_DIR
DB_PATH = DATA_PATH / DB_FILENAME
BACKUP_PATH = DATA_PATH / BACKUP_DIR


def today_text() -> str:
    return date.today().isoformat()


def ensure_data_dirs() -> None:
    DATA_PATH.mkdir(exist_ok=True)
    BACKUP_PATH.mkdir(exist_ok=True)


def get_connection() -> sqlite3.Connection:
    ensure_data_dirs()
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys = ON")
    return conn


def initialize_database() -> None:
    with get_connection() as conn:
        conn.execute(
            """
            CREATE TABLE IF NOT EXISTS app_meta (
                key TEXT PRIMARY KEY,
                value TEXT NOT NULL
            )
            """
        )
        conn.execute(
            """
            CREATE TABLE IF NOT EXISTS inventory (
                inventory_id TEXT PRIMARY KEY,
                genre TEXT NOT NULL,
                card_name TEXT NOT NULL,
                rarity TEXT NOT NULL DEFAULT '',
                set_name TEXT NOT NULL DEFAULT '',
                language TEXT NOT NULL DEFAULT '',
                collector_number TEXT NOT NULL DEFAULT '',
                note TEXT NOT NULL DEFAULT '',
                condition TEXT NOT NULL DEFAULT '',
                quantity INTEGER NOT NULL,
                purchase_price INTEGER,
                sale_price INTEGER NOT NULL,
                status TEXT NOT NULL,
                registered_date TEXT NOT NULL,
                last_checked_date TEXT NOT NULL,
                updated_date TEXT NOT NULL,
                memo TEXT NOT NULL DEFAULT ''
            )
            """
        )
        conn.execute(
            """
            CREATE TABLE IF NOT EXISTS price_search_settings (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                genre TEXT NOT NULL DEFAULT '',
                site_name TEXT NOT NULL,
                url_template TEXT NOT NULL,
                query_template TEXT NOT NULL,
                enabled INTEGER NOT NULL DEFAULT 1
            )
            """
        )
        conn.execute(
            """
            INSERT INTO app_meta(key, value)
            VALUES('schema_version', '1')
            ON CONFLICT(key) DO NOTHING
            """
        )
        conn.execute("PRAGMA user_version = 1")
        seed_default_price_search_settings(conn)


def seed_default_price_search_settings(conn: sqlite3.Connection) -> None:
    row = conn.execute("SELECT COUNT(*) AS count FROM price_search_settings").fetchone()
    if row["count"]:
        return
    defaults = (
        (
            "MTG",
            "晴れる屋",
            "https://www.hareruyamtg.com/ja/products/search?product={query}",
            "{card_name} {set} {collector_number}",
            1,
        ),
        (
            "ポケカ",
            "カードラッシュ ポケモン",
            "https://www.cardrush-pokemon.jp/product-list?keyword={query}",
            "{card_name} {set} {collector_number}",
            1,
        ),
    )
    conn.executemany(
        """
        INSERT INTO price_search_settings(genre, site_name, url_template, query_template, enabled)
        VALUES(?, ?, ?, ?, ?)
        """,
        defaults,
    )


def create_backup(reason: str) -> Path | None:
    ensure_data_dirs()
    if not DB_PATH.exists():
        return None
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    safe_reason = "".join(ch for ch in reason if ch.isalnum() or ch in ("-", "_")) or "backup"
    target = BACKUP_PATH / f"inventory_{timestamp}_{safe_reason}.sqlite3"
    shutil.copy2(DB_PATH, target)
    return target


@contextmanager
def transaction() -> Iterable[sqlite3.Connection]:
    conn = get_connection()
    try:
        conn.execute("BEGIN")
        yield conn
    except Exception:
        conn.rollback()
        raise
    else:
        conn.commit()
    finally:
        conn.close()


def next_inventory_id(conn: sqlite3.Connection) -> str:
    row = conn.execute(
        """
        SELECT MAX(CAST(SUBSTR(inventory_id, 5) AS INTEGER)) AS max_number
        FROM inventory
        WHERE inventory_id LIKE 'INV-%'
        """
    ).fetchone()
    next_number = (row["max_number"] or 0) + 1
    return f"INV-{next_number:06d}"


def list_inventory(status_filter: str = "販売中") -> list[sqlite3.Row]:
    with get_connection() as conn:
        if status_filter:
            return list(
                conn.execute(
                    """
                    SELECT * FROM inventory
                    WHERE status = ?
                    ORDER BY updated_date DESC, inventory_id DESC
                    """,
                    (status_filter,),
                )
            )
        return list(
            conn.execute(
                """
                SELECT * FROM inventory
                ORDER BY updated_date DESC, inventory_id DESC
                """
            )
        )


def list_all_inventory() -> list[sqlite3.Row]:
    with get_connection() as conn:
        return list(conn.execute("SELECT * FROM inventory"))


def get_inventory(inventory_id: str) -> sqlite3.Row | None:
    with get_connection() as conn:
        return conn.execute(
            "SELECT * FROM inventory WHERE inventory_id = ?",
            (inventory_id,),
        ).fetchone()


def insert_inventory(conn: sqlite3.Connection, data: dict[str, object]) -> str:
    inventory_id = next_inventory_id(conn)
    payload = dict(data)
    payload["inventory_id"] = inventory_id
    conn.execute(
        """
        INSERT INTO inventory (
            inventory_id, genre, card_name, rarity, set_name, language,
            collector_number, note, condition, quantity, purchase_price,
            sale_price, status, registered_date, last_checked_date,
            updated_date, memo
        ) VALUES (
            :inventory_id, :genre, :card_name, :rarity, :set_name, :language,
            :collector_number, :note, :condition, :quantity, :purchase_price,
            :sale_price, :status, :registered_date, :last_checked_date,
            :updated_date, :memo
        )
        """,
        payload,
    )
    return inventory_id


def duplicate_inventory(conn: sqlite3.Connection, source_inventory_id: str) -> str:
    source = conn.execute(
        "SELECT * FROM inventory WHERE inventory_id = ?",
        (source_inventory_id,),
    ).fetchone()
    if not source:
        raise ValueError("複製元の在庫が見つかりません。")
    today = today_text()
    payload = {
        "genre": source["genre"],
        "card_name": source["card_name"],
        "rarity": source["rarity"],
        "set_name": source["set_name"],
        "language": source["language"],
        "collector_number": source["collector_number"],
        "note": source["note"],
        "condition": source["condition"],
        "quantity": source["quantity"],
        "purchase_price": source["purchase_price"],
        "sale_price": source["sale_price"],
        "status": source["status"],
        "registered_date": today,
        "last_checked_date": today,
        "updated_date": today,
        "memo": source["memo"],
    }
    return insert_inventory(conn, payload)


def update_inventory(conn: sqlite3.Connection, inventory_id: str, data: dict[str, object]) -> None:
    payload = dict(data)
    payload["inventory_id"] = inventory_id
    assignments = ", ".join(f"{field} = :{field}" for field in payload if field != "inventory_id")
    conn.execute(
        f"UPDATE inventory SET {assignments} WHERE inventory_id = :inventory_id",
        payload,
    )


def bulk_update_inventory(conn: sqlite3.Connection, inventory_ids: list[str], data: dict[str, object]) -> int:
    if not inventory_ids or not data:
        return 0
    assignments = ", ".join(f"{field} = :{field}" for field in data)
    payloads = [dict(data, inventory_id=inventory_id) for inventory_id in inventory_ids]
    conn.executemany(
        f"UPDATE inventory SET {assignments} WHERE inventory_id = :inventory_id",
        payloads,
    )
    return len(payloads)


def get_app_setting(key: str, default: str = "") -> str:
    with get_connection() as conn:
        row = conn.execute("SELECT value FROM app_meta WHERE key = ?", (key,)).fetchone()
        return row["value"] if row else default


def set_app_setting(conn: sqlite3.Connection, key: str, value: str) -> None:
    conn.execute(
        """
        INSERT INTO app_meta(key, value)
        VALUES(?, ?)
        ON CONFLICT(key) DO UPDATE SET value = excluded.value
        """,
        (key, value),
    )


def list_price_search_settings(include_disabled: bool = False) -> list[sqlite3.Row]:
    with get_connection() as conn:
        if include_disabled:
            return list(
                conn.execute(
                    """
                    SELECT * FROM price_search_settings
                    ORDER BY enabled DESC, genre, site_name, id
                    """
                )
            )
        return list(
            conn.execute(
                """
                SELECT * FROM price_search_settings
                WHERE enabled = 1
                ORDER BY genre, site_name, id
                """
            )
        )


def upsert_price_search_setting(conn: sqlite3.Connection, data: dict[str, object]) -> int:
    payload = {
        "id": data.get("id"),
        "genre": str(data.get("genre") or "").strip(),
        "site_name": str(data.get("site_name") or "").strip(),
        "url_template": str(data.get("url_template") or "").strip(),
        "query_template": str(data.get("query_template") or "").strip(),
        "enabled": 1 if data.get("enabled") else 0,
    }
    if not payload["site_name"]:
        raise ValueError("サイト名は必須です。")
    if "{query}" not in payload["url_template"]:
        raise ValueError("検索URLテンプレートには {query} を含めてください。")
    if not payload["query_template"]:
        raise ValueError("検索語テンプレートは必須です。")
    if payload["id"]:
        conn.execute(
            """
            UPDATE price_search_settings
            SET genre = :genre, site_name = :site_name, url_template = :url_template,
                query_template = :query_template, enabled = :enabled
            WHERE id = :id
            """,
            payload,
        )
        return int(payload["id"])
    cursor = conn.execute(
        """
        INSERT INTO price_search_settings(genre, site_name, url_template, query_template, enabled)
        VALUES(:genre, :site_name, :url_template, :query_template, :enabled)
        """,
        payload,
    )
    return int(cursor.lastrowid)
