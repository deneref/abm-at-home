import tkinter as tk
from tkinter import ttk, messagebox
import database
import calculation
from matplotlib.figure import Figure
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg


class AnalysisPage(ttk.Frame):
    def __init__(self, parent):
        super().__init__(parent)
        self.build_ui()

    def build_ui(self):
        top = ttk.Frame(self)
        top.pack(fill="x")
        ttk.Label(top, text="Объект затрат").pack(side="left")
        self.obj_cb = ttk.Combobox(top, state="readonly", width=30)
        self.obj_cb.pack(side="left", padx=5)
        ttk.Button(top, text="Рассчитать",
                   command=self.calculate).pack(side="left")

        self.table = ttk.Treeview(self, columns=(
            "activity", "amount", "perc"), show="headings")
        for col, lbl in [("activity", "Активность"), ("amount", "Затраты"), ("perc", "%")]:
            self.table.heading(col, text=lbl)
            self.table.column(col, width=120)
        self.table.pack(fill="both", expand=True, pady=5)

        self.chart_frame = ttk.Frame(self)
        self.chart_frame.pack(fill="both", expand=True)

        self.refresh()

    def refresh(self):
        con = database.get_connection()
        cur = con.cursor()
        cur.execute("SELECT id, name FROM cost_objects")
        self.objs = cur.fetchall()
        con.close()
        self.obj_cb["values"] = [f"{o[0]}: {o[1]}" for o in self.objs]

    def parse_id(self, value):
        return int(value.split(":")[0]) if value else None

    def calculate(self):
        obj_id = self.parse_id(self.obj_cb.get())
        if not obj_id:
            messagebox.showerror("Error", "Выберите объект")
            return
        con = database.get_connection()
        totals, breakdown = calculation.calculate_costs(con)
        con.close()
        if obj_id not in totals:
            messagebox.showinfo(
                "Нет данных", "Для выбранного объекта нет данных")
            return
        total_val = totals[obj_id]
        # заполняем таблицу
        for item in self.table.get_children():
            self.table.delete(item)
        act_break = breakdown.get(obj_id, {})
        for act_id, amt in act_break.items():
            act_name = self.get_activity_name(act_id)
            perc = amt / total_val * 100 if total_val else 0
            self.table.insert("", "end", values=(
                act_name, f"{amt:.2f}", f"{perc:.1f}%"))

        self.draw_pie_chart(act_break)

    def get_activity_name(self, act_id):
        con = database.get_connection()
        cur = con.cursor()
        cur.execute("SELECT name FROM activities WHERE id=?", (act_id,))
        row = cur.fetchone()
        con.close()
        return row[0] if row else str(act_id)

    def draw_pie_chart(self, data):
        for w in self.chart_frame.winfo_children():
            w.destroy()
        if not data:
            return
        labels = [self.get_activity_name(a) for a in data]
        sizes = [data[a] for a in data]
        fig = Figure(figsize=(4, 4))
        ax = fig.add_subplot(111)
        ax.pie(sizes, labels=labels, autopct="%1.1f%%")
        canvas = FigureCanvasTkAgg(fig, master=self.chart_frame)
        canvas.draw()
        canvas.get_tk_widget().pack(fill="both", expand=True)
