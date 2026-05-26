# Sabhyakriti — Local Development Guide

Run the entire Sabhyakriti platform on your local machine using Docker Compose.

---

## Prerequisites

Install these before starting:

| Tool | Version | Download |
|---|---|---|
| Docker Desktop | Latest | https://www.docker.com/products/docker-desktop |
| Python | 3.11+ | https://www.python.org/downloads |
| Node.js | 20 LTS | https://nodejs.org |
| Git | Any | https://git-scm.com |

**Windows users**: Use Git Bash or WSL2 to run the shell scripts.

---

## Step 1: One-Time Setup (Run Once)

```bash
cd C:\AI-Projects\sabhyakriti
bash scripts/setup-local.sh
```

This script:
- Generates an RSA-2048 key pair for JWT signing
- Copies `.env.example` to `.env` for each service
- Installs frontend Node.js dependencies
- Prints what to do next

---

## Step 2: Configure Local Environment

Edit `.env.local` in the workspace root and fill in your Razorpay **test** keys:

```
RAZORPAY_KEY_ID=rzp_test_XXXXXXXXXXXX
RAZORPAY_KEY_SECRET=XXXXXXXXXXXXXXXXXXXX
```

Get test keys free at: https://dashboard.razorpay.com → Settings → API Keys → Test Mode

Everything else (Google OAuth, Twilio, AWS) is **optional** for local testing:
- **Email/SMS** — In `ENVIRONMENT=development` mode, OTPs and emails are printed to the service's Docker logs instead of being sent. No Twilio or SES account needed.
- **OAuth** — Only needed if testing Google/Facebook login. Email/password + Phone OTP work without it.
- **Product images** — S3/CloudFront is not set up locally. Products will show without images.

---

## Step 3: Start All Backend Services

```bash
bash scripts/start-local.sh
```

This will:
1. Build all 7 Docker images (takes 3–5 minutes on first run)
2. Start PostgreSQL and Redis
3. Run all database migrations (creates all schemas and tables)
4. Start all 7 backend services
5. Print service URLs when ready

**Services started:**

| Service | URL | API Docs |
|---|---|---|
| Auth | http://localhost:8001 | http://localhost:8001/docs |
| Product | http://localhost:8002 | http://localhost:8002/docs |
| Cart | http://localhost:8003 | http://localhost:8003/docs |
| Order | http://localhost:8004 | http://localhost:8004/docs |
| Payment | http://localhost:8005 | http://localhost:8005/docs |
| Notification | http://localhost:8006 | (internal only) |
| Admin BFF | http://localhost:8007 | http://localhost:8007/api/docs |

---

## Step 4: Start the Frontend

Open a **new terminal** and run:

```bash
cd C:\AI-Projects\sabhyakriti\sabhyakriti-frontend
npm run dev
```

Open **http://localhost:5173** in your browser.

---

## Step 5: Seed Sample Data

After all services are running, create sample categories and products:

```bash
python3 scripts/seed-data.py
```

This creates:
- 15 saree categories (5 Fabric + 5 Occasion + 5 Region)
- 6 sample saree products
- Prompts you to create an admin user

---

## How to Access the Admin Panel

1. Register at http://localhost:5173/register with `admin@sabhyakriti.com`
2. Check the auth-service logs for the verification token:
   ```bash
   docker compose -f docker-compose.all.yml logs auth-service | grep "verification"
   ```
3. Open the verification URL in your browser
4. Log in → navigate to http://localhost:5173/admin

**Note:** For local testing you can also directly update the user role in the database:
```bash
docker compose -f docker-compose.all.yml exec postgres psql -U postgres -d sabhyakriti -c \
  "UPDATE auth.users SET role='ADMIN', is_email_verified=TRUE WHERE email='admin@sabhyakriti.com';"
```

---

## Common Commands

```bash
# View logs for a specific service
docker compose -f docker-compose.all.yml logs -f auth-service

# Restart a single service after code changes
docker compose -f docker-compose.all.yml up -d --build product-service

# Stop everything
docker compose -f docker-compose.all.yml down

# Stop and delete all data (fresh start)
docker compose -f docker-compose.all.yml down -v

# Check service health
docker compose -f docker-compose.all.yml ps

# Run a migration manually
docker compose -f docker-compose.all.yml exec auth-service alembic upgrade head

# Open a PostgreSQL shell
docker compose -f docker-compose.all.yml exec postgres psql -U postgres -d sabhyakriti

# Check all auth users
docker compose -f docker-compose.all.yml exec postgres psql -U postgres -d sabhyakriti \
  -c "SELECT email, role, is_email_verified FROM auth.users;"
```

---

## Development Workflow (Making Code Changes)

When you edit Python code in a service:

```bash
# Option 1: Rebuild and restart that service
docker compose -f docker-compose.all.yml up -d --build auth-service

# Option 2: Run outside Docker with hot reload (faster)
cd sabhyakriti-auth-service
source .venv/bin/activate
uvicorn main:app --reload --port 8001
# Then update docker-compose.all.yml to not start auth-service (comment it out)
```

When you edit frontend code — Vite hot-reloads automatically. No restart needed.

---

## Reading OTPs and Emails Locally

Since real Twilio/SES is not configured, check Docker logs:

```bash
# See OTP codes (Phone login)
docker compose -f docker-compose.all.yml logs -f auth-service | grep -i otp

# See email content (order confirmation, etc.)
docker compose -f docker-compose.all.yml logs -f notification-service
```

---

## Testing Payments Locally

1. Use Razorpay **Test Mode** key in `.env.local`
2. On the checkout payment page, use Razorpay test cards:
   - Success: Card `4111 1111 1111 1111`, any future date, any CVV
   - Failure: Card `4000 0000 0000 0002`
3. For COD: select Cash on Delivery — no payment details required

For webhook testing locally, use [Razorpay's test webhook](https://dashboard.razorpay.com/app/webhooks) pointing to `http://localhost:8005/api/v1/payments/webhook` (requires ngrok for external access).

---

## Architecture Overview (Local)

```
Browser (http://localhost:5173)
    |
    | Vite Dev Server (proxy)
    |
    +---> /api/v1/auth/*      → auth-service:8001
    +---> /api/v1/products/*  → product-service:8002
    +---> /api/v1/cart/*      → cart-service:8003
    +---> /api/v1/orders/*    → order-service:8004
    +---> /api/v1/payments/*  → payment-service:8005
    +---> /api/v1/admin/*     → admin-service:8007

Internal (Docker network):
    order-service   → cart-service    (read/clear cart on checkout)
    order-service   → product-service (reserve/release stock)
    order-service   → notification-service (emails/SMS)
    payment-service → order-service   (confirm/cancel order)
    payment-service → notification-service (payment receipt)
    all services    → auth-service    (JWKS for JWT validation)
```

---

## Troubleshooting

| Problem | Solution |
|---|---|
| `Port already in use` | Stop the conflicting process or change port in docker-compose |
| `Database connection refused` | Wait 30s for PostgreSQL to start; check `docker compose ps` |
| `alembic: target database is not up to date` | Run `bash scripts/start-local.sh` again |
| `JWT validation failed` | Ensure auth-service started successfully and JWKS endpoint works: `curl http://localhost:8001/auth/.well-known/jwks.json` |
| `Product images not showing` | Expected — S3/CloudFront not configured locally |
| OTP not received | Check notification-service logs: `docker compose logs -f notification-service` |
| Frontend shows CORS error | Check that Vite proxy in `vite.config.ts` is running on port 5173 |
