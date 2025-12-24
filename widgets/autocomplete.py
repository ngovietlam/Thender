import tkinter as tk
from utils.matcher import smart_match


class AutocompleteEntry(tk.Entry):
    def __init__(self, values, master=None, max_items=6, **kw):
        super().__init__(master, **kw)
        self.values = values
        self.max_items = max_items
        self.listbox = None
        self.active = -1

        self.bind("<KeyRelease>", self.on_key)
        self.bind("<Down>", self.on_down)
        self.bind("<Up>", self.on_up)
        self.bind("<Return>", self.on_enter)
        master.bind("<Button-1>", self.on_click_outside, add="+")

    def on_key(self, e):
        if e.keysym in ("Up", "Down", "Return", "Escape"):
            return
        key = self.get().strip()
        if not key:
            self.hide()
            return
        matched = [(smart_match(key, v), v) for v in self.values if smart_match(key, v)]
        if not matched:
            self.hide()
            return
        matched.sort(key=lambda x: (-x[0], x[1]))
        self.show([v for _, v in matched[: self.max_items]])

    def show(self, items):
        if not self.listbox:
            self.listbox = tk.Listbox(self.master, font=self["font"])
            self.listbox.bind("<ButtonRelease-1>", self.select)
        self.listbox.delete(0, tk.END)
        for i in items:
            self.listbox.insert(tk.END, i)
        self.active = -1
        self.listbox.place(in_=self, relx=0, rely=1, relwidth=1)

    def hide(self):
        if self.listbox:
            self.listbox.destroy()
            self.listbox = None

    def on_down(self, _):
        if self.listbox and self.active < self.listbox.size() - 1:
            self.active += 1
            self.listbox.selection_set(self.active)
        return "break"

    def on_up(self, _):
        if self.listbox and self.active > 0:
            self.active -= 1
            self.listbox.selection_set(self.active)
        return "break"

    def on_enter(self, _):
        if self.listbox:
            self.pick(self.active)
        return "break"

    def select(self, e):
        self.pick(self.listbox.nearest(e.y))

    def pick(self, idx):
        if idx < 0:
            return
        self.delete(0, tk.END)
        self.insert(0, self.listbox.get(idx))
        self.hide()
        self.event_generate("<<AutocompleteSelected>>")

    def on_click_outside(self, e):
        if self.listbox and not str(e.widget).startswith(str(self.listbox)):
            self.hide()
