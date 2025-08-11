import os
import json
from typing import Any, Dict, List, Tuple

import requests

ACCESS_TOKEN_PATH = "secrest/yandex_key.txt"


class YandexMarketClient:
    """Simple client for Yandex Market Partner API.

    Only minimal functionality is implemented to satisfy the project requirements.
    The client reads the access token from ``ACCESS_TOKEN_PATH`` and performs
    basic requests to the Yandex Market API. If the token file is missing or
    empty the methods will raise an exception.
    """

    def __init__(self, token_path: str = ACCESS_TOKEN_PATH):
        self.token_path = token_path
        self._token: str | None = None

    # ------------------------------------------------------------------ utils
    def _read_token(self) -> str:
        if self._token is not None:
            return self._token
        if not os.path.exists(self.token_path):
            raise FileNotFoundError(f"Token file not found: {self.token_path}")
        with open(self.token_path, "r", encoding="utf-8") as f:
            token = f.read().strip()
        if not token:
            raise ValueError("Token file is empty")
        self._token = token
        return token

    def _headers(self) -> Dict[str, str]:
        token = self._read_token()
        return {
            "Authorization": f"Bearer {token}",
            "Accept": "application/json",
        }

    # ------------------------------------------------------------------ public
    def test_connection(self, config: Dict[str, Any]) -> Tuple[bool, str]:
        """Try to perform a simple request to check that token and seller info
        are valid.

        Returns a tuple ``(success, message)``.
        """

        try:
            headers = self._headers()
        except Exception as exc:  # pragma: no cover - trivial
            return False, str(exc)

        # Yandex Market API has a ``ping`` endpoint. If it is not available we
        # simply report that authentication looks OK.
        url = "https://api.partner.market.yandex.ru/ping"
        try:
            resp = requests.get(url, headers=headers, timeout=5)
            if resp.status_code == 200:
                return True, "Connection successful"
            return False, f"HTTP {resp.status_code}: {resp.text}"
        except Exception as exc:  # pragma: no cover - network errors
            return False, str(exc)

    # ------------------------------------------------------------------
    def fetch_sales(self, config: Dict[str, Any], date_from: str, date_to: str) -> List[Dict[str, Any]]:
        """Fetch sales for the given date range.

        The function parses a subset of the Yandex Market order representation
        and returns a list of dictionaries with the following keys:
        ``order_id``, ``order_date``, ``item_id``, ``item_name``, ``quantity``,
        ``price``, ``currency``.

        On any error an empty list is returned.
        """

        try:
            headers = self._headers()
        except Exception:
            return []

        campaign_id = config.get("campaign_id") or config.get("seller_id")
        if not campaign_id:
            return []

        url = f"https://api.partner.market.yandex.ru/campaigns/{campaign_id}/orders.json"
        params = {
            "dateFrom": date_from,
            "dateTo": date_to,
        }
        try:
            resp = requests.get(url, headers=headers, params=params, timeout=10)
            resp.raise_for_status()
            data = resp.json()
        except Exception:
            return []

        sales: List[Dict[str, Any]] = []
        for order in data.get("orders", []):
            order_id = order.get("id")
            order_date = order.get("creationDate")
            items = order.get("items") or []
            for it in items:
                sales.append(
                    {
                        "order_id": order_id,
                        "order_date": order_date,
                        "item_id": it.get("offerId"),
                        "item_name": it.get("offerName"),
                        "quantity": it.get("count", 1),
                        "price": it.get("price", {}).get("amount", 0.0),
                        "currency": it.get("price", {}).get("currency", "RUR"),
                    }
                )
        return sales


class ProductMappingStore:
    """Persistent storage for mapping Yandex items to ABM products."""

    def __init__(self, path: str = "yandex_product_mappings.json"):
        self.path = path
        self.mappings: Dict[str, str] = {}

    # -------------------------------------------------------------- persistence
    def load(self) -> Dict[str, str]:
        if os.path.exists(self.path):
            with open(self.path, "r", encoding="utf-8") as f:
                self.mappings = json.load(f)
        return self.mappings

    def save(self) -> None:
        with open(self.path, "w", encoding="utf-8") as f:
            json.dump(self.mappings, f, ensure_ascii=False, indent=2)

    def apply(self, raw_sales: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        result: List[Dict[str, Any]] = []
        for rec in raw_sales:
            pid = self.mappings.get(rec.get("item_id"))
            res = dict(rec)
            if pid:
                res["product"] = pid
            result.append(res)
        return result


class ABMImporter:
    """Importer that writes normalized Yandex Market sales into the ABM DB."""

    def __init__(self, db_module):
        self.db = db_module

    def upsert_sales(self, normalized_sales: List[Dict[str, Any]]) -> Dict[str, Any]:
        con = self.db.get_connection()
        cur = con.cursor()
        inserted = 0
        for rec in normalized_sales:
            product = rec.get("product")
            if not product:
                continue
            date = rec.get("order_date")
            qty = rec.get("quantity", 0)
            price = rec.get("price", 0)
            amt = qty * price
            cur.execute(
                "INSERT INTO sales(date, channel, product, cost_amt) VALUES(?, ?, ?, ?)",
                (date, "Yandex Market", product, amt),
            )
            inserted += 1
        con.commit()
        con.close()
        return {"inserted": inserted}
