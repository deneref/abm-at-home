import objc
from Cocoa import NSObject, NSMakeRect
from AppKit import NSView, NSTextField, NSButton, NSScrollView, NSTableView, NSTableColumn, NSAlert
from AppKit import NSViewWidthSizable, NSViewHeightSizable, NSViewMaxYMargin
import database


class ResourcesPage(NSObject):
    def init(self):
        self = objc.super(ResourcesPage, self).init()
        if self is None:
            return None
        content_rect = NSMakeRect(0, 0, 1000, 620)
        self.view = NSView.alloc().initWithFrame_(content_rect)
        self.view.setAutoresizingMask_(
            NSViewWidthSizable | NSViewHeightSizable)
        table_rect = NSMakeRect(0, 30, 1000, 590)
        self.tree = NSTableView.alloc().initWithFrame_(table_rect)
        columns = [("id", 120), ("name", 120),
                   ("cost_total", 120), ("unit", 120)]
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
        scroll_view.setAutoresizingMask_(
            NSViewWidthSizable | NSViewHeightSizable)
        self.view.addSubview_(scroll_view)
        form_rect = NSMakeRect(0, 0, 1000, 30)
        form_view = NSView.alloc().initWithFrame_(form_rect)
        form_view.setAutoresizingMask_(NSViewWidthSizable | NSViewMaxYMargin)
        name_label = NSTextField.labelWithString_("Name")
        name_label.setFrame_(NSMakeRect(5, 5, 50, 20))
        form_view.addSubview_(name_label)
        self.name_field = NSTextField.alloc().initWithFrame_(NSMakeRect(60, 5, 150, 20))
        form_view.addSubview_(self.name_field)
        cost_label = NSTextField.labelWithString_("Cost")
        cost_label.setFrame_(NSMakeRect(220, 5, 40, 20))
        form_view.addSubview_(cost_label)
        self.cost_field = NSTextField.alloc().initWithFrame_(NSMakeRect(265, 5, 100, 20))
        form_view.addSubview_(self.cost_field)
        unit_label = NSTextField.labelWithString_("Unit")
        unit_label.setFrame_(NSMakeRect(380, 5, 30, 20))
        form_view.addSubview_(unit_label)
        self.unit_field = NSTextField.alloc().initWithFrame_(NSMakeRect(415, 5, 100, 20))
        form_view.addSubview_(self.unit_field)
        add_button = NSButton.alloc().initWithFrame_(NSMakeRect(530, 0, 100, 30))
        add_button.setTitle_("Add / Update")
        add_button.setTarget_(self)
        add_button.setAction_("save:")
        form_view.addSubview_(add_button)
        del_button = NSButton.alloc().initWithFrame_(NSMakeRect(640, 0, 80, 30))
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
        elif col_id == "cost_total":
            return str(self.rows[rowIndex][2])
        elif col_id == "unit":
            return self.rows[rowIndex][3]
        return ""

    def tableViewSelectionDidChange_(self, notification):
        if self.tree.numberOfSelectedRows() == 0:
            return
        row = self.tree.selectedRow()
        if row < 0 or row >= len(self.rows):
            return
        selected = self.rows[row]
        self.name_field.setStringValue_(selected[1])
        self.cost_field.setStringValue_(str(selected[2]))
        self.unit_field.setStringValue_(selected[3])

    def save_(self, sender):
        name = self.name_field.stringValue().strip()
        cost_str = self.cost_field.stringValue().strip()
        unit = self.unit_field.stringValue().strip()
        if not name or not unit:
            alert = NSAlert.alloc().init()
            alert.setMessageText_("Error")
            alert.setInformativeText_("Name and unit required")
            alert.addButtonWithTitle_("OK")
            alert.runModal()
            return
        try:
            cost = float(cost_str)
        except ValueError:
            alert = NSAlert.alloc().init()
            alert.setMessageText_("Error")
            alert.setInformativeText_("Invalid cost")
            alert.addButtonWithTitle_("OK")
            alert.runModal()
            return
        con = database.get_connection()
        cur = con.cursor()
        if self.tree.numberOfSelectedRows() > 0:
            # Update existing resource (current period cost updated)
            row = self.tree.selectedRow()
            rid = self.rows[row][0]
            cur.execute(
                "UPDATE resources SET name=?, cost_total=?, unit=? WHERE id=?", (name, cost, unit, rid))
            cur.execute("UPDATE resource_costs SET cost=? WHERE resource_id=? AND period=?",
                        (cost, rid, database.current_period))
        else:
            # Insert new resource and add costs for all periods
            cur.execute(
                "INSERT INTO resources (name, cost_total, unit) VALUES (?, ?, ?)", (name, cost, unit))
            rid = cur.lastrowid
            # Populate resource_costs for all periods
            cur.execute(
                "INSERT INTO resource_costs(resource_id, period, cost) SELECT ?, period, ? FROM periods", (rid, cost))
        con.commit()
        con.close()
        self.refresh()
        self.clear_form()

    def clear_form(self):
        self.name_field.setStringValue_("")
        self.cost_field.setStringValue_("0.0")
        self.unit_field.setStringValue_("")
        self.tree.deselectAll_(None)

    def delete_(self, sender):
        if self.tree.numberOfSelectedRows() == 0:
            return
        row = self.tree.selectedRow()
        rid = self.rows[row][0]
        alert = NSAlert.alloc().init()
        alert.setMessageText_("Confirm")
        alert.setInformativeText_("Delete selected resource?")
        alert.addButtonWithTitle_("Yes")
        alert.addButtonWithTitle_("No")
        response = alert.runModal()
        if response == 1000:
            con = database.get_connection()
            cur = con.cursor()
            cur.execute("DELETE FROM resources WHERE id=?", (rid,))
            con.commit()
            con.close()
            self.refresh()
            self.clear_form()

    def refresh(self):
        con = database.get_connection()
        cur = con.cursor()
        # Fetch resource data for current period costs
        cur.execute("""SELECT r.id, r.name, 
                              COALESCE(rc.cost, r.cost_total) AS cost_val, 
                              r.unit 
                       FROM resources r 
                       LEFT JOIN resource_costs rc 
                         ON r.id = rc.resource_id AND rc.period=?""", (database.current_period,))
        self.rows = cur.fetchall()
        con.close()
        self.tree.reloadData()
