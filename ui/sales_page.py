import objc
from Cocoa import NSObject, NSMakeRect
from AppKit import (
    NSView,
    NSTextField,
    NSButton,
    NSScrollView,
    NSTableView,
    NSTableColumn,
    NSAlert,
    NSViewWidthSizable,
    NSViewHeightSizable,
    NSViewMaxYMargin,
)
import database


class SalesPage(NSObject):
    def init(self):
        self = objc.super(SalesPage, self).init()
        if self is None:
            return None
        content_rect = NSMakeRect(0, 0, 1000, 620)
        self.view = NSView.alloc().initWithFrame_(content_rect)
        self.view.setAutoresizingMask_(NSViewWidthSizable | NSViewHeightSizable)
        table_rect = NSMakeRect(0, 30, 1000, 590)
        self.table = NSTableView.alloc().initWithFrame_(table_rect)
        columns = [("date", 150), ("channel", 150), ("product", 150), ("cost_amt", 100)]
        for col_id, width in columns:
            col = NSTableColumn.alloc().initWithIdentifier_(col_id)
            col.setWidth_(width)
            col.headerCell().setStringValue_(col_id)
            self.table.addTableColumn_(col)
        self.table.setDelegate_(self)
        self.table.setDataSource_(self)
        self.table.setAllowsMultipleSelection_(False)
        self.table.setUsesAlternatingRowBackgroundColors_(True)
        scroll_view = NSScrollView.alloc().initWithFrame_(table_rect)
        scroll_view.setDocumentView_(self.table)
        scroll_view.setHasVerticalScroller_(True)
        scroll_view.setAutoresizingMask_(NSViewWidthSizable | NSViewHeightSizable)
        self.view.addSubview_(scroll_view)
        form_rect = NSMakeRect(0, 0, 1000, 30)
        form_view = NSView.alloc().initWithFrame_(form_rect)
        form_view.setAutoresizingMask_(NSViewWidthSizable | NSViewMaxYMargin)
        date_label = NSTextField.labelWithString_("Date")
        date_label.setFrame_(NSMakeRect(5, 5, 40, 20))
        form_view.addSubview_(date_label)
        self.date_field = NSTextField.alloc().initWithFrame_(NSMakeRect(50, 5, 100, 20))
        form_view.addSubview_(self.date_field)
        ch_label = NSTextField.labelWithString_("Channel")
        ch_label.setFrame_(NSMakeRect(160, 5, 60, 20))
        form_view.addSubview_(ch_label)
        self.channel_field = NSTextField.alloc().initWithFrame_(
            NSMakeRect(225, 5, 100, 20)
        )
        form_view.addSubview_(self.channel_field)
        prod_label = NSTextField.labelWithString_("Product")
        prod_label.setFrame_(NSMakeRect(335, 5, 60, 20))
        form_view.addSubview_(prod_label)
        self.product_field = NSTextField.alloc().initWithFrame_(
            NSMakeRect(400, 5, 100, 20)
        )
        form_view.addSubview_(self.product_field)
        cost_label = NSTextField.labelWithString_("Amount")
        cost_label.setFrame_(NSMakeRect(510, 5, 50, 20))
        form_view.addSubview_(cost_label)
        self.cost_field = NSTextField.alloc().initWithFrame_(NSMakeRect(565, 5, 80, 20))
        form_view.addSubview_(self.cost_field)
        add_button = NSButton.alloc().initWithFrame_(NSMakeRect(655, 0, 100, 30))
        add_button.setTitle_("Add / Update")
        add_button.setTarget_(self)
        add_button.setAction_("save:")
        form_view.addSubview_(add_button)
        del_button = NSButton.alloc().initWithFrame_(NSMakeRect(765, 0, 80, 30))
        del_button.setTitle_("Delete")
        del_button.setTarget_(self)
        del_button.setAction_("delete:")
        form_view.addSubview_(del_button)
        self.view.addSubview_(form_view)
        self.refresh()
        return self

    def numberOfRowsInTableView_(self, tableView):
        return len(self.rows) if hasattr(self, "rows") else 0

    def tableView_objectValueForTableColumn_row_(self, tableView, tableColumn, row):
        col_id = str(tableColumn.identifier())
        rec = self.rows[row]
        if col_id == "date":
            return rec[1]
        elif col_id == "channel":
            return rec[2]
        elif col_id == "product":
            return rec[3]
        elif col_id == "cost_amt":
            return str(rec[4])
        return ""

    def tableViewSelectionDidChange_(self, notification):
        if self.table.numberOfSelectedRows() == 0:
            return
        row = self.table.selectedRow()
        if row < 0 or row >= len(self.rows):
            return
        rec = self.rows[row]
        self.date_field.setStringValue_(rec[1])
        self.channel_field.setStringValue_(rec[2])
        self.product_field.setStringValue_(rec[3])
        self.cost_field.setStringValue_(str(rec[4]))

    def save_(self, sender):
        date = self.date_field.stringValue().strip()
        channel = self.channel_field.stringValue().strip()
        product = self.product_field.stringValue().strip()
        cost_str = self.cost_field.stringValue().strip()
        try:
            cost = float(cost_str)
        except ValueError:
            alert = NSAlert.alloc().init()
            alert.setMessageText_("Error")
            alert.setInformativeText_("Invalid amount")
            alert.runModal()
            return
        if not date or not channel or not product:
            alert = NSAlert.alloc().init()
            alert.setMessageText_("Error")
            alert.setInformativeText_("All fields required")
            alert.runModal()
            return
        con = database.get_connection()
        cur = con.cursor()
        if self.table.numberOfSelectedRows() > 0:
            row = self.table.selectedRow()
            sid = self.rows[row][0]
            cur.execute(
                "UPDATE sales SET date=?, channel=?, product=?, cost_amt=? WHERE id=?",
                (date, channel, product, cost, sid),
            )
        else:
            cur.execute(
                "INSERT INTO sales(date, channel, product, cost_amt) VALUES(?, ?, ?, ?)",
                (date, channel, product, cost),
            )
        con.commit()
        con.close()
        self.refresh()
        self.clear_form()

    def delete_(self, sender):
        if self.table.numberOfSelectedRows() == 0:
            return
        row = self.table.selectedRow()
        sid = self.rows[row][0]
        con = database.get_connection()
        con.execute("DELETE FROM sales WHERE id=?", (sid,))
        con.commit()
        con.close()
        self.refresh()
        self.clear_form()

    def clear_form(self):
        self.date_field.setStringValue_("")
        self.channel_field.setStringValue_("")
        self.product_field.setStringValue_("")
        self.cost_field.setStringValue_("")
        self.table.deselectAll_(None)

    def refresh(self):
        self.rows = database.get_sales()
        self.table.reloadData()
