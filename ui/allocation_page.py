import tkinter as tk
from tkinter import ttk, messagebox
import database


class AllocationPage(ttk.Frame):
    def __init__(self, parent):
        super().__init__(parent)
        self.build_ui()
        self.refresh()

    def build_ui(self):
        ttk.Label(self, text="Распределение ресурсов на активности").pack(
            anchor="w", pady=(5, 0))
        top = ttk.Frame(self)
        top.pack(fill="x")

        self.resource_cb = ttk.Combobox(top, state="readonly", width=25)
        self.activity_cb = ttk.Combobox(top, state="readonly", width=25)
        self.amount_var = tk.DoubleVar()

        ttk.Button(top, text="Add / Update",
                   command=self.save_res_alloc).pack(side="right", padx=5)
        ttk.Entry(top, textvariable=self.amount_var,
                  width=10).pack(side="right")
        ttk.Label(top, text="Количество").pack(side="right")
        self.activity_cb.pack(side="right", padx=5)
        ttk.Label(top, text="Активность").pack(side="right")
        self.resource_cb.pack(side="right", padx=5)
        ttk.Label(top, text="Ресурс").pack(side="right")

        self.tree_res_alloc = ttk.Treeview(self, columns=(
            "resource", "activity", "amount"), show="headings", height=5)
        for col, lbl in [("resource", "Ресурс"), ("activity", "Активность"), ("amount", "Количество")]:
            self.tree_res_alloc.heading(col, text=lbl)
        self.tree_res_alloc.pack(fill="both", expand=True, pady=(0, 10))
        ttk.Button(self, text="Delete", command=self.delete_res_alloc).pack()

        ttk.Separator(self, orient="horizontal").pack(fill="x", pady=10)

        ttk.Label(self, text="Распределение активностей на объекты затрат").pack(
            anchor="w")
        bot = ttk.Frame(self)
        bot.pack(fill="x")

        self.activity_cb2 = ttk.Combobox(bot, state="readonly", width=25)
        self.costobj_cb = ttk.Combobox(bot, state="readonly", width=25)
        self.quantity_var = tk.DoubleVar()

        ttk.Button(bot, text="Add / Update",
                   command=self.save_act_alloc).pack(side="right", padx=5)
        ttk.Entry(bot, textvariable=self.quantity_var,
                  width=10).pack(side="right")
        ttk.Label(bot, text="Объем").pack(side="right")
        self.costobj_cb.pack(side="right", padx=5)
        ttk.Label(bot, text="Объект").pack(side="right")
        self.activity_cb2.pack(side="right", padx=5)
        ttk.Label(bot, text="Активность").pack(side="right")

        self.tree_act_alloc = ttk.Treeview(self, columns=(
            "activity", "cost_object", "quantity"), show="headings", height=5)
        for col, lbl in [("activity", "Активность"), ("cost_object", "Объект"), ("quantity", "Объем")]:
            self.tree_act_alloc.heading(col, text=lbl)
        self.tree_act_alloc.pack(fill="both", expand=True, pady=(0, 10))
        ttk.Button(self, text="Delete", command=self.delete_act_alloc).pack()

    def refresh(self):
        con = database.get_connection()
        cur = con.cursor()
        cur.execute("SELECT id, name FROM resources")
        res = cur.fetchall()
        cur.execute("SELECT id, name FROM activities")
        acts = cur.fetchall()
        cur.execute("SELECT id, name FROM cost_objects")
        objs = cur.fetchall()
        con.close()
        self.resource_cb["values"] = [f"{r[0]}: {r[1]}" for r in res]
        self.activity_cb["values"] = [f"{a[0]}: {a[1]}" for a in acts]
        self.activity_cb2["values"] = [f"{a[0]}: {a[1]}" for a in acts]
        self.costobj_cb["values"] = [f"{o[0]}: {o[1]}" for o in objs]

        for t in (self.tree_res_alloc, self.tree_act_alloc):
            for item in t.get_children():
                t.delete(item)
        con = database.get_connection()
        cur = con.cursor()
        cur.execute(
            """
            SELECT r.name, a.name, ra.amount
            FROM resource_allocations ra
            JOIN resources r ON r.id = ra.resource_id
            JOIN activities a ON a.id = ra.activity_id
            """
        )
        for r_name, a_name, amt in cur.fetchall():
            self.tree_res_alloc.insert("", "end", values=(r_name, a_name, amt))

        cur.execute(
            """
            SELECT a.name, c.name, aa.quantity
            FROM activity_allocations aa
            JOIN activities a ON a.id = aa.activity_id
            JOIN cost_objects c ON c.id = aa.cost_object_id
            """
        )
        for a_name, c_name, qty in cur.fetchall():
            self.tree_act_alloc.insert("", "end", values=(a_name, c_name, qty))
        con.close()

    def parse_id(self, value):
        return int(value.split(":")[0]) if value else None

    def save_res_alloc(self):
        r_id = self.parse_id(self.resource_cb.get())
        a_id = self.parse_id(self.activity_cb.get())
        try:
            amt = float(self.amount_var.get())
        except ValueError:
            messagebox.showerror("Error", "Invalid amount")
            return
        if not r_id or not a_id:
            messagebox.showerror("Error", "Select resource and activity")
            return
        con = database.get_connection()
        con.execute(
            """INSERT INTO resource_allocations(resource_id, activity_id, amount)
               VALUES(?,?,?)
               ON CONFLICT(resource_id, activity_id) DO UPDATE SET amount=excluded.amount""",
            (r_id, a_id, amt),
        )
        con.commit()
        con.close()
        self.refresh()

    def delete_res_alloc(self):
        sel = self.tree_res_alloc.selection()
        if not sel:
            return
        r_name, a_name, _ = self.tree_res_alloc.item(sel[0], "values")
        con = database.get_connection()
        cur = con.cursor()
        cur.execute("SELECT id FROM resources WHERE name=?", (r_name,))
        r_id = cur.fetchone()[0]
        cur.execute("SELECT id FROM activities WHERE name=?", (a_name,))
        a_id = cur.fetchone()[0]
        cur.execute(
            "DELETE FROM resource_allocations WHERE resource_id=? AND activity_id=?", (r_id, a_id))
        con.commit()
        con.close()
        self.refresh()

    def save_act_alloc(self):
        a_id = self.parse_id(self.activity_cb2.get())
        c_id = self.parse_id(self.costobj_cb.get())
        try:
            qty = float(self.quantity_var.get())
        except ValueError:
            messagebox.showerror("Error", "Invalid quantity")
            return
        if not a_id or not c_id:
            messagebox.showerror("Error", "Select activity and object")
            return
        con = database.get_connection()
        con.execute(
            """INSERT INTO activity_allocations(activity_id, cost_object_id, quantity)
               VALUES(?,?,?)
               ON CONFLICT(activity_id, cost_object_id) DO UPDATE SET quantity=excluded.quantity""",
            (a_id, c_id, qty),
        )
        con.commit()
        con.close()
        self.refresh()

    def delete_act_alloc(self):
        sel = self.tree_act_alloc.selection()
        if not sel:
            return
        a_name, c_name, _ = self.tree_act_alloc.item(sel[0], "values")
        con = database.get_connection()
        cur = con.cursor()
        cur.execute("SELECT id FROM activities WHERE name=?", (a_name,))
        a_id = cur.fetchone()[0]
        cur.execute("SELECT id FROM cost_objects WHERE name=?", (c_name,))
        c_id = cur.fetchone()[0]
        cur.execute(
            "DELETE FROM activity_allocations WHERE activity_id=? AND cost_object_id=?",
            (a_id, c_id),
        )
        con.commit()
        con.close()
        self.refresh()
