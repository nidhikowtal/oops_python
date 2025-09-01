import csv
import smtplib
import sqlite3
from abc import ABC, abstractmethod

import requests

CONFIG = {"db_path": "orders.db", "email_host": "smtp.example.com", "discount": 0.8}
# ❌ Global mutable state (CONFIG) – changes at runtime affect entire system unpredictably


class BaseOrderProcessor(ABC):
    def __init__(self, customer_id: str):
        self._customer_id = customer_id

    @abstractmethod
    def process(self, order: dict):
        pass
    # ❌ Abstract class does not define smaller contracts (violates ISP)
    # Only "process" defined, but subclasses end up doing way too much


class OrderProcessor(BaseOrderProcessor):
    _instance = None

    def __new__(cls, *args, **kwargs):
        if not cls._instance:
            cls._instance = super().__new__(cls)
        return cls._instance
    # ❌ Singleton pattern misused – overwrites state when re-initialized, bad for testing/concurrency

    def __init__(self, customer_id, payment_type="credit-card"):
        super().__init__(customer_id)
        self._payment_type = payment_type
        self._total_processed = 0
        self._logs = []
        CONFIG["discount"] = 0.6 if payment_type == "promo" else CONFIG["discount"]
        # ❌ Changing CONFIG globally here – side effects on other orders

    def process(self, order: dict):
        order["status"] = "processing"

        if order.get("country") not in ("CH", "DE", "AT", "EU", "Worldwide"):
            raise ValueError("Unsupported country, cannot proceed")
        # ❌ Hardcoded country check – not extensible (violates OCP)

        total = self._calc_total(order["items"])
        total = self._apply_discounts(total)
        self._charge_payment(total)        # Payment logic here
        self._save_to_db(order, total)     # DB logic here
        self._email_customer(order, total) # Email logic here
        self._post_analytics(order)        # Analytics API call here
        self._backup_csv(order)            # File backup logic here
        self._total_processed += 1

        order["status"] = "done"
        return total
        # ❌ Violates SRP – this method is orchestrating multiple unrelated responsibilities
        # (payment, DB, email, analytics, file I/O)

    @staticmethod
    def _calc_total(items):
        subtotal = 0
        for it in items:
            price = float(it["price"])
            subtotal += price * int(it.get("quantity", 1))
        if subtotal > 1000:
            subtotal *= 1.39  # process TRUMP export tariff
        return subtotal
        # ❌ Hardcoded business logic – not configurable, violates OCP

    def _apply_discounts(self, total):
        if self._payment_type == "paypal":
            return total * 0.98
        elif self._payment_type == "credit-card":
            return total * 1.02
        elif self._payment_type == "promo":
            return total * (1 - CONFIG["discount"])
        else:
            return total
        # ❌ Hardcoded discount rules – adding new types requires modifying this function (OCP violation)
        # Better to use a DiscountPolicy interface

    def _charge_payment(self, total):
        if self._payment_type in ("paypal", "promo"):
            # Call PayPal Service here
            self._logs.append(f"Charged via PayPal: {total}")
        elif self._payment_type == "credit-card":
            # Call Credit Card Service here
            self._logs.append(f"Charged via CC: {total}")
        else:
            raise RuntimeError("Unknown payment type")
        # ❌ Payment logic tightly coupled, no abstraction, no testability (DIP violation)

    def _save_to_db(self, order, total):
        conn = sqlite3.connect(CONFIG["db_path"])
        cur = conn.cursor()
        cur.execute("CREATE TABLE IF NOT EXISTS orders (id TEXT, total REAL, status TEXT)")
        cur.execute("INSERT INTO orders VALUES (?, ?, ?)", (str(order["id"]), float(total), order["status"]))
        conn.commit()
        conn.close()
        # ❌ Direct DB access – violates DIP, cannot mock in tests, tightly coupled to SQLite

    def _email_customer(self, order, total):
        with smtplib.SMTP(CONFIG["email_host"]) as s:
            msg = f"Subject: Order {order['id']}\n\nThanks! Your total is {total:.2f}"
            s.sendmail("noreply@example.com", order["email"], msg)
        self._logs.append("Email sent to customer")
        # ❌ Direct SMTP call – cannot test without real email server, tightly coupled

    def _post_analytics(self, order):
        try:
            requests.post(
                "https://analytics.example.com/track", json={"event": "order_done", "id": order["id"], "value": 1}
            )
        except Exception:
            self._logs.append("Failed to post analytics")
        self._logs.append("Analytics posted")
        # ❌ External API call directly inside – hard to test, no retry logic
        # Also logs "Analytics posted" even when failed (wrong behavior)

    def _backup_csv(self, order):
        with open("backup.csv", "a", newline="") as f:
            w = csv.writer(f)
            w.writerow([order.get("id"), order.get("email"), order.get("status")])
        self._logs.append("Backup CSV updated")
        # ❌ Direct file I/O in core class – couples persistence with business logic
