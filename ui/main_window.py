import objc
from Cocoa import NSObject, NSApplication, NSApp, NSWindow, NSTabView, NSTabViewItem
from Cocoa import NSMakeRect
from AppKit import NSWindowStyleMaskTitled, NSWindowStyleMaskClosable, NSWindowStyleMaskResizable, NSWindowStyleMaskMiniaturizable, NSBackingStoreBuffered
from AppKit import NSViewWidthSizable, NSViewHeightSizable
from ui.resources_page import ResourcesPage
from ui.activities_page import ActivitiesPage
from ui.cost_objects_page import CostObjectsPage
from ui.allocation_page import AllocationPage
from ui.analysis_page import AnalysisPage
from ui.visualization_page import VisualizationPage

class MainWindow(NSObject):
    def init(self):
        self = objc.super(MainWindow, self).init()
        if self is None:
            return None
        # Инициализация приложения Cocoa
        app = NSApplication.sharedApplication()
        try:
            import AppKit
            if hasattr(AppKit, "NSApplicationActivationPolicyRegular"):
                app.setActivationPolicy_(AppKit.NSApplicationActivationPolicyRegular)
        except Exception:
            pass

        # Создание главного окна
        rect = NSMakeRect(0, 0, 1000, 650)
        style_mask = NSWindowStyleMaskTitled | NSWindowStyleMaskClosable | NSWindowStyleMaskResizable | NSWindowStyleMaskMiniaturizable
        self.window = NSWindow.alloc().initWithContentRect_styleMask_backing_defer_(rect, style_mask, NSBackingStoreBuffered, False)
        self.window.setTitle_("ABM Manager")

        # Добавление вкладок (NSTabView) в окно
        self.tab_view = NSTabView.alloc().initWithFrame_(rect)
        self.tab_view.setAutoresizingMask_(NSViewWidthSizable | NSViewHeightSizable)
        self.window.setContentView_(self.tab_view)

        # Создание вкладок и страниц
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

        # Назначение делегатов для обработки событий
        self.window.setDelegate_(self)
        self.tab_view.setDelegate_(self)

        # Показ окна
        self.window.makeKeyAndOrderFront_(None)
        return self

    def run(self):
        # Запуск цикла обработки событий приложения
        app = NSApplication.sharedApplication()
        app.activateIgnoringOtherApps_(True)
        import PyObjCTools.AppHelper as AppHelper
        AppHelper.runEventLoop()

    def windowWillClose_(self, notification):
        # Завершение приложения при закрытии окна
        NSApplication.sharedApplication().terminate_(self)

    def tabView_didSelectTabViewItem_(self, tabview, item):
        # Обновление данных при переключении вкладок
        identifier = str(item.identifier())
        page_obj = None
        if identifier == "resources":
            page_obj = self.resourcesPage
        elif identifier == "activities":
            page_obj = self.activitiesPage
        elif identifier == "cost_objects":
            page_obj = self.costObjectsPage
        elif identifier == "allocation":
            page_obj = self.allocationPage
        elif identifier == "analysis":
            page_obj = self.analysisPage
        elif identifier == "visualization":
            page_obj = self.visualizationPage
        if page_obj and hasattr(page_obj, "refresh"):
            page_obj.refresh()