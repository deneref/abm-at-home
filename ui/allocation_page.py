import objc
from Cocoa import NSObject, NSMakeRect
from AppKit import NSView, NSTextField, NSButton, NSScrollView, NSTableView, NSTableColumn, NSComboBox, NSAlert
from AppKit import NSViewWidthSizable, NSViewMinYMargin, NSViewMaxYMargin
import database

class AllocationPage(NSObject):
    def init(self):
        self = objc.super(AllocationPage, self).init()
        if self is None:
            return None
        # Основной контейнер страницы
        content_rect = NSMakeRect(0, 0, 1000, 620)
        self.view = NSView.alloc().initWithFrame_(content_rect)
        self.view.setAutoresizingMask_(NSViewWidthSizable | NSViewHeightSizable)
        # Первый раздел (распределение ресурсов на активности)
        first_section_rect = NSMakeRect(0, 310, 1000, 310)
        first_section = NSView.alloc().initWithFrame_(first_section_rect)
        first_section.setAutoresizingMask_(NSViewWidthSizable | NSViewMinYMargin)
        first_label = NSTextField.labelWithString_("Распределение ресурсов на активности")
        first_label.setFrame_(NSMakeRect(5, 290, 400, 20))
        first_section.addSubview_(first_label)
        # Панель ввода для первого раздела (ресурс, активность, количество)
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
        add_btn1.setAction_("save_res_alloc:")
        add_btn1.setAutoresizingMask_(NSViewMinYMargin)
        first_section.addSubview_(add_btn1)
        # Таблица первого раздела (распределения ресурсов на активности)
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
        del_btn1.setAction_("delete_res_alloc:")
        first_section.addSubview_(del_btn1)
        # Второй раздел (распределение активностей на объекты затрат)
        second_section_rect = NSMakeRect(0, 0, 1000, 310)
        second_section = NSView.alloc().initWithFrame_(second_section_rect)
        second_section.setAutoresizingMask_(NSViewWidthSizable | NSViewMaxYMargin)
        second_label = NSTextField.labelWithString_("Распределение активностей на объекты затрат")
        second_label.setFrame_(NSMakeRect(5, 290, 400, 20))
        second_section.addSubview_(second_label)
        # Панель ввода для второго раздела (активность, объект, объем)
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
        qty_label = NSTextField.labelWithString_("Объем")
        qty_label.setFrame_(NSMakeRect(480, 260, 50, 20))
        second_section.addSubview_(qty_label)
        self.quantity_field = NSTextField.alloc().initWithFrame_(NSMakeRect(535, 255, 80, 25))
        second_section.addSubview_(self.quantity_field)
        add_btn2 = NSButton.alloc().initWithFrame_(NSMakeRect(610, 250, 100, 30))
        add_btn2.setTitle_("Add / Update")
        add_btn2.setTarget_(self)
        add_btn2.setAction_("save_act_alloc:")
        add_btn2.setAutoresizingMask_(NSViewMinXMargin)
        second_section.addSubview_(add_btn2)
        # Таблица второго раздела (распределения активностей на объекты затрат)
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
        del_btn2.setAction_("delete_act_alloc:")
        second_section.addSubview_(del_btn2)
        # Добавление разделов на страницу
        self.view.addSubview_(first_section)
        self.view.addSubview_(second_section)
        # Загрузка начальных данных
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

    def save_res_alloc_(self, sender):
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
        con.execute("INSERT INTO resource_allocations(resource_id, activity_id, amount) VALUES(?,?,?) ON CONFLICT(resource_id, activity_id) DO UPDATE SET amount=excluded.amount", (r_id, a_id, amt))
        con.commit()
        con.close()
        self.refresh()

    def delete_res_alloc_(self, sender):
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
        cur.execute("DELETE FROM resource_allocations WHERE resource_id=? AND activity_id=?", (r_id, a_id))
        con.commit()
        con.close()
        self.refresh()

    def save_act_alloc_(self, sender):
        a_id = self.parse_id(self.activity_cb2.stringValue())
        c_id = self.parse_id(self.costobj_cb.stringValue())
        try:
            qty = float(self.quantity_field.stringValue())
        except ValueError:
            alert = NSAlert.alloc().init()
            alert.setMessageText_("Error")
            alert.setInformativeText_("Invalid quantity")
            alert.addButtonWithTitle_("OK")
            alert.runModal()
            return
        if not a_id or not c_id:
            alert = NSAlert.alloc().init()
            alert.setMessageText_("Error")
            alert.setInformativeText_("Select activity and object")
            alert.addButtonWithTitle_("OK")
            alert.runModal()
            return
        con = database.get_connection()
        con.execute("INSERT INTO activity_allocations(activity_id, cost_object_id, quantity) VALUES(?,?,?) ON CONFLICT(activity_id, cost_object_id) DO UPDATE SET quantity=excluded.quantity", (a_id, c_id, qty))
        con.commit()
        con.close()
        self.refresh()

    def delete_act_alloc_(self, sender):
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
        cur.execute("DELETE FROM activity_allocations WHERE activity_id=? AND cost_object_id=?", (a_id, c_id))
        con.commit()
        con.close()
        self.refresh()

    def refresh(self):
        # Обновление списков в Combobox
        con = database.get_connection()
        cur = con.cursor()
        cur.execute("SELECT id, name FROM resources")
        res_list = [f"{r[0]}: {r[1]}" for r in cur.fetchall()]
        cur.execute("SELECT id, name FROM activities")
        acts_list = [f"{a[0]}: {a[1]}" for a in cur.fetchall()]
        cur.execute("SELECT id, name FROM cost_objects")
        objs_list = [f"{o[0]}: {o[1]}" for o in cur.fetchall()]
        con.close()
        self.resource_cb.removeAllItems()
        self.resource_cb.addItemsWithObjectValues_(res_list)
        self.activity_cb.removeAllItems()
        self.activity_cb.addItemsWithObjectValues_(acts_list)
        self.activity_cb2.removeAllItems()
        self.activity_cb2.addItemsWithObjectValues_(acts_list)
        self.costobj_cb.removeAllItems()
        self.costobj_cb.addItemsWithObjectValues_(objs_list)
        # Обновление таблиц распределений
        con = database.get_connection()
        cur = con.cursor()
        cur.execute("""SELECT r.name, a.name, ra.amount 
                       FROM resource_allocations ra 
                       JOIN resources r ON r.id = ra.resource_id 
                       JOIN activities a ON a.id = ra.activity_id""")
        self.res_alloc_rows = cur.fetchall()
        cur.execute("""SELECT a.name, c.name, aa.quantity 
                       FROM activity_allocations aa 
                       JOIN activities a ON a.id = aa.activity_id 
                       JOIN cost_objects c ON c.id = aa.cost_object_id""")
        self.act_alloc_rows = cur.fetchall()
        con.close()
        self.tree_res_alloc.reloadData()
        self.tree_act_alloc.reloadData()