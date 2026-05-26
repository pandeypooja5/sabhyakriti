# Railway Setup Guide for Sabhyakriti

## Step 1: Create Railway Account & Project

1. Go to [railway.app](https://railway.app)
2. Click **"Start Free"** → Sign up (GitHub recommended)
3. Create new project → **"Empty Project"**
4. Name it: `sabhyakriti`

## Step 2: Add Database & Cache Plugins

1. In your project dashboard, click **"+ New"**
2. Search **"PostgreSQL"** → click it → **"Add PostgreSQL"**
   - Wait for it to deploy (green checkmark)
   - Click the PostgreSQL service → **"Variables"** tab
   - Copy the `DATABASE_URL` value (you'll need this)

3. Click **"+ New"** again
4. Search **"Redis"** → click it → **"Add Redis"**
   - Wait for it to deploy
   - Click the Redis service → **"Variables"** tab
   - Copy the `REDIS_URL` value

**Save these URLs** — you'll use them in Step 3.

---

## Step 3: Deploy Backend Services (7 total)

For each service, follow this process:

### Service 1: Auth Service

1. In Railway, click **"+ New"** → **"GitHub Repo"**
2. Connect your GitHub account (if prompted)
3. Select your `sabhyakriti` repo
4. In **"Service Name"**, type: `auth-service`
5. In **"Root Directory"**, type: `sabhyakriti-auth-service`
6. Click **"Create"** → wait for it to build & deploy

Once deployed (green), click the `auth-service` card:
- Go to **"Variables"** tab
- Click **"Add Variable"** and add these:

```
DATABASE_URL=<paste the PostgreSQL URL from Step 2>
REDIS_URL=<paste the Redis URL from Step 2>
ENVIRONMENT=production
FRONTEND_ORIGIN=https://sabhyakriti.com
INTERNAL_SERVICE_SECRET=<generate a random 32-char secret>
JWT_PUBLIC_KEY_URL=https://auth-sabhyakriti.up.railway.app/.well-known/jwks.json
GOOGLE_CLIENT_ID=<your Google OAuth client ID>
FACEBOOK_CLIENT_ID=<your Facebook app ID>
TWILIO_ACCOUNT_SID=<your Twilio SID>
TWILIO_AUTH_TOKEN=<your Twilio token>
TWILIO_FROM_NUMBER=<your Twilio number>
```

After adding each variable, press **Enter**.

Once done, go to **"Deployments"** tab and wait for the build to complete.

---

### Services 2–7: Repeat This Process

For each service below, click **"+ New"** → **"GitHub Repo"** and follow the same steps as Auth Service, but use this configuration:

#### Service 2: Product Service
- Service Name: `product-service`
- Root Directory: `sabhyakriti-product-service`
- Variables (common + these):
```
DATABASE_URL=<PostgreSQL URL>
REDIS_URL=<Redis URL>
ENVIRONMENT=production
FRONTEND_ORIGIN=https://sabhyakriti.com
INTERNAL_SERVICE_SECRET=<same secret as auth-service>
JWT_PUBLIC_KEY_URL=https://auth-sabhyakriti.up.railway.app/.well-known/jwks.json
PRODUCT_SERVICE_URL=http://product-service.railway.internal:8002
NOTIFICATION_SERVICE_URL=http://notification-service.railway.internal:8006
```

#### Service 3: Cart Service
- Service Name: `cart-service`
- Root Directory: `sabhyakriti-cart-service`
- Variables:
```
DATABASE_URL=<PostgreSQL URL>
REDIS_URL=<Redis URL>
ENVIRONMENT=production
FRONTEND_ORIGIN=https://sabhyakriti.com
INTERNAL_SERVICE_SECRET=<same secret>
JWT_PUBLIC_KEY_URL=https://auth-sabhyakriti.up.railway.app/.well-known/jwks.json
PRODUCT_SERVICE_URL=http://product-service.railway.internal:8002
NOTIFICATION_SERVICE_URL=http://notification-service.railway.internal:8006
```

#### Service 4: Order Service
- Service Name: `order-service`
- Root Directory: `sabhyakriti-order-service`
- Variables:
```
DATABASE_URL=<PostgreSQL URL>
REDIS_URL=<Redis URL>
ENVIRONMENT=production
FRONTEND_ORIGIN=https://sabhyakriti.com
INTERNAL_SERVICE_SECRET=<same secret>
JWT_PUBLIC_KEY_URL=https://auth-sabhyakriti.up.railway.app/.well-known/jwks.json
PRODUCT_SERVICE_URL=http://product-service.railway.internal:8002
PAYMENT_SERVICE_URL=http://payment-service.railway.internal:8005
NOTIFICATION_SERVICE_URL=http://notification-service.railway.internal:8006
```

#### Service 5: Payment Service
- Service Name: `payment-service`
- Root Directory: `sabhyakriti-payment-service`
- Variables:
```
DATABASE_URL=<PostgreSQL URL>
REDIS_URL=<Redis URL>
ENVIRONMENT=production
FRONTEND_ORIGIN=https://sabhyakriti.com
INTERNAL_SERVICE_SECRET=<same secret>
JWT_PUBLIC_KEY_URL=https://auth-sabhyakriti.up.railway.app/.well-known/jwks.json
RAZORPAY_KEY_ID=<production Razorpay key>
RAZORPAY_KEY_SECRET=<production Razorpay secret>
NOTIFICATION_SERVICE_URL=http://notification-service.railway.internal:8006
```

#### Service 6: Notification Service
- Service Name: `notification-service`
- Root Directory: `sabhyakriti-notification-service`
- Variables:
```
DATABASE_URL=<PostgreSQL URL>
REDIS_URL=<Redis URL>
ENVIRONMENT=production
FRONTEND_ORIGIN=https://sabhyakriti.com
INTERNAL_SERVICE_SECRET=<same secret>
JWT_PUBLIC_KEY_URL=https://auth-sabhyakriti.up.railway.app/.well-known/jwks.json
TWILIO_ACCOUNT_SID=<your Twilio SID>
TWILIO_AUTH_TOKEN=<your Twilio token>
TWILIO_FROM_NUMBER=<your Twilio number>
```

#### Service 7: Admin Service
- Service Name: `admin-service`
- Root Directory: `sabhyakriti-admin-service`
- Variables:
```
ENVIRONMENT=production
FRONTEND_ORIGIN=https://sabhyakriti.com
INTERNAL_SERVICE_SECRET=<same secret>
JWT_PUBLIC_KEY_URL=https://auth-sabhyakriti.up.railway.app/.well-known/jwks.json
AUTH_SERVICE_URL=http://auth-service.railway.internal:8001
PRODUCT_SERVICE_URL=http://product-service.railway.internal:8002
CART_SERVICE_URL=http://cart-service.railway.internal:8003
ORDER_SERVICE_URL=http://order-service.railway.internal:8004
PAYMENT_SERVICE_URL=http://payment-service.railway.internal:8005
NOTIFICATION_SERVICE_URL=http://notification-service.railway.internal:8006
```

---

## Step 4: Verify All Services Are Running

1. In Railway dashboard, you should see 10 services:
   - PostgreSQL ✓
   - Redis ✓
   - auth-service ✓
   - product-service ✓
   - cart-service ✓
   - order-service ✓
   - payment-service ✓
   - notification-service ✓
   - admin-service ✓

2. Each service should have a **green checkmark** (deployed status)

3. Click each service to find its **public Railway URL**:
   - Click service → **"Settings"** → scroll to **"Public Networking"**
   - Copy the URL (e.g., `https://auth-sabhyakriti.up.railway.app`)

---

## Step 5: Update vercel.json with Real Railway URLs

Once all services are deployed and have public URLs:

1. Edit `sabhyakriti-frontend/vercel.json`
2. Replace placeholder URLs with real Railway URLs:

```json
"destination": "https://auth-sabhyakriti.up.railway.app/api/v1/auth/:path*"
"destination": "https://product-sabhyakriti.up.railway.app/api/v1/products/:path*"
...
```

---

## Step 6: Run Database Migrations

1. In Railway, click **PostgreSQL** service → **"Connect"** tab → **"CLI"** 
   - Copy the psql connection command

2. For each service with a database (auth, product, cart, order, payment):
   - Click service → **"Settings"** → **"Shell"** tab
   - Run: `cd /app && alembic upgrade head`
   - Wait for completion (should see "Alembic OK" or similar)

---

## Troubleshooting

**Service won't deploy:**
- Check the **"Deployments"** tab → view the build log for errors
- Common issues: missing env vars, wrong root directory, GitHub auth issues

**Services can't communicate:**
- Verify all services use `http://<service-name>.railway.internal:<port>` for inter-service URLs
- Not `https://` — Railway internal network uses HTTP

**Database connection fails:**
- Ensure `DATABASE_URL` is copied exactly (no extra spaces)
- Check PostgreSQL service is deployed and has green checkmark

---

## Next: Deploy Frontend to Vercel

Once Railway is fully set up and all services are running, follow these steps:

1. Push the repo to GitHub (with `vercel.json` updated)
2. Go to [vercel.com](https://vercel.com) → New Project → Import from GitHub
3. Select `sabhyakriti` repo
4. Set Root Directory: `sabhyakriti-frontend`
5. Add environment variable: `VITE_RAZORPAY_KEY_ID=<your key>`
6. Deploy

Then configure DNS on GoDaddy as shown in the main deployment plan.
