# Deployment Instructions: Approval Notification Persistence

## Changes Made

This deployment includes the following updates:

### Backend Changes
1. **Database Migration**: Added `is_approved` field to `notifications` table
   - File: `backend/alembic/versions/359da806863c_add_is_approved_field_to_notifications.py`
   - Default: `FALSE` for all existing notifications
   - This field tracks whether a notification has been explicitly approved (separate from `is_read`)

2. **Model Updates**: 
   - Added `is_approved` field to Notification model
   - Updated notification creation to set `is_approved=False` for approval notifications
   - Changed notification type from `approval_required` to `approval`

3. **New API Endpoint**:
   - `POST /notifications/{notification_id}/approve`
   - Marks notification as approved and deletes it from the database
   - Only callable by the notification's owner user

4. **Updated Endpoint**:
   - When orders are approved, the related approval notification is marked as `is_approved=True`

### Frontend Changes
1. **API Updates**:
   - Added `is_approved` field to NotificationResponse interface
   - Added new `approve()` method to notificationsApi

2. **UI Updates**:
   - Added "Approve" button for approval notifications (type="approval")
   - Button only shows when notification is not yet approved
   - Approval button calls the new approve endpoint
   - Approval notifications styled with amber highlight to distinguish from regular notifications

3. **Hooks**:
   - Added `useApproveNotification()` mutation hook

## Deployment Steps

### Step 1: SSH into Production Server
```bash
ssh your-user@64.227.191.1
cd ~/c9-erp
```

### Step 2: Pull Latest Code
```bash
git pull origin main
```

### Step 3: Pull Latest Docker Images
```bash
docker compose -f docker-compose.production.yml pull
```

### Step 4: Run Database Migration
```bash
docker compose -f docker-compose.production.yml exec backend python -m alembic upgrade head
```

### Step 5: Rebuild and Deploy Services
```bash
docker compose -f docker-compose.production.yml down
docker compose -f docker-compose.production.yml up -d
```

### Step 6: Verify Deployment
```bash
# Check if all services are running
docker compose -f docker-compose.production.yml ps

# Check backend logs
docker compose -f docker-compose.production.yml logs backend | tail -20

# Verify database migration
docker compose -f docker-compose.production.yml exec backend python -m alembic current
```

### Step 7: Test in Production
1. Navigate to the application at https://erp.thecloud9corp.com
2. Create a new order and submit for approval
3. Verify that the approver receives an approval notification
4. Check that clicking the notification shows the approve button (not just a read button)
5. Click Approve and verify the notification is removed

## Rollback Instructions

If issues occur, you can rollback:

```bash
# Revert database migration
docker compose -f docker-compose.production.yml exec backend python -m alembic downgrade -1

# Stop services
docker compose -f docker-compose.production.yml down

# Pull previous code (if needed)
git checkout <previous-commit-hash>

# Restart services
docker compose -f docker-compose.production.yml up -d
```

## Database Backup

Before deploying, ensure you have a recent backup of the PostgreSQL database:

```bash
# Create a backup
docker compose -f docker-compose.production.yml exec postgres \
  pg_dump -U postgres cloud9_erp > ~/backups/cloud9_erp_$(date +%Y%m%d_%H%M%S).sql
```

## Breaking Changes

- Approval notification type changed from `approval_required` to `approval`
- Any custom code referencing `approval_required` type should be updated to use `approval`

## Monitoring After Deployment

1. Check backend logs for any errors:
   ```bash
   docker compose -f docker-compose.production.yml logs -f backend
   ```

2. Monitor database performance after migration:
   - The new index on `(user_id, type, is_approved)` should improve query performance for filtering approval notifications

3. Verify user experience:
   - Approval notifications should persist until explicitly approved
   - Regular notifications should work as before
