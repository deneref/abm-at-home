import tkinter as tk
from tkinter import ttk, messagebox
import database


class CostObjectsPage(ttk.Frame):
    def __init__(self, parent):
        super().__init__(parent)
        self.build_ui()
        self.refresh()

    def build_ui(self):
        columns = ("id", "name")
        self.tree = ttk.Treeview(self, columns=columns, show="headings")
        for col in columns:
            self.tree.heading(col, text=col)
            self.tree.column(col, width=150)
        self.tree.pack(fill="both", expand=True)

        form = ttk.Frame(self)
        form.pack(fill="x", pady=5)

        ttk.Label(form, text="Name").grid(row=0, column=0)
        self.name_var = tk.StringVar()
        ttk.Entry(form, textvariable=self.name_var).grid(row=0, column=1)

        ttk.Button(form, text="Add / Update",
                   command=self.save).grid(row=0, column=2, padx=5)
        ttk.Button(form, text="Delete", command=self.delete).grid(
            row=0, column=3)

        self.tree.bind("<<TreeviewSelect>>", self.on_select)

    def refresh(self):
        for item in self.tree.get_children():
            self.tree.delete(item)
        con = database.get_connection()
        cur = con.cursor()
        cur.execute("SELECT id, name FROM cost_objects")
        for row in cur.fetchall():
            self.tree.insert("", "end", values=row)
        con.close()

    def on_select(self, event):
        sel = self.tree.selection()
        if not sel:
            return
        self.name_var.set(self.tree.item(sel[0], "values")[1])

    def save(self):
        name = self.name_var.get().strip()
        if not name:
            messagebox.showerror("Error", "Name required")
            return
        sel = self.tree.selection()
        con = database.get_connection()
        cur = con.cursor()
        if sel:
            co_id = self.tree.item(sel[0], "values")[0]
            cur.execute(
                "UPDATE cost_objects SET name=? WHERE id=?", (name, co_id))
        else:
            cur.execute("INSERT INTO cost_objects(name) VALUES(?)", (name,))
        con.commit()
        con.close()
        self.refresh()
        self.clear_form()

    def clear_form(self):
        self.name_var.set("")
        self.tree.selection_remove(self.tree.selection())

    def delete(self):
        sel = self.tree.selection()
        if not sel:
            return
        co_id = self.tree.item(sel[0], "values")[0]
        if messagebox.askyesno("Confirm", "Delete selected object?"):
            con = database.get_connection()
            con.execute("DELETE FROM cost_objects WHERE id=?", (co_id,))
            con.commit()
            con.close()
            self.refresh()
            self.clear_form()
