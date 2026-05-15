from __future__ import annotations

import tkinter as tk
from datetime import date
from pathlib import Path
from tkinter import filedialog, messagebox, ttk

from .constants import (
    APP_NAME,
    DETAIL_EDIT_FIELDS,
    EDIT_FIELDS,
    FIELD_TO_HEADER,
    LIST_COLUMNS,
    STATUS_VALUES,
)
from .csv_io import export_csv, import_csv, preview_import, write_sample_csv
from .database import ROOT_DIR, get_inventory, initialize_database, insert_inventory, list_inventory, transaction
from .validation import ValidationError, normalize_inventory_payload


FIELD_LABELS = FIELD_TO_HEADER.copy()


class InventoryApp(tk.Tk):
    def __init__(self) -> None:
        super().__init__()
        self.title(APP_NAME)
        self.geometry("1180x760")
        self.minsize(980, 620)
        initialize_database()
        write_sample_csv(ROOT_DIR / "sample_inventory.csv")
        self.status_filter = tk.StringVar(value="販売中")
        self.add_vars: dict[str, tk.StringVar] = {}
        self._build_ui()
        self.refresh_inventory()

    def _build_ui(self) -> None:
        self.columnconfigure(0, weight=1)
        self.rowconfigure(1, weight=1)

        header = ttk.Frame(self, padding=(16, 12))
        header.grid(row=0, column=0, sticky="ew")
        header.columnconfigure(0, weight=1)
        ttk.Label(header, text=APP_NAME, font=("", 18, "bold")).grid(row=0, column=0, sticky="w")
        ttk.Label(header, text="Phase 1: SQLite保存、追加、編集、通常CSV入出力").grid(row=1, column=0, sticky="w")

        notebook = ttk.Notebook(self)
        notebook.grid(row=1, column=0, sticky="nsew", padx=16, pady=(0, 16))
        self.inventory_tab = ttk.Frame(notebook, padding=12)
        self.add_tab = ttk.Frame(notebook, padding=12)
        self.csv_tab = ttk.Frame(notebook, padding=12)
        notebook.add(self.inventory_tab, text="在庫一覧")
        notebook.add(self.add_tab, text="商品追加")
        notebook.add(self.csv_tab, text="CSV")

        self._build_inventory_tab()
        self._build_add_tab()
        self._build_csv_tab()

    def _build_inventory_tab(self) -> None:
        self.inventory_tab.columnconfigure(0, weight=1)
        self.inventory_tab.rowconfigure(1, weight=1)

        controls = ttk.Frame(self.inventory_tab)
        controls.grid(row=0, column=0, sticky="ew", pady=(0, 8))
        ttk.Label(controls, text="表示ステータス").pack(side="left")
        status_box = ttk.Combobox(
            controls,
            textvariable=self.status_filter,
            values=("", *STATUS_VALUES),
            width=14,
            state="readonly",
        )
        status_box.pack(side="left", padx=(8, 12))
        ttk.Button(controls, text="更新", command=self.refresh_inventory).pack(side="left")
        ttk.Button(controls, text="通常編集", command=self.edit_selected).pack(side="left", padx=(12, 0))
        ttk.Button(controls, text="詳細編集", command=self.detail_edit_selected).pack(side="left", padx=(8, 0))

        tree_frame = ttk.Frame(self.inventory_tab)
        tree_frame.grid(row=1, column=0, sticky="nsew")
        tree_frame.columnconfigure(0, weight=1)
        tree_frame.rowconfigure(0, weight=1)
        self.tree = ttk.Treeview(tree_frame, columns=LIST_COLUMNS, show="headings", selectmode="browse")
        for column in LIST_COLUMNS:
            self.tree.heading(column, text=FIELD_LABELS[column])
            self.tree.column(column, width=120, anchor="w")
        self.tree.column("inventory_id", width=100)
        self.tree.column("card_name", width=230)
        self.tree.column("note", width=180)
        self.tree.grid(row=0, column=0, sticky="nsew")
        scrollbar = ttk.Scrollbar(tree_frame, orient="vertical", command=self.tree.yview)
        scrollbar.grid(row=0, column=1, sticky="ns")
        self.tree.configure(yscrollcommand=scrollbar.set)
        self.tree.bind("<Double-1>", lambda _event: self.edit_selected())

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
            else:
                widget = ttk.Entry(form, textvariable=var, width=30)
            widget.grid(row=row, column=col + 1, sticky="ew", padx=(0, 16), pady=4)
        form.columnconfigure(1, weight=1)
        form.columnconfigure(3, weight=1)
        ttk.Button(self.add_tab, text="保存", command=self.add_inventory).grid(row=1, column=0, sticky="w", pady=12)

    def _build_csv_tab(self) -> None:
        self.csv_tab.columnconfigure(0, weight=1)
        text = (
            "通常CSV形式のインポート/エクスポートを行います。\n"
            "インポート時は既存データを上書きせず、新しい在庫IDを採番します。\n"
            "インポート前にはDBバックアップを作成し、登録処理はトランザクションで実行します。"
        )
        ttk.Label(self.csv_tab, text=text, justify="left").grid(row=0, column=0, sticky="w")
        actions = ttk.Frame(self.csv_tab)
        actions.grid(row=1, column=0, sticky="w", pady=14)
        ttk.Button(actions, text="CSVインポート", command=self.import_csv).pack(side="left")
        ttk.Button(actions, text="CSVエクスポート", command=self.export_csv).pack(side="left", padx=(8, 0))
        sample = ROOT_DIR / "sample_inventory.csv"
        ttk.Label(self.csv_tab, text=f"サンプルCSV: {sample}").grid(row=2, column=0, sticky="w", pady=(8, 0))

    def refresh_inventory(self) -> None:
        for item in self.tree.get_children():
            self.tree.delete(item)
        for row in list_inventory(self.status_filter.get()):
            values = ["" if row[column] is None else row[column] for column in LIST_COLUMNS]
            self.tree.insert("", "end", iid=row["inventory_id"], values=values)

    def selected_inventory_id(self) -> str | None:
        selected = self.tree.selection()
        if not selected:
            messagebox.showinfo(APP_NAME, "在庫を1件選択してください。")
            return None
        return selected[0]

    def add_inventory(self) -> None:
        raw = {field: var.get() for field, var in self.add_vars.items()}
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
        self.refresh_inventory()

    def edit_selected(self) -> None:
        inventory_id = self.selected_inventory_id()
        if not inventory_id:
            return
        row = get_inventory(inventory_id)
        if not row:
            messagebox.showerror(APP_NAME, "選択した在庫が見つかりません。")
            return
        self._open_edit_dialog(row, EDIT_FIELDS, title="通常編集")

    def detail_edit_selected(self) -> None:
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
            readonly = (
                f"在庫ID: {row['inventory_id']}    "
                f"登録日: {row['registered_date']}    更新日: {row['updated_date']}"
            )
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
            else:
                widget = ttk.Entry(content, textvariable=var, width=40)
            widget.grid(row=index, column=1, sticky="ew", pady=4)
        buttons = ttk.Frame(content)
        buttons.grid(row=start_row + len(fields), column=0, columnspan=2, sticky="e", pady=(12, 0))
        ttk.Button(buttons, text="キャンセル", command=dialog.destroy).pack(side="right")
        ttk.Button(
            buttons,
            text="保存",
            command=lambda: self._save_edit(dialog, row, vars_by_field),
        ).pack(side="right", padx=(0, 8))
        dialog.wait_window()

    def _save_edit(self, dialog: tk.Toplevel, original_row, vars_by_field: dict[str, tk.StringVar]) -> None:
        raw = {field: original_row[field] for field in FIELD_TO_HEADER if field != "inventory_id"}
        raw.update({field: var.get() for field, var in vars_by_field.items()})
        try:
            payload = normalize_inventory_payload(raw, for_insert=False)
            with transaction() as conn:
                from .database import update_inventory

                update_inventory(conn, original_row["inventory_id"], payload)
        except ValidationError as exc:
            messagebox.showerror(APP_NAME, str(exc), parent=dialog)
            return
        dialog.destroy()
        self.refresh_inventory()

    def import_csv(self) -> None:
        path = filedialog.askopenfilename(
            title="CSVインポート",
            filetypes=(("CSV files", "*.csv"), ("All files", "*.*")),
        )
        if not path:
            return
        try:
            rows, errors = preview_import(path)
        except ValidationError as exc:
            messagebox.showerror(APP_NAME, str(exc))
            return
        if errors:
            sample = "\n".join(errors[:10])
            skip = messagebox.askyesno(
                APP_NAME,
                f"エラーが{len(errors)}件あります。\n\n{sample}\n\nエラー行をスキップして取り込みますか？",
            )
            if not skip:
                return
        elif not messagebox.askyesno(APP_NAME, f"{len(rows)}件を取り込みます。よろしいですか？"):
            return
        try:
            count, _errors = import_csv(path, skip_errors=True)
        except Exception as exc:
            messagebox.showerror(APP_NAME, f"インポートに失敗しました。\n{exc}")
            return
        messagebox.showinfo(APP_NAME, f"{count}件を取り込みました。")
        self.refresh_inventory()

    def export_csv(self) -> None:
        path = filedialog.asksaveasfilename(
            title="CSVエクスポート",
            defaultextension=".csv",
            filetypes=(("CSV files", "*.csv"), ("All files", "*.*")),
        )
        if not path:
            return
        try:
            count = export_csv(path, self.status_filter.get())
        except Exception as exc:
            messagebox.showerror(APP_NAME, f"エクスポートに失敗しました。\n{exc}")
            return
        messagebox.showinfo(APP_NAME, f"{count}件をエクスポートしました。")


def main() -> None:
    app = InventoryApp()
    app.mainloop()


if __name__ == "__main__":
    main()

