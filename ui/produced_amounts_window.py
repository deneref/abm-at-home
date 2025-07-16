import objc
from Cocoa import NSObject, NSMakeRect, NSWindow
from AppKit import (
    NSTableView, NSTableColumn, NSScrollView, NSTextField,
    NSButton, NSViewWidthSizable, NSViewHeightSizable,
    NSViewMaxYMargin, NSBackingStoreBuffered, NSWindowStyleMaskTitled,
    NSWindowStyleMaskClosable
)
import database


class ProducedAmountsWindow(NSObject):
    def init(self):
        self = objc.super(ProducedAmountsWindow, self).init()
        if self is None:
            return None
        rect = NSMakeRect(100, 100, 400, 300)
        style = NSWindowStyleMaskTitled | NSWindowStyleMaskClosable
        self.window = NSWindow.alloc().initWithContentRect_styleMask_backing_defer_(
            rect, style, NSBackingStoreBuffered, False
        )
        self.window.setTitle_("Produced Amounts")
        content = self.window.contentView()

        table_rect = NSMakeRect(0, 40, 400, 260)
        self.table = NSTableView.alloc().initWithFrame_(table_rect)
        for col_id, width in [("product", 200), ("amount", 100)]:
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

        form_rect = NSMakeRect(0, 0, 400, 40)
        form_view = objc.lookUpClass("NSView").alloc().initWithFrame_(form_rect)
        form_view.setAutoresizingMask_(NSViewWidthSizable | NSViewMaxYMargin)
        amt_label = NSTextField.labelWithString_("Amount")
        amt_label.setFrame_(NSMakeRect(5, 10, 60, 20))
        form_view.addSubview_(amt_label)
        self.amount_field = NSTextField.alloc().initWithFrame_(NSMakeRect(70, 10, 100, 20))
        form_view.addSubview_(self.amount_field)
        save_btn = NSButton.alloc().initWithFrame_(NSMakeRect(180, 5, 80, 30))
        save_btn.setTitle_("Save")
        save_btn.setTarget_(self)
        save_btn.setAction_("save:")
        form_view.addSubview_(save_btn)
        content.addSubview_(form_view)

        self.refresh()
        return self

    def show(self):
        self.window.makeKeyAndOrderFront_(None)

    # -------- table data source --------
    def numberOfRowsInTableView_(self, tableView):
        return len(self.rows) if hasattr(self, 'rows') else 0

    def tableView_objectValueForTableColumn_row_(self, tableView, tableColumn, row):
        col_id = str(tableColumn.identifier())
        if col_id == "product":
            return self.rows[row][0]
        elif col_id == "amount":
            return str(self.rows[row][1])
        return ""

    def tableViewSelectionDidChange_(self, notification):
        if self.table.numberOfSelectedRows() == 0:
            return
        row = self.table.selectedRow()
        if row < 0 or row >= len(self.rows):
            return
        self.amount_field.setStringValue_(str(self.rows[row][1]))

    # -------- actions --------
    def save_(self, sender):
        if self.table.numberOfSelectedRows() == 0:
            return
        row = self.table.selectedRow()
        product = self.rows[row][0]
        try:
            amt = float(self.amount_field.stringValue())
        except ValueError:
            return
        database.set_produced_amount(product, amt)
        self.refresh()
        if hasattr(self, 'refresh_callback'):
            self.refresh_callback()

    def refresh(self):
        con = database.get_connection()
        cur = con.cursor()
        cur.execute(
            "SELECT p.product, COALESCE(pa.amount, 0)"
            "  FROM (SELECT DISTINCT product FROM cost_objects) p"
            "  LEFT JOIN produced_amounts pa ON pa.product = p.product"
        )
        self.rows = cur.fetchall()
        con.close()
        self.table.reloadData()
        self.amount_field.setStringValue_("")

    def windowWillClose_(self, notification):
        if hasattr(self, 'on_close') and callable(self.on_close):
            self.on_close()
