import tkinter as tk
from tkinter import ttk, messagebox
import database


class ActivitiesPage(ttk.Frame):
    def __init__(self, parent):
        super().__init__(parent)
        self.build_ui()
        self.refresh()

    def build_ui(self):
        columns = ("id", "name", "driver")
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

        ttk.Label(form, text="Driver").grid(row=0, column=2)
        self.driver_var = tk.StringVar()
        ttk.Entry(form, textvariable=self.driver_var).grid(row=0, column=3)

        ttk.Button(form, text="Add / Update",
                   command=self.save).grid(row=0, column=4, padx=5)
        ttk.Button(form, text="Delete", command=self.delete).grid(
            row=0, column=5)

        self.tree.bind("<<TreeviewSelect>>", self.on_select)

    def refresh(self):
        for item in self.tree.get_children():
            self.tree.delete(item)
        con = database.get_connection()
        cur = con.cursor()
        cur.execute("SELECT id, name, driver FROM activities")
        for row in cur.fetchall():
            self.tree.insert("", "end", values=row)
        con.close()

    def on_select(self, event):
        sel = self.tree.selection()
        if not sel:
            return
        vals = self.tree.item(sel[0], "values")
        self.name_var.set(vals[1])
        self.driver_var.set(vals[2])

    def save(self):
        name = self.name_var.get().strip()
        driver = self.driver_var.get().strip()
        if not name or not driver:
            messagebox.showerror("Error", "Fill all fields")
            return
        sel = self.tree.selection()
        con = database.get_connection()
        cur = con.cursor()
        if sel:
            a_id = self.tree.item(sel[0], "values")[0]
            cur.execute(
                "UPDATE activities SET name=?, driver=? WHERE id=?", (name, driver, a_id))
        else:
            cur.execute(
                "INSERT INTO activities(name, driver) VALUES(?, ?)", (name, driver))
        con.commit()
        con.close()
        self.refresh()
        self.clear_form()

    def clear_form(self):
        self.name_var.set("")
        self.driver_var.set("")
        self.tree.selection_remove(self.tree.selection())

    def delete(self):
        sel = self.tree.selection()
        if not sel:
            return
        a_id = self.tree.item(sel[0], "values")[0]
        if messagebox.askyesno("Confirm", "Delete selected activity?"):
            con = database.get_connection()
            con.execute("DELETE FROM activities WHERE id=?", (a_id,))
            con.commit()
            con.close()
            self.refresh()
            self.clear_form()
