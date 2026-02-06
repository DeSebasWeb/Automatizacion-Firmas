"""
Database models package - SQLAlchemy ORM models.

BEST PRACTICES IMPLEMENTED:
✅ One class per file (single responsibility)
✅ Type hints everywhere
✅ Explicit relationships with back_populates
✅ Server-side defaults for timestamps and UUIDs
✅ Proper indexing on foreign keys and frequently queried fields
✅ Cascade deletion where appropriate
✅ Properties for computed values
✅ Clear docstrings

ARCHITECTURE NOTES:
- These are INFRASTRUCTURE models (SQLAlchemy/PostgreSQL specific)
- Domain entities live in src/domain/entities/
- Repositories translate between infrastructure models and domain entities
- Never import these models directly in domain or application layers
"""

# Lookup/Catalog Tables (reference data)
from src.infrastructure.database.models.period_type import PeriodType
from src.infrastructure.database.models.resource_type import ResourceType
from src.infrastructure.database.models.limit_type import LimitType
from src.infrastructure.database.models.subscription_status import SubscriptionStatus
from src.infrastructure.database.models.subscription_billing_cycle import (
    SubscriptionBillingCycle,
)
from src.infrastructure.database.models.invoice_status import InvoiceStatus
from src.infrastructure.database.models.payment_method import PaymentMethod
from src.infrastructure.database.models.invoice_item_type import InvoiceItemType
from src.infrastructure.database.models.usage_event_type import UsageEventType

# Permission System (NEW)
from src.infrastructure.database.models.document_type import DocumentType
from src.infrastructure.database.models.permission_type import PermissionType
from src.infrastructure.database.models.api_permission_scope import APIPermissionScope

# Core Entities
from src.infrastructure.database.models.user import User
from src.infrastructure.database.models.user_profile import UserProfile
from src.infrastructure.database.models.subscription_plan import SubscriptionPlan

# Subscription Models
from src.infrastructure.database.models.user_subscription import UserSubscription
from src.infrastructure.database.models.plan_feature import PlanFeature
from src.infrastructure.database.models.plan_limit import PlanLimit

# API Key Models
from src.infrastructure.database.models.api_key import APIKey
from src.infrastructure.database.models.api_key_scope import APIKeyScope
from src.infrastructure.database.models.api_key_custom_limit import APIKeyCustomLimit

# Usage Tracking Models
from src.infrastructure.database.models.usage_event import UsageEvent
from src.infrastructure.database.models.usage_event_metadata import UsageEventMetadata
from src.infrastructure.database.models.usage_counter import UsageCounter

# Invoice Models
from src.infrastructure.database.models.invoice import Invoice
from src.infrastructure.database.models.invoice_line_item import InvoiceLineItem

__all__ = [
    # Lookup Tables
    "PeriodType",
    "ResourceType",
    "LimitType",
    "SubscriptionStatus",
    "SubscriptionBillingCycle",
    "InvoiceStatus",
    "PaymentMethod",
    "InvoiceItemType",
    "UsageEventType",
    # Permission System
    "DocumentType",
    "PermissionType",
    "APIPermissionScope",
    # Core Entities
    "User",
    "UserProfile",
    "SubscriptionPlan",
    # Subscription Models
    "UserSubscription",
    "PlanFeature",
    "PlanLimit",
    # API Key Models
    "APIKey",
    "APIKeyScope",
    "APIKeyCustomLimit",
    # Usage Tracking
    "UsageEvent",
    "UsageEventMetadata",
    "UsageCounter",
    # Invoices
    "Invoice",
    "InvoiceLineItem",
]
