import json
import os
import objc
from Cocoa import NSObject, NSMakeRect, NSWindow, NSAlert, NSOpenPanel, NSSavePanel, NSTextField, NSButton
from AppKit import (
    NSWindowStyleMaskTitled,
    NSWindowStyleMaskClosable,
    NSBackingStoreBuffered,
    NSViewWidthSizable,
    NSViewHeightSizable,
    NSViewMaxYMargin,
)

from services.yandex_market import YandexMarketClient, ACCESS_TOKEN_PATH

CONFIG_PATH = "yandex_market_config.json"


class YandexMarketConfigWindow(NSObject):
    def init(self):
        self = objc.super(YandexMarketConfigWindow, self).init()
        if self is None:
            return None
        rect = NSMakeRect(200, 200, 400, 240)
        style = NSWindowStyleMaskTitled | NSWindowStyleMaskClosable
        self.window = NSWindow.alloc().initWithContentRect_styleMask_backing_defer_(
            rect, style, NSBackingStoreBuffered, False
        )
        self.window.setTitle_("Configure Yandex Market Extension")
        content = self.window.contentView()

        token_label = NSTextField.labelWithString_(f"Token file: {ACCESS_TOKEN_PATH}")
        token_label.setFrame_(NSMakeRect(10, 200, 380, 20))
        content.addSubview_(token_label)

        seller_label = NSTextField.labelWithString_("Seller ID")
        seller_label.setFrame_(NSMakeRect(10, 170, 100, 20))
        content.addSubview_(seller_label)
        self.seller_field = NSTextField.alloc().initWithFrame_(NSMakeRect(120, 170, 150, 20))
        content.addSubview_(self.seller_field)

        camp_label = NSTextField.labelWithString_("Campaign ID")
        camp_label.setFrame_(NSMakeRect(10, 140, 100, 20))
        content.addSubview_(camp_label)
        self.camp_field = NSTextField.alloc().initWithFrame_(NSMakeRect(120, 140, 150, 20))
        content.addSubview_(self.camp_field)

        from_label = NSTextField.labelWithString_("Default from")
        from_label.setFrame_(NSMakeRect(10, 110, 100, 20))
        content.addSubview_(from_label)
        self.from_field = NSTextField.alloc().initWithFrame_(NSMakeRect(120, 110, 150, 20))
        content.addSubview_(self.from_field)

        to_label = NSTextField.labelWithString_("Default to")
        to_label.setFrame_(NSMakeRect(10, 80, 100, 20))
        content.addSubview_(to_label)
        self.to_field = NSTextField.alloc().initWithFrame_(NSMakeRect(120, 80, 150, 20))
        content.addSubview_(self.to_field)

        save_btn = NSButton.alloc().initWithFrame_(NSMakeRect(10, 10, 80, 30))
        save_btn.setTitle_("Save")
        save_btn.setTarget_(self)
        save_btn.setAction_("save:")
        content.addSubview_(save_btn)

        test_btn = NSButton.alloc().initWithFrame_(NSMakeRect(100, 10, 120, 30))
        test_btn.setTitle_("Test connection")
        test_btn.setTarget_(self)
        test_btn.setAction_("test:")
        content.addSubview_(test_btn)

        export_btn = NSButton.alloc().initWithFrame_(NSMakeRect(230, 10, 70, 30))
        export_btn.setTitle_("Export")
        export_btn.setTarget_(self)
        export_btn.setAction_("export:")
        content.addSubview_(export_btn)

        import_btn = NSButton.alloc().initWithFrame_(NSMakeRect(310, 10, 70, 30))
        import_btn.setTitle_("Import")
        import_btn.setTarget_(self)
        import_btn.setAction_("import:")
        content.addSubview_(import_btn)

        self.load_config()
        return self

    # ------------------------------------------------------------------ helpers
    def load_config(self):
        if os.path.exists(CONFIG_PATH):
            with open(CONFIG_PATH, "r", encoding="utf-8") as f:
                cfg = json.load(f)
            self.seller_field.setStringValue_(cfg.get("seller_id", ""))
            self.camp_field.setStringValue_(cfg.get("campaign_id", ""))
            self.from_field.setStringValue_(cfg.get("date_from", ""))
            self.to_field.setStringValue_(cfg.get("date_to", ""))

    def current_config(self) -> dict:
        return {
            "seller_id": self.seller_field.stringValue(),
            "campaign_id": self.camp_field.stringValue(),
            "date_from": self.from_field.stringValue(),
            "date_to": self.to_field.stringValue(),
        }

    def show(self):
        self.window.makeKeyAndOrderFront_(None)

    # ------------------------------------------------------------------ actions
    def save_(self, sender):
        cfg = self.current_config()
        with open(CONFIG_PATH, "w", encoding="utf-8") as f:
            json.dump(cfg, f, ensure_ascii=False, indent=2)

    def test_(self, sender):
        cfg = self.current_config()
        client = YandexMarketClient()
        success, message = client.test_connection(cfg)
        alert = NSAlert.alloc().init()
        if success:
            alert.setMessageText_("Success")
        else:
            alert.setMessageText_("Error")
        alert.setInformativeText_(message)
        alert.runModal()

    def export_(self, sender):
        panel = NSSavePanel.savePanel()
        if panel.runModal() == 0:
            return
        path = panel.URL().path()
        with open(path, "w", encoding="utf-8") as f:
            json.dump(self.current_config(), f, ensure_ascii=False, indent=2)

    def import_(self, sender):
        panel = NSOpenPanel.openPanel()
        if panel.runModal() == 0:
            return
        path = panel.URLs()[0].path()
        try:
            with open(path, "r", encoding="utf-8") as f:
                cfg = json.load(f)
            self.seller_field.setStringValue_(cfg.get("seller_id", ""))
            self.camp_field.setStringValue_(cfg.get("campaign_id", ""))
            self.from_field.setStringValue_(cfg.get("date_from", ""))
            self.to_field.setStringValue_(cfg.get("date_to", ""))
        except Exception as exc:  # pragma: no cover - trivial UI
            alert = NSAlert.alloc().init()
            alert.setMessageText_("Error")
            alert.setInformativeText_(str(exc))
            alert.runModal()
