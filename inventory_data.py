class InventoryDataMixin:
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
                if hasattr(date, "strftime"):
                    date_text = date.strftime("%Y-%m-%d")
                else:
                    date_text = str(date) if date is not None else ""
                results.append(f"{name} | {date_text} | {code}")

        return results

    def get_in_product_names(self):
        """Danh sách tên hàng đã nhập để autocomplete khi Nhập"""
        wb, ws = self.excel.load_sheet("DATA_IN")
        results = []

        for r in range(2, ws.max_row + 1):
            name = ws.cell(r, 3).value
            if name:
                results.append(name)

        return results

    # ================= MODE =================
    def get_current_sheet(self):
        return "DATA_IN" if self.mode_var.get() == "IN" else "DATA_OUT"

    def get_code_prefix(self):
        return "NK" if self.mode_var.get() == "IN" else "XK"
