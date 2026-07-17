# MediSafe Database Documentation

**Project:** MediSafe — Drug Interaction & Medication Management System
**Version:** 1.0.0
**Database:** Django ORM (SQL / PostgreSQL compatible)

---

## Table of Contents

1. [Database Schema Overview](#1-database-schema-overview)
2. [Users & Authentication Tables](#2-users--authentication-tables)
3. [OAuth Tables](#3-oauth-tables)
4. [Drug & Interaction Tables](#4-drug--interaction-tables)
5. [User Data Tables](#5-user-data-tables)
6. [Utility Tables](#6-utility-tables)
7. [Relationships & Foreign Keys](#7-relationships--foreign-keys)
8. [Indexes](#8-indexes)
9. [Triggers & Auto-functions](#9-triggers--auto-functions)
10. [Data Types Reference](#10-data-types-reference)
11. [Transaction Management](#11-transaction-management)
12. [Query Optimization Notes](#12-query-optimization-notes)
13. [Data Integrity & Constraints](#13-data-integrity--constraints)
14. [Sample Queries](#14-sample-queries)
15. [Custom Manager Methods Usage](#15-custom-manager-methods-usage)
16. [Migration Notes](#16-migration-notes)
17. [Security Considerations](#17-security-considerations)
18. [Deployment Checklist](#18-deployment-checklist)
19. [Troubleshooting](#19-troubleshooting)
20. [Data Retention Policy](#20-data-retention-policy)

---

## 1. Database Schema Overview

| # | Table | Description |
|---|---|---|
| 1 | `Users` | Core user account data |
| 2 | `UserProfile` | User preferences and settings |
| 3 | `OAuthAccount` | OAuth authentication data |
| 4 | `Drug` | Drug information from DrugBank |
| 5 | `Drug_Interactions` | Drug interaction records |
| 6 | `UserHistory` | User's interaction check history |
| 7 | `UserMedications` | User's personal medications |
| 8 | `OTP` | One-time password storage |
| 9 | `NotificationTrigger` | User notification tracking |

---

## 2. Users & Authentication Tables

### 2.1 Users Table

Primary table for all user accounts.

| Field | Type | Constraints | Description |
|---|---|---|---|
| `id` | UUID | Primary key, not null, indexed | Unique identifier |
| `full_name` | VARCHAR(255) | Not null | User's full name |
| `pass_hash` | VARCHAR(255) | Nullable | Hashed password |
| `email` | VARCHAR(255) | Unique, nullable, blank | User's email address |
| `created_at` | DATETIME | Auto-now-add | Account creation timestamp |
| `last_logged_in_at` | DATETIME | Nullable, blank | Last login timestamp |
| `is_oauth_user` | BOOLEAN | Default: `False` | OAuth authentication flag |

**Indexes**
- `email` (for fast user lookup)

**Manager Methods**
- `create_user_and_profile(email, full_name, password)` — Creates user with profile
- `update_user_settings(user_id, ...)` — Updates user and profile settings
- `create_oauth_user_and_profile(...)` — Creates OAuth user with profile

**Instance Methods**
- `update_last_login()` — Updates `last_logged_in_at` to current time
- `has_password()` — Returns `True` if password hash exists

---

### 2.2 UserProfile Table

One-to-one relationship with `Users`.

| Field | Type | Constraints | Description |
|---|---|---|---|
| `user` | OneToOneField | Primary key, cascade delete | Reference to `Users` |
| `profile_image` | ImageField | Nullable, blank, validator: jpg/jpeg/png | User's profile picture |
| `two_factor_auth` | BOOLEAN | Default: `False` | 2FA enabled status |
| `safety_alerts` | BOOLEAN | Default: `False` | High-priority safety alerts |
| `monthly_usage_reports` | BOOLEAN | Default: `False` | Monthly usage reports |
| `updated_at` | DATETIME | Auto-now | Last update timestamp |

**Methods**
- `__str__()` — Returns `"Profile of [user.full_name]"`

**Metadata**
- `verbose_name`: "User Profile"
- `verbose_name_plural`: "User Profiles"

---

## 3. OAuth Tables

### 3.1 OAuthAccount Table

Stores OAuth authentication data for third-party providers.

| Field | Type | Constraints | Description |
|---|---|---|---|
| `id` | UUID | Primary key, not null | Unique identifier |
| `user` | ForeignKey | Not null, cascade delete | Reference to `Users` |
| `provider` | VARCHAR(50) | Not null, choices | `'google'` or `'github'` |
| `provider_user_id` | VARCHAR(255) | Not null | ID from OAuth provider |
| `access_token` | TEXT | Not null | OAuth access token |
| `refresh_token` | TEXT | Nullable, blank | OAuth refresh token |
| `token_expires_at` | DATETIME | Nullable, blank | Token expiration time |
| `provider_name` | VARCHAR(255) | Not null | Full name from provider |
| `created_at` | DATETIME | Auto-now-add | When account was linked |
| `updated_at` | DATETIME | Auto-now | Last update timestamp |

**Unique Constraints**
- `(provider, provider_user_id)` — Unique together

**Indexes**
- `(provider, provider_user_id)` — For OAuth lookups
- `(user, provider)` — For a user's OAuth accounts

**Methods**
- `is_token_valid()` — Returns `True` if token hasn't expired

---

## 4. Drug & Interaction Tables

### 4.1 Drug Table

Drug information from the DrugBank database.

| Field | Type | Constraints | Description |
|---|---|---|---|
| `drug_bank_id` | VARCHAR(50) | Primary key, unique | DrugBank identifier |
| `common_name` | VARCHAR | Unique | Common drug name |
| `synonyms` | VARCHAR | Not null | Drug synonyms |
| `smile_structure` | VARCHAR | Not null | Chemical structure |

**Indexes**
- `drug_common_name_lower_idx`: `Lower(common_name)` for case-insensitive search

**Methods**
- `__str__()` — Returns `"[common_name], [drug_bank_id]"`

---

### 4.2 Drug_Interactions Table

Stores drug interaction data.

| Field | Type | Constraints | Description |
|---|---|---|---|
| `id` | AutoField | Primary key, not null | Auto-incrementing ID |
| `first_drug` | ForeignKey | Not null, cascade delete | Reference to `Drug` |
| `second_drug` | ForeignKey | Not null, cascade delete | Reference to `Drug` |
| `description` | TEXT | Not null | Interaction description |
| `severity` | VARCHAR(20) | Not null | `'Low'`, `'Moderate'`, `'High'` |
| `severity_level` | INTEGER | Not null | `0` = Low, `1` = Moderate, `2` = High |

**Indexes**
- `(first_drug, second_drug)` — For interaction lookups

**Manager Methods (`InteractionManager`)**
- `create_interaction_and_history(user, drug1, drug2, description, severity, severityLevel, dateTime)` — Creates interaction and history entry
- `create_history_of_interaction(user, interaction, dateTime)` — Creates history entry for an existing interaction

---

## 5. User Data Tables

### 5.1 UserHistory Table

Tracks a user's drug interaction checks.

| Field | Type | Constraints | Description |
|---|---|---|---|
| `id` | AutoField | Primary key, not null | Auto-incrementing ID |
| `user` | ForeignKey | Not null, cascade delete | Reference to `Users` |
| `date_time` | DATETIME | Auto-now-add | Check timestamp |
| `interaction` | ForeignKey | Not null, cascade delete | Reference to `Drug_Interactions` |

**Indexes**
- `(user, -date_time)` — For user history queries
- Ordering: `['-date_time']` (newest first)

**Methods**
- `__str__()` — Returns formatted `date_time`

---

### 5.2 UserMedications Table

User's personal medication list.

| Field | Type | Constraints | Description |
|---|---|---|---|
| `id` | AutoField | Primary key, not null | Auto-incrementing ID |
| `user` | ForeignKey | Not null, cascade delete | Reference to `Users` |
| `name` | VARCHAR(100) | Not null | Medication name |
| `dosage_amount_mg` | DECIMAL(8,2) | Not null | Dosage in milligrams |
| `dosage_frequency` | VARCHAR(100) | Default: `'unknown'` | How often to take |
| `last_refill` | DATETIME | Auto-now-add | Last refill date |
| `active` | BOOLEAN | Default: `True` | Currently active status |
| `category` | VARCHAR(100) | Default: `'UnIdentified'` | Drug category |
| `medication_more` | TEXT | Default: `''` | Additional notes |

**Indexes**
- `(user, last_refill)` — For medication queries by user

**Methods**
- `__str__()` — Returns `"[name], [dosage_amount_mg], [dosage_frequency]"`

---

## 6. Utility Tables

### 6.1 OTP Table

One-time password storage for 2FA and password reset.

| Field | Type | Constraints | Description |
|---|---|---|---|
| `id` | AutoField | Primary key, not null | Auto-incrementing ID |
| `email` | TEXT | Unique, not null | User's email address |
| `otp` | VARCHAR(5) | Not null | 5-digit OTP code |
| `expiration_time` | DATETIME | Not null | When OTP expires |
| `attempts` | INTEGER | Default: `0` | Number of attempts |

**Manager Methods (`OTPManager`)**
- `remove_and_create(email, otpval, expiration_time)` — Deletes existing OTP and creates a new one
- `incrementAttempt(otpObj)` — Increments attempt counter
- `removeExpiredOTP()` — Deletes all expired OTPs

**Methods**
- `__str__()` — Returns detailed OTP information

---

### 6.2 NotificationTrigger Table

Tracks monthly notification triggers.

| Field | Type | Constraints | Description |
|---|---|---|---|
| `id` | AutoField | Primary key, not null | Auto-incrementing ID |
| `user` | OneToOneField | Not null, cascade delete | Reference to `Users` |
| `notified_date` | DATETIME | Auto-now-add | Last notification date |

**Manager Methods (`NotificationManager`)**
- `shouldNotificationTrigger(noti)` — Checks if notification should trigger (returns `True` if new month)
- `afterNotificationTriggered(noti)` — Updates `notified_date` to current time

**Methods**
- `__str__()` — Returns `"[notified_date]"`

---

## 7. Relationships & Foreign Keys

### 7.1 One-to-One Relationships

| Relationship | Detail |
|---|---|
| `Users` ↔ `UserProfile` | `Users.user_profile` (OneToOne) / `UserProfile.user` (ForeignKey, CASCADE) |
| `Users` ↔ `NotificationTrigger` | `Users.notification_trigger` (OneToOne) / `NotificationTrigger.user` (ForeignKey, CASCADE) |

### 7.2 One-to-Many Relationships

| Relationship | Detail |
|---|---|
| `Users` → `OAuthAccount` | `Users.oauth_accounts` (Many) / `OAuthAccount.user` (ForeignKey, CASCADE) |
| `Users` → `UserHistory` | `Users.history` (Many) / `UserHistory.user` (ForeignKey, CASCADE) |
| `Users` → `UserMedications` | `Users.usersMedications` (Many) / `UserMedications.user` (ForeignKey, CASCADE) |
| `Drug` → `Drug_Interactions` (as `first_drug`) | `Drug.first_drug` (Many) / `Drug_Interactions.first_drug` (ForeignKey, CASCADE) |
| `Drug` → `Drug_Interactions` (as `second_drug`) | `Drug.second_drug` (Many) / `Drug_Interactions.second_drug` (ForeignKey, CASCADE) |
| `Drug_Interactions` → `UserHistory` | `Drug_Interactions.interaction` (Many) / `UserHistory.interaction` (ForeignKey, CASCADE) |

### 7.3 Cascade Delete Rules

- All foreign keys use `CASCADE` delete
- Deleting a `User` deletes all related data:
  - Profile
  - OAuth accounts
  - History
  - Medications
  - Notification trigger
- Deleting a `Drug` deletes related interactions
- Deleting an interaction deletes related history records

---

## 8. Indexes

### 8.1 Primary Keys

| Table | Primary Key |
|---|---|
| `Users` | `id` (UUID, indexed) |
| `OAuthAccount` | `id` (UUID) |
| `Drug` | `drug_bank_id` (VARCHAR) |
| `Drug_Interactions` | `id` (AutoField) |
| `UserHistory` | `id` (AutoField) |
| `UserMedications` | `id` (AutoField) |
| `OTP` | `id` (AutoField) |
| `NotificationTrigger` | `id` (AutoField) |

### 8.2 Foreign Key Indexes (auto-created by Django)

- `UserProfile.user`
- `OAuthAccount.user`
- `OAuthAccount.provider` + `provider_user_id` (unique together)
- `Drug_Interactions.first_drug`
- `Drug_Interactions.second_drug`
- `UserHistory.user`
- `UserHistory.interaction`
- `UserMedications.user`
- `NotificationTrigger.user`

### 8.3 Custom Indexes

- `Users`: `email` (for login lookups)
- `Drug`: `drug_common_name_lower_idx` (`Lower(common_name)`)
- `Drug_Interactions`: `(first_drug, second_drug)`
- `UserHistory`: `(user, -date_time)` with ordering
- `UserMedications`: `(user, last_refill)`
- `OAuthAccount`: `(provider, provider_user_id)`
- `OAuthAccount`: `(user, provider)`

---

## 9. Triggers & Auto-functions

### 9.1 Auto-populated Fields

- `created_at` — Set automatically on record creation
- `last_refill` — Set automatically on medication creation
- `updated_at` — Updates automatically on record save
- `last_logged_in_at` — Updated manually via `update_last_login()`
- `notified_date` — Set on `NotificationTrigger` creation

### 9.2 Manager Methods

**`UserManager`**
- `create_user_and_profile()` — Creates user + profile in transaction
- `update_user_settings()` — Updates user + profile in transaction
- `create_oauth_user_and_profile()` — Creates OAuth user in transaction

**`InteractionManager`**
- `create_interaction_and_history()` — Creates interaction + history in transaction
- `create_history_of_interaction()` — Creates history for existing interaction

**`OTPManager`**
- `remove_and_create()` — Ensures only one OTP per email
- `incrementAttempt()` — Tracks failed attempts
- `removeExpiredOTP()` — Cleans expired OTPs

**`NotificationManager`**
- `shouldNotificationTrigger()` — Checks if notification is due
- `afterNotificationTriggered()` — Updates notification timestamp

---

## 10. Data Types Reference

### 10.1 String Fields

| Type | Used For |
|---|---|
| `VARCHAR(50)` | DrugBank ID, OAuth provider |
| `VARCHAR(100)` | Medication name, dosage frequency, category |
| `VARCHAR(255)` | Full name, password hash, provider_user_id |
| `TEXT` | OTP email, OAuth tokens, description, medication_more |
| `EmailField` | User email (validated) |
| `ImageField` | Profile image (validated for jpg/jpeg/png) |

### 10.2 Numeric Fields

| Type | Used For |
|---|---|
| `IntegerField` | `severity_level`, OTP attempts |
| `DecimalField(8,2)` | `dosage_amount_mg` (max `99999.99`) |
| `AutoField` | Auto-incrementing IDs |
| `BooleanField` | True/False flags |

### 10.3 Date/Time Fields

| Type | Notes |
|---|---|
| `DateTimeField` | Timestamps with timezone support |
| `DateField` | Not used directly (datetime used instead) |

### 10.4 UUID Fields

- `Users.id` — UUID primary key
- `OAuthAccount.id` — UUID primary key

### 10.5 Special Fields

- `ForeignKey` — Database relationships with cascade delete
- `OneToOneField` — One-to-one relationships
- `ImageField` — File upload with image validation

---

## 11. Transaction Management

### 11.1 Atomic Transactions

All manager methods that modify multiple tables use:

```python
with transaction.atomic():
    # Multiple database operations
    # All succeed or all rollback
```

### 11.2 Transaction Examples

- `create_user_and_profile()` — Creates `User` + `Profile`
- `update_user_settings()` — Updates `User` + `Profile`
- `create_oauth_user_and_profile()` — Creates/updates `OAuthAccount` + `User` + `Profile`
- `create_interaction_and_history()` — Creates `Interaction` + `History`

---

## 12. Query Optimization Notes

### 12.1 Use `select_related()` for Foreign Keys

```python
# Good:
history = UserHistory.objects.select_related(
    'interaction',
    'interaction__first_drug',
    'interaction__second_drug'
)

# Avoid N+1 queries
```

### 12.2 Use `only()` for Specific Fields

```python
# Good:
UserHistory.objects.only(
    'id', 'date_time',
    'interaction__severity',
    'interaction__first_drug__common_name'
)

# Reduces data transfer
```

### 12.3 Use Pagination for Large Datasets

```python
from django.core.paginator import Paginator
paginator = Paginator(query_set, per_page)
```

### 12.4 Indexed Fields for Filters

```python
# Efficient queries use indexed fields:
UserHistory.objects.filter(user=user)              # (user, -date_time) index
Drug.objects.filter(common_name__icontains=search)  # Lower index
```

---

## 13. Data Integrity & Constraints

### 13.1 Unique Constraints

- `Users.email` — Unique
- `Drug.common_name` — Unique
- `Drug.drug_bank_id` — Unique
- `OTP.email` — Unique
- `(OAuthAccount.provider, OAuthAccount.provider_user_id)` — Unique together

### 13.2 Required Fields (NOT NULL)

- All primary keys (not null)
- `Users.full_name` (not null)
- `Drug_Interactions.first_drug`, `second_drug` (not null)
- All `UserHistory` fields (not null)
- `OTP.otp`, `OTP.expiration_time` (not null)

### 13.3 Default Values

| Field | Default |
|---|---|
| `Users.is_oauth_user` | `False` |
| `UserProfile.two_factor_auth` | `False` |
| `UserProfile.safety_alerts` | `False` |
| `UserProfile.monthly_usage_reports` | `False` |
| `UserMedications.dosage_frequency` | `'unknown'` |
| `UserMedications.active` | `True` |
| `UserMedications.category` | `'UnIdentified'` |
| `UserMedications.medication_more` | `''` |
| `OTP.attempts` | `0` |

### 13.4 ON DELETE Behavior

- **All foreign keys:** `CASCADE` — deleting a parent deletes all children

---

## 14. Sample Queries

### 14.1 Get User with Profile

```python
user = Users.objects.select_related('profile').get(id=user_id)
```

### 14.2 Get User's History with Details

```python
history = UserHistory.objects.filter(
    user=user
).select_related(
    'interaction',
    'interaction__first_drug',
    'interaction__second_drug'
).order_by('-date_time')
```

### 14.3 Get Active Medications

```python
medications = UserMedications.objects.filter(
    user=user,
    active=True
)
```

### 14.4 Check if Email Exists

```python
exists = Users.objects.filter(email=email).exists()
```

### 14.5 Check OAuth User

```python
user = Users.objects.get(email=email)
if user.is_oauth_user:
    # Handle OAuth user
    pass
```

### 14.6 Check Drug Interaction Exists

```python
interaction = Drug_Interactions.objects.filter(
    first_drug=drug1,
    second_drug=drug2
).first()
```

---

## 15. Custom Manager Methods Usage

### 15.1 Creating a New User

```python
from django.db import transaction

with transaction.atomic():
    user = Users.objects.create_user_and_profile(
        email="user@example.com",
        full_name="John Doe",
        password="securepassword123"
    )
```

### 15.2 Creating an OAuth User

```python
user = Users.objects.create_oauth_user_and_profile(
    full_name="Jane Doe",
    provider="google",
    provider_user_id="12345",
    access_token="abc123",
    provider_name="Google"
)
```

### 15.3 Updating User Settings

```python
user = Users.objects.update_user_settings(
    user_id=user_id,
    full_name="New Name",
    safety_alerts=True,
    two_factor_auth=True
)
```

### 15.4 Creating Interaction with History

```python
history = Drug_Interactions.objects.create_interaction_and_history(
    user=user,
    drug1="DB00945",
    drug2="DB00682",
    description="Interaction description",
    severity="High",
    severityLevel=2,
    dateTime=timezone.now()
)
```

### 15.5 Creating History Only

```python
history = Drug_Interactions.objects.create_history_of_interaction(
    user=user,
    interaction=interaction_obj,
    dateTime=timezone.now()
)
```

### 15.6 OTP Management

```python
# Create new OTP
otp = OTP.objects.remove_and_create(
    email="user@example.com",
    otpval="12345"
)

# Check and increment attempts
otp_obj = OTP.objects.get(email="user@example.com")
if otp_obj.attempts < MAX_OTP_ATTEMPTS:
    OTP.objects.incrementAttempt(otp_obj)

# Clean expired OTPs
OTP.objects.removeExpiredOTP()
```

### 15.7 Notification Management

```python
# Check if notification should trigger
notification = NotificationTrigger.objects.get(user=user)
if NotificationTrigger.objects.shouldNotificationTrigger(notification):
    # Send notification
    NotificationTrigger.objects.afterNotificationTriggered(notification)
```

---

## 16. Migration Notes

### 16.1 App Name

App name is not explicitly set but appears to be the main app.

### 16.2 Migration Dependencies

Django will automatically create migration files.

### 16.3 Backward Compatibility

All constraints and defaults are designed for backward compatibility.

### 16.4 Database Engine

Compatible with:
- PostgreSQL (recommended for production)
- MySQL
- SQLite (development)

---

## 17. Security Considerations

### 17.1 Password Storage

- Passwords stored as hashes (`helpers.hash_password`)
- Never store plaintext passwords
- OAuth users have `NULL` `pass_hash`

### 17.2 OAuth Tokens

- Access tokens stored encrypted (should be, in production)
- Refresh tokens stored with optional expiry
- Token expiration tracked

### 17.3 OTP Security

- 5-digit numeric codes
- Expiration time (default: 20 minutes)
- Attempt limiting (5 attempts max)
- Single-use (deleted after verification)

### 17.4 User Data Protection

- Foreign keys with `CASCADE` prevent orphaned records
- All user data deletable via `user.delete()`
- Email field has unique constraint

---

## 18. Deployment Checklist

### 18.1 Before Migration

- [ ] Review and adjust `MAX_OTP_ATTEMPTS` in settings
- [ ] Configure OTP expiration time (default: 20 minutes)
- [ ] Set up media storage for profile images
- [ ] Configure email backend for OTP
- [ ] Set up OAuth credentials

### 18.2 Database Setup

- [ ] Run migrations: `python manage.py migrate`
- [ ] Create superuser: `python manage.py createsuperuser`
- [ ] Test OTP functionality
- [ ] Test OAuth login flow
- [ ] Import initial drug data

### 18.3 Performance Tuning

- [ ] Add database indexes (auto-created)
- [ ] Configure database connection pooling
- [ ] Set up caching for drug lookups
- [ ] Optimize history queries with `select_related`

---

## 19. Troubleshooting

### 19.1 Common Errors

| Error | Cause |
|---|---|
| "A user with this email already exists" | Email is unique |
| "User not authenticated" | Missing or expired session |
| "Drug not found in the Database" | DrugBank ID doesn't exist |
| "Invalid OTP" | OTP expired or incorrect |
| "IntegrityError" | Duplicate OAuth account or email |

### 19.2 Debug Tips

- Check database logs for SQL errors
- Use Django Debug Toolbar for query analysis
- Monitor OTP attempts to prevent brute force
- Verify OAuth callback URLs match configuration

---

## 20. Data Retention Policy

### 20.1 OTP Records

- Automatically removed after expiration
- Removed after successful verification
- Cleaned by `removeExpiredOTP()`

### 20.2 User Data

- User data persists until user deletes account
- All related data deleted via `CASCADE`
- No soft delete implemented

### 20.3 History Records

- Preserved indefinitely
- No automatic cleanup
- Users can export and delete manually

---

*End of database documentation*
