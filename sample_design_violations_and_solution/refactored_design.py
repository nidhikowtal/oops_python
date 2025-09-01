import csv
import smtplib
import sqlite3
from abc import ABC, abstractmethod

import requests
# Discount Strategy (Open Close Principle)

class DiscountPolicy(ABC):
    @abstractmethod
    def _apply_discounts(self, total):
        # abstract means child must implement this
        pass

class NoDiscount(DiscountPolicy):
    def _apply_discounts(self, total):
        print("No discount applied")
        return total

class PaypalDiscount(DiscountPolicy):
    def _apply_discounts(self, total):
        print("2% discount for PayPal")
        return total * 0.98

class CreditCardFee(DiscountPolicy):
    def _apply_discounts(self, total):
        print("2% fee for Credit Card")
        return total * 1.02

class PromoDiscount(DiscountPolicy):
    def __init__(self, rate): self.rate = rate
    def _apply_discounts(self, total):
        print(f"Promo discount of {self.rate*100}% applied")
        return total * (1 - self.rate)


# Payment Strategy (Open Close Principle)

class PaymentGateway(ABC):
    @abstractmethod
    def _charge_payment(self, total):
        pass

class PaypalGateway(PaymentGateway):
    def _charge_payment(self, total):
        print(f"✅ Charged {total} via PayPal")

class CreditCardGateway(PaymentGateway):
    def _charge_payment(self, total):
        print(f"✅ Charged {total} via Credit Card")


# Repositories & Services (Dependency Inversion Principle)

class OrderRepository(ABC):
    @abstractmethod
    def _save_to_db(self, order, total):
        pass

class SqliteOrderRepository(OrderRepository):
    def __init__(self, db_path):
        self.db_path = db_path

    def _save_to_db(self, order, total):
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        cursor.execute(
            "INSERT INTO orders (id, email, country, status, total) VALUES (?, ?, ?, ?, ?)",
            (order.id, order.email, order.country, order.status, total)
        )
        conn.commit()
        conn.close()
        print(f"✅ Order {order.id} saved to DB with total {total}")

class NotificationService(ABC):
    @abstractmethod
    def _email_customer(self, order, total):
        pass

class EmailNotification(NotificationService):
    def __init__(self, host):
        self.host = host

    def _email_customer(self, order, total):
        msg = MIMEText(f"Your order {order.id} has been processed. Total: {total}")
        msg["Subject"] = "Order Confirmation"
        msg["From"] = "no-reply@shop.com"
        msg["To"] = order.email

        with smtplib.SMTP(self.host) as server:
            server.send_message(msg)

        print(f"📧 Email sent to {order.email} for order {order.id}")

class AnalyticsService(ABC):
    @abstractmethod
    def track(self, order):
        pass

class HttpAnalytics(AnalyticsService):
    def __init__(self):
        self._logs = []

    def track(self, order):
        try:
            requests.post(
                "https://analytics.example.com/track",
                json={
                    "event": "order_done",
                    "id": order.id,
                    "value": 1,
                    "country": order.country,
                    "email": order.email,
                }
            )
        except Exception:
            self._logs.append(f"⚠️ Failed to post analytics for order {order.id}")
        self._logs.append(f"📊 Analytics posted for order {order.id}")

class BackupService(ABC):
    @abstractmethod
    def backup(self, order):
        pass

class CsvBackup(BackupService):
    def backup(self, order):
        print(f"📝 Backing up order {order.id} to CSV")

# OrderProcessor (Coordinator only → SRP)
class OrderProcessor:
    def __init__(self, discount_policy, payment_gateway,
                 repo, notifier, analytics, backup):
        self.discount_policy = discount_policy
        self.payment_gateway = payment_gateway
        self.repo = repo
        self.notifier = notifier
        self.analytics = analytics
        self.backup = backup

    def process(self, order: Order):
        order.status = "processing"

        # ✅ Business logic only
        total = sum(float(i["price"]) * int(i.get("quantity", 1)) for i in order.items)
        total = self.discount_policy.apply(total)

        self.payment_gateway.charge(total)
        self.repo.save(order, total)
        self.notifier.notify(order, total)
        self.analytics.track(order)
        self.backup.backup(order)

        order.status = "done"
        return total



