from __future__ import annotations

import csv
from pathlib import Path

from .constants import CSV_HEADERS, FIELD_TO_HEADER, HEADER_TO_FIELD
from .database import create_backup, insert_inventory, list_inventory, today_text, transaction
from .validation import ValidationError, normalize_inventory_payload

MANABOX_REQUIRED_HEADERS = (
    "Name",
    "Set code",
    "Collector number",
    "Foil",
    "Rarity",
    "Quantity",
    "Language",
)

IMPORT_FORMAT_LABELS = {
    "normal": "通常CSV",
    "manabox": "Manabox CSV",
}


def _read_csv(path: Path) -> tuple[list[str], list[dict[str, str]]]:
    encodings = ("utf-8-sig", "cp932")
    last_error: Exception | None = None
    for encoding in encodings:
        try:
            with path.open("r", encoding=encoding, newline="") as file:
                reader = csv.DictReader(file)
                if not reader.fieldnames:
                    raise ValidationError("CSVヘッダー行が見つかりません。")
                return list(reader.fieldnames), list(reader)
        except UnicodeDecodeError as exc:
            last_error = exc
    raise ValidationError("CSVの文字コードを読み込めません。UTF-8またはCP932で保存してください。") from last_error


def detect_import_format(headers: list[str]) -> str:
    header_set = set(headers)
    if all(header in header_set for header in MANABOX_REQUIRED_HEADERS):
        return "manabox"
    if all(header in header_set for header in CSV_HEADERS):
        return "normal"

    missing_normal = [header for header in CSV_HEADERS if header not in header_set]
    missing_manabox = [header for header in MANABOX_REQUIRED_HEADERS if header not in header_set]
    raise ValidationError(
        "CSV形式を判別できません。\n"
        "通常CSVの不足列: "
        + ", ".join(missing_normal)
        + "\nManabox CSVの不足列: "
        + ", ".join(missing_manabox)
    )


def _foil_to_note(value: object) -> str:
    text = str(value or "").strip()
    lowered = text.casefold()
    if lowered == "foil":
        return "#Foil"
    if lowered == "normal":
        return ""
    return text


def _rarity_to_code(value: object) -> str:
    text = str(value or "").strip()
    return {
        "common": "C",
        "uncommon": "U",
        "rare": "R",
        "mythic": "M",
    }.get(text.casefold(), text)


def _language_to_code(value: object) -> str:
    text = str(value or "").strip()
    return "jp" if text.casefold() == "ja" else text


def _normal_row_to_raw(row: dict[str, str]) -> dict[str, object]:
    raw = {field: row.get(header, "") for header, field in HEADER_TO_FIELD.items()}
    raw["inventory_id"] = ""
    return raw


def _manabox_row_to_raw(row: dict[str, str]) -> dict[str, object]:
    today = today_text()
    return {
        "inventory_id": "",
        "genre": "MTG",
        "card_name": row.get("Name", ""),
        "rarity": _rarity_to_code(row.get("Rarity", "")),
        "set_name": row.get("Set code", ""),
        "language": _language_to_code(row.get("Language", "")),
        "collector_number": row.get("Collector number", ""),
        "note": _foil_to_note(row.get("Foil", "")),
        "condition": "",
        "quantity": row.get("Quantity", ""),
        "purchase_price": "",
        "sale_price": "0",
        "status": "準備中",
        "registered_date": today,
        "last_checked_date": today,
        "updated_date": today,
        "memo": "",
    }


def preview_import(path: str) -> tuple[list[dict[str, object]], list[str]]:
    headers, rows = _read_csv(Path(path))
    import_format = detect_import_format(headers)
    normalized_rows: list[dict[str, object]] = []
    errors: list[str] = []
    for index, row in enumerate(rows, start=2):
        raw = _manabox_row_to_raw(row) if import_format == "manabox" else _normal_row_to_raw(row)
        try:
            normalized = normalize_inventory_payload(raw, for_insert=True)
        except ValidationError as exc:
            errors.append(f"{index}行目: {exc}")
            continue
        normalized_rows.append(normalized)
    return normalized_rows, errors


def preview_import_with_format(path: str) -> tuple[str, list[dict[str, object]], list[str]]:
    headers, _rows = _read_csv(Path(path))
    import_format = detect_import_format(headers)
    rows, errors = preview_import(path)
    return IMPORT_FORMAT_LABELS[import_format], rows, errors


def import_csv(path: str, *, skip_errors: bool) -> tuple[int, list[str]]:
    normalized_rows, errors = preview_import(path)
    if errors and not skip_errors:
        return 0, errors
    if not normalized_rows:
        return 0, errors

    create_backup("before_csv_import")
    with transaction() as conn:
        for row in normalized_rows:
            insert_inventory(conn, row)
    return len(normalized_rows), errors


def export_csv(path: str, status_filter: str = "", rows: list[object] | None = None) -> int:
    if rows is None:
        rows = list_inventory(status_filter)
    with Path(path).open("w", encoding="utf-8-sig", newline="") as file:
        writer = csv.DictWriter(file, fieldnames=CSV_HEADERS)
        writer.writeheader()
        for row in rows:
            writer.writerow(
                {
                    header: "" if row[field] is None else row[field]
                    for field, header in FIELD_TO_HEADER.items()
                }
            )
    return len(rows)


def write_sample_csv(path: Path) -> None:
    if path.exists():
        return
    today = today_text()
    rows = [
        {
            "在庫ID": "",
            "ジャンル": "MTG",
            "カード名": "Lightning Bolt",
            "レア": "C",
            "セット": "4EDBB",
            "言語": "jp",
            "コレクター番号": "",
            "補足": "#通常版",
            "カード状態": "MP",
            "枚数": "1",
            "買取価格": "1000",
            "販売価格": "2100",
            "在庫ステータス": "販売中",
            "登録日": today,
            "最終確認日": today,
            "更新日": today,
            "メモ": "",
        }
    ]
    with path.open("w", encoding="utf-8-sig", newline="") as file:
        writer = csv.DictWriter(file, fieldnames=CSV_HEADERS)
        writer.writeheader()
        writer.writerows(rows)
