from __future__ import annotations

import re
from datetime import date

from .constants import STATUS_VALUES

DATE_PATTERN = re.compile(r"^\d{4}-\d{2}-\d{2}$")


class ValidationError(ValueError):
    pass


def parse_date_text(value: object, field_name: str) -> str:
    text = str(value or "").strip()
    if not text:
        raise ValidationError(f"{field_name}は必須です。")
    if not DATE_PATTERN.match(text):
        raise ValidationError(f"{field_name}はYYYY-MM-DD形式で入力してください。")
    try:
        date.fromisoformat(text)
    except ValueError as exc:
        raise ValidationError(f"{field_name}の日付が不正です。") from exc
    return text


def parse_required_text(value: object, field_name: str) -> str:
    text = str(value or "").strip()
    if not text:
        raise ValidationError(f"{field_name}は必須です。")
    return text


def parse_optional_text(value: object) -> str:
    return str(value or "").strip()


def parse_required_int(value: object, field_name: str, minimum: int = 0) -> int:
    text = str(value or "").strip()
    if not text:
        raise ValidationError(f"{field_name}は必須です。")
    try:
        number = int(text)
    except ValueError as exc:
        raise ValidationError(f"{field_name}は整数で入力してください。") from exc
    if number < minimum:
        raise ValidationError(f"{field_name}は{minimum}以上で入力してください。")
    return number


def parse_optional_int(value: object, field_name: str, minimum: int = 0) -> int | None:
    text = str(value or "").strip()
    if not text:
        return None
    try:
        number = int(text)
    except ValueError as exc:
        raise ValidationError(f"{field_name}は整数で入力してください。") from exc
    if number < minimum:
        raise ValidationError(f"{field_name}は{minimum}以上で入力してください。")
    return number


def normalize_inventory_payload(raw: dict[str, object], *, for_insert: bool) -> dict[str, object]:
    today = date.today().isoformat()
    registered_date = raw.get("registered_date") or today
    last_checked_date = raw.get("last_checked_date") or registered_date
    updated_date = raw.get("updated_date") or today
    status = str(raw.get("status") or "販売中").strip()

    if status not in STATUS_VALUES:
        raise ValidationError("在庫ステータスは指定された候補から選択してください。")

    payload: dict[str, object] = {
        "genre": parse_required_text(raw.get("genre"), "ジャンル"),
        "card_name": parse_required_text(raw.get("card_name"), "カード名"),
        "rarity": parse_optional_text(raw.get("rarity")),
        "set_name": parse_optional_text(raw.get("set_name")),
        "language": parse_optional_text(raw.get("language")),
        "collector_number": parse_optional_text(raw.get("collector_number")),
        "note": parse_optional_text(raw.get("note")),
        "condition": parse_optional_text(raw.get("condition")),
        "quantity": parse_required_int(raw.get("quantity"), "枚数", 0),
        "purchase_price": parse_optional_int(raw.get("purchase_price"), "買取価格", 0),
        "sale_price": parse_required_int(raw.get("sale_price"), "販売価格", 0),
        "status": status,
        "registered_date": parse_date_text(registered_date, "登録日"),
        "last_checked_date": parse_date_text(last_checked_date, "最終確認日"),
        "updated_date": parse_date_text(updated_date, "更新日"),
        "memo": parse_optional_text(raw.get("memo")),
    }
    if not for_insert:
        payload["updated_date"] = today
    return payload

