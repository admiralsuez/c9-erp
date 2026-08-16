# Cloud9 ERP System

A comprehensive inventory and order management system for Cloud9, built with Python/FastAPI, PostgreSQL, and React.

## Project Structure

```
.
├── backend/                    # FastAPI backend
│   ├── app/
│   │   ├── core/              # Config, database, auth
│   │   ├── routers/           # API endpoints by domain
│   │   ├── services/          # Business logic
│   │   ├── repositories/      # Data access
│   │   └── models.py          # SQLAlchemy models
│   ├── tests/                 # Unit and integration tests
│   ├── main.py                # FastAPI entry point
│   └── requirements.txt
├── frontend/                  # React + TypeScript
├── docker-compose.yml         # Local development setup
└── README.md
```

## Quick Start

### Prerequisites
- Docker and Docker Compose

### Run the Stack

```bash
docker-compose up --build
```

This will start:
- **PostgreSQL** on `5432`
- **FastAPI** on `8000`
- **React** on `3000`

### Initial Setup

Once the API is running, populate the database with seed data:

```bash
curl -X POST http://localhost:8000/seed-data
```

Or manually via Python:

```bash
python backend/seed_data.py
```

## Architecture

### Backend
- **Framework**: FastAPI
- **Database**: PostgreSQL + SQLAlchemy ORM + Alembic migrations
- **Auth**: JWT + bcrypt
- **Testing**: pytest + pytest-asyncio

### Frontend
- **Framework**: React 18 + TypeScript
- **UI Library**: shadcn/ui
- **Forms**: React Hook Form
- **Data Fetching**: TanStack Query
- **Tables**: TanStack Table

## Development Workflow

### Phase 1: Auth + RBAC + Inventory Core + Settings (Current)

**Goals**:
1. Get Docker Compose running ✓
2. Implement JWT auth + RBAC
3. Inventory CRUD with transaction ledger
4. Vendor dedup with fuzzy search
5. Warehouse location hierarchy
6. Seed data + tests

**Definition of Done**:
- [ ] Admin logs in, creates Manager and Warehouse User
- [ ] Warehouse User restocks an item; ledger updates correctly
- [ ] Restock by permission-less role returns 403
- [ ] Vendor "ABC Traders" then "abc traders" is blocked/flagged
- [ ] Every quantity change visible in transaction history
- [ ] Barcode lookup works
- [ ] Soft-deleted records are restorable
- [ ] Tests cover: permissions, ledger math, vendor dedup

### Future Phases
- Phase 2: Orders + Reservation + Approval Matrix
- Phase 3: Documents + Requisition PDF + Signature Workflow
- Phase 4: Returnable Asset Lifecycle + Returns Module
- Phase 5: Stock Transfers
- Phase 6: Reports + Dashboard + Notifications
- Phase 7: Offline Support + Mobile-First UX
- Phase 8+: HRMS, CRM, Purchase, Finance modules (optionally)

## Important Rules

1. **Never build all phases at once** - focus on one, get it to Definition of Done
2. **Ledger is source of truth** - `current_quantity` and `reserved_quantity` are caches written only by specific functions
3. **Soft delete everything** - no hard deletes; support restore
4. **Domain-Driven Design** - each module owns its models, services, repos, routes
5. **Atomic transactions** - stock movements are DB transactions, never partial
6. **Test auth, ledger, and money** - non-negotiable
7. **No direct quantity writes** - only through `inventory_transactions` rows

## API Routes (Phase 1)

### Authentication
```
POST   /auth/login              -> { access_token, refresh_token }
POST   /auth/refresh            -> { access_token }
POST   /auth/logout             -> { success }
```

### Users & Roles
```
GET    /users                   -> list (users.manage required)
POST   /users                   -> create (users.manage required)
GET    /users/{id}
PATCH  /users/{id}
DELETE /users/{id}              -> soft delete
POST   /users/{id}/restore      -> Admin only

GET    /roles
GET    /permissions
```

### Settings
```
GET    /settings
PATCH  /settings                -> Admin only
```

### Vendors
```
GET    /vendors?search=&page=&size=
POST   /vendors                 -> 409 + fuzzy matches on duplicate
GET    /vendors/{id}
PATCH  /vendors/{id}
DELETE /vendors/{id}            -> soft delete
GET    /vendors/{id}/summary
```

### Warehouse
```
GET    /warehouses              -> full hierarchy
POST   /warehouses
POST   /warehouses/{id}/zones
POST   /warehouses/{id}/zones/{zone_id}/racks
```

### Inventory
```
GET    /inventory/categories
POST   /inventory/categories
GET    /inventory/items?search=&category=&low_stock=&page=&size=
POST   /inventory/items         -> creates item + opening_balance transaction
GET    /inventory/items/{id}    -> includes available_quantity
PATCH  /inventory/items/{id}    -> metadata only, NOT quantity
DELETE /inventory/items/{id}    -> soft delete
GET    /inventory/items/{id}/transactions
GET    /inventory/items/barcode/{barcode}

POST   /inventory/restock       -> { item_id, quantity, reason }
POST   /inventory/adjust        -> { item_id, new_quantity, reason }
```

### Audit Log
```
GET    /audit-logs?user_id=&action=&entity_type=&page=&size=   (Admin only)
```

## Testing

Run all tests:
```bash
pytest backend/tests -v
```

Run specific test:
```bash
pytest backend/tests/test_auth.py::test_login -v
```

Run with coverage:
```bash
pytest backend/tests --cov=app --cov-report=html
```

## Environment Variables

Create `.env` in the backend directory:

```
DATABASE_URL=postgresql://erp_user:erp_password@postgres:5432/erp_db
JWT_SECRET=your-very-secret-key-change-in-production
JWT_ALGORITHM=HS256
JWT_EXPIRATION_HOURS=24
REFRESH_TOKEN_EXPIRATION_DAYS=30
DEBUG=true
SQL_ECHO=false
```

## Database Migrations

Create a new migration:
```bash
alembic revision --autogenerate -m "Add some feature"
```

Apply migrations:
```bash
alembic upgrade head
```

## Contributing

- Keep routers thin (validation + permission checks only)
- Business logic goes in services
- Data access goes in repositories
- Write tests for auth, transactions, and state transitions
- Follow the Domain-Driven Design pattern

## License

Internal use only.
