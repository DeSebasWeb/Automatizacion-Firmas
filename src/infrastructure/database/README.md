# Database Models - VerifyID Core

## Architecture Overview

This package contains **SQLAlchemy ORM models** that map to the PostgreSQL database `VerifyID_core`. These are **infrastructure-layer** models, not domain entities.

### Clean Architecture Separation

```
Domain Layer (src/domain/entities/)
         ↓
  [Repository Interface]
         ↓
Infrastructure Layer (src/infrastructure/database/models/)
         ↓
    PostgreSQL Database
```

## Best Practices Implemented

✅ **One class per file** - Each model has its own file (e.g., `user.py`, `invoice.py`)
✅ **Type hints everywhere** - Full type annotations for IDE support
✅ **Explicit relationships** - All relationships use `back_populates` for bidirectional clarity
✅ **Server-side defaults** - UUID generation, timestamps handled by PostgreSQL
✅ **Proper indexing** - Foreign keys and frequently queried fields are indexed
✅ **Cascade deletion** - Parent-child relationships properly configured
✅ **Computed properties** - Business logic as `@property` methods
✅ **Clear documentation** - Every model has docstrings explaining purpose

## Database Schema

### Lookup Tables (Catalogs)

| Table | Model | Description |
|-------|-------|-------------|
| `period_types` | `PeriodType` | Time periods (hourly, daily, monthly, yearly) |
| `resource_types` | `ResourceType` | Billable resources (api_calls, documents, storage) |
| `limit_types` | `LimitType` | Limit types for plans (max_api_calls, max_storage) |
| `subscription_statuses` | `SubscriptionStatus` | Subscription states (active, trial, cancelled, expired) |
| `subscription_billing_cycles` | `SubscriptionBillingCycle` | Billing periods (monthly, quarterly, annual) |
| `invoice_statuses` | `InvoiceStatus` | Invoice states (draft, pending, paid, overdue) |
| `payment_methods` | `PaymentMethod` | Payment methods (credit_card, paypal, stripe) |
| `invoice_item_types` | `InvoiceItemType` | Line item types (subscription_fee, usage_charge, credit) |
| `api_permission_scopes` | `APIPermissionScope` | API scopes (read:user, write:verification, admin:all) |
| `usage_event_types` | `UsageEventType` | Event types (api_call_success, document_processed) |

### Core Entities

| Table | Model | Key Fields |
|-------|-------|------------|
| `users` | `User` | email, password_hash, email_verified, is_active |
| `user_profiles` | `UserProfile` | primer_nombre, apellidos, organizacion, country_code |
| `subscription_plans` | `SubscriptionPlan` | plan_code, precio_mensual_usd, features, limits |

### Subscriptions

| Table | Model | Purpose |
|-------|-------|---------|
| `user_subscriptions` | `UserSubscription` | Links users to plans with billing cycle and status |
| `plan_features` | `PlanFeature` | Features included in each plan |
| `plan_limits` | `PlanLimit` | Resource limits per plan (max API calls, storage, etc.) |

### API Keys

| Table | Model | Purpose |
|-------|-------|---------|
| `api_keys` | `APIKey` | User API keys with hash, prefix, expiration |
| `api_key_scopes` | `APIKeyScope` | Many-to-many: API keys to permission scopes |
| `api_key_custom_limits` | `APIKeyCustomLimit` | Custom limits per API key (overrides plan limits) |

### Usage Tracking

| Table | Model | Purpose |
|-------|-------|---------|
| `usage_events` | `UsageEvent` | Individual usage events with cost calculation |
| `usage_event_metadata` | `UsageEventMetadata` | Key-value metadata for events |
| `usage_counters` | `UsageCounter` | Aggregated counters for rate limiting |

### Invoicing

| Table | Model | Purpose |
|-------|-------|---------|
| `invoices` | `Invoice` | Invoices with totals, taxes, payment status |
| `invoice_line_items` | `InvoiceLineItem` | Line items (subscriptions, usage charges, credits) |

## Relationships Diagram

