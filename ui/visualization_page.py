import objc
from Cocoa import NSObject, NSMakeRect, NSData
from AppKit import NSView, NSTextField, NSImageView
from AppKit import NSViewWidthSizable, NSViewMinYMargin, NSViewMaxYMargin
import database
import calculation
import matplotlib
matplotlib.use("Agg")
from matplotlib.figure import Figure
import io

class VisualizationPage(NSObject):
    def init(self):
        self = objc.super(VisualizationPage, self).init()
        if self is None:
            return None
        content_rect = NSMakeRect(0, 0, 1000, 620)
        self.view = NSView.alloc().initWithFrame_(content_rect)
        self.view.setAutoresizingMask_(NSViewWidthSizable | NSViewHeightSizable)
        # Первый блок – распределение затрат по объектам затрат
        first_section_rect = NSMakeRect(0, 310, 1000, 310)
        self.first_section = NSView.alloc().initWithFrame_(first_section_rect)
        self.first_section.setAutoresizingMask_(NSViewWidthSizable | NSViewMinYMargin)
        label1 = NSTextField.labelWithString_("Распределение по объектам затрат")
        label1.setFrame_(NSMakeRect(5, 280, 400, 20))
        self.first_section.addSubview_(label1)
        # Второй блок – распределение затрат по активностям
        second_section_rect = NSMakeRect(0, 0, 1000, 310)
        self.second_section = NSView.alloc().initWithFrame_(second_section_rect)
        self.second_section.setAutoresizingMask_(NSViewWidthSizable | NSViewMaxYMargin)
        label2 = NSTextField.labelWithString_("Распределение по активностям")
        label2.setFrame_(NSMakeRect(5, 280, 300, 20))
        self.second_section.addSubview_(label2)
        # Добавление блоков на основное представление
        self.view.addSubview_(self.first_section)
        self.view.addSubview_(self.second_section)
        # Отрисовка начальных графиков
        self.refresh()
        return self

    def refresh(self):
        # Удаление предыдущих изображений (если есть)
        if hasattr(self, "img_view1") and self.img_view1:
            self.img_view1.removeFromSuperview()
            self.img_view1 = None
        if hasattr(self, "img_view2") and self.img_view2:
            self.img_view2.removeFromSuperview()
            self.img_view2 = None
        # Получение распределения затрат
        con = database.get_connection()
        totals, breakdown = calculation.calculate_costs(con)
        con.close()
        if not totals:
            # Нет данных для визуализации
            return
        # Распределение по объектам затрат
        costobj_totals = totals  # {cost_object_id: value}
        con2 = database.get_connection()
        cur2 = con2.cursor()
        cur2.execute("SELECT id, name FROM cost_objects")
        all_costobjs = {row[0]: row[1] for row in cur2.fetchall()}
        con2.close()
        labels1 = []
        sizes1 = []
        for co_id, val in costobj_totals.items():
            labels1.append(all_costobjs.get(co_id, str(co_id)))
            sizes1.append(val)
        # Распределение по активностям
        activity_totals = {}
        for acts in breakdown.values():
            for a_id, value in acts.items():
                activity_totals[a_id] = activity_totals.get(a_id, 0) + value
        con3 = database.get_connection()
        cur3 = con3.cursor()
        cur3.execute("SELECT id, name FROM activities")
        all_activities = {row[0]: row[1] for row in cur3.fetchall()}
        con3.close()
        labels2 = []
        sizes2 = []
        for a_id, val in activity_totals.items():
            labels2.append(all_activities.get(a_id, str(a_id)))
            sizes2.append(val)
        # Построение диаграмм с помощью matplotlib
        fig1 = Figure(figsize=(4, 4), dpi=100)
        ax1 = fig1.add_subplot(111)
        if sizes1:
            ax1.pie(sizes1, labels=labels1, autopct="%1.1f%%")
        fig2 = Figure(figsize=(4, 4), dpi=100)
        ax2 = fig2.add_subplot(111)
        if sizes2:
            ax2.pie(sizes2, labels=labels2, autopct="%1.1f%%")
        # Конвертация графиков в изображения NSImage
        buf1 = io.BytesIO()
        fig1.savefig(buf1, format="png")
        img_data1 = buf1.getvalue()
        nsdata1 = NSData.dataWithBytes_length_(img_data1, len(img_data1))
        image1 = objc.lookUpClass("NSImage").alloc().initWithData_(nsdata1) if nsdata1 else None
        buf2 = io.BytesIO()
        fig2.savefig(buf2, format="png")
        img_data2 = buf2.getvalue()
        nsdata2 = NSData.dataWithBytes_length_(img_data2, len(img_data2))
        image2 = objc.lookUpClass("NSImage").alloc().initWithData_(nsdata2) if nsdata2 else None
        # Отображение изображений на интерфейсе
        if image1:
            self.img_view1 = NSImageView.alloc().initWithFrame_(NSMakeRect(0, 0, self.first_section.frame().size.width, 270))
            self.img_view1.setImage_(image1)
            try:
                from AppKit import NSImageScaleProportionallyUpOrDown
                self.img_view1.setImageScaling_(NSImageScaleProportionallyUpOrDown)
            except Exception:
                pass
            self.img_view1.setAutoresizingMask_(NSViewWidthSizable)
            self.first_section.addSubview_(self.img_view1)
        if image2:
            self.img_view2 = NSImageView.alloc().initWithFrame_(NSMakeRect(0, 0, self.second_section.frame().size.width, 270))
            self.img_view2.setImage_(image2)
            try:
                from AppKit import NSImageScaleProportionallyUpOrDown
                self.img_view2.setImageScaling_(NSImageScaleProportionallyUpOrDown)
            except Exception:
                pass
            self.img_view2.setAutoresizingMask_(NSViewWidthSizable)
            self.second_section.addSubview_(self.img_view2)