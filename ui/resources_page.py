import tkinter as tk
from tkinter import ttk, messagebox
import database


class ResourcesPage(ttk.Frame):
    def __init__(self, parent):
        super().__init__(parent)
        self.build_ui()
        self.refresh()

    def build_ui(self):
        columns = ("id", "name", "cost_total", "unit")
        self.tree = ttk.Treeview(self, columns=columns, show="headings")
        for col in columns:
            self.tree.heading(col, text=col)
            self.tree.column(col, width=120)
        self.tree.pack(fill="both", expand=True)

        form = ttk.Frame(self)
        form.pack(fill="x", pady=5)

        ttk.Label(form, text="Name").grid(row=0, column=0)
        self.name_var = tk.StringVar()
        ttk.Entry(form, textvariable=self.name_var).grid(row=0, column=1)

        ttk.Label(form, text="Cost").grid(row=0, column=2)
        self.cost_var = tk.DoubleVar()
        ttk.Entry(form, textvariable=self.cost_var).grid(row=0, column=3)

        ttk.Label(form, text="Unit").grid(row=0, column=4)
        self.unit_var = tk.StringVar()
        ttk.Entry(form, textvariable=self.unit_var).grid(row=0, column=5)

        ttk.Button(form, text="Add / Update",
                   command=self.save).grid(row=0, column=6, padx=5)
        ttk.Button(form, text="Delete", command=self.delete).grid(
            row=0, column=7)

        self.tree.bind("<<TreeviewSelect>>", self.on_select)

    def refresh(self):
        for item in self.tree.get_children():
            self.tree.delete(item)
        con = database.get_connection()
        cur = con.cursor()
        cur.execute("SELECT id, name, cost_total, unit FROM resources")
        for row in cur.fetchall():
            self.tree.insert("", "end", values=row)
        con.close()

    def on_select(self, event):
        sel = self.tree.selection()
        if not sel:
            return
        vals = self.tree.item(sel[0], "values")
        self.name_var.set(vals[1])
        self.cost_var.set(vals[2])
        self.unit_var.set(vals[3])

    def save(self):
        name = self.name_var.get().strip()
        try:
            cost = float(self.cost_var.get())
        except ValueError:
            messagebox.showerror("Error", "Invalid cost")
            return
        unit = self.unit_var.get().strip()
        if not name or not unit:
            messagebox.showerror("Error", "Name and unit required")
            return
        sel = self.tree.selection()
        con = database.get_connection()
        cur = con.cursor()
        if sel:
            rid = self.tree.item(sel[0], "values")[0]
            cur.execute(
                "UPDATE resources SET name=?, cost_total=?, unit=? WHERE id=?", (name, cost, unit, rid))
        else:
            cur.execute(
                "INSERT INTO resources (name, cost_total, unit) VALUES (?,?,?)", (name, cost, unit))
        con.commit()
        con.close()
        self.refresh()
        self.clear_form()

    def clear_form(self):
        self.name_var.set("")
        self.cost_var.set(0.0)
        self.unit_var.set("")
        self.tree.selection_remove(self.tree.selection())

    def delete(self):
        sel = self.tree.selection()
        if not sel:
            return
        rid = self.tree.item(sel[0], "values")[0]
        if messagebox.askyesno("Confirm", "Delete selected resource?"):
            con = database.get_connection()
            con.execute("DELETE FROM resources WHERE id=?", (rid,))
            con.commit()
            con.close()
            self.refresh()
            self.clear_form()
