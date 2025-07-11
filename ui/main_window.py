import tkinter as tk
from tkinter import ttk
from ui.resources_page import ResourcesPage
from ui.activities_page import ActivitiesPage
from ui.cost_objects_page import CostObjectsPage
from ui.allocation_page import AllocationPage
from ui.analysis_page import AnalysisPage


class MainWindow(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title("ABM Manager")
        self.geometry("1000x650")

        nb = ttk.Notebook(self)
        nb.pack(fill="both", expand=True)

        self.resources_tab = ResourcesPage(nb)
        nb.add(self.resources_tab, text="Ресурсы")

        self.activities_tab = ActivitiesPage(nb)
        nb.add(self.activities_tab, text="Активности")

        self.cost_objects_tab = CostObjectsPage(nb)
        nb.add(self.cost_objects_tab, text="Объекты затрат")

        self.allocation_tab = AllocationPage(nb)
        nb.add(self.allocation_tab, text="Распределения")

        self.analysis_tab = AnalysisPage(nb)
        nb.add(self.analysis_tab, text="Анализ")

        # При переключении вкладок обновляем выпадающие списки в Allocation & Analysis
        nb.bind("<<NotebookTabChanged>>", self.on_tab_change)

    def on_tab_change(self, event):
        tab = event.widget.nametowidget(event.widget.select())
        if hasattr(tab, "refresh"):
            tab.refresh()
