import objc
from Cocoa import NSObject, NSMakeRect
from AppKit import (
    NSView, NSTextField, NSButton, NSScrollView, NSTableView, NSTableColumn,
    NSComboBox, NSAlert,
    NSViewWidthSizable, NSViewMinYMargin, NSViewMaxYMargin, NSViewHeightSizable, NSViewMinXMargin
)
import database

COMBO_VISIBLE_ITEMS = 15  # Show 15 items in drop-down (3x the default 5)


class AllocationPage(NSObject):
    def init(self):
        self = objc.super(AllocationPage, self).init()
        if self is None:
            return None

        # Main container view
        # width increased to accommodate wider fields
        content_rect = NSMakeRect(0, 0, 1400, 620)
        self.view = NSView.alloc().initWithFrame_(content_rect)
        self.view.setAutoresizingMask_(
            NSViewWidthSizable | NSViewHeightSizable)

        # =========================== 1st Section ============================ #
        first_section_rect = NSMakeRect(0, 310, 1400, 310)  # width increased
        first_section = NSView.alloc().initWithFrame_(first_section_rect)
        first_section.setAutoresizingMask_(
            NSViewWidthSizable | NSViewMinYMargin)

        first_label = NSTextField.labelWithString_(
            "Распределение ресурсов на активности")
        first_label.setFrame_(NSMakeRect(5, 290, 400, 20))
        first_section.addSubview_(first_label)

        # ----------- Input panel (Resource → Activity) ----------- #
        res_label = NSTextField.labelWithString_("Ресурс")
        res_label.setFrame_(NSMakeRect(5, 260, 50, 20))
        first_section.addSubview_(res_label)

        self.resource_cb = NSComboBox.alloc().initWithFrame_(
            NSMakeRect(60, 255, 450, 25))  # wider combo box
        self.__tuneCombo__(self.resource_cb)
        first_section.addSubview_(self.resource_cb)

        act_label = NSTextField.labelWithString_("Активность")
        act_label.setFrame_(NSMakeRect(520, 260, 80, 20))  # shifted right
        first_section.addSubview_(act_label)

        self.activity_cb = NSComboBox.alloc().initWithFrame_(
            NSMakeRect(605, 255, 450, 25))  # wider combo box
        self.__tuneCombo__(self.activity_cb)
        first_section.addSubview_(self.activity_cb)

        amt_label = NSTextField.labelWithString_("Количество")
        amt_label.setFrame_(NSMakeRect(1065, 260, 90, 20))  # shifted right
        first_section.addSubview_(amt_label)

        self.amount_field = NSTextField.alloc().initWithFrame_(
            NSMakeRect(1160, 255, 80, 25))
        first_section.addSubview_(self.amount_field)

        add_btn1 = NSButton.alloc().initWithFrame_(NSMakeRect(1250, 250, 100, 30))
        add_btn1.setTitle_("Add / Update")
        add_btn1.setTarget_(self)
        add_btn1.setAction_("saveResAlloc:")
        add_btn1.setAutoresizingMask_(NSViewMinYMargin)
        first_section.addSubview_(add_btn1)

        # Table for Resource→Activity allocations
        tree1_rect = NSMakeRect(0, 40, 1400, 180)
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

        # =========================== 2nd Section ============================ #
        second_section_rect = NSMakeRect(0, 0, 1400, 310)  # width increased
        second_section = NSView.alloc().initWithFrame_(second_section_rect)
        second_section.setAutoresizingMask_(
            NSViewWidthSizable | NSViewMaxYMargin)

        second_label = NSTextField.labelWithString_(
            "Распределение активностей на объекты затрат")
        second_label.setFrame_(NSMakeRect(5, 290, 400, 20))
        second_section.addSubview_(second_label)

        # Table for Activity→CostObject allocations
        tree2_rect = NSMakeRect(0, 40, 1400, 240)
        self.tree_act_alloc = NSTableView.alloc().initWithFrame_(tree2_rect)
        for col_id, col_label in [("activity", "Активность"), ("cost_object", "Объект"), ("driver_amt", "Driver Amt"), ("allocated_cost", "Стоимость")]:
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

        # Add both sections to the main view
        self.view.addSubview_(first_section)
        self.view.addSubview_(second_section)

        # Load initial data
        self.refresh()
        return self

    # ---------------- Internal Utilities ---------------- #
    def __tuneCombo__(self, combo: NSComboBox):
        combo.setEditable_(False)
        combo.setNumberOfVisibleItems_(COMBO_VISIBLE_ITEMS)

        if combo is getattr(self, 'resource_cb', None):
            combo.setTarget_(self)
            combo.setAction_("resourceSelectionChanged:")

    # --------------- TableView Data Source ---------------- #
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
            elif col_id == "driver_amt":
                return str(self.act_alloc_rows[rowIndex][2])
            elif col_id == "allocated_cost":
                return str(self.act_alloc_rows[rowIndex][3])
        return ""

    # ---------------- Handlers (Section 1) ---------------- #
    def saveResAlloc_(self, sender):
        r_id = self.parse_id(self.resource_cb.stringValue())
        a_id = self.parse_id(self.activity_cb.stringValue())
        try:
            amt = float(self.amount_field.stringValue())
        except ValueError:
            self.__showError__("Invalid amount")
            return
        if not r_id or not a_id:
            self.__showError__("Select resource and activity")
            return

        con = database.get_connection()
        cur = con.cursor()
        cur.execute("""
            INSERT INTO resource_allocations(resource_id, activity_id, amount)
            VALUES(?,?,?)
            ON CONFLICT(resource_id, activity_id) DO UPDATE
            SET amount = excluded.amount
        """, (r_id, a_id, amt))
        con.commit()
        con.close()
        database.update_activity_costs()
        self.refresh()

    def deleteResAlloc_(self, sender):
        sel = self.tree_res_alloc.selectedRow()
        if sel is None or sel < 0:
            return
        r_name, a_name, _ = self.res_alloc_rows[sel]
        con = database.get_connection()
        cur = con.cursor()
        # Find IDs by name
        cur.execute("SELECT id FROM resources WHERE name=?", (r_name,))
        r_id = (cur.fetchone() or (None,))[0]
        bproc, act = self.parse_activity_name(a_name)
        if bproc and act:
            cur.execute(
                "SELECT id FROM activities WHERE business_procces=? AND activity=?",
                (bproc, act),
            )
            a_id = (cur.fetchone() or (None,))[0]
        else:
            a_id = None
        if r_id and a_id:
            cur.execute(
                "DELETE FROM resource_allocations WHERE resource_id=? AND activity_id=?", (r_id, a_id))
            con.commit()
        con.close()
        database.update_activity_costs()
        self.refresh()

    # ------------- Show remaining cost on resource selection ------------- #
    def resourceSelectionChanged_(self, sender):
        """Calculates and displays the unallocated remainder of the selected resource's cost."""
        r_id = self.parse_id(sender.stringValue())
        if not r_id:
            self.amount_field.setStringValue_("")
            return
        con = database.get_connection()
        cur = con.cursor()
        # 1) Find the resource's total cost (cost_total)
        cur.execute("SELECT cost_total FROM resources WHERE id=?", (r_id,))
        row = cur.fetchone()
        total = float(row[0]) if row and row[0] is not None else None
        if total is None:
            con.close()
            self.amount_field.setStringValue_("")
            return
        # 2) Sum already allocated amount for this resource
        cur.execute(
            "SELECT COALESCE(SUM(amount), 0) FROM resource_allocations WHERE resource_id=?", (r_id,))
        allocated = float(cur.fetchone()[0] or 0.0)
        remaining = max(total - allocated, 0.0)
        self.amount_field.setStringValue_(str(remaining))
        con.close()

    # ---------------- Handlers (Section 2) ---------------- #
    def deleteActAlloc_(self, sender):
        sel = self.tree_act_alloc.selectedRow()
        if sel is None or sel < 0:
            return
        a_name, c_name, _ = self.act_alloc_rows[sel]
        con = database.get_connection()
        cur = con.cursor()
        bproc, act = self.parse_activity_name(a_name)
        if bproc and act:
            cur.execute(
                "SELECT id FROM activities WHERE business_procces=? AND activity=?",
                (bproc, act),
            )
            a_id = (cur.fetchone() or (None,))[0]
        else:
            a_id = None
        prod, cbp = self.parse_costobj_name(c_name)
        if prod and cbp:
            cur.execute(
                "SELECT id FROM cost_objects WHERE product=? AND business_procces=?",
                (prod, cbp),
            )
            c_id = (cur.fetchone() or (None,))[0]
        else:
            c_id = None
        if a_id and c_id:
            cur.execute(
                "DELETE FROM activity_allocations WHERE activity_id=? AND cost_object_id=?", (a_id, c_id))
            con.commit()
        con.close()
        database.update_cost_object_costs()
        self.refresh()

    # ---------------- Refresh UI/Data ---------------- #
    def refresh(self):
        # Refresh drop-down lists
        con = database.get_connection()
        cur = con.cursor()
        cur.execute("SELECT id, name FROM resources")
        res_list = [f"{r[0]}: {r[1]}" for r in cur.fetchall()]
        cur.execute(
            "SELECT id, business_procces || ' X ' || activity AS name, driver_id, evenly FROM activities"
        )
        acts = cur.fetchall()
        acts_list = [f"{a[0]}: {a[1]}" for a in acts]
        self.activities_info = {a[0]: (a[2], a[3]) for a in acts}
        cur.execute(
            "SELECT id, product || ' X ' || business_procces AS name FROM cost_objects"
        )
        objs_list = [f"{o[0]}: {o[1]}" for o in cur.fetchall()]
        con.close()

        self.resource_cb.removeAllItems()
        self.resource_cb.addItemsWithObjectValues_(res_list)
        self.activity_cb.removeAllItems()
        self.activity_cb.addItemsWithObjectValues_(acts_list)
        # Refresh tables
        con2 = database.get_connection()
        cur2 = con2.cursor()
        cur2.execute(
            """SELECT r.name,
                      a.business_procces || ' X ' || a.activity AS act_name,
                      ra.amount
                 FROM resource_allocations ra
                 JOIN resources  r ON r.id = ra.resource_id
                 JOIN activities a ON a.id = ra.activity_id"""
        )
        self.res_alloc_rows = cur2.fetchall()
        cur2.execute(
            """SELECT a.business_procces || ' X ' || a.activity AS act_name,
                      c.product || ' X ' || c.business_procces AS obj_name,
                      aa.driver_amt, aa.allocated_cost
                 FROM activity_allocations aa
                 JOIN activities   a ON a.id = aa.activity_id
                 JOIN cost_objects c ON c.id = aa.cost_object_id"""
        )
        self.act_alloc_rows = cur2.fetchall()
        con2.close()
        self.tree_res_alloc.reloadData()
        self.tree_act_alloc.reloadData()

        # If a resource is already selected, update the remaining cost display
        if self.parse_id(self.resource_cb.stringValue()):
            self.resourceSelectionChanged_(self.resource_cb)

    def parse_id(self, value):
        """Utility to parse the ID (integer before the colon) from a combo box string value."""
        try:
            return int(value.split(":")[0]) if value else None
        except Exception:
            return None

    def parse_activity_name(self, text: str):
        if "X" not in text:
            return None, None
        bproc, act = text.split("X", 1)
        return bproc.strip(), act.strip()

    def parse_costobj_name(self, text: str):
        if "X" not in text:
            return None, None
        prod, bproc = text.split("X", 1)
        return prod.strip(), bproc.strip()

    def __showError__(self, msg: str):
        alert = NSAlert.alloc().init()
        alert.setMessageText_("Error")
        alert.setInformativeText_(msg)
        alert.addButtonWithTitle_("OK")
        alert.runModal()
