import tkinter as tk
from tkinter import messagebox
from datetime import datetime
import logging
import os

from services.excel_service import ExcelService
from services.partner_service import PartnerService
from widgets.autocomplete import AutocompleteEntry

# ===== CONFIG =====
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
EXCEL_FILE = os.path.join(BASE_DIR, "data.xlsx")
FONT = ("Segoe UI", 11)


class InventoryApp:
    def __init__(self, root):
        self.root = root
        self.mode_var = tk.StringVar(value="IN")  # IN / OUT
        self.root.title("Nhập liệu kho")
        self.root.geometry("900x650")
        self.root.columnconfigure(1, weight=1)

        # services
        self.excel = ExcelService(EXCEL_FILE, "DATA")
        self.partner_service = PartnerService(EXCEL_FILE)

        # state
        self.editing_row = None
        self._code_checked = None
        self.partners = self.partner_service.get_all()

        # ui
        self.build_ui()
        self.update_code()

    # ================= DATA =================
    def get_in_product_strings(self):
        """Danh sách hàng nhập để autocomplete khi Xuất"""
        wb, ws = self.excel.load_sheet("DATA_IN")
        results = []

        for r in range(2, ws.max_row + 1):
            name = ws.cell(r, 3).value
            date = ws.cell(r, 1).value
            code = ws.cell(r, 2).value

            if name and code:
                results.append(f"{name} | {date} | {code}")

        return results

    # ================= MODE =================
    def get_current_sheet(self):
        return "DATA_IN" if self.mode_var.get() == "IN" else "DATA_OUT"

    def get_code_prefix(self):
        return "NK" if self.mode_var.get() == "IN" else "XK"

    def on_mode_change(self):
        self.editing_row = None
        self._code_checked = None
        self.clear()

        # rebuild ô tên hàng
        self.rebuild_name_field()

        # khóa / mở mã
        if self.mode_var.get() == "OUT":
            self.e_code.config(state="readonly")
        else:
            self.e_code.config(state="normal")

        self.update_code()
        self.root.title("Xuất hàng" if self.mode_var.get() == "OUT" else "Nhập liệu kho")

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

            # 🔥 BẮT SỰ KIỆN CHỌN HÀNG
            self.e_name.bind("<FocusOut>", self.on_out_name_selected)
        else:
            self.e_name = tk.Entry(self.root, font=FONT)

        self.e_name.grid(row=3, column=1, sticky="ew", padx=12, pady=5)


    # ================= LOGIC =================
    def on_out_name_selected(self, event=None):
        if self.mode_var.get() != "OUT":
            return

        value = self.e_name.get().strip()
        if "|" not in value:
            return

        parts = [x.strip() for x in value.split("|")]
        if len(parts) != 3:
            return

        name, date, in_code = parts

        # set lại tên hàng (chỉ tên)
        self.e_name.delete(0, tk.END)
        self.e_name.insert(0, name)

        # set lại mã = mã nhập
        self.e_code.config(state="normal")
        self.e_code.delete(0, tk.END)
        self.e_code.insert(0, in_code)
        self.e_code.config(state="readonly")

    def on_date_change(self, *_):
        self.editing_row = None
        self._code_checked = None
        self.update_code()

    def update_code(self, *_):
        if self.mode_var.get() == "OUT":
            return
        if self.editing_row and self._code_checked == self.e_code.get().strip():
            return

        try:
            d = self.e_date.get().strip()
            datetime.strptime(d, "%Y-%m-%d")

            sheet = self.get_current_sheet()
            prefix = self.get_code_prefix()
            wb, ws = self.excel.load_sheet(sheet)

            nums = []
            date_key = d.replace("-", "")
            for r in range(2, ws.max_row + 1):
                code = ws.cell(r, 2).value
                if isinstance(code, str) and code.startswith(f"{prefix}-{date_key}"):
                    try:
                        nums.append(int(code.split("-")[-1]))
                    except:
                        pass

            next_num = max(nums) + 1 if nums else 1
            new_code = f"{prefix}-{date_key}-{str(next_num).zfill(3)}"

            self.e_code.delete(0, tk.END)
            self.e_code.insert(0, new_code)

        except Exception as e:
            logging.warning(f"Update code error: {e}")

    def on_code_change(self, *_):
        if self.mode_var.get() == "OUT":
            return

        code = self.e_code.get().strip()
        if not code or self._code_checked == code:
            return

        sheet = self.get_current_sheet()
        wb, ws = self.excel.load_sheet(sheet)
        row = self.excel.find_row_by_code(ws, code)

        if row:
            self._code_checked = code
            self.editing_row = row
            self.load_row(ws, row)
    def on_out_name_selected(self, event=None):
        """
        Khi xuất hàng:
        - Ngay lúc chọn tên hàng (focus out)
        - Cập nhật Tên / Ngày / Mã theo lần nhập
        """
        if self.mode_var.get() != "OUT":
            return

        value = self.e_name.get().strip()
        if "|" not in value:
            return

        parts = [x.strip() for x in value.split("|")]
        if len(parts) != 3:
            return

        name, in_date, in_code = parts

        # === TÊN HÀNG: chỉ giữ tên ===
        self.e_name.delete(0, tk.END)
        self.e_name.insert(0, name)

        # === NGÀY: theo ngày nhập ===
        self.e_date.delete(0, tk.END)
        self.e_date.insert(0, in_date)

        # === MÃ: dùng mã nhập ===
        self.e_code.config(state="normal")
        self.e_code.delete(0, tk.END)
        self.e_code.insert(0, in_code)
        self.e_code.config(state="readonly")


    def submit(self):
        try:
            if not self.e_qty.get().strip():
                raise ValueError("Vui lòng nhập SỐ LƯỢNG")

            qty = int(self.e_qty.get())

            # ===== XUẤT =====
            if self.mode_var.get() == "OUT":
                value = self.e_name.get().strip()

                if "|" not in value:
                    raise ValueError("Vui lòng chọn hàng từ danh sách gợi ý")

                parts = [x.strip() for x in value.split("|")]
                if len(parts) != 3:
                    raise ValueError("Dữ liệu hàng hóa không hợp lệ")

                name, date, in_code = parts

                # ✅ Ô TÊN HÀNG: CHỈ GIỮ TÊN
                self.e_name.delete(0, tk.END)
                self.e_name.insert(0, name)

                # # đơn giá (nếu có)
                # price = int(self.e_price.get().replace(",", "")) if self.e_price.get() else 0

                self.e_code.config(state="normal")
                self.e_code.config(state="readonly")

                price = int(self.e_price.get().replace(",", "")) if self.e_price.get() else 0

            # ===== NHẬP =====
            else:
                if not self.e_price.get().strip():
                    raise ValueError("Vui lòng nhập ĐƠN GIÁ")
                price = int(self.e_price.get().replace(",", ""))

            fee = int(self.e_fee.get().replace(",", "")) if self.e_fee.get() else 0
            tax = float(self.e_tax.get()) / 100 if self.e_tax.get() else 0

            sheet = self.get_current_sheet()
            wb, ws = self.excel.load_sheet(sheet)
            row_idx = self.editing_row or self.excel.find_next_row(ws)

            row = [
                self.e_date.get(),
                self.e_code.get(),
                self.e_name.get(),
                qty,
                price,
                self.e_unit.get(),
                tax,
                f"=F{row_idx}*H{row_idx}",
                f"=F{row_idx}*E{row_idx}",
                f"=J{row_idx}+I{row_idx}",
                fee,
                self.e_invoice_date.get(),
                self.e_invoice_no.get(),
                self.e_partner.get(),
            ]

            for c, v in enumerate(row, 1):
                ws.cell(row=row_idx, column=c, value=v)

            wb.save(EXCEL_FILE)
            messagebox.showinfo("Thành công", "Đã lưu dữ liệu")

            self.editing_row = None
            self._code_checked = None
            self.clear()
            self.update_code()

        except Exception as e:
            messagebox.showerror("Lỗi", str(e))
            logging.error(str(e))

    def clear(self):
        for e in (
            self.e_name, self.e_qty, self.e_price, self.e_unit,
            self.e_tax, self.e_fee, self.e_invoice_date,
            self.e_invoice_no, self.e_partner,
        ):
            e.delete(0, tk.END)