```
User (1) ──────┬──────> (1) UserProfile
               │
               ├──────> (*) UserSubscription
               │              ↓
               │         SubscriptionPlan (1) ──┬──> (*) PlanFeature
               │                                └──> (*) PlanLimit
               │
               ├──────> (*) APIKey
               │              ├──> (*) APIKeyScope ──> (*) APIPermissionScope
               │              └──> (*) APIKeyCustomLimit
               │
               ├──────> (*) UsageEvent
               │              └──> (*) UsageEventMetadata
               │
               ├──────> (*) UsageCounter
               │
               └──────> (*) Invoice
                              └──> (*) InvoiceLineItem
```

## Usage Examples

### Connecting to Database

```python
from src.infrastructure.database.session import DatabaseSession

# Initialize database connection
db = DatabaseSession(
    database_url="postgresql://user:pass@localhost/VerifyID_core",
    echo=True  # Enable SQL logging
)

# Use context manager for session
with db.get_session() as session:
    user = session.query(User).filter_by(email="test@example.com").first()
    print(user.profile.full_name)
```

### Querying Models

```python
from src.infrastructure.database.models import User, UserSubscription
from sqlalchemy.orm import joinedload

with db.get_session() as session:
    # Eager loading relationships
    user = session.query(User)\
        .options(joinedload(User.profile))\
        .options(joinedload(User.subscriptions))\
        .filter(User.id == user_id)\
        .first()

    # Check subscription status
    active_sub = next(
        (sub for sub in user.subscriptions if sub.is_active),
        None
    )
```

### Creating Records

```python
from src.infrastructure.database.models import User, UserProfile

with db.get_session() as session:
    # Create user with profile
    user = User(
        email="newuser@example.com",
        password_hash="hashed_password_here",
        email_verified=False,
    )

    profile = UserProfile(
        user=user,
        primer_nombre="Juan",
        primer_apellido="Pérez",
        country_code="CO",
    )

    session.add(user)
    # session.commit() happens automatically on context exit
```

## Model Properties and Methods

### User Model

```python
user.is_active  # Boolean field
user.profile  # Related UserProfile (1:1)
user.subscriptions  # List of UserSubscription
user.api_keys  # List of APIKey
```

### UserProfile Model

```python
profile.full_name  # Computed property: "Juan Carlos Pérez López"
```

### UserSubscription Model

```python
subscription.is_active  # Property: checks period_end and cancelled_at
subscription.is_trial  # Property: checks trial_ends_at
```

### APIKey Model

```python
api_key.is_valid  # Property: checks active, revoked, expired
```

### UsageEvent Model

```python
event.calculated_billable_amount  # Property: calculates with markup
```

### UsageCounter Model

```python
counter.is_limit_exceeded  # Property: checks if over limit
counter.remaining_quota  # Property: calculates remaining
```

### Invoice Model

```python
invoice.is_paid  # Property: checks paid_at
invoice.is_overdue  # Property: checks due_at vs now
```

## Important Notes

### 🔒 Security Considerations

- **Never store plaintext passwords** - Always use `password_hash`
- **Never store plaintext API keys** - Always use `key_hash` and `key_prefix`
- **Validate user input** - Don't trust data before inserting

### ⚡ Performance Tips

- Use `joinedload()` or `selectinload()` to avoid N+1 queries
- Index foreign keys (already done)
- Use `usage_counters` for rate limiting (don't scan `usage_events`)
- Batch inserts when possible

### 🏗️ Migrations

These models are designed to work with **Alembic** for database migrations:

```bash
# Generate migration from models
alembic revision --autogenerate -m "Initial schema"

# Apply migration
alembic upgrade head
```

## Next Steps

To complete the hexagonal architecture:

1. **Create Domain Entities** in `src/domain/entities/` (pure Python, no SQLAlchemy)
2. **Create Repository Ports** in `src/domain/ports/` (interfaces)
3. **Create Repository Implementations** in `src/infrastructure/database/repositories/`
4. **Create Use Cases** in `src/application/use_cases/`

Example repository structure:
```python
# src/domain/ports/user_repository_port.py
class UserRepositoryPort(ABC):
    @abstractmethod
    def get_by_email(self, email: str) -> Optional[UserEntity]:
        pass

# src/infrastructure/database/repositories/user_repository.py
class UserRepository(UserRepositoryPort):
    def get_by_email(self, email: str) -> Optional[UserEntity]:
        # Query User model, convert to UserEntity
        pass
```
