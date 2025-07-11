import objc
from Cocoa import NSObject, NSMakeRect
from AppKit import NSView, NSTextField, NSButton, NSScrollView, NSTableView, NSTableColumn, NSComboBox, NSAlert
from AppKit import NSViewWidthSizable, NSViewMinYMargin, NSViewMaxYMargin, NSViewHeightSizable, NSViewMinXMargin
import database


class AllocationPage(NSObject):
    def init(self):
        self = objc.super(AllocationPage, self).init()
        if self is None:
            return None
        # Main container view
        content_rect = NSMakeRect(0, 0, 1000, 620)
        self.view = NSView.alloc().initWithFrame_(content_rect)
        self.view.setAutoresizingMask_(
            NSViewWidthSizable | NSViewHeightSizable)
        # First section (Resource -> Activity allocations)
        first_section_rect = NSMakeRect(0, 310, 1000, 310)
        first_section = NSView.alloc().initWithFrame_(first_section_rect)
        first_section.setAutoresizingMask_(
            NSViewWidthSizable | NSViewMinYMargin)
        first_label = NSTextField.labelWithString_(
            "Распределение ресурсов на активности")
        first_label.setFrame_(NSMakeRect(5, 290, 400, 20))
        first_section.addSubview_(first_label)
        # Input panel for first section
        res_label = NSTextField.labelWithString_("Ресурс")
        res_label.setFrame_(NSMakeRect(5, 260, 50, 20))
        first_section.addSubview_(res_label)
        self.resource_cb = NSComboBox.alloc().initWithFrame_(NSMakeRect(60, 255, 150, 25))
        self.resource_cb.setEditable_(False)
        first_section.addSubview_(self.resource_cb)
        act_label = NSTextField.labelWithString_("Активность")
        act_label.setFrame_(NSMakeRect(220, 260, 80, 20))
        first_section.addSubview_(act_label)
        self.activity_cb = NSComboBox.alloc().initWithFrame_(NSMakeRect(305, 255, 150, 25))
        self.activity_cb.setEditable_(False)
        first_section.addSubview_(self.activity_cb)
        amt_label = NSTextField.labelWithString_("Количество")
        amt_label.setFrame_(NSMakeRect(460, 260, 90, 20))
        first_section.addSubview_(amt_label)
        self.amount_field = NSTextField.alloc().initWithFrame_(NSMakeRect(555, 255, 80, 25))
        first_section.addSubview_(self.amount_field)
        add_btn1 = NSButton.alloc().initWithFrame_(NSMakeRect(650, 250, 100, 30))
        add_btn1.setTitle_("Add / Update")
        add_btn1.setTarget_(self)
        add_btn1.setAction_("saveResAlloc:")
        add_btn1.setAutoresizingMask_(NSViewMinYMargin)
        first_section.addSubview_(add_btn1)
        # Table for first section
        tree1_rect = NSMakeRect(0, 40, 1000, 180)
        self.tree_res_alloc = NSTableView.alloc().initWithFrame_(tree1_rect)
        for col_id, col_label in [("resource", "Ресурс"), ("activity", "Активность"), ("amount", "Количество")]:
            col = NSTableColumn.alloc().initWithIdentifier_(col_id)
            col.headerCell().setStringValue_(col_label)
            self.tree_res_alloc.addTableColumn_(col)
        self.tree_res_alloc.setDelegate_(self)
        self.tree_res_alloc.setDataSource_(self)
        self.tree_res_alloc.setAllowsMultipleSelection_(False)
        self.tree_res_alloc.setUsesAlternatingRowBackgroundColors_(True)
        scroll1 = NSScrollView.alloc().initWithFrame_(tree1_rect)
        scroll1.setDocumentView_(self.tree_res_alloc)
        scroll1.setHasVerticalScroller_(True)
        scroll1.setAutoresizingMask_(NSViewWidthSizable)
        first_section.addSubview_(scroll1)
        del_btn1 = NSButton.alloc().initWithFrame_(NSMakeRect(5, 5, 80, 30))
        del_btn1.setTitle_("Delete")
        del_btn1.setTarget_(self)
        del_btn1.setAction_("deleteResAlloc:")
        first_section.addSubview_(del_btn1)
        # Second section (Activity -> CostObject allocations)
        second_section_rect = NSMakeRect(0, 0, 1000, 310)
        second_section = NSView.alloc().initWithFrame_(second_section_rect)
        second_section.setAutoresizingMask_(
            NSViewWidthSizable | NSViewMaxYMargin)
        second_label = NSTextField.labelWithString_(
            "Распределение активностей на объекты затрат")
        second_label.setFrame_(NSMakeRect(5, 290, 400, 20))
        second_section.addSubview_(second_label)
        # Input panel for second section
        sec_act_label = NSTextField.labelWithString_("Активность")
        sec_act_label.setFrame_(NSMakeRect(5, 260, 80, 20))
        second_section.addSubview_(sec_act_label)
        self.activity_cb2 = NSComboBox.alloc().initWithFrame_(NSMakeRect(90, 255, 150, 25))
        self.activity_cb2.setEditable_(False)
        second_section.addSubview_(self.activity_cb2)
        obj_label = NSTextField.labelWithString_("Объект")
        obj_label.setFrame_(NSMakeRect(250, 260, 60, 20))
        second_section.addSubview_(obj_label)
        self.costobj_cb = NSComboBox.alloc().initWithFrame_(NSMakeRect(315, 255, 150, 25))
        self.costobj_cb.setEditable_(False)
        second_section.addSubview_(self.costobj_cb)
        desc_label = NSTextField.labelWithString_("Описание")
        desc_label.setFrame_(NSMakeRect(470, 260, 60, 20))
        second_section.addSubview_(desc_label)
        self.driver_val_cb = NSComboBox.alloc().initWithFrame_(
            NSMakeRect(535, 255, 120, 25))
        self.driver_val_cb.setEditable_(False)
        self.driver_val_cb.setEnabled_(False)
        second_section.addSubview_(self.driver_val_cb)
        qty_label = NSTextField.labelWithString_("Объем")
        qty_label.setFrame_(NSMakeRect(660, 260, 50, 20))
        second_section.addSubview_(qty_label)
        self.quantity_field = NSTextField.alloc().initWithFrame_(
            NSMakeRect(715, 255, 80, 25))
        second_section.addSubview_(self.quantity_field)
        add_btn2 = NSButton.alloc().initWithFrame_(NSMakeRect(810, 250, 100, 30))
        add_btn2.setTitle_("Add / Update")
        add_btn2.setTarget_(self)
        add_btn2.setAction_("saveActAlloc:")
        add_btn2.setAutoresizingMask_(NSViewMinXMargin)
        second_section.addSubview_(add_btn2)
        # Table for second section
        tree2_rect = NSMakeRect(0, 40, 1000, 180)
        self.tree_act_alloc = NSTableView.alloc().initWithFrame_(tree2_rect)
        for col_id, col_label in [("activity", "Активность"), ("cost_object", "Объект"), ("quantity", "Объем")]:
            col = NSTableColumn.alloc().initWithIdentifier_(col_id)
            col.headerCell().setStringValue_(col_label)
            self.tree_act_alloc.addTableColumn_(col)
        self.tree_act_alloc.setDelegate_(self)
        self.tree_act_alloc.setDataSource_(self)
        self.tree_act_alloc.setAllowsMultipleSelection_(False)
        self.tree_act_alloc.setUsesAlternatingRowBackgroundColors_(True)
        scroll2 = NSScrollView.alloc().initWithFrame_(tree2_rect)
        scroll2.setDocumentView_(self.tree_act_alloc)
        scroll2.setHasVerticalScroller_(True)
        scroll2.setAutoresizingMask_(NSViewWidthSizable)
        second_section.addSubview_(scroll2)
        del_btn2 = NSButton.alloc().initWithFrame_(NSMakeRect(5, 5, 80, 30))
        del_btn2.setTitle_("Delete")
        del_btn2.setTarget_(self)
        del_btn2.setAction_("deleteActAlloc:")
        second_section.addSubview_(del_btn2)
        # Add sections to main view
        self.view.addSubview_(first_section)
        self.view.addSubview_(second_section)
        # Load initial data
        self.refresh()
        return self

    def numberOfRowsInTableView_(self, tableView):
        if tableView == self.tree_res_alloc:
            return len(self.res_alloc_rows) if hasattr(self, 'res_alloc_rows') else 0
        elif tableView == self.tree_act_alloc:
            return len(self.act_alloc_rows) if hasattr(self, 'act_alloc_rows') else 0
        return 0

    def tableView_objectValueForTableColumn_row_(self, tableView, tableColumn, rowIndex):
        col_id = str(tableColumn.identifier())
        if tableView == self.tree_res_alloc:
            if col_id == "resource":
                return self.res_alloc_rows[rowIndex][0]
            elif col_id == "activity":
                return self.res_alloc_rows[rowIndex][1]
            elif col_id == "amount":
                return str(self.res_alloc_rows[rowIndex][2])
        elif tableView == self.tree_act_alloc:
            if col_id == "activity":
                return self.act_alloc_rows[rowIndex][0]
            elif col_id == "cost_object":
                return self.act_alloc_rows[rowIndex][1]
            elif col_id == "quantity":
                return str(self.act_alloc_rows[rowIndex][2])
        return ""

    def parse_id(self, value):
        try:
            return int(value.split(":")[0]) if value else None
        except Exception:
            return None

    def saveResAlloc_(self, sender):
        r_id = self.parse_id(self.resource_cb.stringValue())
        a_id = self.parse_id(self.activity_cb.stringValue())
        try:
            amt = float(self.amount_field.stringValue())
        except ValueError:
            alert = NSAlert.alloc().init()
            alert.setMessageText_("Error")
            alert.setInformativeText_("Invalid amount")
            alert.addButtonWithTitle_("OK")
            alert.runModal()
            return
        if not r_id or not a_id:
            alert = NSAlert.alloc().init()
            alert.setMessageText_("Error")
            alert.setInformativeText_("Select resource and activity")
            alert.addButtonWithTitle_("OK")
            alert.runModal()
            return
        con = database.get_connection()
        cur = con.cursor()
        # Insert or update base allocation
        cur.execute("INSERT INTO resource_allocations(resource_id, activity_id, amount) VALUES(?,?,?) "
                    "ON CONFLICT(resource_id, activity_id) DO UPDATE SET amount=excluded.amount",
                    (r_id, a_id, amt))
        # Sync monthly values for all periods
        cur.execute(
            "UPDATE resource_allocations_monthly SET amount=? WHERE resource_id=? AND activity_id=?", (amt, r_id, a_id))
        if cur.rowcount == 0:
            # If not existing, insert for all periods
            cur.execute("INSERT INTO resource_allocations_monthly(resource_id, activity_id, period, amount) "
                        "SELECT ?, ?, period, ? FROM periods", (r_id, a_id, amt))
        con.commit()
        con.close()
        self.refresh()

    def deleteResAlloc_(self, sender):
        sel = self.tree_res_alloc.selectedRow()
        if sel is None or sel < 0:
            return
        r_name, a_name, _ = self.res_alloc_rows[sel]
        con = database.get_connection()
        cur = con.cursor()
        cur.execute("SELECT id FROM resources WHERE name=?", (r_name,))
        row = cur.fetchone()
        r_id = row[0] if row else None
        cur.execute("SELECT id FROM activities WHERE name=?", (a_name,))
        row = cur.fetchone()
        a_id = row[0] if row else None
        if r_id is None or a_id is None:
            con.close()
            return
        cur.execute(
            "DELETE FROM resource_allocations WHERE resource_id=? AND activity_id=?", (r_id, a_id))
        cur.execute(
            "DELETE FROM resource_allocations_monthly WHERE resource_id=? AND activity_id=?", (r_id, a_id))
        con.commit()
        con.close()
        self.refresh()

    def saveActAlloc_(self, sender):
        a_id = self.parse_id(self.activity_cb2.stringValue())
        c_id = self.parse_id(self.costobj_cb.stringValue())
        if not a_id or not c_id:
            alert = NSAlert.alloc().init()
            alert.setMessageText_("Error")
            alert.setInformativeText_("Выберите активность и объект")
            alert.addButtonWithTitle_("OK")
            alert.runModal()
            return
        # Determine if activity uses a driver or evenly
        driver_val_id = None
        qty = None
        # Get activity driver info
        con = database.get_connection()
        cur = con.cursor()
        cur.execute(
            "SELECT driver_id, evenly FROM activities WHERE id=?", (a_id,))
        info = cur.fetchone()
        if info:
            act_driver_id, act_evenly = info[0], info[1]
        else:
            act_driver_id, act_evenly = None, 0
        # Validate input based on driver/evenly
        if act_evenly == 1:
            # Evenly: ignore any quantity input
            qty = 1.0
        elif act_driver_id is not None:
            # Activity has a driver: require driver value selection
            driver_val_id = self.parse_id(self.driver_val_cb.stringValue())
            if not driver_val_id:
                con.close()
                alert = NSAlert.alloc().init()
                alert.setMessageText_("Error")
                alert.setInformativeText_("Выберите значение драйвера")
                alert.addButtonWithTitle_("OK")
                alert.runModal()
                return
            # Get the numeric value for selected driver entry
            cur.execute(
                "SELECT value FROM driver_values WHERE id=?", (driver_val_id,))
            row = cur.fetchone()
            qty = row[0] if row else None
            if qty is None:
                con.close()
                alert = NSAlert.alloc().init()
                alert.setMessageText_("Error")
                alert.setInformativeText_("Invalid driver value")
                alert.addButtonWithTitle_("OK")
                alert.runModal()
                return
        else:
            # No driver and not evenly: use manual quantity
            try:
                qty = float(self.quantity_field.stringValue())
            except ValueError:
                con.close()
                alert = NSAlert.alloc().init()
                alert.setMessageText_("Error")
                alert.setInformativeText_("Invalid quantity")
                alert.addButtonWithTitle_("OK")
                alert.runModal()
                return
        # Insert/update allocation in database
        cur2 = con.cursor()
        # Check if allocation already exists
        cur2.execute(
            "SELECT 1 FROM activity_allocations WHERE activity_id=? AND cost_object_id=?", (a_id, c_id))
        exists = cur2.fetchone()
        if exists:
            # Update existing allocation
            cur2.execute("UPDATE activity_allocations SET quantity=?, driver_value_id=? WHERE activity_id=? AND cost_object_id=?",
                         (qty, driver_val_id, a_id, c_id))
            cur2.execute("UPDATE activity_allocations_monthly SET quantity=?, driver_value_id=? WHERE activity_id=? AND cost_object_id=?",
                         (qty, driver_val_id, a_id, c_id))
        else:
            # Insert new allocation (base and all periods)
            cur2.execute("INSERT INTO activity_allocations(activity_id, cost_object_id, quantity, driver_value_id) VALUES(?,?,?,?)",
                         (a_id, c_id, qty, driver_val_id))
            cur2.execute("INSERT INTO activity_allocations_monthly(activity_id, cost_object_id, period, quantity, driver_value_id) "
                         "SELECT ?, ?, period, ?, ? FROM periods", (a_id, c_id, qty, driver_val_id))
        con.commit()
        con.close()
        self.refresh()

    def deleteActAlloc_(self, sender):
        sel = self.tree_act_alloc.selectedRow()
        if sel is None or sel < 0:
            return
        a_name, c_name, _ = self.act_alloc_rows[sel]
        con = database.get_connection()
        cur = con.cursor()
        cur.execute("SELECT id FROM activities WHERE name=?", (a_name,))
        row = cur.fetchone()
        a_id = row[0] if row else None
        cur.execute("SELECT id FROM cost_objects WHERE name=?", (c_name,))
        row = cur.fetchone()
        c_id = row[0] if row else None
        if a_id is None or c_id is None:
            con.close()
            return
        cur.execute(
            "DELETE FROM activity_allocations WHERE activity_id=? AND cost_object_id=?", (a_id, c_id))
        cur.execute(
            "DELETE FROM activity_allocations_monthly WHERE activity_id=? AND cost_object_id=?", (a_id, c_id))
        con.commit()
        con.close()
        self.refresh()

    def refresh(self):
        # Update combobox lists
        con = database.get_connection()
        cur = con.cursor()
        cur.execute("SELECT id, name FROM resources")
        res_list = [f"{r[0]}: {r[1]}" for r in cur.fetchall()]
        cur.execute("SELECT id, name, driver_id, evenly FROM activities")
        acts = cur.fetchall()
        acts_list = [f"{a[0]}: {a[1]}" for a in acts]
        # Store activity driver info for dynamic behavior
        self.activities_info = {a[0]: (a[2], a[3]) for a in acts}
        cur.execute("SELECT id, name FROM cost_objects")
        objs_list = [f"{o[0]}: {o[1]}" for o in cur.fetchall()]
        con.close()
        self.resource_cb.removeAllItems()
        self.resource_cb.addItemsWithObjectValues_(res_list)
        self.activity_cb.removeAllItems()
        self.activity_cb.addItemsWithObjectValues_(acts_list)
        self.activity_cb2.removeAllItems()
        self.activity_cb2.addItemsWithObjectValues_(acts_list)
        self.activity_cb2.setTarget_(self)
        self.activity_cb2.setAction_("activitySelectionChanged:")
        self.costobj_cb.removeAllItems()
        self.costobj_cb.addItemsWithObjectValues_(objs_list)
        # Update allocation tables data
        con2 = database.get_connection()
        cur2 = con2.cursor()
        cur2.execute("""SELECT r.name, a.name, ra.amount
                        FROM resource_allocations ra
                        JOIN resources r ON r.id = ra.resource_id
                        JOIN activities a ON a.id = ra.activity_id""")
        self.res_alloc_rows = cur2.fetchall()
        cur2.execute("""SELECT a.name, c.name, aa.quantity
                        FROM activity_allocations aa
                        JOIN activities a ON a.id = aa.activity_id
                        JOIN cost_objects c ON c.id = aa.cost_object_id""")
        self.act_alloc_rows = cur2.fetchall()
        con2.close()
        self.tree_res_alloc.reloadData()
        self.tree_act_alloc.reloadData()

    def activitySelectionChanged_(self, sender):
        # When an activity is selected in allocation (second section)
        a_id = self.parse_id(sender.stringValue())
        if not a_id:
            return
        # Get driver info for this activity
        info = self.activities_info.get(a_id)
        act_driver_id = info[0] if info else None
        act_evenly = info[1] if info else 0
        # Configure UI based on driver/evenly
        if act_evenly == 1:
            self.driver_val_cb.removeAllItems()
            self.driver_val_cb.setEnabled_(False)
            # Disable quantity input (evenly distributes)
            self.quantity_field.setEnabled_(False)
        elif act_driver_id is not None:
            # Populate driver values list for this activity's driver
            con = database.get_connection()
            cur = con.cursor()
            cur.execute(
                "SELECT id, description FROM driver_values WHERE driver_id=?", (act_driver_id,))
            vals = [f"{row[0]}: {row[1]}" for row in cur.fetchall()]
            con.close()
            self.driver_val_cb.removeAllItems()
            self.driver_val_cb.addItemsWithObjectValues_(vals)
            self.driver_val_cb.setEnabled_(True)
            # Disable manual quantity input when using driver values
            self.quantity_field.setEnabled_(False)
        else:
            # Activity has no driver and is not evenly – enable manual quantity, no driver values
            self.driver_val_cb.removeAllItems()
            self.driver_val_cb.setEnabled_(False)
            self.quantity_field.setEnabled_(True)
