# Cloud9 ERP: DigitalOcean App Platform Deployment Guide

This guide walks you through deploying Cloud9 ERP to DigitalOcean App Platform with reliable configuration, persistent storage, and production-ready setup.

## Prerequisites

1. **DigitalOcean Account** with an active project
2. **doctl CLI** installed and authenticated (`doctl auth init`)
3. **GitHub Repository** with the Cloud9 ERP code pushed to `main` branch
4. **Domain Name** for your ERP instance (e.g., `cloud9beverages.com`)

Install doctl if needed:
```bash
# macOS
brew install doctl

# Linux/Windows (or use the installer from https://github.com/digitalocean/doctl)
cd ~
wget https://github.com/digitalocean/doctl/releases/download/v1.94.0/doctl-1.94.0-linux-x86_64.tar.gz
tar xf doctl-1.94.0-linux-x86_64.tar.gz
sudo mv doctl /usr/local/bin
```

## Step 1: Update app.yaml with Your GitHub Repository

Edit `.do/app.yaml` and replace the placeholder GitHub repository:

```yaml
services:
  - name: frontend
    github:
      branch: main
      repo: YOUR-GITHUB-ORG/c9-erp  # ← Update this
    ...
  - name: backend
    github:
      branch: main
      repo: YOUR-GITHUB-ORG/c9-erp  # ← Update this
    ...
```

Example: if your repo is at `https://github.com/mycompany/cloud9-erp`, use:
```yaml
repo: mycompany/cloud9-erp
```

## Step 2: Create the App on DigitalOcean

Use doctl to create the app from the spec:

```bash
doctl apps create --spec .do/app.yaml
```

This will:
1. Create an App Platform project
2. Provision the **frontend** service (static site)
3. Provision the **backend** service (Python/Uvicorn)
4. Create a **PostgreSQL database** (managed, production-ready, SSL required)
5. Register the app and await deployment

**Output:** The command will print an **App ID** (e.g., `abc123def456`). Save this for later commands.

Example output:
```
app_id: 9a1b2c3d-4e5f-6789-abcd-ef1234567890
...
```

### Alternative: Create via DigitalOcean Dashboard

You can also create the app manually:
1. Go to **Apps** → **Create App** → **GitHub**
2. Connect your GitHub repo and select `c9-erp`
3. Upload `.do/app.yaml` or configure the components manually
4. Review settings and click **Create**

## Step 3: Configure Secrets

The deployment requires a **JWT_SECRET** for authentication tokens. Set this via doctl:

```bash
# Generate a secure random secret (minimum 32 characters recommended)
openssl rand -hex 32

# Example output: a1b2c3d4e5f6g7h8i9j0k1l2m3n4o5p6

# Set the secret in your app (replace APP_ID with your actual app ID)
doctl apps create-secret APP_ID --key JWT_SECRET --value a1b2c3d4e5f6g7h8i9j0k1l2m3n4o5p6
```

Or via dashboard: **Apps** → Your App → **Settings** → **Secret Manager** → **Add Secret**

**Important:** Use a strong, randomly generated value. This protects session tokens.

## Step 4: Configure DNS Records

Once the app is created, add CNAME records in your domain registrar pointing to DigitalOcean:

### 1. For the Frontend (ERPInterface)

