# MediSafe API Documentation

**Project:** MediSafe — Drug Interaction & Medication Management System

---

## Table of Contents

1. [Authentication](#1-authentication)
2. [User Management](#2-user-management)
3. [Drug Interactions](#3-drug-interactions)
4. [Medication Management](#4-medication-management)
5. [History & Reports](#5-history--reports)
6. [Export Functions](#6-export-functions)
7. [Utility APIs](#7-utility-apis)
8. [Error Codes](#8-error-codes)
9. [Authentication Requirements](#9-authentication-requirements)
10. [File Upload Restrictions](#10-file-upload-restrictions)
11. [Sample Requests](#11-sample-requests)
12. [Database Models Reference](#12-database-models-reference)
13. [Notes & Disclaimers](#13-notes--disclaimers)
14. [Contact & Support](#14-contact--support)

---

## 1. Authentication

### 1.1 User Registration

|                 |                             |
| --------------- | --------------------------- |
| **Endpoint**    | `/register/`                |
| **Method**      | `POST`                      |
| **Description** | Register a new user account |

**Parameters (form-data)**

| Parameter          | Required | Description                    |
| ------------------ | -------- | ------------------------------ |
| `fullname`         | Yes      | User's full name (min 4 chars) |
| `email`            | Yes      | Valid email address            |
| `password`         | Yes      | Password (min 8 chars)         |
| `confirm_password` | Yes      | Must match password            |

**Response**

- **Success:** Redirect to index page
- **Error:** Returns to registration page with error messages

---

### 1.2 User Login

|                 |                                      |
| --------------- | ------------------------------------ |
| **Endpoint**    | `/login/`                            |
| **Method**      | `POST`                               |
| **Description** | Authenticate user and create session |

**Parameters (form-data)**

| Parameter  | Required    | Description                        |
| ---------- | ----------- | ---------------------------------- |
| `email`    | Yes         | User's email                       |
| `password` | Yes         | User's password                    |
| `remember` | No          | `"on"` for 2-week session expiry   |
| `otp`      | Conditional | One-time password (if 2FA enabled) |

**Response (JSON)**

Success:

```json
{
  "success": true,
  "msg": null
}
```

Error:

```json
{
  "success": false,
  "msg": "Invalid User Credentials"
}
```

---

### 1.3 Validate Login (AJAX)

|                 |                                    |
| --------------- | ---------------------------------- |
| **Endpoint**    | `/validate_login/`                 |
| **Method**      | `POST`                             |
| **Description** | AJAX endpoint for login validation |
| **Parameters**  | Same as `/login/`                  |
| **Response**    | JSON with success/error status     |

---

### 1.4 Google OAuth Login

|                 |                                        |
| --------------- | -------------------------------------- |
| **Endpoint**    | `/auth/google/`                        |
| **Method**      | `GET`                                  |
| **Description** | Redirect to Google OAuth authorization |

---

### 1.5 Google OAuth Callback

|                 |                              |
| --------------- | ---------------------------- |
| **Endpoint**    | `/auth/google/callback/`     |
| **Method**      | `GET`                        |
| **Description** | Handle Google OAuth callback |

---

### 1.6 GitHub OAuth Login

|                 |                                        |
| --------------- | -------------------------------------- |
| **Endpoint**    | `/auth/github/`                        |
| **Method**      | `GET`                                  |
| **Description** | Redirect to GitHub OAuth authorization |

---

### 1.7 GitHub OAuth Callback

|                 |                              |
| --------------- | ---------------------------- |
| **Endpoint**    | `/auth/github/callback/`     |
| **Method**      | `GET`                        |
| **Description** | Handle GitHub OAuth callback |

---

### 1.8 Logout

|                 |                        |
| --------------- | ---------------------- |
| **Endpoint**    | `/logout/`             |
| **Method**      | `GET`                  |
| **Description** | Terminate user session |

---

### 1.9 Check 2FA Status

|                 |                                    |
| --------------- | ---------------------------------- |
| **Endpoint**    | `/api/isTfaEnabled/`               |
| **Method**      | `POST`                             |
| **Description** | Check if 2FA is enabled for a user |

**Request (JSON)**

```json
{
  "email": "user@example.com"
}
```

**Response (JSON)**

```json
{
  "enabled": true,
  "error": null
}
```

---

## 2. User Management

### 2.1 Dashboard

|                    |                         |
| ------------------ | ----------------------- |
| **Endpoint**       | `/sub/dashboard/`       |
| **Method**         | `GET`                   |
| **Description**    | Get user dashboard data |
| **Authentication** | Required                |

**Response:** Renders dashboard with statistics including:

- Total checks
- Monthly checks
- Percentage change
- High-risk alerts
- Recent interactions

---

### 2.2 User Settings

|                    |                               |
| ------------------ | ----------------------------- |
| **Endpoint**       | `/sub/settings/`              |
| **Method**         | `GET`, `POST`                 |
| **Description**    | View and update user settings |
| **Authentication** | Required                      |

**POST Parameters (form-data)**

| Parameter               | Description                    |
| ----------------------- | ------------------------------ |
| `fullname`              | Updated full name              |
| `email`                 | Updated email                  |
| `tfa`                   | `"on"` to enable 2FA           |
| `safety_alerts`         | `"on"` to enable safety alerts |
| `monthly_usage_reports` | `"on"` to enable reports       |

---

### 2.3 Delete Account

|                    |                                 |
| ------------------ | ------------------------------- |
| **Endpoint**       | `/delete_account/`              |
| **Method**         | `POST`                          |
| **Description**    | Permanently delete user account |
| **Authentication** | Required                        |

**Response (JSON)**

```json
{
  "success": true,
  "reason": null
}
```

---

### 2.4 Request OTP

|                 |                                              |
| --------------- | -------------------------------------------- |
| **Endpoint**    | `/api/requestotp`                            |
| **Method**      | `POST`                                       |
| **Description** | Request one-time password for password reset |

**Request (JSON)**

```json
{
  "email": "user@example.com"
}
```

**Response (JSON)**

```json
{
  "error": null
}
```

_`null` on success, error message on failure_

---

### 2.5 Reset Password

|                 |                                       |
| --------------- | ------------------------------------- |
| **Endpoint**    | `/api/requestPassReset`               |
| **Method**      | `POST`                                |
| **Description** | Reset password using OTP verification |

**Request (JSON)**

```json
{
  "email": "user@example.com",
  "otp": "123456",
  "password": "new_password"
}
```

**Response (JSON)**

```json
{
  "error": null
}
```

_`null` on success, error message on failure_

---

## 3. Drug Interactions

### 3.1 Check Drug Interaction

|                    |                                       |
| ------------------ | ------------------------------------- |
| **Endpoint**       | `/sub/intanalysis/`                   |
| **Method**         | `GET`                                 |
| **Description**    | Analyze interaction between two drugs |
| **Authentication** | Required                              |

**Parameters (query string)**

| Parameter | Required | Description                |
| --------- | -------- | -------------------------- |
| `drug1`   | Yes      | DrugBank ID of first drug  |
| `drug2`   | Yes      | DrugBank ID of second drug |

**Response:** Renders interaction analysis page with:

- Drug names
- Severity level (Low / Moderate / High)
- Description
- Automatically creates history entry

---

### 3.2 Validate Drug Name

|                 |                                |
| --------------- | ------------------------------ |
| **Endpoint**    | `/api/checkdrug/`              |
| **Method**      | `GET`                          |
| **Description** | Validate and find drug by name |

**Parameters (query string)**

| Parameter  | Required | Description         |
| ---------- | -------- | ------------------- |
| `drugname` | Yes      | Drug name to search |

**Response (JSON)**

```json
{
  "commonname": "Aspirin",
  "synonym": "Aspirin",
  "drugbankId": "DB00945",
  "error": null
}
```

---

### 3.3 Extract Drug Name from Image

|                 |                                                     |
| --------------- | --------------------------------------------------- |
| **Endpoint**    | `/api/extract-name`                                 |
| **Method**      | `POST`                                              |
| **Description** | Extract drug name from prescription image using OCR |

**Parameters (multipart/form-data)**

| Parameter | Required | Description          |
| --------- | -------- | -------------------- |
| `image`   | Yes      | Image file (JPG/PNG) |

**Response (JSON)**

Success:

```json
{
  "success": true,
  "commonname": "Aspirin"
}
```

Failure:

```json
{
  "success": false,
  "commonname": null
}
```

---

## 4. Medication Management

### 4.1 View Medications

|                    |                             |
| ------------------ | --------------------------- |
| **Endpoint**       | `/sub/medications`          |
| **Method**         | `GET`                       |
| **Description**    | View user's medication list |
| **Authentication** | Required                    |
| **Response**       | Renders medications page    |

---

### 4.2 Get Medications (AJAX)

|                    |                                        |
| ------------------ | -------------------------------------- |
| **Endpoint**       | `/api/medications/`                    |
| **Method**         | `GET`                                  |
| **Description**    | Paginated medication list with filters |
| **Authentication** | Required                               |

**Parameters (query string)**

| Parameter  | Optional | Description                                      |
| ---------- | -------- | ------------------------------------------------ |
| `page`     | Yes      | Page number (default: `1`)                       |
| `per_page` | Yes      | Items per page (default: `10`)                   |
| `search`   | Yes      | Search term                                      |
| `active`   | Yes      | `"true"`, `"false"`, or `"all"` (default: `all`) |

**Response (JSON)**

```json
{
  "success": true,
  "data": [
    {
      "id": 1,
      "name": "Aspirin",
      "dosage_amount": 500.0,
      "dosage_frequency": "Once daily",
      "category": "NSAID",
      "last_refill": "January 15, 2026",
      "active": true
    }
  ],
  "pagination": {
    "current_page": 1,
    "total_pages": 5,
    "total_items": 50,
    "start_index": 1,
    "end_index": 10,
    "has_previous": false,
    "has_next": true,
    "previous_page": null,
    "next_page": 2
  }
}
```

---

### 4.3 Add Medication

|                    |                                   |
| ------------------ | --------------------------------- |
| **Endpoint**       | `/sub/addmedications`             |
| **Method**         | `POST`, `GET`                     |
| **Description**    | Add new medication to user's list |
| **Authentication** | Required                          |

**POST Request (JSON)**

```json
{
  "medication_name": "Aspirin",
  "dosage_unit": "mg",
  "dosage_value": "500",
  "dosage_frequency": "Once daily",
  "medication_more": "Take with food"
}
```

**Response (JSON)**

```json
{
  "error": null
}
```

_`null` on success, error message on failure_

---

### 4.4 Delete Medication

|                    |                                         |
| ------------------ | --------------------------------------- |
| **Endpoint**       | `/delete_medication/<int:medicationId>` |
| **Method**         | `GET`                                   |
| **Description**    | Delete a medication from user's list    |
| **Authentication** | Required                                |

**URL Parameters**

| Parameter      | Required | Description                |
| -------------- | -------- | -------------------------- |
| `medicationId` | Yes      | ID of medication to delete |

**Response:** Redirects to medication page

---

### 4.5 Toggle Medication Status

|                    |                                          |
| ------------------ | ---------------------------------------- |
| **Endpoint**       | `/switch_status/<int:medicationId>`      |
| **Method**         | `GET`                                    |
| **Description**    | Toggle medication active/inactive status |
| **Authentication** | Required                                 |

**URL Parameters**

| Parameter      | Required | Description      |
| -------------- | -------- | ---------------- |
| `medicationId` | Yes      | ID of medication |

**Response:** Redirects to medication page

---

## 5. History & Reports

### 5.1 View History

|                    |                                 |
| ------------------ | ------------------------------- |
| **Endpoint**       | `/sub/history`                  |
| **Method**         | `GET`                           |
| **Description**    | View user's interaction history |
| **Authentication** | Required                        |
| **Response**       | Renders history page            |

---

### 5.2 Get History (AJAX)

|                    |                                |
| ------------------ | ------------------------------ |
| **Endpoint**       | `/api/history/`                |
| **Method**         | `GET`                          |
| **Description**    | Paginated history with filters |
| **Authentication** | Required                       |

**Parameters (query string)**

| Parameter   | Optional | Description                                 |
| ----------- | -------- | ------------------------------------------- |
| `page`      | Yes      | Page number (default: `1`)                  |
| `per_page`  | Yes      | Items per page (default: `10`)              |
| `search`    | Yes      | Search by drug name                         |
| `severity`  | Yes      | `"high"`, `"moderate"`, `"low"`, or `"all"` |
| `date_from` | Yes      | Filter from date (`YYYY-MM-DD`)             |
| `date_to`   | Yes      | Filter to date (`YYYY-MM-DD`)               |

**Response (JSON)**

```json
{
  "success": true,
  "data": [
    {
      "id": 1,
      "date": "January 15, 2026",
      "time": "02:30 PM",
      "drug1": "Aspirin",
      "drug2": "Warfarin",
      "severity": "High",
      "severity_level": 2,
      "description": "Increased risk of bleeding"
    }
  ],
  "pagination": {
    "current_page": 1,
    "total_pages": 5,
    "total_items": 50,
    "start_index": 1,
    "end_index": 10,
    "has_previous": false,
    "has_next": true,
    "previous_page": null,
    "next_page": 2
  }
}
```

---

### 5.3 Get Single History Record

|                    |                                          |
| ------------------ | ---------------------------------------- |
| **Endpoint**       | `/api/gethistory/<int:historyId>`        |
| **Method**         | `GET`                                    |
| **Description**    | Get details of a specific history record |
| **Authentication** | Required                                 |

**URL Parameters**

| Parameter   | Required | Description          |
| ----------- | -------- | -------------------- |
| `historyId` | Yes      | ID of history record |

**Response (JSON)**

```json
{
  "success": true,
  "error": null,
  "id": 1,
  "drug1": "Aspirin",
  "drug2": "Warfarin",
  "description": "Increased risk of bleeding",
  "severity": "High",
  "severity_level": 2,
  "checked_date": "January 15, 2026",
  "checked_time": "02:30 PM"
}
```

---

## 6. Export Functions

### 6.1 Export Combined PDF

|                    |                                              |
| ------------------ | -------------------------------------------- |
| **Endpoint**       | `/export/combined/pdf/`                      |
| **Method**         | `GET`                                        |
| **Description**    | Export both medications and history as PDF   |
| **Authentication** | Required                                     |
| **Response**       | PDF file download                            |
| **Filename**       | `complete_export_[username]_[timestamp].pdf` |

**Content includes:**

- Medications list with details
- Interaction history with full descriptions
- Summary statistics

---

### 6.2 Export History PDF

|                    |                                                  |
| ------------------ | ------------------------------------------------ |
| **Endpoint**       | `/export/history/pdf/`                           |
| **Method**         | `GET`                                            |
| **Description**    | Export interaction history as PDF                |
| **Authentication** | Required                                         |
| **Response**       | PDF file download                                |
| **Filename**       | `interaction_history_[username]_[timestamp].pdf` |

---

### 6.3 Export Single Interaction PDF

|                    |                                             |
| ------------------ | ------------------------------------------- |
| **Endpoint**       | `/export/interaction/pdf/<int:history_id>/` |
| **Method**         | `GET`                                       |
| **Description**    | Export a single interaction report as PDF   |
| **Authentication** | Required                                    |

**URL Parameters**

| Parameter    | Required | Description          |
| ------------ | -------- | -------------------- |
| `history_id` | Yes      | ID of history record |

**Response:** PDF file download
**Filename:** `interaction_report_[history_id]_[timestamp].pdf`

---

### 6.4 Export History CSV

|                    |                                                  |
| ------------------ | ------------------------------------------------ |
| **Endpoint**       | `/export/history/csv/`                           |
| **Method**         | `GET`                                            |
| **Description**    | Export interaction history as CSV                |
| **Authentication** | Required                                         |
| **Response**       | CSV file download                                |
| **Filename**       | `interaction_history_[username]_[timestamp].csv` |

**CSV Columns:**

- Date Checked
- Time
- Drug 1
- Drug 2
- Severity
- Description

---

## 7. Utility APIs

### 7.1 Check Alert Notifications

|                    |                                               |
| ------------------ | --------------------------------------------- |
| **Endpoint**       | `/api/canAlertNot/`                           |
| **Method**         | `GET`                                         |
| **Description**    | Check if user can receive alert notifications |
| **Authentication** | Required                                      |

**Response (JSON)**

```json
{
  "allowed": true
}
```

---

### 7.2 Check Reminder Notifications

|                    |                                                 |
| ------------------ | ----------------------------------------------- |
| **Endpoint**       | `/api/canReminderNot/`                          |
| **Method**         | `GET`                                           |
| **Description**    | Check if reminder notification should be pushed |
| **Authentication** | Required                                        |

**Response (JSON)**

```json
{
  "allowed": true
}
```

---

## 8. Error Codes

### HTTP Status Codes

| Code          | Meaning               |
| ------------- | --------------------- |
| `200`         | Success               |
| `301` / `302` | Redirect              |
| `400`         | Bad Request           |
| `401`         | Unauthorized          |
| `404`         | Not Found             |
| `405`         | Method Not Allowed    |
| `500`         | Internal Server Error |

### Response Formats

| Format | Description                     |
| ------ | ------------------------------- |
| HTML   | Rendered pages (standard views) |
| JSON   | API endpoints                   |
| PDF    | Export files                    |
| CSV    | Export files                    |

### Common Error Messages

- "Invalid email or password"
- "Password must be at least 8 characters long"
- "Invalid OTP"
- "User not authenticated"
- "Drug not found in database"
- "No file provided"
- "Only JPG and PNG allowed"
- "Email already exists"

---

## 9. Authentication Requirements

### Session Requirements

- All `/sub/*` endpoints require active session authentication
- Session established after successful login
- Session expired or missing: redirect to `/login/`

### OAuth Users

- OAuth users cannot reset passwords
- OAuth users are created automatically on first login
- OAuth users bypass standard password authentication

### OTP Requirements

- Maximum attempts per OTP: 5 (configurable)
- OTP expiration: 5 minutes (configurable)
- OTPs are single-use and deleted after successful verification

---

## 10. File Upload Restrictions

### Image Upload (OCR Endpoint)

|                     |                                                                         |
| ------------------- | ----------------------------------------------------------------------- |
| **Allowed formats** | JPG, PNG                                                                |
| **Content types**   | `image/jpeg`, `image/png`                                               |
| **Storage**         | Files are temporarily stored and automatically deleted after processing |

---

## 11. Sample Requests

### 11.1 Login Request

```http
POST /login/
Content-Type: application/x-www-form-urlencoded

email=user@example.com&password=mypassword&remember=on
```

### 11.2 Add Medication

```http
POST /sub/addmedications
Content-Type: application/json
Authorization: Session (cookie)

{
  "medication_name": "Aspirin",
  "dosage_unit": "mg",
  "dosage_value": "500",
  "dosage_frequency": "Once daily",
  "medication_more": "Take with food"
}
```

### 11.3 Get History with Filters

```http
GET /api/history/?severity=high&date_from=2026-01-01&page=2
```

---

## 12. Database Models Reference

### Core Models

| Model                 | Description                    |
| --------------------- | ------------------------------ |
| `Users`               | User account information       |
| `Profile`             | User settings and preferences  |
| `Drug`                | Drug information from DrugBank |
| `Drug_Interactions`   | Drug interaction records       |
| `UserHistory`         | User interaction history       |
| `UserMedications`     | User's personal medications    |
| `OTP`                 | One-time password storage      |
| `NotificationTrigger` | User notification preferences  |

---

## 13. Notes & Disclaimers

- All date/times are in server's timezone (Django `TIME_ZONE` setting)
- Drug names are matched using the DrugBank database
- OCR service supports English text extraction from prescription images
- 2FA uses email-based OTP verification
- PDF exports include medical disclaimers
- All exports include timestamp and user information
- The application is for educational purposes only
- Always consult a physician before making medical decisions

---

## 14. Contact & Support

For issues or questions about the API, contact the development team.

- **GitHub:** https://github.com/sampadathapachhetri/Capstone-Project

---

_End of documentation_
