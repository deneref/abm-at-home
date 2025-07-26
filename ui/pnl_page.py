from ui.allocation_page import COMBO_VISIBLE_ITEMS
import database
import objc
from Cocoa import NSObject, NSMakeRect, NSData
from AppKit import (
    NSView,
    NSTextField,
    NSComboBox,
    NSImageView,
    NSViewWidthSizable,
    NSViewHeightSizable,
    NSViewMinYMargin,
    NSViewMaxYMargin,
)
import io
from matplotlib.figure import Figure
import matplotlib
matplotlib.use("Agg")


class PNLPage(NSObject):
    def init(self):
        self = objc.super(PNLPage, self).init()
        if self is None:
            return None
        # allow the graphs to stretch across the entire window
        content_rect = NSMakeRect(0, 0, 1400, 620)
        self.view = NSView.alloc().initWithFrame_(content_rect)
        self.view.setAutoresizingMask_(
            NSViewWidthSizable | NSViewHeightSizable)

        label = NSTextField.labelWithString_("Product")
        # give enough space so the combo box doesn't overlap
        label.setFrame_(NSMakeRect(10, 585, 80, 20))
        label.setAutoresizingMask_(NSViewMinYMargin)
        self.view.addSubview_(label)

        # wider combo for better visibility
        self.product_cb = NSComboBox.alloc().initWithFrame_(NSMakeRect(100, 580, 450, 25))
        self.product_cb.setEditable_(False)
        self.product_cb.setNumberOfVisibleItems_(COMBO_VISIBLE_ITEMS)
        self.product_cb.setTarget_(self)
        self.product_cb.setAction_("productChanged:")
        self.product_cb.setDelegate_(self)
        self.product_cb.setAutoresizingMask_(NSViewMinYMargin)
        self.view.addSubview_(self.product_cb)

        first_rect = NSMakeRect(0, 310, 1400, 310)
        self.first_section = NSView.alloc().initWithFrame_(first_rect)
        self.first_section.setAutoresizingMask_(
            NSViewWidthSizable | NSViewMinYMargin)
        self.view.addSubview_(self.first_section)

        second_rect = NSMakeRect(0, 0, 1400, 310)
        self.second_section = NSView.alloc().initWithFrame_(second_rect)
        self.second_section.setAutoresizingMask_(
            NSViewWidthSizable | NSViewMaxYMargin)
        title2 = NSTextField.labelWithString_("Revenue vs Cost")
        title2.setFrame_(NSMakeRect(5, 280, 200, 20))
        self.second_section.addSubview_(title2)
        self.view.addSubview_(self.second_section)

        self.refresh()
        return self

    def refresh(self):
        con = database.get_connection()
        cur = con.cursor()
        cur.execute("SELECT DISTINCT product FROM cost_objects")
        products = [row[0] for row in cur.fetchall()]
        con.close()
        self.product_cb.removeAllItems()
        self.product_cb.addItemsWithObjectValues_(products)
        if products:
            self.product_cb.selectItemAtIndex_(0)
        self.draw_charts()

    def comboBoxSelectionDidChange_(self, notification):
        """Trigger redraw when product is changed via dropdown."""
        sender = notification.object()
        if sender is self.product_cb:
            self.productChanged_(sender)

    def productChanged_(self, sender):
        self.draw_charts()

    def draw_charts(self):
        prod = self.product_cb.stringValue().strip()
        for attr in ("img_view1", "img_view2"):
            if hasattr(self, attr):
                view = getattr(self, attr)
                if view:
                    view.removeFromSuperview()
                    setattr(self, attr, None)
        if not prod:
            return
        con = database.get_connection()
        cur = con.cursor()
        cur.execute(
            "SELECT business_procces, SUM(allocated_cost) FROM cost_objects WHERE product=? GROUP BY business_procces",
            (prod,),
        )
        rows = cur.fetchall()
        con.close()
        total_rev, total_cost = database.get_revenue_and_cost(prod)
        labels = [r[0] for r in rows]
        values = [r[1] for r in rows]
        fig1 = Figure(figsize=(16, 3), dpi=100)
        ax1 = fig1.add_subplot(111)
        if values:
            ax1.barh(labels, values, color="#6699cc")
        ax1.set_xlabel("Cost")
        buf1 = io.BytesIO()
        fig1.tight_layout()
        fig1.savefig(buf1, format="png")
        img_data1 = buf1.getvalue()
        nsdata1 = NSData.dataWithBytes_length_(img_data1, len(img_data1))
        image1 = objc.lookUpClass("NSImage").alloc(
        ).initWithData_(nsdata1) if nsdata1 else None
        if image1:
            self.img_view1 = NSImageView.alloc().initWithFrame_(
                NSMakeRect(0, 0, self.first_section.frame().size.width, 260))
            self.img_view1.setImage_(image1)
            try:
                from AppKit import NSImageScaleProportionallyUpOrDown
                self.img_view1.setImageScaling_(
                    NSImageScaleProportionallyUpOrDown)
            except Exception:
                pass
            self.img_view1.setAutoresizingMask_(NSViewWidthSizable)
            self.first_section.addSubview_(self.img_view1)

        fig2 = Figure(figsize=(16, 3), dpi=100)
        ax2 = fig2.add_subplot(111)
        ax2.barh(["Revenue", "Cost"], [total_rev, total_cost],
                 color=["#66cc66", "#cc6666"])
        ax2.set_xlabel("Amount")
        buf2 = io.BytesIO()
        fig2.tight_layout()
        fig2.savefig(buf2, format="png")
        img_data2 = buf2.getvalue()
        nsdata2 = NSData.dataWithBytes_length_(img_data2, len(img_data2))
        image2 = objc.lookUpClass("NSImage").alloc(
        ).initWithData_(nsdata2) if nsdata2 else None
        if image2:
            self.img_view2 = NSImageView.alloc().initWithFrame_(
                NSMakeRect(0, 0, self.second_section.frame().size.width, 260))
            self.img_view2.setImage_(image2)
            try:
                from AppKit import NSImageScaleProportionallyUpOrDown
                self.img_view2.setImageScaling_(
                    NSImageScaleProportionallyUpOrDown)
            except Exception:
                pass
            self.img_view2.setAutoresizingMask_(NSViewWidthSizable)
            self.second_section.addSubview_(self.img_view2)
