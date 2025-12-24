import tkinter as tk

from app_config import EXCEL_FILE
from inventory_data import InventoryDataMixin
from inventory_logic import InventoryLogicMixin
from inventory_ui import InventoryUiMixin
from services.excel_service import ExcelService
from services.partner_service import PartnerService


class InventoryApp(InventoryDataMixin, InventoryLogicMixin, InventoryUiMixin):
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
        self.e_code.config(state="readonly")
        self.update_code()
