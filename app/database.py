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
            INSERT INTO app_meta(key, value)
            VALUES('schema_version', '1')
            ON CONFLICT(key) DO NOTHING
            """
        )
        conn.execute("PRAGMA user_version = 1")


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


def update_inventory(conn: sqlite3.Connection, inventory_id: str, data: dict[str, object]) -> None:
    payload = dict(data)
    payload["inventory_id"] = inventory_id
    assignments = ", ".join(f"{field} = :{field}" for field in payload if field != "inventory_id")
    conn.execute(
        f"UPDATE inventory SET {assignments} WHERE inventory_id = :inventory_id",
        payload,
    )

