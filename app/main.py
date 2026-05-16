from __future__ import annotations

import calendar
import re
import tkinter as tk
import unicodedata
import webbrowser
from datetime import date, timedelta
from string import Formatter
from tkinter import filedialog, messagebox, ttk
from urllib.parse import quote_plus

from .constants import (
    APP_NAME,
    DEFAULT_VISIBLE_COLUMNS,
    DETAIL_EDIT_FIELDS,
    DISPLAYABLE_COLUMNS,
    EDIT_FIELDS,
    FIELD_TO_HEADER,
    PURCHASE_MODE_EDIT_FIELDS,
    SORT_FIELDS,
    STATUS_VALUES,
    VIRTUAL_FIELD_LABELS,
    WORK_MODES,
)
from .csv_io import export_csv, import_csv, preview_import_with_format, write_sample_csv
from .database import (
    ROOT_DIR,
    bulk_update_inventory,
    duplicate_inventory,
    get_app_setting,
    get_inventory,
    initialize_database,
    insert_inventory,
    list_all_inventory,
    list_price_search_settings,
    set_app_setting,
    transaction,
    update_inventory,
    upsert_price_search_setting,
)
from .validation import ValidationError, normalize_inventory_payload


FIELD_LABELS = FIELD_TO_HEADER | VIRTUAL_FIELD_LABELS
ALL_STATUS_FILTER_LABEL = "全商品"
TREE_COLUMNS = ("selected", *DISPLAYABLE_COLUMNS, "actions")
TEXT_FILTER_FIELDS = ("genre", "card_name", "rarity", "set_name", "language", "collector_number", "note")
DATE_FILTERS = (
    ("date_from", "日付From"),
    ("date_to", "日付To"),
)
DATE_FILTER_LABEL_TO_FIELD = {
    "登録日": "registered_date",
    "更新日": "updated_date",
    "最終確認日": "last_checked_date",
}
QUICK_EDIT_EXCLUDED_FIELDS = {
    "selected",
    "inventory_id",
    "registered_date",
    "updated_date",
    "price_links",
}
def normalize_search_text(value: object) -> str:
    return unicodedata.normalize("NFKC", str(value or "")).casefold()


def tagize_note(value: str) -> str:
    parts = [part.strip() for part in re.split(r"\s+", value.strip()) if part.strip()]
    if not parts:
        return ""
    return " ".join(part if part.startswith("#") else f"#{part}" for part in parts)


def row_to_dict(row) -> dict[str, object]:
    return {key: row[key] for key in row.keys()}


def build_price_search_url(row: dict[str, object], setting) -> str:
    values = {
        "genre": row.get("genre", ""),
        "card_name": row.get("card_name", ""),
        "set": row.get("set_name", ""),
        "language": row.get("language", ""),
        "collector_number": row.get("collector_number", ""),
        "condition": row.get("condition", ""),
        "note": row.get("note", ""),
        "query": "",
    }
    query_template = setting["query_template"]
    query = query_template
    for _, field_name, _, _ in Formatter().parse(query_template):
        if field_name:
            query = query.replace("{" + field_name + "}", str(values.get(field_name, "")))
    values["query"] = quote_plus(" ".join(query.split()))
    return setting["url_template"].replace("{query}", values["query"])


