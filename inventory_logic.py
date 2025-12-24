import logging
from datetime import date, datetime
from tkinter import messagebox


class InventoryLogicMixin:
    # ================= MODE =================
    def on_mode_change(self):
        self.editing_row = None
        self._code_checked = None
        self.clear()

        # rebuild ô tên hàng
        self.rebuild_name_field()

        # khóa mã: luôn readonly (tự sinh hoặc theo đơn cũ)
        self.e_code.config(state="readonly")

        self.update_code()
        self.root.title("Xuất hàng" if self.mode_var.get() == "OUT" else "Nhập liệu kho")

    # ================= LOGIC =================
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

        # Tên hàng: chỉ giữ tên
        self.e_name.delete(0, "end")
        self.e_name.insert(0, name)

        # Ngày: theo ngày nhập
        self.e_date.delete(0, "end")
        self.e_date.insert(0, in_date)

        # Mã: dùng mã nhập
        self._set_code_value(in_code)

    def on_in_name_selected(self, event=None):
        if self.mode_var.get() != "IN":
            return

        name = self.e_name.get().strip()
        if not name:
            return

        wb, ws = self.excel.load_sheet("DATA_IN")
        headers = {}
        for c in range(1, ws.max_column + 1):
            key = ws.cell(1, c).value
            if isinstance(key, str):
                headers[key.strip()] = c

        def col(name, fallback=None):
            idx = headers.get(name)
            return idx if idx is not None else fallback

        row = None
        fallback = None
        for r in range(ws.max_row, 1, -1):
            if ws.cell(r, 3).value == name:
                if fallback is None:
                    fallback = r
                qty_val = ws.cell(r, col("Số lượng", 4)).value
                price_val = ws.cell(r, col("Đơn giá", 5)).value
                unit_val = ws.cell(r, col("Đơn vị tính", 6)).value
                if self._is_valid_in_row(qty_val, price_val, unit_val):
                    row = r
                    break

        if not row:
            row = fallback

        if not row:
            return

        in_date = ws.cell(row, col("Ngày", 1)).value
        code = ws.cell(row, col("Mã nhập", 2)).value
        qty = ws.cell(row, col("Số lượng", 4)).value
        price = ws.cell(row, col("Đơn giá", 5)).value
        unit = ws.cell(row, col("Đơn vị tính", 6)).value
        tax = ws.cell(row, col("% Thuế", 7)).value
        fee = ws.cell(row, col("Số tiền phí", 11)).value
        invoice_date = ws.cell(row, col("Ngày hóa đơn", 12)).value
        invoice_no = ws.cell(row, col("Số hóa đơn", 13)).value
        partner = ws.cell(row, col("Đối tác", 14)).value

        qty_num = self._parse_number(qty)
        price_num = self._parse_number(price)
        fee_num = self._parse_number(fee)

        self._set_entry(self.e_date, in_date)
        if code:
            self._set_code_value(str(code))
            self._code_checked = str(code)
            self.editing_row = row
        self._set_entry(self.e_qty, qty_num if qty_num is not None else qty)
        self._set_entry(self.e_price, price_num if price_num is not None else price, money=True)
        self._set_entry(self.e_unit, unit)
        self._set_entry(self.e_tax, self._tax_to_percent(tax))
        self._set_entry(self.e_fee, fee_num if fee_num is not None else fee, money=True)
        self._set_entry(self.e_invoice_date, invoice_date)
        self._set_entry(self.e_invoice_no, invoice_no)
        self._set_entry(self.e_partner, partner)
        self.update_code()

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
                    except Exception:
                        pass

            next_num = max(nums) + 1 if nums else 1
            new_code = f"{prefix}-{date_key}-{str(next_num).zfill(3)}"

            self._set_code_value(new_code)

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

    def submit(self):
        try:
            if not self.e_qty.get().strip():
                raise ValueError("Vui lòng nhập SỐ LƯỢNG")

            qty = int(self.e_qty.get().replace(",", ""))

            # ===== XUẤT =====
            if self.mode_var.get() == "OUT":
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
            row_idx = self.editing_row
            if row_idx is None:
                code = self.e_code.get().strip()
                if code:
                    row_idx = self.excel.find_row_by_code(ws, code)
                    if row_idx:
                        self.editing_row = row_idx
            if row_idx is None:
                row_idx = self.excel.find_next_row(ws)

            row = [
                self.e_date.get(),
                self.e_code.get(),
                self.e_name.get(),
                qty,
                price,
                self.e_unit.get(),
                tax,
                f"=E{row_idx}*G{row_idx}",
                f"=E{row_idx}*D{row_idx}",
                f"=(E{row_idx}+H{row_idx})*D{row_idx}",
                fee,
                self.e_invoice_date.get(),
                self.e_invoice_no.get(),
                self.e_partner.get(),
            ]

            for c, v in enumerate(row, 1):
                ws.cell(row=row_idx, column=c, value=v)

            self._save_workbook(wb, sheet, row_idx, row)
            messagebox.showinfo("Thành công", "Đã lưu dữ liệu")

            self.editing_row = None
            self._code_checked = None
            self.clear()
            self.update_code()

        except Exception as e:
            messagebox.showerror("Lỗi", str(e))
            logging.error(str(e))

    def _set_entry(self, entry, value, money=False):
        entry.delete(0, "end")
        if value is None or value == "":
            return
        if isinstance(value, (datetime, date)):
            entry.insert(0, value.strftime("%Y-%m-%d"))
            return
        if money and isinstance(value, (int, float)):
            if isinstance(value, float) and value.is_integer():
                value = int(value)
            if isinstance(value, float):
                text = f"{value:,.2f}".rstrip("0").rstrip(".")
            else:
                text = f"{value:,}"
            entry.insert(0, text)
            return
        entry.insert(0, str(value))

    def _set_code_value(self, value):
        prev = self.e_code.cget("state")
        if prev == "readonly":
            self.e_code.config(state="normal")
        self.e_code.delete(0, "end")
        self.e_code.insert(0, str(value))
        if prev == "readonly":
            self.e_code.config(state="readonly")

    def load_row(self, ws, row):
        self._code_checked = None
        self.editing_row = row

        in_date = ws.cell(row, 1).value
        code = ws.cell(row, 2).value
        name = ws.cell(row, 3).value
        qty = ws.cell(row, 4).value
        price = ws.cell(row, 5).value
        unit = ws.cell(row, 6).value
        tax = ws.cell(row, 7).value
        fee = ws.cell(row, 11).value
        invoice_date = ws.cell(row, 12).value
        invoice_no = ws.cell(row, 13).value
        partner = ws.cell(row, 14).value

        self._set_entry(self.e_date, in_date)
        if code:
            self._set_code_value(str(code))
            self._code_checked = str(code)
        if name:
            self.e_name.delete(0, "end")
            self.e_name.insert(0, str(name))
        self._set_entry(self.e_qty, qty)
        self._set_entry(self.e_price, self._parse_number(price), money=True)
        self._set_entry(self.e_unit, unit)
        self._set_entry(self.e_tax, self._tax_to_percent(tax))
        self._set_entry(self.e_fee, self._parse_number(fee), money=True)
        self._set_entry(self.e_invoice_date, invoice_date)
        self._set_entry(self.e_invoice_no, invoice_no)
        self._set_entry(self.e_partner, partner)

    def _tax_to_percent(self, value):
        if value is None or value == "":
            return None
        if isinstance(value, (int, float)):
            return value * 100
        text = str(value).strip()
        if text.endswith("%"):
            text = text[:-1].strip()
        try:
            return float(text)
        except ValueError:
            return None

    def _parse_number(self, value):
        if value is None or value == "":
            return None
        if isinstance(value, (int, float)):
            return value
        if isinstance(value, str):
            text = value.replace(",", "").strip()
            if not text:
                return None
            try:
                return float(text)
            except ValueError:
                return None
        return None

    def _is_valid_in_row(self, qty, price, unit):
        qty_num = self._parse_number(qty)
        price_num = self._parse_number(price)
        if qty_num is None or price_num is None:
            return False
        if not isinstance(unit, str) or not unit.strip():
            return False
        return True

    def _save_workbook(self, wb, sheet_name, row_idx, row):
        try:
            wb.save(self.excel.excel_file)
            return
        except PermissionError:
            pass
        except Exception as e:
            messagebox.showerror("Lỗi", f"Không thể lưu file: {e}")
            raise

        if self._save_with_excel_com(sheet_name, row_idx, row):
            return

        messagebox.showerror(
            "Lỗi",
            "Không thể lưu vì file Excel đang mở. "
            "Hãy đóng file rồi thử lại."
        )
        raise PermissionError("Excel file is locked")

    def _save_with_excel_com(self, sheet_name, row_idx, row):
        try:
            import os
            import win32com.client  # type: ignore
        except Exception:
            return False

        file_path = os.path.normcase(os.path.abspath(self.excel.excel_file))

        excel = None
        workbook = None
        opened_by_me = False

        try:
            workbook = win32com.client.GetObject(file_path)
            excel = workbook.Application
        except Exception:
            workbook = None

        if excel is None:
            try:
                excel = win32com.client.GetActiveObject("Excel.Application")
            except Exception:
                excel = win32com.client.Dispatch("Excel.Application")

        excel.DisplayAlerts = False
        try:
            excel.Calculation = -4105  # xlCalculationAutomatic
        except Exception:
            pass

        try:
            if workbook is None:
                for wb in excel.Workbooks:
                    if os.path.normcase(os.path.abspath(wb.FullName)) == file_path:
                        workbook = wb
                        break

            if workbook is None:
                workbook = excel.Workbooks.Open(file_path)
                opened_by_me = True

            if workbook.ReadOnly:
                return False

            sheet = workbook.Worksheets(sheet_name)
            for i, value in enumerate(row, 1):
                sheet.Cells(row_idx, i).Value = value
            try:
                excel.CalculateFull()
            except Exception:
                pass
            workbook.Save()
            return True
        except Exception:
            return False
        finally:
            try:
                if opened_by_me and workbook is not None:
                    workbook.Close(SaveChanges=True)
            except Exception:
                pass
