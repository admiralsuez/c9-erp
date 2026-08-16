# Cloud9 ERP - Project Folder Structure

## Overview
Your project is now organized with dedicated folders for different file types, making maintenance and deployment cleaner.

## Backend Organization

```
backend/
├── app/                      # FastAPI application code
│   ├── api/                  # API routes and endpoints
│   ├── models/               # Pydantic models and schemas
│   ├── services/             # Business logic
│   ├── db/                   # Database models and sessions
│   └── core/                 # Core utilities and config
│
├── alembic/                  # Database migrations
│   ├── versions/             # Migration files
│   └── alembic.ini           # Migration config
│
├── logs/                     # Application logs (Git-ignored)
│   └── .gitkeep              # Placeholder for version control
│
├── uploads/                  # User-generated content
│   ├── documents/            # Document uploads (Git-ignored)
│   │   └── .gitkeep
│   └── images/               # Image files (Git-ignored)
│       └── .gitkeep
│
├── temp/                     # Temporary files (Git-ignored)
│   └── .gitkeep              # Placeholder for version control
│
├── config/                   # Configuration files
│   └── .gitkeep
│
├── requirements.txt          # Python dependencies
├── main.py                   # Application entry point
└── .env                      # Environment variables (not in Git)
```

## Frontend Organization

```
frontend/
├── src/
│   ├── pages/                # Page components
│   ├── components/           # Reusable components
│   ├── services/             # API service calls
│   └── utils/                # Utility functions
│
├── public/                   # Static assets
├── package.json              # Node dependencies
└── .env.local                # Environment variables (not in Git)
```

## File Type Guidelines

### Logs (`backend/logs/`)
- **What goes here**: Application logs (*.log files)
- **Git**: Ignored (no version control needed)
- **Cleanup**: Safe to delete old logs periodically
- **Example**: `app.log`, `error.log`, `access.log`

### Uploads (`backend/uploads/documents/` & `backend/uploads/images/`)
- **What goes here**: User-uploaded files
- **Git**: Ignored (stored separately or in cloud storage)
- **Subdirectories**: 
  - `documents/` - PDFs, Word docs, spreadsheets
  - `images/` - Photos, diagrams, product images
- **Example**: Child variant photos, inventory images

### Temporary Files (`backend/temp/`)
- **What goes here**: Cache, temp processing files
- **Git**: Ignored
- **Cleanup**: Can be cleared between deployments
- **Example**: Processing cache, intermediate files

### Configuration (`backend/config/`)
- **What goes here**: Config files (*.yaml, *.json, *.ini)
- **Git**: Tracked (with sensitive values in .env)
- **Example**: Database config, feature flags

## .gitignore Rules

The updated `.gitignore` includes:
- Ignores content in logs, temp, and uploads folders
- Preserves folder structure with `.gitkeep` files
- Maintains backwards compatibility with existing patterns

## Development Workflow

### Running the Application
```bash
cd backend
python main.py
```

### Adding Logs
```python
# Logs automatically save to backend/logs/
import logging
logger = logging.getLogger(__name__)
logger.info("Message")
```

### Uploading Files
```python
# Images save to backend/uploads/images/
# Documents save to backend/uploads/documents/
from app.services.image_service import upload_image
result = upload_image(file, item_id)
```

## Deployment Considerations

- **Logs folder**: Can be mounted as a volume in Docker
- **Uploads folder**: Should be backed up or stored in cloud (S3/DigitalOcean Spaces)
- **Temp folder**: Can be cleared on container restart
- **Config folder**: Include in version control, exclude `.env`

## Maintenance

### Cleaning Old Logs
```bash
# Remove logs older than 7 days
find backend/logs -name "*.log" -mtime +7 -delete
```

### Checking Folder Sizes
```bash
# View disk usage by folder
du -sh backend/*/
```

## References

- **Image Upload Service**: `backend/app/services/image_service.py`
- **Current Configuration**: `backend/.env` (not in Git)
- **Version Control**: `.gitignore` (root directory)
