import tkinter as tk
from datetime import datetime

from app_config import FONT
from widgets.autocomplete import AutocompleteEntry


class InventoryUiMixin:
    # ================= UI =================
    def format_money(self, event):
        entry = event.widget
        value = entry.get().replace(",", "")
        if value.isdigit():
            entry.delete(0, tk.END)
            entry.insert(0, f"{int(value):,}")

    def build_ui(self):
        def lbl(text, row):
            tk.Label(self.root, text=text, font=FONT).grid(
                row=row, column=0, sticky="w", padx=12, pady=5
            )

        def ent(row):
            e = tk.Entry(self.root, font=FONT)
            e.grid(row=row, column=1, sticky="ew", padx=12, pady=5)
            return e

        # ===== MODE =====
        lbl("Chế độ", 0)
        tk.Radiobutton(
            self.root, text="Nhập hàng",
            variable=self.mode_var, value="IN",
            command=self.on_mode_change
        ).grid(row=0, column=1, sticky="w", padx=12)

        tk.Radiobutton(
            self.root, text="Xuất hàng",
            variable=self.mode_var, value="OUT",
            command=self.on_mode_change
        ).grid(row=0, column=1, sticky="w", padx=120)

        # ===== FORM =====
        lbl("Ngày", 1)
        self.e_date = ent(1)
        self.e_date.insert(0, datetime.now().strftime("%Y-%m-%d"))
        self.e_date.bind("<KeyRelease>", self.on_date_change)

        lbl("Mã", 2)
        self.e_code = ent(2)
        self.e_code.bind("<FocusOut>", self.on_code_change)
        self.e_code.bind("<Return>", self.on_code_change)

        lbl("Tên hàng", 3)
        self.rebuild_name_field()

        lbl("Số lượng", 4)
        self.e_qty = ent(4)

        lbl("Đơn giá", 5)
        self.e_price = ent(5)
        self.e_price.bind("<KeyRelease>", self.format_money)

        lbl("Đơn vị", 6)
        self.e_unit = ent(6)

        lbl("% Thuế", 7)
        self.e_tax = ent(7)

        lbl("Phí", 8)
        self.e_fee = ent(8)
        self.e_fee.bind("<KeyRelease>", self.format_money)

        lbl("Ngày HĐ", 9)
        self.e_invoice_date = ent(9)

        lbl("Số HĐ", 10)
        self.e_invoice_no = ent(10)

        lbl("Đối tác", 11)
        self.e_partner = AutocompleteEntry(self.partners, self.root, font=FONT)
        self.e_partner.grid(row=11, column=1, sticky="ew", padx=12, pady=5)

        tk.Button(
            self.root,
            text="Hoàn tất",
            font=FONT,
            height=2,
            command=self.submit
        ).grid(row=12, column=0, columnspan=2, sticky="ew", padx=20, pady=25)

    def rebuild_name_field(self):
        if hasattr(self, "e_name"):
            self.e_name.destroy()

        if self.mode_var.get() == "OUT":
            products = self.get_in_product_strings()
            self.e_name = AutocompleteEntry(products, self.root, font=FONT)

            # BẮT SỰ KIỆN CHỌN HÀNG
            self.e_name.bind("<FocusOut>", self.on_out_name_selected)
            self.e_name.bind("<<AutocompleteSelected>>", self.on_out_name_selected)
        else:
            names = self.get_in_product_names()
            self.e_name = AutocompleteEntry(names, self.root, font=FONT)
            self.e_name.bind("<FocusOut>", self.on_in_name_selected)
            self.e_name.bind("<<AutocompleteSelected>>", self.on_in_name_selected)

        self.e_name.grid(row=3, column=1, sticky="ew", padx=12, pady=5)

    def clear(self):
        for e in (
            self.e_name, self.e_qty, self.e_price, self.e_unit,
            self.e_tax, self.e_fee, self.e_invoice_date,
            self.e_invoice_no, self.e_partner,
        ):
            e.delete(0, tk.END)
