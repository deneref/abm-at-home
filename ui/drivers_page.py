import objc
from Cocoa import NSObject, NSMakeRect
from AppKit import NSView, NSTextField, NSButton, NSScrollView, NSTableView, NSTableColumn, NSAlert
from AppKit import NSViewWidthSizable, NSViewHeightSizable, NSViewMinYMargin, NSViewMaxYMargin
import database


class DriversPage(NSObject):
    def init(self):
        self = objc.super(DriversPage, self).init()
        if self is None:
            return None
        # Container for drivers page
        content_rect = NSMakeRect(0, 0, 1000, 620)
        self.view = NSView.alloc().initWithFrame_(content_rect)
        self.view.setAutoresizingMask_(
            NSViewWidthSizable | NSViewHeightSizable)
        # First section (Drivers list)
        first_section_rect = NSMakeRect(0, 310, 1000, 310)
        first_section = NSView.alloc().initWithFrame_(first_section_rect)
        first_section.setAutoresizingMask_(
            NSViewWidthSizable | NSViewMinYMargin)
        # Table of drivers
        table_rect = NSMakeRect(0, 30, 1000, 280)
        self.driver_table = NSTableView.alloc().initWithFrame_(table_rect)
        for col_id, width in [("id", 120), ("name", 200)]:
            col = NSTableColumn.alloc().initWithIdentifier_(col_id)
            col.setWidth_(width)
            col.headerCell().setStringValue_(col_id)
            self.driver_table.addTableColumn_(col)
        self.driver_table.setDelegate_(self)
        self.driver_table.setDataSource_(self)
        self.driver_table.setAllowsMultipleSelection_(False)
        self.driver_table.setUsesAlternatingRowBackgroundColors_(True)
        scroll_view = NSScrollView.alloc().initWithFrame_(table_rect)
        scroll_view.setDocumentView_(self.driver_table)
        scroll_view.setHasVerticalScroller_(True)
        scroll_view.setAutoresizingMask_(
            NSViewWidthSizable | NSViewHeightSizable)
        first_section.addSubview_(scroll_view)
        # Form for adding/updating drivers
        form_rect = NSMakeRect(0, 0, 1000, 30)
        form_view = NSView.alloc().initWithFrame_(form_rect)
        form_view.setAutoresizingMask_(NSViewWidthSizable | NSViewMaxYMargin)
        name_label = NSTextField.labelWithString_("Name")
        name_label.setFrame_(NSMakeRect(5, 5, 50, 20))
        form_view.addSubview_(name_label)
        self.name_field = NSTextField.alloc().initWithFrame_(NSMakeRect(60, 5, 150, 20))
        form_view.addSubview_(self.name_field)
        add_button = NSButton.alloc().initWithFrame_(NSMakeRect(220, 0, 100, 30))
        add_button.setTitle_("Add / Update")
        add_button.setTarget_(self)
        add_button.setAction_("saveDriver:")
        form_view.addSubview_(add_button)
        del_button = NSButton.alloc().initWithFrame_(NSMakeRect(330, 0, 80, 30))
        del_button.setTitle_("Delete")
        del_button.setTarget_(self)
        del_button.setAction_("deleteDriver:")
        form_view.addSubview_(del_button)
        first_section.addSubview_(form_view)
        # Second section (Driver values list)
        second_section_rect = NSMakeRect(0, 0, 1000, 310)
        second_section = NSView.alloc().initWithFrame_(second_section_rect)
        second_section.setAutoresizingMask_(
            NSViewWidthSizable | NSViewMaxYMargin)
        # Label for values section
        self.values_label = NSTextField.labelWithString_("Значения драйвера:")
        self.values_label.setFrame_(NSMakeRect(5, 370, 400, 20))
        second_section.addSubview_(self.values_label)
        # Table of driver values
        table2_rect = NSMakeRect(0, 30, 1000, 335)
        self.value_table = NSTableView.alloc().initWithFrame_(table2_rect)
        for col_id, width in [("id", 120), ("product", 300), ("value", 100)]:
            col = NSTableColumn.alloc().initWithIdentifier_(col_id)
            col.setWidth_(width)
            col.headerCell().setStringValue_(col_id)
            self.value_table.addTableColumn_(col)
        self.value_table.setDelegate_(self)
        self.value_table.setDataSource_(self)
        self.value_table.setAllowsMultipleSelection_(False)
        self.value_table.setUsesAlternatingRowBackgroundColors_(True)
        scroll_view2 = NSScrollView.alloc().initWithFrame_(table2_rect)
        scroll_view2.setDocumentView_(self.value_table)
        scroll_view2.setHasVerticalScroller_(True)
        scroll_view2.setAutoresizingMask_(
            NSViewWidthSizable | NSViewHeightSizable)
        second_section.addSubview_(scroll_view2)
        # Form for adding/updating driver values
        form2_rect = NSMakeRect(0, 0, 1000, 30)
        form2_view = NSView.alloc().initWithFrame_(form2_rect)
        form2_view.setAutoresizingMask_(NSViewWidthSizable | NSViewMaxYMargin)
        desc_label = NSTextField.labelWithString_("Cost Object")
        desc_label.setFrame_(NSMakeRect(5, 5, 80, 20))
        form2_view.addSubview_(desc_label)
        self.desc_field = NSTextField.alloc().initWithFrame_(NSMakeRect(90, 5, 150, 20))
        form2_view.addSubview_(self.desc_field)
        val_label = NSTextField.labelWithString_("Value")
        val_label.setFrame_(NSMakeRect(250, 5, 40, 20))
        form2_view.addSubview_(val_label)
        self.val_field = NSTextField.alloc().initWithFrame_(NSMakeRect(295, 5, 100, 20))
        form2_view.addSubview_(self.val_field)
        add_val_button = NSButton.alloc().initWithFrame_(NSMakeRect(410, 0, 100, 30))
        add_val_button.setTitle_("Add / Update")
        add_val_button.setTarget_(self)
        add_val_button.setAction_("saveValue:")
        form2_view.addSubview_(add_val_button)
        del_val_button = NSButton.alloc().initWithFrame_(NSMakeRect(520, 0, 80, 30))
        del_val_button.setTitle_("Delete")
        del_val_button.setTarget_(self)
        del_val_button.setAction_("deleteValue:")
        form2_view.addSubview_(del_val_button)
        second_section.addSubview_(form2_view)
        # Add both sections to page
        self.view.addSubview_(first_section)
        self.view.addSubview_(second_section)
        # Load initial data
        self.refresh()
        return self

    def numberOfRowsInTableView_(self, tableView):
        if tableView == self.driver_table:
            return len(self.driver_rows) if hasattr(self, 'driver_rows') else 0
        elif tableView == self.value_table:
            return len(self.value_rows) if hasattr(self, 'value_rows') else 0
        return 0

    def tableView_objectValueForTableColumn_row_(self, tableView, tableColumn, rowIndex):
        col_id = str(tableColumn.identifier())
        if tableView == self.driver_table:
            if col_id == "id":
                return str(self.driver_rows[rowIndex][0])
            elif col_id == "name":
                return self.driver_rows[rowIndex][1]
        elif tableView == self.value_table:
            if col_id == "id":
                return str(self.value_rows[rowIndex][0])
            elif col_id == "product":
                return self.value_rows[rowIndex][1]
            elif col_id == "value":
                return str(self.value_rows[rowIndex][2])
        return ""

    def tableViewSelectionDidChange_(self, notification):
        tableView = notification.object()
        if tableView == self.driver_table:
            if self.driver_table.numberOfSelectedRows() == 0:
                # No driver selected: clear values list
                self.current_driver_id = None
                self.values_label.setStringValue_("Значения драйвера:")
                self.value_rows = []
                self.value_table.reloadData()
                self.clear_value_form()
                return
            row = self.driver_table.selectedRow()
            if row < 0 or row >= len(self.driver_rows):
                return
            selected = self.driver_rows[row]
            d_id = selected[0]
            d_name = selected[1]
            self.current_driver_id = d_id
            # Update form fields
            self.name_field.setStringValue_(d_name)
            # Update values section title
            self.values_label.setStringValue_(f"Значения драйвера: {d_name}")
            # Load driver values for this driver
            con = database.get_connection()
            cur = con.cursor()
            cur.execute(
                "SELECT id, product, value FROM driver_values WHERE driver_id=?", (d_id,))
            self.value_rows = cur.fetchall()
            con.close()
            self.value_table.reloadData()
            self.clear_value_form()
        elif tableView == self.value_table:
            if self.value_table.numberOfSelectedRows() == 0:
                return
            row = self.value_table.selectedRow()
            if row < 0 or row >= len(self.value_rows):
                return
            selected = self.value_rows[row]
            # selected = (id, product, value)
            self.desc_field.setStringValue_(selected[1])
            self.val_field.setStringValue_(str(selected[2]))

    def saveDriver_(self, sender):
        name = self.name_field.stringValue().strip()
        if not name:
            alert = NSAlert.alloc().init()
            alert.setMessageText_("Error")
            alert.setInformativeText_("Name required")
            alert.addButtonWithTitle_("OK")
            alert.runModal()
            return
        con = database.get_connection()
        cur = con.cursor()
        if self.driver_table.numberOfSelectedRows() > 0:
            # Update existing driver
            row = self.driver_table.selectedRow()
            d_id = self.driver_rows[row][0]
            cur.execute("UPDATE drivers SET name=? WHERE id=?", (name, d_id))
        else:
            # Insert new driver
            cur.execute("INSERT INTO drivers(name) VALUES(?)", (name,))
        try:
            con.commit()
        except Exception as e:
            con.rollback()
            con.close()
            alert = NSAlert.alloc().init()
            alert.setMessageText_("Error")
            alert.setInformativeText_(f"Failed to save driver: {e}")
            alert.addButtonWithTitle_("OK")
            alert.runModal()
            return
        con.close()
        self.refresh()
        self.clear_driver_form()

    def deleteDriver_(self, sender):
        if self.driver_table.numberOfSelectedRows() == 0:
            return
        row = self.driver_table.selectedRow()
        d_id = self.driver_rows[row][0]
        alert = NSAlert.alloc().init()
        alert.setMessageText_("Confirm")
        alert.setInformativeText_("Delete selected driver?")
        alert.addButtonWithTitle_("Yes")
        alert.addButtonWithTitle_("No")
        response = alert.runModal()
        if response != 1000:
            return
        con = database.get_connection()
        cur = con.cursor()
        # Check if any activities use this driver
        cur.execute(
            "SELECT COUNT(*) FROM activities WHERE driver_id=?", (d_id,))
        count = cur.fetchone()[0]
        if count > 0:
            con.close()
            alert = NSAlert.alloc().init()
            alert.setMessageText_("Error")
            alert.setInformativeText_("Cannot delete: driver is in use")
            alert.addButtonWithTitle_("OK")
            alert.runModal()
            return
        cur.execute("DELETE FROM drivers WHERE id=?", (d_id,))
        con.commit()
        con.close()
        self.refresh()
        self.clear_driver_form()

    def saveValue_(self, sender):
        if not hasattr(self, "current_driver_id") or self.current_driver_id is None:
            alert = NSAlert.alloc().init()
            alert.setMessageText_("Error")
            alert.setInformativeText_("Select a driver first")
            alert.addButtonWithTitle_("OK")
            alert.runModal()
            return
        co_name = self.desc_field.stringValue().strip()
        val_str = self.val_field.stringValue().strip()
        if not co_name or not val_str:
            alert = NSAlert.alloc().init()
            alert.setMessageText_("Error")
            alert.setInformativeText_("Fill all fields")
            alert.addButtonWithTitle_("OK")
            alert.runModal()
            return
        try:
            val = float(val_str)
        except ValueError:
            alert = NSAlert.alloc().init()
            alert.setMessageText_("Error")
            alert.setInformativeText_("Invalid value")
            alert.addButtonWithTitle_("OK")
            alert.runModal()
            return
        con = database.get_connection()
        cur = con.cursor()
        if self.value_table.numberOfSelectedRows() > 0:
            # Update existing driver value
            row = self.value_table.selectedRow()
            val_id = self.value_rows[row][0]
            cur.execute(
                "UPDATE driver_values SET product=?, value=? WHERE id=?", (co_name, val, val_id))
        else:
            # Insert new driver value for current driver
            cur.execute("INSERT INTO driver_values(driver_id, product, value) VALUES(?, ?, ?)",
                        (self.current_driver_id, co_name, val))
            val_id = cur.lastrowid
        try:
            con.commit()
        except Exception as e:
            con.rollback()
            con.close()
            alert = NSAlert.alloc().init()
            alert.setMessageText_("Error")
            alert.setInformativeText_(f"Failed to save value: {e}")
            alert.addButtonWithTitle_("OK")
            alert.runModal()
            return
        con.close()
        database.apply_driver_values([val_id])
        # Reload values list
        if self.current_driver_id is not None:
            con2 = database.get_connection()
            cur2 = con2.cursor()
            cur2.execute(
                "SELECT id, product, value FROM driver_values WHERE driver_id=?", (self.current_driver_id,))
            self.value_rows = cur2.fetchall()
            con2.close()
            self.value_table.reloadData()
        self.clear_value_form()

    def deleteValue_(self, sender):
        if self.value_table.numberOfSelectedRows() == 0:
            return
        row = self.value_table.selectedRow()
        val_id = self.value_rows[row][0]
        alert = NSAlert.alloc().init()
        alert.setMessageText_("Confirm")
        alert.setInformativeText_("Delete selected value?")
        alert.addButtonWithTitle_("Yes")
        alert.addButtonWithTitle_("No")
        response = alert.runModal()
        if response != 1000:
            return
        # Check if this value is used in any allocations
        con = database.get_connection()
        cur = con.cursor()
        cur.execute(
            "SELECT COUNT(*) FROM activity_allocations WHERE driver_value_id=?", (val_id,))
        count = cur.fetchone()[0]
        if count > 0:
            con.close()
            alert = NSAlert.alloc().init()
            alert.setMessageText_("Error")
            alert.setInformativeText_("Cannot delete: value is in use")
            alert.addButtonWithTitle_("OK")
            alert.runModal()
            return
        cur.execute("DELETE FROM driver_values WHERE id=?", (val_id,))
        con.commit()
        con.close()
        # Reload remaining values
        if hasattr(self, "current_driver_id") and self.current_driver_id is not None:
            con2 = database.get_connection()
            cur2 = con2.cursor()
            cur2.execute(
                "SELECT id, product, value FROM driver_values WHERE driver_id=?", (self.current_driver_id,))
            self.value_rows = cur2.fetchall()
            con2.close()
            self.value_table.reloadData()
        self.clear_value_form()

    def refresh(self):
        # Load drivers list
        con = database.get_connection()
        cur = con.cursor()
        cur.execute("SELECT id, name FROM drivers")
        self.driver_rows = cur.fetchall()
        con.close()
        self.driver_table.reloadData()
        # Clear selection and forms
        self.clear_driver_form()
        self.current_driver_id = None
        self.values_label.setStringValue_("Значения драйвера:")
        self.value_rows = []
        self.value_table.reloadData()
        self.clear_value_form()

    def clear_driver_form(self):
        self.name_field.setStringValue_("")
        self.driver_table.deselectAll_(None)

    def clear_value_form(self):
        self.desc_field.setStringValue_("")
        self.val_field.setStringValue_("0.0")
        self.value_table.deselectAll_(None)
