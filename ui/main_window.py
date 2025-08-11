import objc
from Cocoa import (
    NSObject,
    NSApplication,
    NSApp,
    NSWindow,
    NSTabView,
    NSTabViewItem,
    NSMakeRect,
    NSMenu,
    NSMenuItem,
)
from AppKit import (
    NSWindowStyleMaskTitled,
    NSWindowStyleMaskClosable,
    NSWindowStyleMaskResizable,
    NSWindowStyleMaskMiniaturizable,
    NSBackingStoreBuffered,
    NSViewWidthSizable,
    NSViewHeightSizable,
    NSOpenPanel,
    NSSavePanel,
    NSAlert,
)
from ui.resources_page import ResourcesPage
from ui.activities_page import ActivitiesPage
from ui.cost_objects_page import CostObjectsPage
from ui.allocation_page import AllocationPage
from ui.pnl_page import PNLPage
from ui.drivers_page import DriversPage
from ui.graph_page import GraphPage
from ui.produced_amounts_window import ProducedAmountsWindow
from ui.sales_page import SalesPage
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
                app.setActivationPolicy_(AppKit.NSApplicationActivationPolicyRegular)
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
            "Quit", "terminate:", "q"
        )
        app_menu.addItem_(quit_item)
        app_item.setSubmenu_(app_menu)

        file_item = NSMenuItem.alloc().init()
        main_menu.addItem_(file_item)
        file_menu = NSMenu.alloc().initWithTitle_("File")
        import_item = NSMenuItem.alloc().initWithTitle_action_keyEquivalent_(
            "Import...", "importExcel:", ""
        )
        export_item = NSMenuItem.alloc().initWithTitle_action_keyEquivalent_(
            "Export...", "exportExcel:", ""
        )
        prod_item = NSMenuItem.alloc().initWithTitle_action_keyEquivalent_(
            "Configure Produced Amounts", "openProdAmounts:", ""
        )
        file_menu.addItem_(import_item)
        file_menu.addItem_(export_item)
        file_menu.addItem_(prod_item)
        file_item.setSubmenu_(file_menu)

        NSApp().setMainMenu_(main_menu)

        # Контейнер для выпадающего списка и вкладок
        content_view = objc.lookUpClass("NSView").alloc().initWithFrame_(rect)
        content_view.setAutoresizingMask_(NSViewWidthSizable | NSViewHeightSizable)
        self.window.setContentView_(content_view)

        # TabView на всё окно
        self.tab_view = NSTabView.alloc().initWithFrame_(rect)
        self.tab_view.setAutoresizingMask_(NSViewWidthSizable | NSViewHeightSizable)
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

        self.salesPage = SalesPage.alloc().init()
        sales_item = NSTabViewItem.alloc().initWithIdentifier_("sales")
        sales_item.setLabel_("Sales")
        sales_item.setView_(self.salesPage.view)
        self.tab_view.addTabViewItem_(sales_item)

        self.allocationPage = AllocationPage.alloc().init()
        allocation_item = NSTabViewItem.alloc().initWithIdentifier_("allocation")
        allocation_item.setLabel_("Распределения")
        allocation_item.setView_(self.allocationPage.view)
        self.tab_view.addTabViewItem_(allocation_item)

        self.pnlPage = PNLPage.alloc().init()
        pnl_item = NSTabViewItem.alloc().initWithIdentifier_("pnl")
        pnl_item.setLabel_("PNL")
        pnl_item.setView_(self.pnlPage.view)
        self.tab_view.addTabViewItem_(pnl_item)

        self.graphPage = GraphPage.alloc().init()
        graph_item = NSTabViewItem.alloc().initWithIdentifier_("graph")
        graph_item.setLabel_("Граф")
        graph_item.setView_(self.graphPage.view)
        self.tab_view.addTabViewItem_(graph_item)

        # ---------- Set default period ----------
        con = database.get_connection()
        cur = con.cursor()
        cur.execute("SELECT period FROM periods ORDER BY period LIMIT 1")
        row = cur.fetchone()
        con.close()
        if row:
            database.current_period = row[0]

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
            "sales": self.salesPage,
            "allocation": self.allocationPage,
            "pnl": self.pnlPage,
            "graph": self.graphPage,
        }.get(identifier)
        if page_obj and hasattr(page_obj, "refresh"):
            page_obj.refresh()

    # ==================== Import/Export ====================
    def importExcel_(self, sender):
        panel = NSOpenPanel.openPanel()
        panel.setAllowedFileTypes_(["xlsx"])
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
            self.salesPage,
            self.allocationPage,
            self.pnlPage,
            self.graphPage,
        ):
            if hasattr(page, "refresh"):
                page.refresh()
