# App Separation - SaaS Manager and SaaS Client

## Overview

The SaaS management system has been separated into two distinct apps:

1. **sass_manager** - Main management app (server-side)
2. **sass_client** - Client-side app for ERPNext instances

This separation provides:
- **Security**: Client sites don't have access to management features
- **Separation of Concerns**: Clear distinction between management and client functionality
- **Easier Deployment**: Install only what's needed on each site
- **Better Maintenance**: Independent updates and versioning

## App Responsibilities

### SaaS Manager (sass_manager)

**Install on**: Main server only

**Responsibilities**:
- Manage all client site registrations
- Define subscription packages
- Receive and store synced data from clients
- Track payments and deposits
- Generate reports and analytics
- Provide API endpoints for client communication

**DocTypes**:
- Subscription Package
- Site Registration
- Site Data Sync
- User Deposit
- Package Feature

**No Client-Side Code**: This app contains NO client-side utilities or hooks.

### SaaS Client (sass_client)

**Install on**: Each client ERPNext instance

**Responsibilities**:
- Sync site data to main app
- Enforce user limits based on subscription
- Register site with main app
- Check subscription status

**Features**:
- Automatic hourly sync
- User limit enforcement hooks
- Site registration utilities
- Subscription status checking

**No Management Code**: This app contains NO management features or doctypes.

## Installation Guide

### Main Server Setup

```bash
# Install SaaS Manager
bench get-app sass_manager
bench --site [main-site] install-app sass_manager
bench --site [main-site] migrate
```

### Client Site Setup

```bash
# Install SaaS Client
bench get-app sass_client
bench --site [client-site] install-app sass_client
bench --site [client-site] migrate

# Configure site_config.json
# Add: "saas_manager_url": "https://your-main-app.com"
```

## Migration from Combined App

If you previously had the combined app:

1. **On Main Server**:
   - Keep `sass_manager` app
   - Remove any client-side utilities (already done)
   - Update hooks.py (already done)

2. **On Client Sites**:
   - Install `sass_client` app
   - Configure `saas_manager_url` in site_config.json
   - Site will auto-register on first sync

## Communication Flow

```
Client Site (sass_client)
    ↓
    Sync Data via API
    ↓
Main Server (sass_manager)
    ↓
    Store in Site Data Sync
    ↓
    Generate Reports
```

## API Communication

The client app communicates with the manager app via REST API:

- **Registration**: `sass_manager.api.site_api.register_site`
- **Data Sync**: `sass_manager.api.site_api.sync_site_data`
- **Status Check**: `sass_manager.api.site_api.get_subscription_status`

All endpoints require API key authentication.

## Security Benefits

1. **No Management Access**: Client sites cannot access management features
2. **API Key Authentication**: Secure communication between apps
3. **Read-Only Client**: Client app only reads data, doesn't modify management records
4. **Separate Permissions**: Different permission sets for each app

## File Structure

### sass_manager/
```
sass_manager/
├── api/              # API endpoints
├── doctype/         # Management doctypes
├── tasks.py         # Scheduled tasks
└── hooks.py         # Manager-side hooks only
```

### sass_client/
```
sass_client/
├── utils/           # Client utilities
│   ├── client_sync.py
│   ├── user_limit.py
│   └── client_tasks.py
├── hooks/          # Client hooks
│   └── user_events.py
└── hooks.py         # Client-side hooks config
```

## Support

For issues or questions:
- Email: akingbolahan12@gmail.com
- Check respective app documentation
- Review Error Logs in ERPNext
