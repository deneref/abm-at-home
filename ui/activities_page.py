import objc
from Cocoa import NSObject, NSMakeRect
from AppKit import NSView, NSTextField, NSButton, NSScrollView, NSTableView, NSTableColumn, NSAlert
from AppKit import NSViewWidthSizable, NSViewHeightSizable, NSViewMaxYMargin
import database

class ActivitiesPage(NSObject):
    def init(self):
        self = objc.super(ActivitiesPage, self).init()
        if self is None:
            return None
        content_rect = NSMakeRect(0, 0, 1000, 620)
        self.view = NSView.alloc().initWithFrame_(content_rect)
        self.view.setAutoresizingMask_(NSViewWidthSizable | NSViewHeightSizable)
        table_rect = NSMakeRect(0, 30, 1000, 590)
        self.tree = NSTableView.alloc().initWithFrame_(table_rect)
        columns = [("id", 120), ("name", 150), ("driver", 150)]
        for col_id, width in columns:
            col = NSTableColumn.alloc().initWithIdentifier_(col_id)
            col.setWidth_(width)
            col.headerCell().setStringValue_(col_id)
            self.tree.addTableColumn_(col)
        self.tree.setDelegate_(self)
        self.tree.setDataSource_(self)
        self.tree.setAllowsMultipleSelection_(False)
        self.tree.setUsesAlternatingRowBackgroundColors_(True)
        scroll_view = NSScrollView.alloc().initWithFrame_(table_rect)
        scroll_view.setDocumentView_(self.tree)
        scroll_view.setHasVerticalScroller_(True)
        scroll_view.setAutoresizingMask_(NSViewWidthSizable | NSViewHeightSizable)
        self.view.addSubview_(scroll_view)
        form_rect = NSMakeRect(0, 0, 1000, 30)
        form_view = NSView.alloc().initWithFrame_(form_rect)
        form_view.setAutoresizingMask_(NSViewWidthSizable | NSViewMaxYMargin)
        name_label = NSTextField.labelWithString_("Name")
        name_label.setFrame_(NSMakeRect(5, 5, 50, 20))
        form_view.addSubview_(name_label)
        self.name_field = NSTextField.alloc().initWithFrame_(NSMakeRect(60, 5, 150, 20))
        form_view.addSubview_(self.name_field)
        driver_label = NSTextField.labelWithString_("Driver")
        driver_label.setFrame_(NSMakeRect(220, 5, 50, 20))
        form_view.addSubview_(driver_label)
        self.driver_field = NSTextField.alloc().initWithFrame_(NSMakeRect(275, 5, 150, 20))
        form_view.addSubview_(self.driver_field)
        add_button = NSButton.alloc().initWithFrame_(NSMakeRect(440, 0, 100, 30))
        add_button.setTitle_("Add / Update")
        add_button.setTarget_(self)
        add_button.setAction_("save:")
        form_view.addSubview_(add_button)
        del_button = NSButton.alloc().initWithFrame_(NSMakeRect(550, 0, 80, 30))
        del_button.setTitle_("Delete")
        del_button.setTarget_(self)
        del_button.setAction_("delete:")
        form_view.addSubview_(del_button)
        self.view.addSubview_(form_view)
        self.refresh()
        return self

    def numberOfRowsInTableView_(self, tableView):
        return len(self.rows) if hasattr(self, 'rows') else 0

    def tableView_objectValueForTableColumn_row_(self, tableView, tableColumn, rowIndex):
        col_id = str(tableColumn.identifier())
        if col_id == "id":
            return str(self.rows[rowIndex][0])
        elif col_id == "name":
            return self.rows[rowIndex][1]
        elif col_id == "driver":
            return self.rows[rowIndex][2]
        return ""

    def tableViewSelectionDidChange_(self, notification):
        if self.tree.numberOfSelectedRows() == 0:
            return
        row = self.tree.selectedRow()
        if row < 0 or row >= len(self.rows):
            return
        selected = self.rows[row]
        self.name_field.setStringValue_(selected[1])
        self.driver_field.setStringValue_(selected[2])

    def save_(self, sender):
        name = self.name_field.stringValue().strip()
        driver = self.driver_field.stringValue().strip()
        if not name or not driver:
            alert = NSAlert.alloc().init()
            alert.setMessageText_("Error")
            alert.setInformativeText_("Fill all fields")
            alert.addButtonWithTitle_("OK")
            alert.runModal()
            return
        con = database.get_connection()
        cur = con.cursor()
        if self.tree.numberOfSelectedRows() > 0:
            row = self.tree.selectedRow()
            a_id = self.rows[row][0]
            cur.execute("UPDATE activities SET name=?, driver=? WHERE id=?", (name, driver, a_id))
        else:
            cur.execute("INSERT INTO activities (name, driver) VALUES(?, ?)", (name, driver))
        con.commit()
        con.close()
        self.refresh()
        self.clear_form()

    def clear_form(self):
        self.name_field.setStringValue_("")
        self.driver_field.setStringValue_("")
        self.tree.deselectAll_(None)

    def delete_(self, sender):
        if self.tree.numberOfSelectedRows() == 0:
            return
        row = self.tree.selectedRow()
        a_id = self.rows[row][0]
        alert = NSAlert.alloc().init()
        alert.setMessageText_("Confirm")
        alert.setInformativeText_("Delete selected activity?")
        alert.addButtonWithTitle_("Yes")
        alert.addButtonWithTitle_("No")
        response = alert.runModal()
        if response == 1000:
            con = database.get_connection()
            con.execute("DELETE FROM activities WHERE id=?", (a_id,))
            con.commit()
            con.close()
            self.refresh()
            self.clear_form()

    def refresh(self):
        con = database.get_connection()
        cur = con.cursor()
        cur.execute("SELECT id, name, driver FROM activities")
        self.rows = cur.fetchall()
        con.close()
        self.tree.reloadData()