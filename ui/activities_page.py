import objc
from Cocoa import NSObject, NSMakeRect
from AppKit import NSView, NSTextField, NSButton, NSComboBox, NSAlert
from AppKit import NSViewWidthSizable, NSViewHeightSizable, NSViewMaxYMargin
from AppKit import NSSwitchButton  # for checkbox button type
import database


class ActivitiesPage(NSObject):
    def init(self):
        self = objc.super(ActivitiesPage, self).init()
        if self is None:
            return None
        content_rect = NSMakeRect(0, 0, 1000, 620)
        self.view = NSView.alloc().initWithFrame_(content_rect)
        self.view.setAutoresizingMask_(
            NSViewWidthSizable | NSViewHeightSizable)
        table_rect = NSMakeRect(0, 30, 1000, 590)
        self.tree = objc.lookUpClass(
            "NSTableView").alloc().initWithFrame_(table_rect)
        columns = [
            ("id", 120),
            ("name", 150),
            ("driver", 150),
            ("allocated_cost", 120),
            ("driver_rate", 120),
        ]
        for col_id, width in columns:
            col = objc.lookUpClass(
                "NSTableColumn").alloc().initWithIdentifier_(col_id)
            col.setWidth_(width)
            col.headerCell().setStringValue_(col_id)
            self.tree.addTableColumn_(col)
        self.tree.setDelegate_(self)
        self.tree.setDataSource_(self)
        self.tree.setAllowsMultipleSelection_(False)
        self.tree.setUsesAlternatingRowBackgroundColors_(True)
        scroll_view = objc.lookUpClass(
            "NSScrollView").alloc().initWithFrame_(table_rect)
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
        driver_label = NSTextField.labelWithString_("Driver")
        driver_label.setFrame_(NSMakeRect(220, 5, 50, 20))
        form_view.addSubview_(driver_label)
        self.driver_cb = NSComboBox.alloc().initWithFrame_(NSMakeRect(275, 5, 150, 20))
        self.driver_cb.setEditable_(False)
        form_view.addSubview_(self.driver_cb)
        # "Evenly" checkbox for even distribution
        self.evenly_cb = NSButton.alloc().initWithFrame_(NSMakeRect(440, 5, 100, 20))
        self.evenly_cb.setButtonType_(NSSwitchButton)
        self.evenly_cb.setTitle_("Равномерно")
        self.evenly_cb.setState_(0)
        self.evenly_cb.setTarget_(self)
        self.evenly_cb.setAction_("toggleEvenly:")
        form_view.addSubview_(self.evenly_cb)
        add_button = NSButton.alloc().initWithFrame_(NSMakeRect(550, 0, 100, 30))
        add_button.setTitle_("Add / Update")
        add_button.setTarget_(self)
        add_button.setAction_("save:")
        form_view.addSubview_(add_button)
        del_button = NSButton.alloc().initWithFrame_(NSMakeRect(660, 0, 80, 30))
        del_button.setTitle_("Delete")
        del_button.setTarget_(self)
        del_button.setAction_("delete:")
        form_view.addSubview_(del_button)
        self.view.addSubview_(form_view)
        self.refresh()
        return self

    def parse_id(self, value):
        try:
            return int(value.split(":")[0]) if value else None
        except Exception:
            return None

    def parse_activity_name(self, text: str):
        """Split combined name into business process and activity."""
        if "X" not in text:
            return None, None
        bproc, act = text.split("X", 1)
        return bproc.strip(), act.strip()

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
        elif col_id == "allocated_cost":
            return str(self.rows[rowIndex][4])
        elif col_id == "driver_rate":
            val = self.rows[rowIndex][6]
            return f"{val:.2f}" if val is not None else "\u2014"
        return ""

    def tableViewSelectionDidChange_(self, notification):
        # Fill form fields when selecting an activity
        if self.tree.numberOfSelectedRows() == 0:
            return
        row = self.tree.selectedRow()
        if row < 0 or row >= len(self.rows):
            return
        selected = self.rows[row]
        # selected structure: (id, name, driver_name, evenly_flag, allocated_cost, driver_id, driver_rate)
        self.name_field.setStringValue_(selected[1])
        if selected[3] == 1:  # evenly
            self.evenly_cb.setState_(1)
            self.driver_cb.setEnabled_(False)
            self.driver_cb.setStringValue_("")
        else:
            self.evenly_cb.setState_(0)
            self.driver_cb.setEnabled_(True)
            drv_id = selected[5]
            drv_name = selected[2] or ""
            self.driver_cb.setStringValue_(f"{drv_id}: {drv_name}" if drv_id else "")
        # Note: we do not auto-select driver combo item here; just display name text

    def save_(self, sender):
        name = self.name_field.stringValue().strip()
        driver_str = self.driver_cb.stringValue().strip()
        evenly_flag = int(self.evenly_cb.state())
        if not name or (not driver_str and evenly_flag == 0):
            alert = NSAlert.alloc().init()
            alert.setMessageText_("Error")
            alert.setInformativeText_("Fill all fields")
            alert.addButtonWithTitle_("OK")
            alert.runModal()
            return
        bproc, act_name = self.parse_activity_name(name)
        if not bproc or not act_name:
            alert = NSAlert.alloc().init()
            alert.setMessageText_("Error")
            alert.setInformativeText_("Use format 'bp X activity'")
            alert.addButtonWithTitle_("OK")
            alert.runModal()
            return
        # Determine driver_id for given driver name (unless evenly)
        driver_id = None
        if evenly_flag == 0:
            driver_id = self.parse_id(driver_str)
            if driver_id is None:
                # If driver not found (should not happen if selection made)
                alert = NSAlert.alloc().init()
                alert.setMessageText_("Error")
                alert.setInformativeText_("Invalid driver")
                alert.addButtonWithTitle_("OK")
                alert.runModal()
                return
        con = database.get_connection()
        cur = con.cursor()
        if self.tree.numberOfSelectedRows() > 0:
            # Update existing activity
            row = self.tree.selectedRow()
            a_id = self.rows[row][0]
            cur.execute(
                "UPDATE activities SET business_procces=?, activity=?, driver_id=?, evenly=? WHERE id=?",
                (bproc, act_name, driver_id if not evenly_flag else None, evenly_flag, a_id),
            )
        else:
            # Insert new activity
            cur.execute(
                "INSERT INTO activities (business_procces, activity, driver_id, evenly) VALUES (?, ?, ?, ?)",
                (bproc, act_name, driver_id if not evenly_flag else None, evenly_flag),
            )
            a_id = cur.lastrowid
        con.commit()
        con.close()
        database.update_even_allocations(a_id, evenly_flag)
        database.apply_driver_values()
        self.refresh()
        self.clear_form()

    def clear_form(self):
        self.name_field.setStringValue_("")
        self.driver_cb.setStringValue_("")
        self.evenly_cb.setState_(0)
        self.driver_cb.setEnabled_(True)
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

    def toggleEvenly_(self, sender):
        # Toggle behavior for "Evenly" checkbox
        if sender.state():
            # If evenly checked, disable driver selection
            self.driver_cb.setEnabled_(False)
            self.driver_cb.setStringValue_("")
        else:
            self.driver_cb.setEnabled_(True)

    def refresh(self):
        con = database.get_connection()
        cur = con.cursor()
        # Fetch activities with driver names and evenly flag
        cur.execute(
            """SELECT a.id,
                      a.business_procces || ' X ' || a.activity AS name,
                      CASE WHEN a.evenly=1 THEN 'Evenly' ELSE IFNULL(d.name, '') END AS driver_name,
                      a.evenly,
                      a.allocated_cost,
                      a.driver_id
                 FROM activities a
                 LEFT JOIN drivers d ON a.driver_id = d.id"""
        )
        act_rows = cur.fetchall()
        # Calculate total driver values per activity
        cur.execute(
            "SELECT activity_id, SUM(driver_amt) FROM activity_allocations GROUP BY activity_id"
        )
        totals = {row[0]: row[1] for row in cur.fetchall()}
        self.rows = []
        for rid, name, drv, evenly, cost, drv_id in act_rows:
            total = totals.get(rid)
            rate = cost / total if total and total != 0 else None
            self.rows.append((rid, name, drv, evenly, cost, drv_id, rate))
        # Populate driver list for combo box
        cur.execute("SELECT id, name FROM drivers")
        drivers = [f"{d[0]}: {d[1]}" for d in cur.fetchall()]
        con.close()
        self.driver_cb.removeAllItems()
        self.driver_cb.addItemsWithObjectValues_(drivers)
        self.tree.reloadData()
