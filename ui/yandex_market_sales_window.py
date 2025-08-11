import json
import os
import objc
from Cocoa import NSObject, NSMakeRect, NSWindow, NSAlert, NSOpenPanel, NSSavePanel, NSTextField, NSButton, NSTableView, NSTableColumn, NSScrollView
from AppKit import (
    NSWindowStyleMaskTitled,
    NSWindowStyleMaskClosable,
    NSBackingStoreBuffered,
    NSViewWidthSizable,
    NSViewHeightSizable,
    NSViewMaxYMargin,
)

from services.yandex_market import YandexMarketClient, ProductMappingStore, ABMImporter
import database

CONFIG_PATH = "yandex_market_config.json"
CACHE_PATH = "yandex_sales_cache.json"


class YandexMarketSalesWindow(NSObject):
    def init(self):
        self = objc.super(YandexMarketSalesWindow, self).init()
        if self is None:
            return None
        rect = NSMakeRect(150, 150, 800, 500)
        style = NSWindowStyleMaskTitled | NSWindowStyleMaskClosable
        self.window = NSWindow.alloc().initWithContentRect_styleMask_backing_defer_(
            rect, style, NSBackingStoreBuffered, False
        )
        self.window.setTitle_("Yandex Market Sales")
        content = self.window.contentView()

        table_rect = NSMakeRect(0, 60, 800, 440)
        self.table = NSTableView.alloc().initWithFrame_(table_rect)
        cols = [
            ("order_id", 100),
            ("order_date", 120),
            ("item_name", 200),
            ("product", 150),
            ("quantity", 70),
            ("price", 80),
        ]
        for col_id, width in cols:
            col = NSTableColumn.alloc().initWithIdentifier_(col_id)
            col.setWidth_(width)
            col.headerCell().setStringValue_(col_id)
            self.table.addTableColumn_(col)
        self.table.setDelegate_(self)
        self.table.setDataSource_(self)
        self.table.setAllowsMultipleSelection_(False)
        self.table.setUsesAlternatingRowBackgroundColors_(True)
        scroll = NSScrollView.alloc().initWithFrame_(table_rect)
        scroll.setDocumentView_(self.table)
        scroll.setHasVerticalScroller_(True)
        scroll.setAutoresizingMask_(NSViewWidthSizable | NSViewHeightSizable)
        content.addSubview_(scroll)

        form_rect = NSMakeRect(0, 0, 800, 60)
        form_view = objc.lookUpClass("NSView").alloc().initWithFrame_(form_rect)
        form_view.setAutoresizingMask_(NSViewWidthSizable | NSViewMaxYMargin)
        from_label = NSTextField.labelWithString_("From")
        from_label.setFrame_(NSMakeRect(5, 30, 40, 20))
        form_view.addSubview_(from_label)
        self.from_field = NSTextField.alloc().initWithFrame_(NSMakeRect(50, 30, 100, 20))
        form_view.addSubview_(self.from_field)
        to_label = NSTextField.labelWithString_("To")
        to_label.setFrame_(NSMakeRect(155, 30, 40, 20))
        form_view.addSubview_(to_label)
        self.to_field = NSTextField.alloc().initWithFrame_(NSMakeRect(190, 30, 100, 20))
        form_view.addSubview_(self.to_field)

        load_btn = NSButton.alloc().initWithFrame_(NSMakeRect(300, 25, 120, 30))
        load_btn.setTitle_("Load data from API")
        load_btn.setTarget_(self)
        load_btn.setAction_("load:")
        form_view.addSubview_(load_btn)

        reapply_btn = NSButton.alloc().initWithFrame_(NSMakeRect(430, 25, 100, 30))
        reapply_btn.setTitle_("Re-apply")
        reapply_btn.setTarget_(self)
        reapply_btn.setAction_("reapply:")
        form_view.addSubview_(reapply_btn)

        send_btn = NSButton.alloc().initWithFrame_(NSMakeRect(540, 25, 100, 30))
        send_btn.setTitle_("Send to ABM")
        send_btn.setTarget_(self)
        send_btn.setAction_("send:")
        form_view.addSubview_(send_btn)

        export_btn = NSButton.alloc().initWithFrame_(NSMakeRect(650, 25, 70, 30))
        export_btn.setTitle_("Export")
        export_btn.setTarget_(self)
        export_btn.setAction_("export:")
        form_view.addSubview_(export_btn)

        import_btn = NSButton.alloc().initWithFrame_(NSMakeRect(725, 25, 70, 30))
        import_btn.setTitle_("Import")
        import_btn.setTarget_(self)
        import_btn.setAction_("import:")
        form_view.addSubview_(import_btn)
        content.addSubview_(form_view)

        self.mapping_store = ProductMappingStore()
        self.mapping_store.load()
        self.raw_sales = []
        self.sales = []
        self.load_cache()
        return self

    def show(self):
        self.window.makeKeyAndOrderFront_(None)

    # ------------------------------------------------------------------ helpers
    def load_cache(self):
        if os.path.exists(CACHE_PATH):
            with open(CACHE_PATH, "r", encoding="utf-8") as f:
                self.raw_sales = json.load(f)
            self.sales = self.mapping_store.apply(self.raw_sales)
        else:
            self.raw_sales = []
            self.sales = []

    def current_config(self):
        if os.path.exists(CONFIG_PATH):
            with open(CONFIG_PATH, "r", encoding="utf-8") as f:
                return json.load(f)
        return {}

    # ------------------------------------------------------------------ table
    def numberOfRowsInTableView_(self, tableView):
        return len(self.sales)

    def tableView_objectValueForTableColumn_row_(self, tableView, column, row):
        col = str(column.identifier())
        rec = self.sales[row]
        if col == "order_id":
            return rec.get("order_id")
        if col == "order_date":
            return rec.get("order_date")
        if col == "item_name":
            return rec.get("item_name")
        if col == "product":
            return rec.get("product", "")
        if col == "quantity":
            return str(rec.get("quantity", ""))
        if col == "price":
            return str(rec.get("price", ""))
        return ""

    # ------------------------------------------------------------------ actions
    def load_(self, sender):
        cfg = self.current_config()
        date_from = self.from_field.stringValue() or cfg.get("date_from", "")
        date_to = self.to_field.stringValue() or cfg.get("date_to", "")
        client = YandexMarketClient()
        try:
            sales = client.fetch_sales(cfg, date_from, date_to)
            self.raw_sales = sales
            with open(CACHE_PATH, "w", encoding="utf-8") as f:
                json.dump(self.raw_sales, f, ensure_ascii=False, indent=2)
            self.sales = self.mapping_store.apply(self.raw_sales)
            self.table.reloadData()
        except Exception as exc:  # pragma: no cover
            alert = NSAlert.alloc().init()
            alert.setMessageText_("Error")
            alert.setInformativeText_(str(exc))
            alert.runModal()

    def reapply_(self, sender):
        self.sales = self.mapping_store.apply(self.raw_sales)
        self.table.reloadData()

    def send_(self, sender):
        mapped = [s for s in self.sales if s.get("product")]
        unmapped = len(self.sales) - len(mapped)
        if unmapped:
            alert = NSAlert.alloc().init()
            alert.setMessageText_("Warning")
            alert.setInformativeText_(
                f"There are {unmapped} unmapped items. They will be skipped."
            )
            alert.runModal()
        importer = ABMImporter(database)
        report = importer.upsert_sales(mapped)
        alert = NSAlert.alloc().init()
        alert.setMessageText_("Done")
        alert.setInformativeText_(f"Inserted {report['inserted']} records")
        alert.runModal()

    def export_(self, sender):
        panel = NSSavePanel.savePanel()
        if panel.runModal() == 0:
            return
        path = panel.URL().path()
        with open(path, "w", encoding="utf-8") as f:
            json.dump(self.raw_sales, f, ensure_ascii=False, indent=2)

    def import_(self, sender):
        panel = NSOpenPanel.openPanel()
        if panel.runModal() == 0:
            return
        path = panel.URLs()[0].path()
        with open(path, "r", encoding="utf-8") as f:
            self.raw_sales = json.load(f)
        with open(CACHE_PATH, "w", encoding="utf-8") as f:
            json.dump(self.raw_sales, f, ensure_ascii=False, indent=2)
        self.sales = self.mapping_store.apply(self.raw_sales)
        self.table.reloadData()
