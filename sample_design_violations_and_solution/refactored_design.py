# Configuration
class AppConfig:
    def __init__(self, db_path, email_host, discount=0.8):
        self.db_path = db_path
        self.email_host = email_host
        self.discount = discount

# Entities
class Order:
    def __init__(self, order_id, email, items, country):
        self.id = order_id
        self.email = email
        self.items = items
        self.country = country
        self.status = "new"

# Discount Strategy (Open Close Principle)

from abc import ABC, abstractmethod

class DiscountPolicy(ABC):
    @abstractmethod
    def apply(self, total): ...

class NoDiscount(DiscountPolicy):
    def apply(self, total): return total

class PaypalDiscount(DiscountPolicy):
    def apply(self, total): return total * 0.98

class CreditCardFee(DiscountPolicy):
    def apply(self, total): return total * 1.02

class PromoDiscount(DiscountPolicy):
    def __init__(self, rate): self.rate = rate
    def apply(self, total): return total * (1 - self.rate)

# Payment Strategy (Open Close Principle)

class PaymentGateway(ABC):
    @abstractmethod
    def charge(self, total): ...

class PaypalGateway(PaymentGateway):
    def charge(self, total): print(f"Charged {total} via PayPal")

class CreditCardGateway(PaymentGateway):
    def charge(self, total): print(f"Charged {total} via Credit Card")


# Repositories & Services (Dependency Inversion Principle)

class OrderRepository(ABC):
    @abstractmethod
    def save(self, order, total): ...

class SqliteOrderRepository(OrderRepository):
    def __init__(self, db_path): self.db_path = db_path
    def save(self, order, total):
        # DB code here
        pass

class NotificationService(ABC):
    @abstractmethod
    def notify(self, order, total): ...

class EmailNotification(NotificationService):
    def __init__(self, host): self.host = host
    def notify(self, order, total):
        # SMTP code here
        pass

class AnalyticsService(ABC):
    @abstractmethod
    def track(self, order): ...

class HttpAnalytics(AnalyticsService):
    def track(self, order):
        # HTTP POST here
        pass

class BackupService(ABC):
    @abstractmethod
    def backup(self, order): ...

class CsvBackup(BackupService):
    def backup(self, order):
        # Append row to CSV
        pass

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



