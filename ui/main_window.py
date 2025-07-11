import objc
from Cocoa import NSObject, NSApplication, NSApp, NSWindow, NSTabView, NSTabViewItem, NSMakeRect
from AppKit import NSWindowStyleMaskTitled, NSWindowStyleMaskClosable, NSWindowStyleMaskResizable, NSWindowStyleMaskMiniaturizable, NSBackingStoreBuffered
from AppKit import NSViewWidthSizable, NSViewHeightSizable, NSViewMinYMargin, NSViewMinXMargin
from ui.resources_page import ResourcesPage
from ui.activities_page import ActivitiesPage
from ui.cost_objects_page import CostObjectsPage
from ui.allocation_page import AllocationPage
from ui.analysis_page import AnalysisPage
from ui.visualization_page import VisualizationPage
from ui.drivers_page import DriversPage
from ui.graph_page import GraphPage
import database


class MainWindow(NSObject):
    def init(self):
        self = objc.super(MainWindow, self).init()
        if self is None:
            return None

        # Initialize Cocoa application
        app = NSApplication.sharedApplication()
        try:
            import AppKit
            if hasattr(AppKit, "NSApplicationActivationPolicyRegular"):
                app.setActivationPolicy_(
                    AppKit.NSApplicationActivationPolicyRegular)
        except Exception:
            pass

        # Create main window
        rect = NSMakeRect(0, 0, 1000, 650)
        style_mask = NSWindowStyleMaskTitled | NSWindowStyleMaskClosable | NSWindowStyleMaskResizable | NSWindowStyleMaskMiniaturizable
        self.window = NSWindow.alloc().initWithContentRect_styleMask_backing_defer_(
            rect, style_mask, NSBackingStoreBuffered, False)
        self.window.setTitle_("ABM Manager")

        # Create a container view for dropdown and tabs
        content_view = objc.lookUpClass("NSView").alloc().initWithFrame_(rect)
        content_view.setAutoresizingMask_(
            NSViewWidthSizable | NSViewHeightSizable)
        self.window.setContentView_(content_view)

        # Create tab view occupying full window
        self.tab_view = NSTabView.alloc().initWithFrame_(rect)
        self.tab_view.setAutoresizingMask_(
            NSViewWidthSizable | NSViewHeightSizable)
        content_view.addSubview_(self.tab_view)

        # Create pages and tabs
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

        # Add dropdown for month selection at top
        period_label = objc.lookUpClass(
            "NSTextField").labelWithString_("Месяц")
        period_label.setFrame_(NSMakeRect(710, 625, 50, 20))
        content_view.addSubview_(period_label)
        self.period_cb = objc.lookUpClass("NSComboBox").alloc(
        ).initWithFrame_(NSMakeRect(770, 620, 150, 25))
        self.period_cb.setEditable_(False)
        # Prepare month list Jan 2025 - Dec 2025 (and Jan 2026)
        months = ["Январь", "Февраль", "Март", "Апрель", "Май", "Июнь",
                  "Июль", "Август", "Сентябрь", "Октябрь", "Ноябрь", "Декабрь"]
        display_months = [f"{m} 2025" for m in months] + ["Январь 2026"]
        from datetime import datetime
        current_year = datetime.now().year
        if current_year == 2025:
            # Limit display to current year (remove Jan 2026)
            display_months = display_months[:-1]
        self.period_codes = [
            f"2025-{str(i).zfill(2)}" for i in range(1, 13)] + ["2026-01"]
        if current_year == 2025:
            self.period_codes = self.period_codes[:-1]
        # Populate combo box and select current month
        self.period_cb.addItemsWithObjectValues_(display_months)
        # Default to current month
        current_code = f"{datetime.now().year}-{str(datetime.now().month).zfill(2)}"
        index = self.period_codes.index(
            current_code) if current_code in self.period_codes else 0
        self.period_cb.selectItemAtIndex_(index)
        # Set current period in global database
        if 0 <= index < len(self.period_codes):
            database.current_period = self.period_codes[index]
        # Set action for period selection change
        self.period_cb.setTarget_(self)
        self.period_cb.setAction_("periodChanged:")
        content_view.addSubview_(self.period_cb)

        # Set delegates
        self.window.setDelegate_(self)
        self.tab_view.setDelegate_(self)

        # Show window
        self.window.makeKeyAndOrderFront_(None)
        return self

    def run(self):
        app = NSApplication.sharedApplication()
        app.activateIgnoringOtherApps_(True)
        import PyObjCTools.AppHelper as AppHelper
        AppHelper.runEventLoop()

    def windowWillClose_(self, notification):
        # Quit application on window close
        NSApplication.sharedApplication().terminate_(self)

    def tabView_didSelectTabViewItem_(self, tabview, item):
        # Refresh data when switching tabs
        identifier = str(item.identifier())
        page_obj = None
        if identifier == "resources":
            page_obj = self.resourcesPage
        elif identifier == "activities":
            page_obj = self.activitiesPage
        elif identifier == "drivers":
            page_obj = self.driversPage
        elif identifier == "cost_objects":
            page_obj = self.costObjectsPage
        elif identifier == "allocation":
            page_obj = self.allocationPage
        elif identifier == "analysis":
            page_obj = self.analysisPage
        elif identifier == "visualization":
            page_obj = self.visualizationPage
        elif identifier == "graph":
            page_obj = self.graphPage
        if page_obj and hasattr(page_obj, "refresh"):
            page_obj.refresh()

    def periodChanged_(self, sender):
        # Handle month selection change
        sel_index = self.period_cb.indexOfSelectedItem()
        if sel_index is None or sel_index < 0:
            return
        # Update current period code and recalc model for that month
        code = self.period_codes[sel_index]
        database.current_period = code
        # Refresh pages that depend on period
        if hasattr(self.resourcesPage, "refresh"):
            self.resourcesPage.refresh()
        if hasattr(self.visualizationPage, "refresh"):
            self.visualizationPage.refresh()
        if hasattr(self.graphPage, "refresh"):
            self.graphPage.refresh()
        if hasattr(self.analysisPage, "refresh"):
            # Note: Analysis page requires pressing "Рассчитать" to update chart; we just refresh list
            self.analysisPage.refresh()