class InventoryApp(tk.Tk):
    def __init__(self) -> None:
        super().__init__()
        self.title(APP_NAME)
        self.geometry("1320x820")
        self.minsize(1080, 680)
        initialize_database()
        write_sample_csv(ROOT_DIR / "sample_inventory.csv")
        self.filter_vars: dict[str, tk.StringVar] = {}
        self.active_sort_field: str | None = None
        self.active_sort_direction = ""
        self.filters_open = tk.BooleanVar(value=True)
        self.add_vars: dict[str, tk.StringVar] = {}
        self.visible_column_vars: dict[str, tk.BooleanVar] = {}
        self.mode_status_vars: dict[str, tk.StringVar] = {}
        self.price_setting_vars: dict[str, tk.StringVar | tk.BooleanVar] = {}
        self.editing_price_setting_id: int | None = None
        self.selected_ids: set[str] = set()
        self.current_rows: list[dict[str, object]] = []
        self.filtered_rows: list[dict[str, object]] = []
        self.mode_label_to_key = {config["label"]: key for key, config in WORK_MODES.items()}
        self.current_mode_key = self._load_active_mode()
        self.mode_label_var = tk.StringVar(value=self._mode_label(self.current_mode_key))
        self.settings_mode_label_var = tk.StringVar(value=self._mode_label(self.current_mode_key))
        self.quick_edit_inventory_id: str | None = None
        self.quick_edit_vars: dict[str, tk.StringVar] = {}
        self.quick_edit_fields: list[str] = []
        self.quick_edit_widgets: list[tk.Widget] = []
        self.quick_edit_buttons: ttk.Frame | None = None
        self._tree_values_before_edit: tuple[object, ...] | None = None
        self._tree_resize_after_id: str | None = None
        self._build_ui()
        self.refresh_inventory()

    def _build_ui(self) -> None:
        self.columnconfigure(0, weight=1)
        self.rowconfigure(1, weight=1)

        header = ttk.Frame(self, padding=(16, 12))
        header.grid(row=0, column=0, sticky="ew")
        header.columnconfigure(0, weight=1)
        ttk.Label(header, text=APP_NAME, font=("", 18, "bold")).grid(row=0, column=0, sticky="w")
        ttk.Label(header, text="Phase 3: 作業モード切替、モード別表示列、初期ステータス").grid(row=1, column=0, sticky="w")
        mode_switch = ttk.Frame(header)
        mode_switch.grid(row=0, column=1, rowspan=2, sticky="e")
        ttk.Label(mode_switch, text="作業モード").pack(side="left", padx=(0, 8))
        mode_box = ttk.Combobox(
            mode_switch,
            textvariable=self.mode_label_var,
            values=self._mode_labels(),
            state="readonly",
            width=18,
        )
        mode_box.pack(side="left")
        mode_box.bind("<<ComboboxSelected>>", lambda _event: self.change_mode_from_header())

        notebook = ttk.Notebook(self)
        notebook.grid(row=1, column=0, sticky="nsew", padx=16, pady=(0, 16))
        self.inventory_tab = ttk.Frame(notebook, padding=12)
        self.add_tab = ttk.Frame(notebook, padding=12)
        self.csv_tab = ttk.Frame(notebook, padding=12)
        self.settings_tab = ttk.Frame(notebook, padding=12)
        notebook.add(self.inventory_tab, text="在庫一覧")
        notebook.add(self.add_tab, text="商品追加")
        notebook.add(self.csv_tab, text="CSV")
        notebook.add(self.settings_tab, text="設定")

        self._build_inventory_tab()
        self._build_add_tab()
        self._build_csv_tab()
        self._build_settings_tab()

    def _build_inventory_tab(self) -> None:
        self.inventory_tab.columnconfigure(0, weight=1)
        self.inventory_tab.rowconfigure(2, weight=1)
        self._build_filter_area()
        self._build_inventory_controls()
        self._build_inventory_tree()
        self._build_result_status()

    def _build_filter_area(self) -> None:
        wrapper = ttk.Frame(self.inventory_tab)
        wrapper.grid(row=0, column=0, sticky="ew", pady=(0, 8))
        wrapper.columnconfigure(0, weight=1)
        top = ttk.Frame(wrapper)
        top.grid(row=0, column=0, sticky="ew")
        ttk.Button(top, text="絞り込み条件", command=self.toggle_filters).pack(side="left")
        self.filter_summary_label = ttk.Label(top, text="")
        self.filter_summary_label.pack(side="left", padx=(10, 0))

        self.filter_frame = ttk.LabelFrame(wrapper, text="絞り込み", padding=8)
        defaults = {"status": self._mode_default_status(self.current_mode_key), "review_days": ""}
        for field in (*TEXT_FILTER_FIELDS, "status", "review_days"):
            self.filter_vars[field] = tk.StringVar(value=defaults.get(field, ""))
        self.filter_vars["date_field"] = tk.StringVar(value="最終確認日")
        for field, _label in DATE_FILTERS:
            self.filter_vars[field] = tk.StringVar(value="")

        for column in (1, 3, 5, 7, 9, 11):
            self.filter_frame.columnconfigure(column, weight=1, uniform="filter_input")

        def add_filter_widget(row: int, group: int, label: str, widget: tk.Widget, *, group_span: int = 1) -> None:
            label_col = group * 2
            input_col = label_col + 1
            input_span = (group_span * 2) - 1
            ttk.Label(self.filter_frame, text=label).grid(
                row=row,
                column=label_col,
                sticky="w",
                padx=(0, 6),
                pady=3,
            )
            widget.grid(row=row, column=input_col, columnspan=input_span, sticky="ew", padx=(0, 16), pady=3)

        text_layout = (
            (0, 0, "ジャンル", ttk.Entry(self.filter_frame, textvariable=self.filter_vars["genre"], width=10), 1),
            (0, 1, "セット", ttk.Entry(self.filter_frame, textvariable=self.filter_vars["set_name"], width=10), 1),
            (0, 2, "コレクター番号", ttk.Entry(self.filter_frame, textvariable=self.filter_vars["collector_number"], width=10), 1),
            (0, 3, "言語", ttk.Entry(self.filter_frame, textvariable=self.filter_vars["language"], width=8), 1),
            (2, 0, "カード名", ttk.Entry(self.filter_frame, textvariable=self.filter_vars["card_name"], width=22), 2),
            (2, 2, "補足", ttk.Entry(self.filter_frame, textvariable=self.filter_vars["note"], width=22), 2),
            (2, 4, "レア", ttk.Entry(self.filter_frame, textvariable=self.filter_vars["rarity"], width=8), 1),
        )
        for row, group, label, widget, group_span in text_layout:
            add_filter_widget(row, group, label, widget, group_span=group_span)

        status_box = ttk.Combobox(
            self.filter_frame,
            textvariable=self.filter_vars["status"],
            values=(ALL_STATUS_FILTER_LABEL, *STATUS_VALUES),
            state="readonly",
            width=14,
        )
        add_filter_widget(0, 4, "在庫ステータス", status_box, group_span=2)

        date_frame = ttk.Frame(self.filter_frame)
        ttk.Combobox(
            date_frame,
            textvariable=self.filter_vars["date_field"],
            values=tuple(DATE_FILTER_LABEL_TO_FIELD),
            state="readonly",
            width=12,
        ).pack(side="left")
        self._date_entry(date_frame, self.filter_vars["date_from"], width=12).pack(side="left", padx=(8, 0), fill="x", expand=True)
        ttk.Label(date_frame, text=" ～ ").pack(side="left")
        self._date_entry(date_frame, self.filter_vars["date_to"], width=12).pack(side="left", fill="x", expand=True)
        add_filter_widget(1, 0, "日付", date_frame, group_span=4)

        review = ttk.Frame(self.filter_frame)
        ttk.Button(review, text="30日以上", command=lambda: self.set_review_days("30")).pack(side="left")
        ttk.Button(review, text="90日以上", command=lambda: self.set_review_days("90")).pack(side="left", padx=(4, 0))
        ttk.Entry(review, textvariable=self.filter_vars["review_days"], width=7).pack(side="left", padx=(8, 0))
        ttk.Label(review, text="日以上").pack(side="left", padx=(4, 0))
        add_filter_widget(3, 0, "価格見直し", review, group_span=2)

        buttons = ttk.Frame(self.filter_frame)
        buttons.grid(row=3, column=4, columnspan=8, sticky="e", pady=3)
        ttk.Button(buttons, text="解除", command=self.clear_filters).pack(side="right")
        ttk.Button(buttons, text="適用", command=self.refresh_inventory).pack(side="right", padx=(0, 8))
        self.filter_frame.grid(row=1, column=0, sticky="ew", pady=(8, 0))

    def _build_inventory_controls(self) -> None:
        controls = ttk.Frame(self.inventory_tab)
        controls.grid(row=1, column=0, sticky="ew", pady=(0, 8))
        ttk.Button(controls, text="詳細編集", command=self.detail_edit_selected).pack(side="left")
        ttk.Button(controls, text="複製", command=self.duplicate_selected).pack(side="left", padx=(8, 0))
        ttk.Button(controls, text="確認日を今日にする", command=self.mark_selected_checked_today).pack(side="left", padx=(8, 0))
        ttk.Separator(controls, orient="vertical").pack(side="left", fill="y", padx=12)
        ttk.Button(controls, text="チェック全選択", command=self.select_all_filtered).pack(side="left")
        ttk.Button(controls, text="チェック全解除", command=self.clear_all_selected).pack(side="left", padx=(8, 0))
        ttk.Separator(controls, orient="vertical").pack(side="left", fill="y", padx=12)
        ttk.Button(controls, text="選択確認日を今日にする", command=lambda: self.bulk_action("checked_today")).pack(side="left")
        ttk.Button(controls, text="選択を売却済みにする", command=lambda: self.bulk_action("sold")).pack(side="left", padx=(8, 0))
        ttk.Button(controls, text="選択を削除済みにする", command=lambda: self.bulk_action("deleted")).pack(side="left", padx=(8, 0))

    def _build_inventory_tree(self) -> None:
        tree_frame = ttk.Frame(self.inventory_tab)
        tree_frame.grid(row=2, column=0, sticky="nsew")
        tree_frame.columnconfigure(0, weight=1)
        tree_frame.rowconfigure(0, weight=1)
        self.tree = ttk.Treeview(tree_frame, columns=TREE_COLUMNS, show="headings", selectmode="browse")
        for column in TREE_COLUMNS:
            self.tree.heading(column, text=FIELD_LABELS[column], command=lambda field=column: self.sort_by_heading(field))
            self.tree.column(column, width=120, anchor="w")
        self.tree.column("selected", width=56, anchor="center", stretch=False)
        self.tree.column("inventory_id", width=100, stretch=False)
        self.tree.column("actions", width=136, anchor="center", stretch=False)
        self.tree.column("card_name", width=230)
        self.tree.column("note", width=180)
        self.tree.column("price_links", width=180)
        self._apply_display_columns()
        self.tree.grid(row=0, column=0, sticky="nsew")
        self.tree_scrollbar = ttk.Scrollbar(tree_frame, orient="vertical", command=self._scroll_tree)
        self.tree_scrollbar.grid(row=0, column=1, sticky="ns")
        self.tree.configure(yscrollcommand=self._on_tree_yscroll)
        self.tree.bind("<Double-1>", self._handle_tree_double_click)
        self.tree.bind("<Button-1>", self._handle_tree_click)
        self.tree.bind("<Configure>", self._handle_tree_configure)
        self._update_tree_headings()

    def _build_result_status(self) -> None:
        status = ttk.Frame(self.inventory_tab)
        status.grid(row=3, column=0, sticky="ew", pady=(8, 0))
        self.result_label = ttk.Label(status, text="")
        self.result_label.pack(side="left")

    def _build_add_tab(self) -> None:
        self.add_tab.columnconfigure(0, weight=1)
        form = ttk.LabelFrame(self.add_tab, text="商品追加", padding=12)
        form.grid(row=0, column=0, sticky="new")
        fields = (
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
        today = date.today().isoformat()
        defaults = {"status": "販売中", "quantity": "1", "sale_price": "0", "last_checked_date": today}
        for index, field in enumerate(fields):
            row = index // 2
            col = (index % 2) * 2
            ttk.Label(form, text=FIELD_LABELS[field]).grid(row=row, column=col, sticky="w", padx=(0, 8), pady=4)
            var = tk.StringVar(value=defaults.get(field, ""))
            self.add_vars[field] = var
            if field == "status":
                widget = ttk.Combobox(form, textvariable=var, values=STATUS_VALUES, state="readonly", width=28)
            elif field == "last_checked_date":
                widget = self._date_entry(form, var)
            else:
                widget = ttk.Entry(form, textvariable=var, width=30)
            widget.grid(row=row, column=col + 1, sticky="ew", padx=(0, 16), pady=4)
        form.columnconfigure(1, weight=1)
        form.columnconfigure(3, weight=1)
        actions = ttk.Frame(self.add_tab)
        actions.grid(row=1, column=0, sticky="w", pady=12)
        ttk.Button(actions, text="保存", command=self.add_inventory).pack(side="left")
        ttk.Button(actions, text="入力内容で価格検索", command=self.open_add_price_link).pack(side="left", padx=(8, 0))

    def _build_csv_tab(self) -> None:
        self.csv_tab.columnconfigure(0, weight=1)
        text = (
            "通常CSVまたはManabox CSVを自動判別してインポートします。\n"
            "エクスポートは現在の絞り込み条件を反映します。\n"
            "インポート前にはDBバックアップを作成し、登録処理はトランザクションで実行します。"
        )
        ttk.Label(self.csv_tab, text=text, justify="left").grid(row=0, column=0, sticky="w")
        actions = ttk.Frame(self.csv_tab)
        actions.grid(row=1, column=0, sticky="w", pady=14)
        ttk.Button(actions, text="CSVインポート", command=self.import_csv).pack(side="left")
        ttk.Button(actions, text="CSVエクスポート", command=self.export_csv).pack(side="left", padx=(8, 0))
        sample = ROOT_DIR / "sample_inventory.csv"
        ttk.Label(self.csv_tab, text=f"サンプルCSV: {sample}").grid(row=2, column=0, sticky="w", pady=(8, 0))
        manabox_sample = ROOT_DIR / "manabox-scan-サンプル.csv"
        ttk.Label(self.csv_tab, text=f"ManaboxサンプルCSV: {manabox_sample}").grid(row=3, column=0, sticky="w", pady=(4, 0))

    def _build_settings_tab(self) -> None:
        self.settings_tab.columnconfigure(0, weight=1)
        self.settings_tab.rowconfigure(1, weight=1)
        columns = ttk.LabelFrame(self.settings_tab, text="モード別表示設定", padding=10)
        columns.grid(row=0, column=0, sticky="ew")
        mode_select = ttk.Frame(columns)
        mode_select.grid(row=0, column=0, columnspan=4, sticky="ew", pady=(0, 8))
        ttk.Label(mode_select, text="設定対象モード").pack(side="left", padx=(0, 8))
        settings_mode_box = ttk.Combobox(
            mode_select,
            textvariable=self.settings_mode_label_var,
            values=self._mode_labels(),
            state="readonly",
            width=18,
        )
        settings_mode_box.pack(side="left")
        settings_mode_box.bind("<<ComboboxSelected>>", lambda _event: self.load_mode_display_settings())
        ttk.Label(mode_select, text="初期ステータス").pack(side="left", padx=(18, 8))
        for mode_key in WORK_MODES:
            self.mode_status_vars[mode_key] = tk.StringVar(value=self._mode_default_status(mode_key))
        self.settings_status_box = ttk.Combobox(
            mode_select,
            values=STATUS_VALUES,
            state="readonly",
            width=14,
        )
        self.settings_status_box.pack(side="left")

        configurable_columns = [field for field in DISPLAYABLE_COLUMNS if field != "inventory_id"]
        for index, field in enumerate(configurable_columns):
            var = tk.BooleanVar()
            self.visible_column_vars[field] = var
            ttk.Checkbutton(columns, text=FIELD_LABELS[field], variable=var).grid(
                row=(index // 4) + 1,
                column=index % 4,
                sticky="w",
                padx=(0, 16),
                pady=3,
            )
        ttk.Button(columns, text="モード設定を保存", command=self.save_visible_columns).grid(row=6, column=0, sticky="w", pady=(8, 0))
        self.load_mode_display_settings()

        links = ttk.LabelFrame(self.settings_tab, text="価格検索リンク設定", padding=10)
        links.grid(row=1, column=0, sticky="nsew", pady=(12, 0))
        links.columnconfigure(0, weight=1)
        links.rowconfigure(0, weight=1)
        self.price_settings_tree = ttk.Treeview(
            links,
            columns=("id", "genre", "site_name", "enabled"),
            show="headings",
            height=7,
        )
        for column, width in (("id", 60), ("genre", 120), ("site_name", 220), ("enabled", 80)):
            self.price_settings_tree.heading(column, text={"id": "ID", "genre": "ジャンル", "site_name": "サイト名", "enabled": "有効"}[column])
            self.price_settings_tree.column(column, width=width, anchor="w")
        self.price_settings_tree.grid(row=0, column=0, sticky="nsew")
        self.price_settings_tree.bind("<<TreeviewSelect>>", lambda _event: self.load_selected_price_setting())

        form = ttk.Frame(links)
        form.grid(row=1, column=0, sticky="ew", pady=(10, 0))
        for field in ("genre", "site_name", "url_template", "query_template"):
            self.price_setting_vars[field] = tk.StringVar()
        self.price_setting_vars["enabled"] = tk.BooleanVar(value=True)
        price_fields = (
            ("genre", "ジャンル"),
            ("site_name", "サイト名"),
            ("url_template", "検索URLテンプレート"),
            ("query_template", "検索語テンプレート"),
        )
        for index, (field, label) in enumerate(price_fields):
            ttk.Label(form, text=label).grid(row=index, column=0, sticky="w", padx=(0, 8), pady=3)
            ttk.Entry(form, textvariable=self.price_setting_vars[field], width=80).grid(row=index, column=1, sticky="ew", pady=3)
        ttk.Checkbutton(form, text="有効", variable=self.price_setting_vars["enabled"]).grid(row=4, column=1, sticky="w")
        buttons = ttk.Frame(form)
        buttons.grid(row=5, column=1, sticky="w", pady=(8, 0))
        ttk.Button(buttons, text="新規", command=self.clear_price_setting_form).pack(side="left")
        ttk.Button(buttons, text="保存", command=self.save_price_setting).pack(side="left", padx=(8, 0))
        form.columnconfigure(1, weight=1)
        self.refresh_price_settings()

    def _date_entry(self, parent: tk.Widget, var: tk.StringVar, *, width: int | None = None) -> ttk.Frame:
        frame = ttk.Frame(parent)
        entry_options = {"textvariable": var}
        if width:
            entry_options["width"] = width
        ttk.Entry(frame, **entry_options).pack(side="left", fill="x", expand=True)
        ttk.Button(frame, text="日付", command=lambda: self.pick_date(var)).pack(side="left", padx=(4, 0))
        return frame

    def pick_date(self, target_var: tk.StringVar) -> None:
        base = date.today()
        try:
            if target_var.get().strip():
                base = date.fromisoformat(target_var.get().strip())
        except ValueError:
            pass
        state = {"year": base.year, "month": base.month}
        dialog = tk.Toplevel(self)
        dialog.title("日付選択")
        dialog.transient(self)
        dialog.grab_set()
        header = ttk.Frame(dialog, padding=8)
        header.grid(row=0, column=0, sticky="ew")
        body = ttk.Frame(dialog, padding=(8, 0, 8, 8))
        body.grid(row=1, column=0)
        title = ttk.Label(header, width=14, anchor="center")
        title.pack(side="left", padx=8)

        def render() -> None:
            for child in body.winfo_children():
                child.destroy()
            title.configure(text=f"{state['year']}-{state['month']:02d}")
            for col, name in enumerate(("月", "火", "水", "木", "金", "土", "日")):
                ttk.Label(body, text=name, width=4, anchor="center").grid(row=0, column=col)
            for row_index, week in enumerate(calendar.monthcalendar(state["year"], state["month"]), start=1):
                for col, day in enumerate(week):
                    if not day:
                        ttk.Label(body, text="", width=4).grid(row=row_index, column=col)
                        continue
                    value = date(state["year"], state["month"], day).isoformat()
                    ttk.Button(body, text=str(day), width=4, command=lambda v=value: (target_var.set(v), dialog.destroy())).grid(
                        row=row_index,
                        column=col,
                        padx=1,
                        pady=1,
                    )

        def move(month_delta: int) -> None:
            month = state["month"] + month_delta
            year = state["year"]
            if month < 1:
                month = 12
                year -= 1
            elif month > 12:
                month = 1
                year += 1
            state.update(year=year, month=month)
            render()

        ttk.Button(header, text="<", width=3, command=lambda: move(-1)).pack(side="left")
        ttk.Button(header, text=">", width=3, command=lambda: move(1)).pack(side="right")
        render()
        dialog.wait_window()

    def _mode_labels(self) -> tuple[str, ...]:
        return tuple(config["label"] for config in WORK_MODES.values())

    def _mode_label(self, mode_key: str) -> str:
        return WORK_MODES[self._valid_mode_key(mode_key)]["label"]

    def _mode_key_from_label(self, label: str) -> str:
        return self._valid_mode_key(self.mode_label_to_key.get(label, "management"))

    def _valid_mode_key(self, mode_key: str) -> str:
        if mode_key in WORK_MODES:
            return mode_key
        return next(iter(WORK_MODES))

    def _mode_setting_key(self, mode_key: str, name: str) -> str:
        return f"mode_{self._valid_mode_key(mode_key)}_{name}"

    def _load_active_mode(self) -> str:
        return self._valid_mode_key(get_app_setting("active_mode", "management"))

    def _mode_default_columns(self, mode_key: str) -> tuple[str, ...]:
        return tuple(WORK_MODES[self._valid_mode_key(mode_key)]["default_columns"])

    def _load_mode_columns(self, mode_key: str) -> list[str]:
        mode_key = self._valid_mode_key(mode_key)
        fallback = ",".join(self._mode_default_columns(mode_key))
        if mode_key == "management":
            fallback = get_app_setting("visible_columns", fallback)
        saved = get_app_setting(self._mode_setting_key(mode_key, "visible_columns"), fallback)
        visible = [field for field in saved.split(",") if field in DISPLAYABLE_COLUMNS and field != "inventory_id"]
        return visible or list(self._mode_default_columns(mode_key))

    def _mode_default_status(self, mode_key: str) -> str:
        mode_key = self._valid_mode_key(mode_key)
        saved = get_app_setting(self._mode_setting_key(mode_key, "default_status"), WORK_MODES[mode_key]["default_status"])
        return saved if saved in STATUS_VALUES else WORK_MODES[mode_key]["default_status"]

    def change_mode_from_header(self) -> None:
        if not self._confirm_discard_quick_edit():
            self.mode_label_var.set(self._mode_label(self.current_mode_key))
            return
        mode_key = self._mode_key_from_label(self.mode_label_var.get())
        self.current_mode_key = mode_key
        self.settings_mode_label_var.set(self._mode_label(mode_key))
        with transaction() as conn:
            set_app_setting(conn, "active_mode", mode_key)
        self.filter_vars["status"].set(self._mode_default_status(mode_key))
        self.active_sort_field = None
        self.active_sort_direction = ""
        self._apply_display_columns()
        self.load_mode_display_settings()
        self.refresh_inventory()

    def load_mode_display_settings(self) -> None:
        mode_key = self._mode_key_from_label(self.settings_mode_label_var.get())
        visible = set(self._load_mode_columns(mode_key))
        for field, var in self.visible_column_vars.items():
            var.set(field in visible)
        if mode_key in self.mode_status_vars:
            self.mode_status_vars[mode_key].set(self._mode_default_status(mode_key))
            self.settings_status_box.configure(textvariable=self.mode_status_vars[mode_key])

    def toggle_filters(self) -> None:
        if self.filters_open.get():
            self.filter_frame.grid_remove()
            self.filters_open.set(False)
        else:
            self.filter_frame.grid(row=1, column=0, sticky="ew", pady=(8, 0))
            self.filters_open.set(True)

    def set_review_days(self, days: str) -> None:
        self.filter_vars["review_days"].set(days)
        self.refresh_inventory()

    def clear_filters(self) -> None:
        for var in self.filter_vars.values():
            var.set("")
        self.filter_vars["status"].set(self._mode_default_status(self.current_mode_key))
        self.filter_vars["date_field"].set("最終確認日")
        self.active_sort_field = None
        self.active_sort_direction = ""
        self.refresh_inventory()

    def refresh_inventory(self) -> None:
        if not self._confirm_discard_quick_edit():
            return
        self._clear_quick_edit()
        self.current_rows = [row_to_dict(row) for row in list_all_inventory()]
        try:
            self.filtered_rows = self._filter_rows(self.current_rows)
        except ValidationError as exc:
            messagebox.showerror(APP_NAME, str(exc))
            return
        self._sort_rows(self.filtered_rows)
        self._render_tree()
        self._update_filter_summary()

    def _filter_rows(self, rows: list[dict[str, object]]) -> list[dict[str, object]]:
        result = []
        status = self.filter_vars["status"].get()
        for row in rows:
            if status and status != ALL_STATUS_FILTER_LABEL and row["status"] != status:
                continue
            if any(self.filter_vars[field].get().strip() and normalize_search_text(self.filter_vars[field].get()) not in normalize_search_text(row[field]) for field in TEXT_FILTER_FIELDS):
                continue
            if not self._date_ranges_match(row):
                continue
            days_text = self.filter_vars["review_days"].get().strip()
            if days_text:
                try:
                    days = int(days_text)
                except ValueError:
                    raise ValidationError("価格見直しの日数は整数で入力してください。") from None
                threshold = date.today() - timedelta(days=days)
                try:
                    checked = date.fromisoformat(str(row["last_checked_date"]))
                except ValueError:
                    continue
                if checked > threshold:
                    continue
            result.append(row)
        return result

    def _date_ranges_match(self, row: dict[str, object]) -> bool:
        field = DATE_FILTER_LABEL_TO_FIELD.get(self.filter_vars["date_field"].get(), "last_checked_date")
        value = str(row[field])
        from_value = self.filter_vars["date_from"].get().strip()
        to_value = self.filter_vars["date_to"].get().strip()
        try:
            if from_value:
                date.fromisoformat(from_value)
            if to_value:
                date.fromisoformat(to_value)
        except ValueError as exc:
            raise ValidationError("日付の範囲はYYYY-MM-DD形式で入力してください。") from exc
        if from_value and value < from_value:
            return False
        if to_value and value > to_value:
            return False
        return True

    def _sort_rows(self, rows: list[dict[str, object]]) -> None:
        field = self.active_sort_field or "updated_date"
        reverse = self.active_sort_direction == "desc" if self.active_sort_field else True
        numeric = field in {"quantity", "purchase_price", "sale_price"}
        rows.sort(key=lambda row: int(row.get(field) or 0) if numeric else normalize_search_text(row.get(field)), reverse=reverse)
        self._update_tree_headings()

    def sort_by_heading(self, field: str) -> None:
        if field not in SORT_FIELDS:
            return
        if not self._confirm_discard_quick_edit():
            return
        if self.active_sort_field != field:
            self.active_sort_field = field
            self.active_sort_direction = "asc"
        elif self.active_sort_direction == "asc":
            self.active_sort_direction = "desc"
        else:
            self.active_sort_field = None
            self.active_sort_direction = ""
        self.refresh_inventory()

    def _update_tree_headings(self) -> None:
        if not hasattr(self, "tree"):
            return
        for column in TREE_COLUMNS:
            label = FIELD_LABELS[column]
            if column == self.active_sort_field:
                label = f"{label} {'↑' if self.active_sort_direction == 'asc' else '↓'}"
            self.tree.heading(column, text=label, command=lambda field=column: self.sort_by_heading(field))

    def _render_tree(self) -> None:
        for item in self.tree.get_children():
            self.tree.delete(item)
        for row in self.filtered_rows:
            inventory_id = str(row["inventory_id"])
            values = self._tree_values(row)
            self.tree.insert("", "end", iid=inventory_id, values=values)
        self.result_label.configure(text=f"表示 {len(self.filtered_rows)}件 / 全{len(self.current_rows)}件")

    def _tree_values(self, row: dict[str, object]) -> list[object]:
        values = []
        for column in TREE_COLUMNS:
            if column == "selected":
                values.append("[x]" if row["inventory_id"] in self.selected_ids else "[ ]")
            elif column == "price_links":
                values.append(self._price_link_label(row))
            elif column == "actions":
                values.append("")
            else:
                values.append("" if row[column] is None else row[column])
        return values

    def _price_link_label(self, row: dict[str, object]) -> str:
        names = [setting["site_name"] for setting in self._matching_price_settings(row)]
        return " / ".join(names)

    def _matching_price_settings(self, row: dict[str, object]) -> list[object]:
        settings = []
        genre = str(row.get("genre") or "")
        for setting in list_price_search_settings():
            setting_genre = str(setting["genre"] or "")
            if not setting_genre or setting_genre == genre:
                settings.append(setting)
        return settings

    def _update_filter_summary(self) -> None:
        active = []
        for key, var in self.filter_vars.items():
            value = var.get().strip()
            if value and not (key == "status" and value == self._mode_default_status(self.current_mode_key)):
                active.append(value)
        default_status = self._mode_default_status(self.current_mode_key)
        self.filter_summary_label.configure(text="条件適用中" if active else f"初期条件: {default_status}")

    def _handle_tree_click(self, event: tk.Event) -> None:
        item = self.tree.identify_row(event.y)
        column = self.tree.identify_column(event.x)
        if not item or not column:
            return
        column_name = self.display_columns[int(column[1:]) - 1]
        if column_name == "selected":
            if item in self.selected_ids:
                self.selected_ids.remove(item)
            else:
                self.selected_ids.add(item)
            self._render_tree()
            return "break"
        return None

    def _handle_tree_double_click(self, event: tk.Event) -> None:
        column = self.tree.identify_column(event.x)
        if column:
            column_name = self.display_columns[int(column[1:]) - 1]
            if column_name == "price_links":
                self.open_selected_price_link()
                return
        self.edit_selected()

    def selected_inventory_id(self) -> str | None:
        selected = self.tree.selection()
        if not selected:
            messagebox.showinfo(APP_NAME, "在庫を1件選択してください。")
            return None
        return selected[0]

    def add_inventory(self) -> None:
        raw = {field: var.get() for field, var in self.add_vars.items()}
        raw["note"] = tagize_note(str(raw.get("note") or ""))
        today = date.today().isoformat()
        raw["registered_date"] = today
        raw["updated_date"] = today
        try:
            payload = normalize_inventory_payload(raw, for_insert=True)
            with transaction() as conn:
                inventory_id = insert_inventory(conn, payload)
        except ValidationError as exc:
            messagebox.showerror(APP_NAME, str(exc))
            return
        messagebox.showinfo(APP_NAME, f"在庫を追加しました: {inventory_id}")
        self._clear_add_form_after_save()
        self.refresh_inventory()

    def _clear_add_form_after_save(self) -> None:
        keep_genre = self.add_vars["genre"].get()
        for field, var in self.add_vars.items():
            var.set(keep_genre if field == "genre" else "")

    def edit_selected(self) -> None:
        inventory_id = self.selected_inventory_id()
        if not inventory_id:
            return
        if self.quick_edit_inventory_id == inventory_id:
            return
        if not self._confirm_discard_quick_edit():
            return
        row = get_inventory(inventory_id)
        if not row:
            messagebox.showerror(APP_NAME, "選択した在庫が見つかりません。")
            return
        self._start_quick_edit(row)

    def detail_edit_selected(self) -> None:
        if not self._confirm_discard_quick_edit():
            return
        inventory_id = self.selected_inventory_id()
        if not inventory_id:
            return
        row = get_inventory(inventory_id)
        if not row:
            messagebox.showerror(APP_NAME, "選択した在庫が見つかりません。")
            return
        self._open_edit_dialog(row, DETAIL_EDIT_FIELDS, title="詳細編集", show_readonly=True)

    def _open_edit_dialog(self, row, fields: tuple[str, ...], *, title: str, show_readonly: bool = False) -> None:
        dialog = tk.Toplevel(self)
        dialog.title(title)
        dialog.transient(self)
        dialog.grab_set()
        dialog.columnconfigure(0, weight=1)
        vars_by_field: dict[str, tk.StringVar] = {}
        content = ttk.Frame(dialog, padding=12)
        content.grid(row=0, column=0, sticky="nsew")
        if show_readonly:
            readonly = f"在庫ID: {row['inventory_id']}    登録日: {row['registered_date']}    更新日: {row['updated_date']}"
            ttk.Label(content, text=readonly).grid(row=0, column=0, columnspan=2, sticky="w", pady=(0, 8))
            start_row = 1
        else:
            start_row = 0
        for index, field in enumerate(fields, start=start_row):
            ttk.Label(content, text=FIELD_LABELS[field]).grid(row=index, column=0, sticky="w", padx=(0, 8), pady=4)
            value = "" if row[field] is None else str(row[field])
            var = tk.StringVar(value=value)
            vars_by_field[field] = var
            if field == "status":
                widget = ttk.Combobox(content, textvariable=var, values=STATUS_VALUES, state="readonly", width=36)
            elif field == "last_checked_date":
                widget = self._date_entry(content, var)
            else:
                widget = ttk.Entry(content, textvariable=var, width=40)
            widget.grid(row=index, column=1, sticky="ew", pady=4)
        buttons = ttk.Frame(content)
        buttons.grid(row=start_row + len(fields), column=0, columnspan=2, sticky="e", pady=(12, 0))
        ttk.Button(buttons, text="キャンセル", command=dialog.destroy).pack(side="right")
        ttk.Button(buttons, text="保存", command=lambda: self._save_edit(dialog, row, vars_by_field)).pack(side="right", padx=(0, 8))
        dialog.wait_window()

    def _save_edit(self, dialog: tk.Toplevel, original_row, vars_by_field: dict[str, tk.StringVar]) -> None:
        raw = {field: original_row[field] for field in FIELD_TO_HEADER if field != "inventory_id"}
        raw.update({field: var.get() for field, var in vars_by_field.items()})
        raw["note"] = tagize_note(str(raw.get("note") or ""))
        try:
            payload = self._normalize_update_payload(original_row, raw)
            with transaction() as conn:
                update_inventory(conn, original_row["inventory_id"], payload)
        except ValidationError as exc:
            messagebox.showerror(APP_NAME, str(exc), parent=dialog)
            return
        dialog.destroy()
        self.refresh_inventory()

    def _start_quick_edit(self, row) -> None:
        self._clear_quick_edit()
        inventory_id = row["inventory_id"]
        if not self.tree.exists(inventory_id):
            return
        quick_edit_fields = self._quick_edit_fields()
        if not quick_edit_fields:
            messagebox.showinfo(APP_NAME, "現在の表示列にクイック編集できる項目がありません。")
            return
        self.quick_edit_inventory_id = inventory_id
        self.quick_edit_vars = {}
        self.quick_edit_fields = quick_edit_fields
        self._tree_values_before_edit = tuple(self.tree.item(inventory_id, "values"))
        values = list(self._tree_values_before_edit)
        columns = list(TREE_COLUMNS)
        for field in self.quick_edit_fields:
            index = columns.index(field)
            values[index] = f"編集中: {FIELD_LABELS[field]}"
            var = tk.StringVar(value="" if row[field] is None else str(row[field]))
            self.quick_edit_vars[field] = var
            if field == "status":
                widget = ttk.Combobox(self.tree, textvariable=var, values=STATUS_VALUES, state="readonly")
            elif field == "last_checked_date":
                widget = self._date_entry(self.tree, var)
            else:
                widget = ttk.Entry(self.tree, textvariable=var)
            widget.bind("<Return>", self._handle_quick_edit_save_key)
            widget.bind("<KP_Enter>", self._handle_quick_edit_save_key)
            widget.bind("<Escape>", self._handle_quick_edit_cancel_key)
            self._bind_quick_edit_children(widget)
            self.quick_edit_widgets.append(widget)
        self.tree.item(inventory_id, values=values)
        self.quick_edit_buttons = ttk.Frame(self.tree)
        ttk.Button(self.quick_edit_buttons, text="保存", command=self._save_quick_edit).pack(side="left")
        ttk.Button(self.quick_edit_buttons, text="キャンセル", command=self._cancel_quick_edit).pack(side="left", padx=(4, 0))
        self.tree.selection_set(inventory_id)
        self.tree.focus(inventory_id)
        self.after_idle(self._position_quick_edit_widgets)
        self.after_idle(lambda: self.quick_edit_widgets[0].focus_set() if self.quick_edit_widgets else None)

    def _quick_edit_fields(self) -> list[str]:
        editable_fields = PURCHASE_MODE_EDIT_FIELDS if self.current_mode_key == "purchase" else EDIT_FIELDS
        return [
            field
            for field in self.display_columns
            if field in editable_fields and field not in QUICK_EDIT_EXCLUDED_FIELDS
        ]

    def _handle_quick_edit_save_key(self, _event: tk.Event) -> str:
        self._save_quick_edit()
        return "break"

    def _handle_quick_edit_cancel_key(self, _event: tk.Event) -> str:
        self._cancel_quick_edit()
        return "break"

    def _bind_quick_edit_children(self, widget: tk.Widget) -> None:
        for child in widget.winfo_children():
            child.bind("<Return>", self._handle_quick_edit_save_key)
            child.bind("<KP_Enter>", self._handle_quick_edit_save_key)
            child.bind("<Escape>", self._handle_quick_edit_cancel_key)
            self._bind_quick_edit_children(child)

    def _position_quick_edit_widgets(self) -> None:
        if not self.quick_edit_inventory_id or not self.tree.exists(self.quick_edit_inventory_id):
            return
        if not self.tree.bbox(self.quick_edit_inventory_id):
            return
        for widget, field in zip(self.quick_edit_widgets, self.quick_edit_fields, strict=True):
            bbox = self.tree.bbox(self.quick_edit_inventory_id, field)
            if not bbox:
                widget.place_forget()
                continue
            x, y, width, height = bbox
            widget.place(x=x + 1, y=y + 1, width=max(width - 2, 44), height=max(height - 2, 20))
        if self.quick_edit_buttons:
            actions_bbox = self.tree.bbox(self.quick_edit_inventory_id, "actions")
            if actions_bbox:
                x, y, width, height = actions_bbox
                button_width = 132
                button_x = x + max((width - button_width) // 2, 1)
                self.quick_edit_buttons.place(x=button_x, y=y + 1, width=button_width, height=max(height - 2, 20))

    def _scroll_tree(self, *args) -> None:
        self.tree.yview(*args)
        self._position_quick_edit_widgets()

    def _on_tree_yscroll(self, *args) -> None:
        self.tree_scrollbar.set(*args)
        self._position_quick_edit_widgets()

    def _handle_tree_configure(self, _event: tk.Event) -> None:
        self._position_quick_edit_widgets()
        if self._tree_resize_after_id:
            self.after_cancel(self._tree_resize_after_id)
        self._tree_resize_after_id = self.after(80, self._fit_tree_columns)

    def _fit_tree_columns(self) -> None:
        self._tree_resize_after_id = None
        if not hasattr(self, "display_columns"):
            return
        available_width = max(self.tree.winfo_width() - 8, 600)
        fixed_widths = {
            "selected": 48,
            "inventory_id": 88,
            "actions": 136,
        }
        min_widths = {
            "genre": 72,
            "card_name": 150,
            "rarity": 64,
            "set_name": 90,
            "collector_number": 96,
            "note": 110,
            "condition": 78,
            "quantity": 58,
            "purchase_price": 78,
            "sale_price": 78,
            "last_checked_date": 96,
            "status": 84,
            "memo": 130,
            "price_links": 120,
        }
        weights = {
            "card_name": 3,
            "note": 2,
            "memo": 2,
            "price_links": 2,
            "genre": 1,
            "set_name": 1,
            "collector_number": 1,
            "quantity": 1,
            "purchase_price": 1,
            "sale_price": 1,
            "last_checked_date": 1,
            "status": 1,
        }
        columns = list(self.display_columns)
        fixed_total = sum(fixed_widths.get(column, 0) for column in columns)
        resizable = [column for column in columns if column not in fixed_widths]
        preferred_widths = {column: min_widths.get(column, 92) for column in resizable}
        preferred_total = sum(preferred_widths.values())
        target_total = max(available_width - fixed_total, len(resizable) * 44)
        if preferred_total > target_total:
            scale = target_total / preferred_total
            sized_widths = {
                column: max(int(preferred_widths[column] * scale), 44)
                for column in resizable
            }
        else:
            extra = target_total - preferred_total
            weight_total = sum(weights.get(column, 1) for column in resizable) or 1
            sized_widths = {
                column: preferred_widths[column] + int(extra * weights.get(column, 1) / weight_total)
                for column in resizable
            }
        for column in columns:
            if column in fixed_widths:
                width = fixed_widths[column]
                stretch = False
            else:
                width = sized_widths[column]
                stretch = True
            self.tree.column(column, width=width, minwidth=min(width, 44), stretch=stretch)
        self._position_quick_edit_widgets()

    def _save_quick_edit(self) -> None:
        if not self.quick_edit_inventory_id:
            return
        row = get_inventory(self.quick_edit_inventory_id)
        if not row:
            messagebox.showerror(APP_NAME, "編集中の在庫が見つかりません。")
            self._clear_quick_edit()
            return
        raw = {field: row[field] for field in FIELD_TO_HEADER if field != "inventory_id"}
        raw.update({field: var.get() for field, var in self.quick_edit_vars.items()})
        raw["note"] = tagize_note(str(raw.get("note") or ""))
        try:
            payload = self._normalize_update_payload(row, raw)
            with transaction() as conn:
                update_inventory(conn, self.quick_edit_inventory_id, payload)
        except ValidationError as exc:
            messagebox.showerror(APP_NAME, str(exc))
            return
        self._clear_quick_edit()
        self.refresh_inventory()

    def _normalize_update_payload(self, original_row, raw: dict[str, object]) -> dict[str, object]:
        payload = normalize_inventory_payload(raw, for_insert=False)
        if payload["sale_price"] != original_row["sale_price"]:
            payload["last_checked_date"] = date.today().isoformat()
        return payload

    def mark_selected_checked_today(self) -> None:
        if not self._confirm_discard_quick_edit():
            return
        inventory_id = self.selected_inventory_id()
        if not inventory_id:
            return
        if not messagebox.askyesno(APP_NAME, "選択した商品の最終確認日を今日にしますか？"):
            return
        today = date.today().isoformat()
        with transaction() as conn:
            bulk_update_inventory(conn, [inventory_id], {"last_checked_date": today, "updated_date": today})
        self.refresh_inventory()

    def select_all_filtered(self) -> None:
        if not self._confirm_discard_quick_edit():
            return
        self.selected_ids.update(str(row["inventory_id"]) for row in self.filtered_rows)
        self._render_tree()

    def clear_all_selected(self) -> None:
        if not self._confirm_discard_quick_edit():
            return
        self.selected_ids.clear()
        self._render_tree()

    def bulk_action(self, action: str) -> None:
        if not self._confirm_discard_quick_edit():
            return
        ids = sorted(self.selected_ids)
        if not ids:
            messagebox.showinfo(APP_NAME, "一括操作する在庫にチェックを付けてください。")
            return
        today = date.today().isoformat()
        if action == "checked_today":
            data = {"last_checked_date": today, "updated_date": today}
            message = f"選択した{len(ids)}件の最終確認日を今日にしますか？"
        elif action == "sold":
            data = {"status": "売却済み", "updated_date": today}
            message = f"選択した{len(ids)}件を売却済みに変更します。よろしいですか？"
        else:
            data = {"status": "削除済み", "updated_date": today}
            message = f"選択した{len(ids)}件を削除済みに変更します。よろしいですか？"
        if not messagebox.askyesno(APP_NAME, message):
            return
        with transaction() as conn:
            bulk_update_inventory(conn, ids, data)
        self.selected_ids.clear()
        self.refresh_inventory()

    def duplicate_selected(self) -> None:
        if not self._confirm_discard_quick_edit():
            return
        inventory_id = self.selected_inventory_id()
        if not inventory_id:
            return
        with transaction() as conn:
            new_id = duplicate_inventory(conn, inventory_id)
        self.refresh_inventory()
        if self.tree.exists(new_id):
            self.tree.selection_set(new_id)
            self.tree.focus(new_id)
            row = get_inventory(new_id)
            if row:
                self._start_quick_edit(row)

    def _cancel_quick_edit(self) -> None:
        self._clear_quick_edit(restore_values=True)

    def _clear_quick_edit(self, *, restore_values: bool = False) -> None:
        if restore_values and self.quick_edit_inventory_id and self._tree_values_before_edit and self.tree.exists(self.quick_edit_inventory_id):
            self.tree.item(self.quick_edit_inventory_id, values=self._tree_values_before_edit)
        for widget in self.quick_edit_widgets:
            widget.destroy()
        self.quick_edit_widgets = []
        if self.quick_edit_buttons:
            self.quick_edit_buttons.destroy()
        self.quick_edit_buttons = None
        self.quick_edit_inventory_id = None
        self.quick_edit_vars = {}
        self.quick_edit_fields = []
        self._tree_values_before_edit = None

    def _confirm_discard_quick_edit(self) -> bool:
        if not self.quick_edit_inventory_id:
            return True
        discard = messagebox.askyesno(APP_NAME, "未保存の編集内容があります。破棄して別の商品を編集しますか？")
        if discard:
            self._clear_quick_edit(restore_values=True)
        return discard

    def open_selected_price_link(self) -> None:
        inventory_id = self.selected_inventory_id()
        if not inventory_id:
            return
        row = get_inventory(inventory_id)
        if not row:
            messagebox.showerror(APP_NAME, "選択した在庫が見つかりません。")
            return
        self._open_price_link(row_to_dict(row))

    def open_add_price_link(self) -> None:
        row = {field: var.get() for field, var in self.add_vars.items()}
        row.setdefault("set_name", row.get("set", ""))
        self._open_price_link(row)

    def _open_price_link(self, row: dict[str, object]) -> None:
        settings = self._matching_price_settings(row)
        if not settings:
            messagebox.showinfo(APP_NAME, "有効な価格検索リンク設定がありません。")
            return
        webbrowser.open(build_price_search_url(row, settings[0]), new=2)

    def import_csv(self) -> None:
        if not self._confirm_discard_quick_edit():
            return
        path = filedialog.askopenfilename(title="CSVインポート", filetypes=(("CSV files", "*.csv"), ("All files", "*.*")))
        if not path:
            return
        try:
            import_format, rows, errors = preview_import_with_format(path)
        except ValidationError as exc:
            messagebox.showerror(APP_NAME, str(exc))
            return
        if errors:
            sample = "\n".join(errors[:10])
            skip = messagebox.askyesno(
                APP_NAME,
                f"{import_format}として読み込みました。\n"
                f"エラーが{len(errors)}件あります。\n\n{sample}\n\n"
                "エラー行をスキップして取り込みますか？",
            )
            if not skip:
                return
        elif not messagebox.askyesno(APP_NAME, f"{import_format}として読み込みました。\n{len(rows)}件を取り込みます。よろしいですか？"):
            return
        try:
            count, _errors = import_csv(path, skip_errors=True)
        except Exception as exc:
            messagebox.showerror(APP_NAME, f"インポートに失敗しました。\n{exc}")
            return
        messagebox.showinfo(APP_NAME, f"{count}件を取り込みました。")
        self.refresh_inventory()

    def export_csv(self) -> None:
        if not self._confirm_discard_quick_edit():
            return
        default_filename = f"カード在庫管理_{date.today():%Y%m%d}.csv"
        path = filedialog.asksaveasfilename(
            title="CSVエクスポート",
            initialfile=default_filename,
            defaultextension=".csv",
            filetypes=(("CSV files", "*.csv"), ("All files", "*.*")),
        )
        if not path:
            return
        try:
            count = export_csv(path, rows=self.filtered_rows)
        except Exception as exc:
            messagebox.showerror(APP_NAME, f"エクスポートに失敗しました。\n{exc}")
            return
        messagebox.showinfo(APP_NAME, f"{count}件をエクスポートしました。")

    def save_visible_columns(self) -> None:
        mode_key = self._mode_key_from_label(self.settings_mode_label_var.get())
        visible = [field for field, var in self.visible_column_vars.items() if var.get()]
        if not visible:
            messagebox.showerror(APP_NAME, "表示列は1つ以上選択してください。")
            return
        default_status = self.mode_status_vars[mode_key].get()
        if default_status not in STATUS_VALUES:
            messagebox.showerror(APP_NAME, "初期ステータスを選択してください。")
            return
        with transaction() as conn:
            set_app_setting(conn, self._mode_setting_key(mode_key, "visible_columns"), ",".join(visible))
            set_app_setting(conn, self._mode_setting_key(mode_key, "default_status"), default_status)
            if mode_key == "management":
                set_app_setting(conn, "visible_columns", ",".join(visible))
        if mode_key == self.current_mode_key:
            self.filter_vars["status"].set(default_status)
            self._apply_display_columns()
            self.update_idletasks()
            self._fit_tree_columns()
            self.refresh_inventory()
        messagebox.showinfo(APP_NAME, "モード設定を保存しました。")

    def _apply_display_columns(self) -> None:
        visible = self._load_mode_columns(self.current_mode_key)
        self.display_columns = ("selected", "inventory_id", *visible, "actions")
        self.tree.configure(displaycolumns=self.display_columns)
        self.after_idle(self._fit_tree_columns)

    def refresh_price_settings(self) -> None:
        for item in self.price_settings_tree.get_children():
            self.price_settings_tree.delete(item)
        for setting in list_price_search_settings(include_disabled=True):
            self.price_settings_tree.insert(
                "",
                "end",
                iid=str(setting["id"]),
                values=(setting["id"], setting["genre"], setting["site_name"], "有効" if setting["enabled"] else "無効"),
            )

    def load_selected_price_setting(self) -> None:
        selected = self.price_settings_tree.selection()
        if not selected:
            return
        setting_id = int(selected[0])
        setting = next((s for s in list_price_search_settings(include_disabled=True) if s["id"] == setting_id), None)
        if not setting:
            return
        self.editing_price_setting_id = setting_id
        for field in ("genre", "site_name", "url_template", "query_template"):
            self.price_setting_vars[field].set(setting[field])
        self.price_setting_vars["enabled"].set(bool(setting["enabled"]))

    def clear_price_setting_form(self) -> None:
        self.editing_price_setting_id = None
        for field in ("genre", "site_name", "url_template", "query_template"):
            self.price_setting_vars[field].set("")
        self.price_setting_vars["enabled"].set(True)

    def save_price_setting(self) -> None:
        data = {
            "id": self.editing_price_setting_id,
            "genre": self.price_setting_vars["genre"].get(),
            "site_name": self.price_setting_vars["site_name"].get(),
            "url_template": self.price_setting_vars["url_template"].get(),
            "query_template": self.price_setting_vars["query_template"].get(),
            "enabled": self.price_setting_vars["enabled"].get(),
        }
        try:
            with transaction() as conn:
                self.editing_price_setting_id = upsert_price_search_setting(conn, data)
        except ValueError as exc:
            messagebox.showerror(APP_NAME, str(exc))
            return
        self.refresh_price_settings()
        self.refresh_inventory()
        messagebox.showinfo(APP_NAME, "価格検索リンク設定を保存しました。")


def main() -> None:
    app = InventoryApp()
    app.mainloop()


if __name__ == "__main__":
    main()
