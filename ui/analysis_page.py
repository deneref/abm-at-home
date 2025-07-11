import objc
from Cocoa import NSObject, NSMakeRect, NSData
from AppKit import NSView, NSTextField, NSButton, NSScrollView, NSTableView, NSTableColumn, NSComboBox, NSImageView, NSAlert
from AppKit import NSViewWidthSizable, NSViewHeightSizable, NSViewMinYMargin
import database
import calculation
import matplotlib
matplotlib.use("Agg")
from matplotlib.figure import Figure
import io

class AnalysisPage(NSObject):
    def init(self):
        self = objc.super(AnalysisPage, self).init()
        if self is None:
            return None
        content_rect = NSMakeRect(0, 0, 1000, 620)
        self.view = NSView.alloc().initWithFrame_(content_rect)
        self.view.setAutoresizingMask_(NSViewWidthSizable | NSViewHeightSizable)
        # Верхняя панель (выбор объекта и кнопка "Рассчитать")
        obj_label = NSTextField.labelWithString_("Объект затрат")
        obj_label.setFrame_(NSMakeRect(5, 585, 100, 20))
        self.view.addSubview_(obj_label)
        self.obj_cb = NSComboBox.alloc().initWithFrame_(NSMakeRect(110, 580, 200, 25))
        self.obj_cb.setEditable_(False)
        self.view.addSubview_(self.obj_cb)
        calc_button = NSButton.alloc().initWithFrame_(NSMakeRect(320, 578, 100, 30))
        calc_button.setTitle_("Рассчитать")
        calc_button.setTarget_(self)
        calc_button.setAction_("calculate:")
        self.view.addSubview_(calc_button)
        # Таблица результатов (активность, затраты, %)
        table_rect = NSMakeRect(0, 300, 1000, 270)
        self.table = NSTableView.alloc().initWithFrame_(table_rect)
        for col_id, col_label in [("activity", "Активность"), ("amount", "Затраты"), ("perc", "%")]:
            col = NSTableColumn.alloc().initWithIdentifier_(col_id)
            col.headerCell().setStringValue_(col_label)
            self.table.addTableColumn_(col)
        self.table.setDelegate_(self)
        self.table.setDataSource_(self)
        self.table.setAllowsMultipleSelection_(False)
        scroll = NSScrollView.alloc().initWithFrame_(table_rect)
        scroll.setDocumentView_(self.table)
        scroll.setHasVerticalScroller_(True)
        scroll.setAutoresizingMask_(NSViewWidthSizable | NSViewHeightSizable)
        self.view.addSubview_(scroll)
        # Область для графика (нижняя часть)
        self.chart_container = NSView.alloc().initWithFrame_(NSMakeRect(0, 0, 1000, 300))
        self.chart_container.setAutoresizingMask_(NSViewWidthSizable | NSViewMinYMargin)
        self.view.addSubview_(self.chart_container)
        # Заполнение списка объектов затрат
        self.refresh()
        return self

    def refresh(self):
        con = database.get_connection()
        cur = con.cursor()
        cur.execute("SELECT id, name FROM cost_objects")
        self.objs = cur.fetchall()
        con.close()
        values = [f"{o[0]}: {o[1]}" for o in self.objs]
        self.obj_cb.removeAllItems()
        self.obj_cb.addItemsWithObjectValues_(values)

    def parse_id(self, value):
        try:
            return int(value.split(":")[0]) if value else None
        except Exception:
            return None

    def calculate_(self, sender):
        obj_id = self.parse_id(self.obj_cb.stringValue())
        if not obj_id:
            alert = NSAlert.alloc().init()
            alert.setMessageText_("Error")
            alert.setInformativeText_("Выберите объект")
            alert.addButtonWithTitle_("OK")
            alert.runModal()
            return
        con = database.get_connection()
        totals, breakdown = calculation.calculate_costs(con)
        con.close()
        if obj_id not in totals:
            alert = NSAlert.alloc().init()
            alert.setMessageText_("Нет данных")
            alert.setInformativeText_("Для выбранного объекта нет данных")
            alert.addButtonWithTitle_("OK")
            alert.runModal()
            return
        total_val = totals[obj_id]
        # Заполнение таблицы результатов
        self.result_rows = []
        act_break = breakdown.get(obj_id, {})
        for act_id, amt in act_break.items():
            act_name = self.get_activity_name(act_id)
            perc = (amt / total_val * 100) if total_val else 0
            self.result_rows.append((act_name, f"{amt:.2f}", f"{perc:.1f}%"))
        self.table.reloadData()
        # Построение круговой диаграммы
        self.draw_pie_chart(act_break)

    def get_activity_name(self, act_id):
        con = database.get_connection()
        cur = con.cursor()
        cur.execute("SELECT name FROM activities WHERE id=?", (act_id,))
        row = cur.fetchone()
        con.close()
        return row[0] if row else str(act_id)

    def draw_pie_chart(self, data):
        # Очистка предыдущего графика
        for sub in self.chart_container.subviews():
            sub.removeFromSuperview()
        if not data:
            return
        labels = [self.get_activity_name(a) for a in data.keys()]
        sizes = [data[a] for a in data.keys()]
        fig = Figure(figsize=(4, 4), dpi=100)
        ax = fig.add_subplot(111)
        ax.pie(sizes, labels=labels, autopct="%1.1f%%")
        buf = io.BytesIO()
        fig.savefig(buf, format="png")
        img_data = buf.getvalue()
        nsdata = NSData.dataWithBytes_length_(img_data, len(img_data))
        image = objc.lookUpClass("NSImage").alloc().initWithData_(nsdata) if nsdata else None
        if not image:
            return
        img_view = NSImageView.alloc().initWithFrame_(NSMakeRect(0, 0, self.chart_container.frame().size.width, self.chart_container.frame().size.height))
        img_view.setImage_(image)
        try:
            from AppKit import NSImageScaleProportionallyUpOrDown
            img_view.setImageScaling_(NSImageScaleProportionallyUpOrDown)
        except Exception:
            pass
        img_view.setAutoresizingMask_(NSViewWidthSizable | NSViewHeightSizable)
        self.chart_container.addSubview_(img_view)