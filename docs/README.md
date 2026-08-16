# Documentation Index

Welcome to the Cloud9 ERP documentation. All project documentation is organized in this folder.

## 📁 Quick Navigation

### Setup & Getting Started
- **GETTING_STARTED.md** - Initial project setup
- **QUICK_START.md** - Quick start guide for developers
- **SETUP_GUIDE.md** - Detailed setup instructions

### Deployment
- **DEPLOYMENT_CHECKLIST.md** - Pre-deployment checklist
- **DEPLOYMENT_STEPS.md** - Step-by-step deployment guide
- **DOCKER_DEPLOYMENT_GUIDE.md** - Docker-specific deployment
- **DO_APP_PLATFORM_DEPLOY.md** - DigitalOcean App Platform
- **DROPLET_DEPLOYMENT_GUIDE.md** - DigitalOcean Droplet deployment
- **WEBSITE_DEPLOYMENT_GUIDE.md** - Website/CDN deployment
- **DEPLOYMENT_CADDY.md** - Caddy reverse proxy setup
- **PRODUCTION_RUNBOOK.md** - Production operations guide

### Project Organization
- **FOLDER_STRUCTURE.md** - Backend/frontend folder organization
- **FOLDER_STRUCTURE.md** - File organization guidelines

### Features & Development
- **PHASE1_COMPLETE.md** through **PHASE8_FINAL_SUMMARY.md** - Development phase reports
- **FEATURES_PHASE9.md** - Phase 9 features
- **PASSWORD_RESET_FEATURE.md** - Password reset implementation
- **INVENTORY_FIXES.md** - Inventory system fixes
- **REPORTS_FIXES_SUMMARY.md** - Reports feature fixes

### Troubleshooting & Fixes
- **PRODUCTION_502_DEBUG.md** - Debugging 502 errors
- **QUICK_FIX_GUIDE.md** - Common fixes and solutions
- **CORS_AUTH_FIX_GUIDE.md** - CORS and authentication fixes
- **POST_ENDPOINT_FIX.md** - POST endpoint troubleshooting
- **FIX_VERIFICATION_REPORT.md** - Fix verification results
- **API_ENDPOINT_FIXES.md** - API endpoint fixes

### Maintenance & Cleanup
- **CLEANUP_REPORT.md** - Project cleanup summary
- **CHANGELOG.md** - Change log and history

## 📝 Creating New Documentation

**Important**: All future documentation should be created in the `/docs` folder.

### Naming Convention
Use descriptive, uppercase names:
- `FEATURE_NAME.md`
- `SYSTEM_DEBUG_REPORT.md`
- `IMPLEMENTATION_GUIDE.md`

### File Organization
```
docs/
├── Setup & Configuration (SETUP_*, GETTING_STARTED)
├── Deployment (DEPLOYMENT_*, DOCKER_*, DROPLET_*)
├── Development (PHASE*, FEATURE_*)
├── Troubleshooting (DEBUG_, FIX_, CORS_*)
├── Project Status (*_COMPLETE, *_SUMMARY, *_REPORT)
└── Maintenance (CLEANUP_*, CHANGELOG)
```

## 🔍 Finding Documentation

### By Topic
- **Setup**: Look for SETUP_, GETTING_STARTED, QUICK_START
- **Deployment**: Look for DEPLOYMENT_, DOCKER_, DROPLET_, CADDY_
- **Issues**: Look for DEBUG_, FIX_, TROUBLESHOOTING_
- **Progress**: Look for PHASE_, COMPLETE, SUMMARY, REPORT

### By Frequency
- **Daily Reference**: QUICK_START.md, PRODUCTION_RUNBOOK.md
- **Deployment**: DEPLOYMENT_CHECKLIST.md, DEPLOYMENT_STEPS.md
- **Troubleshooting**: QUICK_FIX_GUIDE.md, PRODUCTION_502_DEBUG.md

## 📋 Current Status

Total Documentation Files: 46

### Recent Additions
- FOLDER_STRUCTURE.md - Project folder organization
- CLEANUP_REPORT.md - Recent cleanup operations

## ⚙️ Git Configuration

All `.md` files in `/docs` are tracked in version control.
The root directory ignores `.md` files (except README.md) to keep the root clean.

See `.gitignore` for details.
