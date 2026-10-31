# SubscriptIQ Email Service Setup & Verification Guide

## 1. Overview

SubscriptIQ implements real, production-ready transactional email delivery for:
1. **Customer Registration Email Verification (6-digit OTP)**
2. **Forgot Password Recovery (6-digit OTP)**

No universal, hardcoded, or demo verification codes (such as `123456`) are permitted. Every registration and password reset operation generates a cryptographically secure random six-digit OTP that is dispatched directly to the recipient's email address.

---

## 2. Configuration Environment Variables

Configure these settings in `backend/.env` (template provided in `.env.example`):

| Variable | Type | Default | Description |
|---|---|---|---|
| `EMAIL_PROVIDER` | string | `smtp` | Email delivery mechanism (`smtp` or `mock` for testing) |
| `SMTP_HOST` | string | *Required* | SMTP host address (e.g., `smtp.gmail.com`, `smtp.resend.com`) |
| `SMTP_PORT` | integer | `587` | Port (`587` for TLS / STARTTLS, `465` for SSL) |
| `SMTP_USERNAME` | string | *Required* | SMTP authentication username / API key |
| `SMTP_PASSWORD` | string | *Required* | SMTP authentication password / app-specific password |
| `SMTP_USE_TLS` | boolean | `True` | Enable STARTTLS encryption (recommended for port 587) |
| `SMTP_USE_SSL` | boolean | `False` | Enable direct SSL encryption (for port 465) |
| `SMTP_FROM_EMAIL` | string | `noreply@subscriptiq.com` | Verified sender email address |
| `SMTP_FROM_NAME` | string | `SubscriptIQ` | Branded sender display name |
| `FRONTEND_URL` | string | `http://127.0.0.1:5173` | Application web frontend URL |
| `OTP_EXPIRE_MINUTES` | integer | `10` | OTP validity window (10 minutes) |
| `OTP_MAX_ATTEMPTS` | integer | `5` | Maximum failed entry attempts before invalidation |
| `OTP_RESEND_COOLDOWN_SECONDS` | integer | `60` | Cooldown period between resend requests |

---

## 3. Provider Setup Walkthroughs

### Option A: Gmail (Recommended for Rapid Development & Demos)
1. Log into your Google Account and navigate to **Security** > **2-Step Verification**.
2. Scroll to the bottom and select **App Passwords**.
3. Generate a new App Password (name it `SubscriptIQ Backend`).
4. Copy the generated 16-character password into `backend/.env`:
   ```bash
   EMAIL_PROVIDER=smtp
   SMTP_HOST=smtp.gmail.com
   SMTP_PORT=587
   SMTP_USERNAME=your-actual-email@gmail.com
   SMTP_PASSWORD=abcd efgh ijkl mnop
   SMTP_USE_TLS=True
   SMTP_USE_SSL=False
   SMTP_FROM_EMAIL=your-actual-email@gmail.com
   SMTP_FROM_NAME=SubscriptIQ
   ```

### Option B: Resend (Modern Transactional Provider)
1. Sign up at [resend.com](https://resend.com) and generate an API Key.
2. In `backend/.env`:
   ```bash
   EMAIL_PROVIDER=smtp
   SMTP_HOST=smtp.resend.com
   SMTP_PORT=587
   SMTP_USERNAME=resend
   SMTP_PASSWORD=re_1234567890abcdef
   SMTP_USE_TLS=True
   SMTP_USE_SSL=False
   SMTP_FROM_EMAIL=onboarding@resend.dev
   SMTP_FROM_NAME=SubscriptIQ
   ```

### Option C: SendGrid / Twilio
1. Create an API Key with **Mail Send** permissions.
2. In `backend/.env`:
   ```bash
   EMAIL_PROVIDER=smtp
   SMTP_HOST=smtp.sendgrid.net
   SMTP_PORT=587
   SMTP_USERNAME=apikey
   SMTP_PASSWORD=SG.your-sendgrid-api-key
   SMTP_USE_TLS=True
   SMTP_USE_SSL=False
   SMTP_FROM_EMAIL=verified-sender@yourdomain.com
   SMTP_FROM_NAME=SubscriptIQ
   ```

---

## 4. Security Architecture & Threat Mitigations

1. **Cryptographic Randomness**: Generated using Python's `secrets.randbelow(1_000_000)` with formatting `f"{...:06d}"`, preserving all leading zeroes.
2. **Zero Plaintext Storage**: The database tables (`pending_registrations`, `password_reset_otps`) store **only SHA-256 hashes** of OTPs. If the database is compromised, plaintext OTPs cannot be recovered.
3. **Constant-Time Verification**: Verification uses `secrets.compare_digest` to prevent timing attacks.
4. **Strict Expiry**: All OTPs expire exactly 10 minutes from dispatch.
5. **Single-Use Enforcement**: Upon successful verification or issuance of a reset token, the OTP is deleted or permanently marked as `USED`.
6. **Attempt Limiting (Anti-Bruteforce)**: Each OTP allows a maximum of 5 attempts. On the 5th failed attempt, the OTP is immediately invalidated and deleted.
7. **Resend Cooldown (Anti-Flooding)**: Enforces a mandatory 60-second cooldown between resend requests per email.
8. **Account Anti-Enumeration**: The `/api/v1/auth/forgot-password` endpoint returns the same generic masked confirmation response whether or not an account exists in the database.
9. **Role Isolation**: Customers verified through registration are strictly assigned the `customer` role and restricted to their self-service portal.