| Type | Name | Value |
|------|------|-------|
| CNAME | erp | your-app-id.ondigitalocean.app |
| A | cloud9beverages.com | (DigitalOcean's IP, usually auto-resolved) |

### 2. For the Backend API

| Type | Name | Value |
|------|------|-------|
| CNAME | api | your-app-id.ondigitalocean.app |

Replace `your-app-id` with the actual App Platform ID (from the `.do/app.yaml` -> domains section, or from the dashboard).

**Verification:**
```bash
# Check DNS propagation (wait 10-30 minutes)
nslookup erp.cloud9beverages.com
nslookup api.cloud9beverages.com
```

## Step 5: Initial Deployment and Verification

The app should deploy automatically. Monitor progress:

```bash
# Check deployment status
doctl apps get APP_ID

# View logs (real-time)
doctl apps logs APP_ID --follow
```

Expected logs during first deployment:
```
[*] Database host: db-postgresql-abc-12345.ondigitalocean.com (port 5432)
[*] Waiting for PostgreSQL to be ready...
[✓] PostgreSQL is ready!
[*] Running first-run setup (admin user, roles, permissions)...
[✓] First-run setup completed successfully
[*] Starting Uvicorn...
Application startup complete [uvicorn 0.24.0]
```

### Verify Backend Health

```bash
curl https://api.cloud9beverages.com/health
```

Expected response:
```json
{"status": "ok"}
```

### Verify Frontend Loads

Open https://erp.cloud9beverages.com in your browser. You should see the login page.

## Step 6: First Login and Configuration

1. **Login** with the admin credentials:
   - Email: `admin@example.com`
   - Password: `admin@123`

2. **Change the admin password immediately**:
   - Go to **Settings** → **Users**
   - Click on your admin account
   - Set a strong password

3. **Configure Company Details**:
   - Go to **Settings** → **Company Profile**
   - Enter your business name, GST number, address, contact info
   - Update PDF header/footer text

4. **Set Up Warehouse Structure**:
   - Go to **Settings** → **Warehouse**
   - Define your warehouse locations and departments

## Persistent Storage (Uploads, Logs, Backups)

### Important: App Platform Has Ephemeral Storage

Files written to the backend filesystem (e.g., `uploads/`, `logs/`, `backups/`) are **deleted on every deployment**.

### Solution: Enable DigitalOcean Spaces

1. **Create a Spaces Bucket** in DigitalOcean:
   ```bash
   doctl compute spaces create --region nyc3 cloud9-erp-uploads
   ```

2. **Generate an Access Key**:
   - Go to **Account** → **API** → **Spaces Keys**
   - Create a new key, note the `Access Key` and `Secret Key`

3. **Set Environment Variables** in your app (via dashboard or doctl):
   ```bash
   doctl apps update APP_ID --set-env-vars \
     DO_SPACES_ENABLED=true \
     DO_SPACES_BUCKET=cloud9-erp-uploads \
     DO_SPACES_REGION=nyc3 \
     DO_SPACES_ACCESS_KEY=your_access_key \
     DO_SPACES_SECRET_KEY=your_secret_key
   ```

4. **Redeploy**:
   ```bash
   doctl apps create-deployment APP_ID --source-type=github
   ```

The backend will now use Spaces for all file uploads, logs, and backups.

## Database Backups

DigitalOcean Managed Databases include automatic backups. To restore:

1. Go to **Databases** → Your Database → **Backups**
2. Choose a backup and click **Restore**
3. DigitalOcean will create a new database instance; update `DATABASE_URL` in the app environment

Or use `pg_dump` for manual backups:
```bash
pg_dump -h DB_HOST -U DB_USER -d DB_NAME > backup.sql
```

## Monitoring and Troubleshooting

### View App Logs

```bash
# Last 100 lines
doctl apps logs APP_ID

# Follow in real-time
doctl apps logs APP_ID --follow

# Last 1000 lines from backend component only
doctl apps logs APP_ID --component backend --tail 1000
```

### Check Database Connection

If the API won't start, verify the database is reachable:

```bash
# From your local machine (requires access to the DB IP)
psql -h your-db-host -U your-db-user -d your-db-name -c "SELECT 1;"
```

The backend logs will show the redacted database URL:
```
[*] Using database: postgresql://***@db-postgresql-abc.ondigitalocean.com/erp
```

### Common Issues

| Symptom | Cause | Fix |
|---------|-------|-----|
| Frontend shows 404 or blank page | VITE_API_URL not set correctly | Check app.yaml `VITE_API_URL` value |
| API returns CORS error | CORS_ORIGINS mismatch | Update `CORS_ORIGINS` in app.yaml to match frontend domain |
| "Failed to create admin user" in logs | Admin already exists | Safe to ignore; database is ready |
| Database connection timeout | DB not responding | Check managed DB status in dashboard |
| Uploads lost on redeploy | Not using Spaces | Enable DO Spaces (see Persistent Storage) |

## Scaling and Costs

- **Frontend**: Static site, minimal cost (~$1-2/month)
- **Backend**: Single container instance (~$5-12/month depending on size)
- **Database**: Managed PostgreSQL starts at ~$15/month
- **Total**: Expect ~$30-40/month for a small production setup

To scale the backend, update `instance_count` in `.do/app.yaml` and redeploy.

## Redeploying Updates

To push code changes to production:

1. Commit and push to `main` branch:
   ```bash
   git add .
   git commit -m "Feature: new report"
   git push origin main
   ```

2. App Platform automatically triggers a new build and deployment

3. Monitor the deployment:
   ```bash
   doctl apps get APP_ID
   ```

## Rollback

To roll back to a previous deployment:

```bash
# List recent deployments
doctl apps deployments list APP_ID

# Redeploy from a specific commit
doctl apps create-deployment APP_ID --source-type=github --git-commit-sha=abc123def456
```

## Next Steps

- Configure **Email** (SendGrid/SMTP) for password resets and notifications
- Set up **Monitoring** (DigitalOcean Monitoring or external service like Datadog)
- Enable **Auto-scaling** if traffic grows
- Plan **Database upgrades** (upgrade to DigitalOcean's managed Redis if caching is needed)

## Support and Documentation

- DigitalOcean App Platform: https://docs.digitalocean.com/products/app-platform/
- Cloud9 ERP Documentation: See `README.md` and other documentation files in the repo
- Issues or questions: Contact your development team

---

**Deployment Checklist:**

- [ ] Updated `.do/app.yaml` with your GitHub repo
- [ ] Created app via `doctl apps create --spec .do/app.yaml`
- [ ] Set `JWT_SECRET` via secret manager
- [ ] Configured DNS CNAME records
- [ ] Verified `/health` endpoint and frontend load
- [ ] Logged in with admin account
- [ ] Changed admin password
- [ ] Configured company details and warehouse
- [ ] (Optional) Enabled DO Spaces for file uploads
- [ ] Tested a real workflow (create order, view report, etc.)
