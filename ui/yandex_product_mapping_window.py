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

from services.yandex_market import ProductMappingStore

CACHE_PATH = "yandex_sales_cache.json"


class YandexProductMappingWindow(NSObject):
    def init(self):
        self = objc.super(YandexProductMappingWindow, self).init()
        if self is None:
            return None
        rect = NSMakeRect(150, 150, 600, 400)
        style = NSWindowStyleMaskTitled | NSWindowStyleMaskClosable
        self.window = NSWindow.alloc().initWithContentRect_styleMask_backing_defer_(
            rect, style, NSBackingStoreBuffered, False
        )
        self.window.setTitle_("Configure Yandex Market Product Names")
        content = self.window.contentView()

        table_rect = NSMakeRect(0, 40, 600, 360)
        self.table = NSTableView.alloc().initWithFrame_(table_rect)
        for col_id, width in [("item_id", 150), ("yandex_name", 250), ("product", 180)]:
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

        form_rect = NSMakeRect(0, 0, 600, 40)
        form_view = objc.lookUpClass("NSView").alloc().initWithFrame_(form_rect)
        form_view.setAutoresizingMask_(NSViewWidthSizable | NSViewMaxYMargin)
        prod_label = NSTextField.labelWithString_("Product")
        prod_label.setFrame_(NSMakeRect(5, 10, 60, 20))
        form_view.addSubview_(prod_label)
        self.product_field = NSTextField.alloc().initWithFrame_(NSMakeRect(70, 10, 200, 20))
        form_view.addSubview_(self.product_field)
        assign_btn = NSButton.alloc().initWithFrame_(NSMakeRect(280, 5, 80, 30))
        assign_btn.setTitle_("Assign")
        assign_btn.setTarget_(self)
        assign_btn.setAction_("assign:")
        form_view.addSubview_(assign_btn)
        save_btn = NSButton.alloc().initWithFrame_(NSMakeRect(370, 5, 60, 30))
        save_btn.setTitle_("Save")
        save_btn.setTarget_(self)
        save_btn.setAction_("save:")
        form_view.addSubview_(save_btn)
        export_btn = NSButton.alloc().initWithFrame_(NSMakeRect(435, 5, 70, 30))
        export_btn.setTitle_("Export")
        export_btn.setTarget_(self)
        export_btn.setAction_("export:")
        form_view.addSubview_(export_btn)
        import_btn = NSButton.alloc().initWithFrame_(NSMakeRect(510, 5, 70, 30))
        import_btn.setTitle_("Import")
        import_btn.setTarget_(self)
        import_btn.setAction_("import:")
        form_view.addSubview_(import_btn)
        content.addSubview_(form_view)

        self.store = ProductMappingStore()
        self.store.load()
        self.items = []
        self.load_items()
        return self

    def show(self):
        self.window.makeKeyAndOrderFront_(None)

    # ------------------------------------------------------------------ table
    def load_items(self):
        if os.path.exists(CACHE_PATH):
            with open(CACHE_PATH, "r", encoding="utf-8") as f:
                sales = json.load(f)
            seen = {}
            for sale in sales:
                iid = sale.get("item_id")
                name = sale.get("item_name")
                if iid:
                    seen[iid] = name
            self.items = [
                (iid, name, self.store.mappings.get(iid)) for iid, name in seen.items()
            ]
        else:
            self.items = []

    def numberOfRowsInTableView_(self, tableView):
        return len(self.items)

    def tableView_objectValueForTableColumn_row_(self, tableView, column, row):
        col = str(column.identifier())
        item = self.items[row]
        if col == "item_id":
            return item[0]
        if col == "yandex_name":
            return item[1]
        if col == "product":
            return item[2] or ""
        return ""

    def tableViewSelectionDidChange_(self, notification):
        if self.table.numberOfSelectedRows() == 0:
            return
        row = self.table.selectedRow()
        self.product_field.setStringValue_(self.items[row][2] or "")

    # ------------------------------------------------------------------ actions
    def assign_(self, sender):
        if self.table.numberOfSelectedRows() == 0:
            return
        row = self.table.selectedRow()
        prod = self.product_field.stringValue().strip()
        iid, name, _ = self.items[row]
        self.store.mappings[iid] = prod
        self.items[row] = (iid, name, prod)
        self.table.reloadData()

    def save_(self, sender):
        self.store.save()

    def export_(self, sender):
        panel = NSSavePanel.savePanel()
        if panel.runModal() == 0:
            return
        path = panel.URL().path()
        with open(path, "w", encoding="utf-8") as f:
            json.dump(self.store.mappings, f, ensure_ascii=False, indent=2)

    def import_(self, sender):
        panel = NSOpenPanel.openPanel()
        if panel.runModal() == 0:
            return
        path = panel.URLs()[0].path()
        with open(path, "r", encoding="utf-8") as f:
            self.store.mappings = json.load(f)
        self.store.save()
        self.load_items()
        self.table.reloadData()
