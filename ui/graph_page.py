from matplotlib.figure import Figure
import io
import objc
from Cocoa import NSObject, NSMakeRect, NSData
from AppKit import (
    NSView, NSImageView, NSButton, NSTextField, NSComboBox,
    NSViewWidthSizable, NSViewHeightSizable, NSViewMinYMargin,
)
from ui.allocation_page import COMBO_VISIBLE_ITEMS
import database
import matplotlib
matplotlib.use("Agg")

from graph_logic import build_graph_data

class GraphPage(NSObject):
    def init(self):
        self = objc.super(GraphPage, self).init()
        if self is None:
            return None
        content_rect = NSMakeRect(0, 0, 1400, 620)
        self.view = NSView.alloc().initWithFrame_(content_rect)
        self.view.setAutoresizingMask_(NSViewWidthSizable | NSViewHeightSizable)

        prod_label = NSTextField.labelWithString_("Product")
        prod_label.setFrame_(NSMakeRect(5, 585, 70, 20))
        prod_label.setAutoresizingMask_(NSViewMinYMargin)
        self.view.addSubview_(prod_label)

        self.product_cb = NSComboBox.alloc().initWithFrame_(NSMakeRect(80, 580, 450, 25))
        self.product_cb.setEditable_(False)
        self.product_cb.setNumberOfVisibleItems_(COMBO_VISIBLE_ITEMS)
        self.product_cb.setAutoresizingMask_(NSViewMinYMargin)
        self.product_cb.setTarget_(self)
        self.product_cb.setAction_("productChanged:")
        self.view.addSubview_(self.product_cb)

        bp_label = NSTextField.labelWithString_("Business Process")
        bp_label.setFrame_(NSMakeRect(540, 585, 120, 20))
        bp_label.setAutoresizingMask_(NSViewMinYMargin)
        self.view.addSubview_(bp_label)

        self.bp_cb = NSComboBox.alloc().initWithFrame_(NSMakeRect(665, 580, 450, 25))
        self.bp_cb.setEditable_(False)
        self.bp_cb.setNumberOfVisibleItems_(COMBO_VISIBLE_ITEMS)
        self.bp_cb.setAutoresizingMask_(NSViewMinYMargin)
        self.view.addSubview_(self.bp_cb)

        btn = NSButton.alloc().initWithFrame_(NSMakeRect(1125, 578, 120, 30))
        btn.setTitle_("Show Graph")
        btn.setTarget_(self)
        btn.setAction_("showGraph:")
        btn.setAutoresizingMask_(NSViewMinYMargin)
        self.view.addSubview_(btn)

        self.refresh_products()
        return self

    def productChanged_(self, sender):
        prod = sender.stringValue().strip()
        con = database.get_connection()
        cur = con.cursor()
        if prod:
            cur.execute(
                "SELECT business_procces FROM cost_objects WHERE product=?",
                (prod,),
            )
            vals = [row[0] for row in cur.fetchall()]
        else:
            vals = []
        con.close()
        self.bp_cb.removeAllItems()
        if vals:
            self.bp_cb.addItemsWithObjectValues_(vals)

    def refresh_products(self):
        con = database.get_connection()
        cur = con.cursor()
        cur.execute("SELECT DISTINCT product FROM cost_objects")
        prods = [row[0] for row in cur.fetchall()]
        con.close()
        self.product_cb.removeAllItems()
        self.product_cb.addItemsWithObjectValues_(prods)
        self.bp_cb.removeAllItems()

    def showGraph_(self, sender):
        product = self.product_cb.stringValue().strip()
        if not product:
            return
        bproc = self.bp_cb.stringValue().strip()
        if not bproc:
            bproc = None
        self.draw_graph(product, bproc)

    def draw_graph(self, product: str, bproc: str | None = None):
        if hasattr(self, "img_view") and self.img_view:
            self.img_view.removeFromSuperview()
            self.img_view = None
        if not database.current_period or not product:
            return

        node_labels, node_colors, edges = build_graph_data(product, bproc)
        if not node_labels:
            return

        pos = {}
        R_nodes = sorted([n for n in node_labels if n.startswith("R")], key=lambda x: int(x[1:]))
        A_nodes = sorted([n for n in node_labels if n.startswith("A")], key=lambda x: int(x[1:]))
        O_nodes = sorted([n for n in node_labels if n.startswith("O")], key=lambda x: int(x[1:]))
        nR, nA, nO = len(R_nodes), len(A_nodes), len(O_nodes)
        for i, node in enumerate(R_nodes):
            y = 1 - ((i + 1) / (nR + 1)) if nR > 0 else 0.5
            pos[node] = (0.1, y)
        for i, node in enumerate(A_nodes):
            y = 1 - ((i + 1) / (nA + 1)) if nA > 0 else 0.5
            pos[node] = (0.5, y)
        for i, node in enumerate(O_nodes):
            y = 1 - ((i + 1) / (nO + 1)) if nO > 0 else 0.5
            pos[node] = (0.9, y)

        fig = Figure(figsize=(10, 6), dpi=100)
        ax = fig.add_subplot(111)
        ax.axis("off")

        for node, (x, y) in pos.items():
            ax.scatter(x, y, s=800, color=node_colors.get(node, "#cccccc"), edgecolors="black", zorder=2)
            ax.text(x, y, node_labels[node], ha="center", va="center", fontsize=9, zorder=3)

        for n1, n2, val in edges:
            x1, y1 = pos.get(n1, (0, 0))
            x2, y2 = pos.get(n2, (0, 0))
            ax.plot([x1, x2], [y1, y2], color="gray", zorder=1)
            ax.text((x1 + x2) / 2, (y1 + y2) / 2, f"{val:.2f}", fontsize=8, ha="center", va="center")

        buf = io.BytesIO()
        fig.savefig(buf, format="png")
        img_data = buf.getvalue()
        nsdata = NSData.dataWithBytes_length_(img_data, len(img_data))
        image = objc.lookUpClass("NSImage").alloc().initWithData_(nsdata) if nsdata else None
        if not image:
            return
        height = self.view.frame().size.height - 60
        self.img_view = NSImageView.alloc().initWithFrame_(NSMakeRect(0, 0, self.view.frame().size.width, height))
        self.img_view.setImage_(image)
        try:
            from AppKit import NSImageScaleProportionallyUpOrDown
            self.img_view.setImageScaling_(NSImageScaleProportionallyUpOrDown)
        except Exception:
            pass
        self.img_view.setAutoresizingMask_(NSViewWidthSizable | NSViewHeightSizable)
        self.view.addSubview_(self.img_view)
