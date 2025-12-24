import tkinter as tk
import os
from app import InventoryApp
from utils.logger import setup_logger

BASE_DIR = os.path.dirname(os.path.abspath(__file__))

if __name__ == "__main__":
    setup_logger(BASE_DIR)
    root = tk.Tk()
    InventoryApp(root)
    root.mainloop()
