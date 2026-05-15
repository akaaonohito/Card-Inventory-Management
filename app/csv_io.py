from __future__ import annotations

import csv
from pathlib import Path

from .constants import CSV_HEADERS, FIELD_TO_HEADER, HEADER_TO_FIELD
from .database import create_backup, insert_inventory, list_inventory, today_text, transaction
from .validation import ValidationError, normalize_inventory_payload


def _read_csv(path: Path) -> list[dict[str, str]]:
    encodings = ("utf-8-sig", "cp932")
    last_error: Exception | None = None
    for encoding in encodings:
        try:
            with path.open("r", encoding=encoding, newline="") as file:
                reader = csv.DictReader(file)
                if not reader.fieldnames:
                    raise ValidationError("CSVヘッダー行が見つかりません。")
                missing = [header for header in CSV_HEADERS if header not in reader.fieldnames]
                if missing:
                    raise ValidationError("通常CSVの列が不足しています: " + ", ".join(missing))
                return list(reader)
        except UnicodeDecodeError as exc:
            last_error = exc
    raise ValidationError("CSVの文字コードを読み込めません。UTF-8またはCP932で保存してください。") from last_error


def preview_import(path: str) -> tuple[list[dict[str, object]], list[str]]:
    rows = _read_csv(Path(path))
    normalized_rows: list[dict[str, object]] = []
    errors: list[str] = []
    for index, row in enumerate(rows, start=2):
        raw = {field: row.get(header, "") for header, field in HEADER_TO_FIELD.items()}
        raw["inventory_id"] = ""
        try:
            normalized = normalize_inventory_payload(raw, for_insert=True)
        except ValidationError as exc:
            errors.append(f"{index}行目: {exc}")
            continue
        normalized_rows.append(normalized)
    return normalized_rows, errors


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


def export_csv(path: str, status_filter: str = "") -> int:
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

