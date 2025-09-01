# Design Flaws in OrderProcessor

## Violations of SOLID Principles

### 1. Single Responsibility Principle (SRP)
- **Problem**: `OrderProcessor` class does everything:
  - Calculates totals
  - Applies discounts
  - Handles payments
  - Talks to DB
  - Sends emails
  - Calls external analytics API
  - Writes CSV backups  
- **Why it’s wrong**: Each of these is a separate responsibility and should be handled by different classes/services.

---

### 2. Open/Closed Principle (OCP)
- **Problem**: Discounts and payment methods are hardcoded in `_apply_discounts()` and `_charge_payment()`.
- **Impact**: Adding a new payment type or discount requires modifying the existing class, not extending it.
- **Fix**: Use **strategy pattern** for payment and discount handling.

---

### 3. Liskov Substitution Principle (LSP)
- **Problem**: `BaseOrderProcessor` is an abstract class but isn’t really substitutable:
  - Only one concrete implementation (`OrderProcessor`).
  - If we add another processor (say `BulkOrderProcessor`), `__new__` Singleton logic in `OrderProcessor` breaks polymorphism.

---

### 4. Interface Segregation Principle (ISP)
- **Problem**: `BaseOrderProcessor` has just `process()`, but `OrderProcessor` has many hidden internal behaviors (`_charge_payment`, `_post_analytics`, `_save_to_db`).
- **Impact**: Interface is too broad and doesn’t separate roles.
- **Fix**: Introduce smaller, role-specific interfaces:
  - `PaymentGateway`
  - `DiscountPolicy`
  - `OrderRepository`
  - `NotificationService`

---

### 5. Dependency Inversion Principle (DIP)
- **Problem**: Class depends directly on low-level modules:
  - `sqlite3`, `smtplib`, `requests`, file system.
- **Impact**: No abstraction → unit testing impossible without hitting real services.
- **Fix**: Depend on interfaces/abstract services, inject them from outside.

---

## Other Design Issues

### Global Mutable State
- **Problem**: Changing payment type mutates global `CONFIG` dictionary → side effects across system.
- **Fix**: Should be immutable or injected as config.

---

### Singleton Misuse
- **Problem**: `OrderProcessor` is Singleton (`__new__` with `_instance`):
  - Still takes `customer_id` in constructor → state overwritten each time.
  - Breaks testability and concurrency.
- **Fix**: Should not be Singleton — processors should be instantiated per request.

---

### Testing Concerns
- **Problem**: Direct use of `sqlite3`, `smtplib`, `requests` makes unit tests impossible.
- **Fix**: Inject abstractions and mock in tests.

---

### Error Handling
- **Problem**: Analytics POST swallows exceptions silently (`except Exception:`) but still logs “Analytics posted”.
- **Impact**: Misleading and brittle in production.
- **Fix**: Add robust error handling and retries.

---

### Tight Coupling
- **Problem**: Monolithic class, all logic tightly coupled.
- **Impact**: Impossible to replace one part (e.g., switch DB to PostgreSQL).
- **Fix**: Break into small, cohesive classes.

---

## ✅ How Should It Be Refactored?

### Introduce Abstractions
- `PaymentGateway` (PayPal, CreditCard, Promo as strategies).
- `DiscountPolicy` (different discount rules).
- `OrderRepository` (DB interactions).
- `NotificationService` (email).
- `AnalyticsTracker`.
- `BackupService`.

### Use Dependency Injection
- Inject services into `OrderProcessor` instead of hardcoding.

### Follow SRP
- Each class should have one job.

### Make it Testable
- Replace `sqlite3`, `smtplib`, `requests` with mocks in unit tests.

---
