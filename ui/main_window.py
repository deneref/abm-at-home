import objc
from Cocoa import NSObject, NSApplication, NSApp, NSWindow, NSTabView, NSTabViewItem, NSMakeRect, NSMenu, NSMenuItem
from AppKit import (
    NSWindowStyleMaskTitled, NSWindowStyleMaskClosable, NSWindowStyleMaskResizable,
    NSWindowStyleMaskMiniaturizable, NSBackingStoreBuffered,
    NSViewWidthSizable, NSViewHeightSizable,
    NSViewMinYMargin, NSViewMaxXMargin,
    NSOpenPanel, NSSavePanel, NSAlert
)
from ui.resources_page import ResourcesPage
from ui.activities_page import ActivitiesPage
from ui.cost_objects_page import CostObjectsPage
from ui.allocation_page import AllocationPage
from ui.analysis_page import AnalysisPage
from ui.visualization_page import VisualizationPage
from ui.drivers_page import DriversPage
from ui.graph_page import GraphPage
from ui.produced_amounts_window import ProducedAmountsWindow
import database


class MainWindow(NSObject):
    def init(self):
        self = objc.super(MainWindow, self).init()
        if self is None:
            return None

        # Инициализируем Cocoa-приложение
        app = NSApplication.sharedApplication()
        try:
            import AppKit
            if hasattr(AppKit, "NSApplicationActivationPolicyRegular"):
                app.setActivationPolicy_(
                    AppKit.NSApplicationActivationPolicyRegular)
        except Exception:
            pass

        # Создаём главное окно
        rect = NSMakeRect(0, 0, 1200, 750)
        style_mask = (
            NSWindowStyleMaskTitled
            | NSWindowStyleMaskClosable
            | NSWindowStyleMaskResizable
            | NSWindowStyleMaskMiniaturizable
        )
        self.window = NSWindow.alloc().initWithContentRect_styleMask_backing_defer_(
            rect, style_mask, NSBackingStoreBuffered, False
        )
        self.window.setTitle_("ABM Manager")

        # --------- Menu bar ---------
        main_menu = NSMenu.alloc().init()
        app_item = NSMenuItem.alloc().init()
        main_menu.addItem_(app_item)
        app_menu = NSMenu.alloc().initWithTitle_("Application")
        quit_item = NSMenuItem.alloc().initWithTitle_action_keyEquivalent_(
            "Quit", "terminate:", "q")
        app_menu.addItem_(quit_item)
        app_item.setSubmenu_(app_menu)

        file_item = NSMenuItem.alloc().init()
        main_menu.addItem_(file_item)
        file_menu = NSMenu.alloc().initWithTitle_("File")
        import_item = NSMenuItem.alloc().initWithTitle_action_keyEquivalent_(
            "Import...", "importExcel:", "")
        export_item = NSMenuItem.alloc().initWithTitle_action_keyEquivalent_(
            "Export...", "exportExcel:", "")
        prod_item = NSMenuItem.alloc().initWithTitle_action_keyEquivalent_(
            "Configure Produced Amounts", "openProdAmounts:", "")
        file_menu.addItem_(import_item)
        file_menu.addItem_(export_item)
        file_menu.addItem_(prod_item)
        file_item.setSubmenu_(file_menu)

        NSApp().setMainMenu_(main_menu)

        # Контейнер для выпадающего списка и вкладок
        content_view = objc.lookUpClass("NSView").alloc().initWithFrame_(rect)
        content_view.setAutoresizingMask_(
            NSViewWidthSizable | NSViewHeightSizable)
        self.window.setContentView_(content_view)

        # TabView на всё окно
        self.tab_view = NSTabView.alloc().initWithFrame_(rect)
        self.tab_view.setAutoresizingMask_(
            NSViewWidthSizable | NSViewHeightSizable)
        content_view.addSubview_(self.tab_view)

        # ---------- Страницы и вкладки ----------
        self.resourcesPage = ResourcesPage.alloc().init()
        resources_item = NSTabViewItem.alloc().initWithIdentifier_("resources")
        resources_item.setLabel_("Ресурсы")
        resources_item.setView_(self.resourcesPage.view)
        self.tab_view.addTabViewItem_(resources_item)

        self.activitiesPage = ActivitiesPage.alloc().init()
        activities_item = NSTabViewItem.alloc().initWithIdentifier_("activities")
        activities_item.setLabel_("Активности")
        activities_item.setView_(self.activitiesPage.view)
        self.tab_view.addTabViewItem_(activities_item)

        self.driversPage = DriversPage.alloc().init()
        drivers_item = NSTabViewItem.alloc().initWithIdentifier_("drivers")
        drivers_item.setLabel_("Драйверы")
        drivers_item.setView_(self.driversPage.view)
        self.tab_view.addTabViewItem_(drivers_item)

        self.costObjectsPage = CostObjectsPage.alloc().init()
        costobj_item = NSTabViewItem.alloc().initWithIdentifier_("cost_objects")
        costobj_item.setLabel_("Объекты затрат")
        costobj_item.setView_(self.costObjectsPage.view)
        self.tab_view.addTabViewItem_(costobj_item)

        self.allocationPage = AllocationPage.alloc().init()
        allocation_item = NSTabViewItem.alloc().initWithIdentifier_("allocation")
        allocation_item.setLabel_("Распределения")
        allocation_item.setView_(self.allocationPage.view)
        self.tab_view.addTabViewItem_(allocation_item)

        self.analysisPage = AnalysisPage.alloc().init()
        analysis_item = NSTabViewItem.alloc().initWithIdentifier_("analysis")
        analysis_item.setLabel_("Анализ")
        analysis_item.setView_(self.analysisPage.view)
        self.tab_view.addTabViewItem_(analysis_item)

        self.visualizationPage = VisualizationPage.alloc().init()
        viz_item = NSTabViewItem.alloc().initWithIdentifier_("visualization")
        viz_item.setLabel_("Визуализация")
        viz_item.setView_(self.visualizationPage.view)
        self.tab_view.addTabViewItem_(viz_item)

        self.graphPage = GraphPage.alloc().init()
        graph_item = NSTabViewItem.alloc().initWithIdentifier_("graph")
        graph_item.setLabel_("Граф")
        graph_item.setView_(self.graphPage.view)
        self.tab_view.addTabViewItem_(graph_item)

        # ---------- Лейбл и комбобокс «Месяц» в левом-верхнем углу ----------
        # Размеры контролов и отступы
        label_w, label_h = 30, 17
        combo_w, combo_h = 150, 25
        padding_x, padding_top = 10, 5

        # Вычисляем y-координаты относительно левого-верхнего угла окна
        label_y = rect.size.height - label_h - padding_top
        combo_y = rect.size.height - combo_h - padding_top

        # Лейбл
        period_label = objc.lookUpClass(
            "NSTextField").labelWithString_(" ")
        period_label.setFrame_(NSMakeRect(
            padding_x, label_y, label_w, label_h))
        period_label.setAutoresizingMask_(
            NSViewMinYMargin | NSViewMaxXMargin)  # фиксируем левый/верх
        content_view.addSubview_(period_label)

        # Комбо-бокс
        self.period_cb = objc.lookUpClass("NSComboBox").alloc().initWithFrame_(
            NSMakeRect(padding_x + label_w + 8, combo_y, combo_w, combo_h)
        )
        self.period_cb.setEditable_(False)
        self.period_cb.setAutoresizingMask_(
            NSViewMinYMargin | NSViewMaxXMargin)
        content_view.addSubview_(self.period_cb)

        # ---------- Заполняем список месяцев ----------
        months = [
            "Январь", "Февраль", "Март", "Апрель", "Май", "Июнь",
            "Июль", "Август", "Сентябрь", "Октябрь", "Ноябрь", "Декабрь"
        ]
        display_months = [f"{m} 2025" for m in months] + ["Январь 2026"]
        from datetime import datetime

        current_year = datetime.now().year
        if current_year == 2025:
            display_months = display_months[:-1]  # убираем Январь-2026

        self.period_codes = [
            f"2025-{str(i).zfill(2)}" for i in range(1, 13)] + ["2026-01"]
        if current_year == 2025:
            self.period_codes = self.period_codes[:-1]

        self.period_cb.addItemsWithObjectValues_(display_months)

        # Текущий месяц по умолчанию
        current_code = f"{datetime.now().year}-{str(datetime.now().month).zfill(2)}"
        index = self.period_codes.index(
            current_code) if current_code in self.period_codes else 0
        self.period_cb.selectItemAtIndex_(index)

        # Сохраняем выбранный период в «database»
        if 0 <= index < len(self.period_codes):
            database.current_period = self.period_codes[index]

        # Обработчик изменения периода
        self.period_cb.setTarget_(self)
        self.period_cb.setAction_("periodChanged:")

        # ---------- Делегаты ----------
        self.window.setDelegate_(self)
        self.tab_view.setDelegate_(self)

        # ---------- Показываем окно ----------
        self.window.makeKeyAndOrderFront_(None)
        return self

    # ==================== Системные колбэки ====================
    def run(self):
        app = NSApplication.sharedApplication()
        app.activateIgnoringOtherApps_(True)
        import PyObjCTools.AppHelper as AppHelper
        AppHelper.runEventLoop()

    def windowWillClose_(self, notification):
        NSApplication.sharedApplication().terminate_(self)

    def tabView_didSelectTabViewItem_(self, tabview, item):
        identifier = str(item.identifier())
        page_obj = {
            "resources": self.resourcesPage,
            "activities": self.activitiesPage,
            "drivers": self.driversPage,
            "cost_objects": self.costObjectsPage,
            "allocation": self.allocationPage,
            "analysis": self.analysisPage,
            "visualization": self.visualizationPage,
            "graph": self.graphPage,
        }.get(identifier)
        if page_obj and hasattr(page_obj, "refresh"):
            page_obj.refresh()

    # ==================== Смена периода ====================
    def periodChanged_(self, sender):
        sel_index = self.period_cb.indexOfSelectedItem()
        if sel_index < 0:
            return
        database.current_period = self.period_codes[sel_index]

        # Обновляем страницы, зависящие от периода
        for page in (
            self.resourcesPage,
            self.visualizationPage,
            self.graphPage,
            self.analysisPage,
        ):
            if hasattr(page, "refresh"):
                page.refresh()

    # ==================== Import/Export ====================
    def importExcel_(self, sender):
        panel = NSOpenPanel.openPanel()
        panel.setAllowedFileTypes_(
            ["xlsx"])
        if panel.runModal():
            file_path = str(panel.URL().path())
            try:
                database.import_from_excel(file_path)
                self.refresh_all_pages()
            except Exception as exc:
                alert = NSAlert.alloc().init()
                alert.setMessageText_("Error")
                alert.setInformativeText_(str(exc))
                alert.runModal()

    def exportExcel_(self, sender):
        panel = NSSavePanel.savePanel()
        panel.setAllowedFileTypes_(["xlsx"])
        if panel.runModal():
            file_path = str(panel.URL().path())
            try:
                database.export_to_excel(file_path)
            except Exception as exc:
                alert = NSAlert.alloc().init()
                alert.setMessageText_("Error")
                alert.setInformativeText_(str(exc))
                alert.runModal()

    def openProdAmounts_(self, sender):
        if not hasattr(self, "_prodAmtWin") or self._prodAmtWin is None:
            self._prodAmtWin = ProducedAmountsWindow.alloc().init()
            self._prodAmtWin.refresh_callback = self.costObjectsPage.refresh
            self._prodAmtWin.on_close = lambda: setattr(self, "_prodAmtWin", None)
        self._prodAmtWin.show()

    def refresh_all_pages(self):
        for page in (
            self.resourcesPage,
            self.activitiesPage,
            self.driversPage,
            self.costObjectsPage,
            self.allocationPage,
            self.analysisPage,
            self.visualizationPage,
            self.graphPage,
        ):
            if hasattr(page, "refresh"):
                page.refresh()

