# SaaS Manager - Installation Guide

## Overview

SaaS Manager is a comprehensive system for managing multiple ERPNext instances. It consists of:

1. **Main App**: Installed on your main server to manage all client sites
2. **Client App**: Installed on each client ERPNext instance to sync data and enforce limits

## Main App Installation

### Step 1: Install the App

```bash
cd /path/to/your/bench
bench get-app sass_manager
bench --site [your-main-site] install-app sass_manager
bench --site [your-main-site] migrate
```

### Step 2: Create Subscription Packages

1. Go to **SaaS Manager > Subscription Package**
2. Create packages with:
   - Package Name (e.g., "Basic", "Premium", "Enterprise")
   - Package Code (unique identifier)
   - Maximum Users allowed
   - Price and Currency
   - Features (optional)

### Step 3: Configure Scheduled Jobs

The app automatically sets up scheduled jobs:
- **Hourly**: Placeholder for server-side tasks
- **Daily**: Check subscription expiry
- **Weekly**: Optional cleanup tasks

### Step 4: Set Up API Access

The API endpoints are automatically available:
- `/api/method/sass_manager.api.site_api.register_site`
- `/api/method/sass_manager.api.site_api.sync_site_data`
- `/api/method/sass_manager.api.site_api.get_subscription_status`
- `/api/method/sass_manager.api.site_api.update_subscription`

## Client App Installation

See [CLIENT_SETUP.md](./CLIENT_SETUP.md) for detailed client-side setup instructions.

## Quick Start

### 1. Register a Client Site

From the client site, the registration happens automatically on first sync, or manually:

```python
from sass_manager.utils.client_sync import register_client_site

api_key = register_client_site(
    site_name="Client Site Name",
    company="Company Name",
    client_type="ERP"
)
```

### 2. Activate Subscription

In the main app:
1. Go to **SaaS Manager > Site Registration**
2. Find the registered site
3. Set:
   - Subscription Package
   - Subscription Start Date
   - Subscription End Date
   - Subscription Status: Active
   - Is Active: ✓

### 3. Monitor Site Data

1. Go to **SaaS Manager > Site Data Sync**
2. View synced data from client sites
3. Create custom reports using the data

## Features

### Main App Features

- **Site Registration**: Manage all client sites
- **Subscription Packages**: Define packages with user limits
- **Site Data Sync**: Receive and store synced data
- **User Deposits**: Track payments
- **Reports**: Generate usage and revenue reports

### Client App Features

- **Automatic Sync**: Syncs data hourly to main app
- **User Limit Enforcement**: Enforces user limits based on package
- **Subscription Status Check**: Checks subscription from main app

## API Usage Examples

### Register Site

```bash
curl -X POST https://your-main-app.com/api/method/sass_manager.api.site_api.register_site \
  -H "Content-Type: application/json" \
  -d '{
    "site_url": "https://client-site.com",
    "site_name": "Client Site",
    "company": "Company Name",
    "client_type": "ERP"
  }'
```

### Sync Data

```bash
curl -X POST https://your-main-app.com/api/method/sass_manager.api.site_api.sync_site_data \
  -H "Content-Type: application/json" \
  -d '{
    "api_key": "your-api-key",
    "data": {
      "total_sales_invoices": 100,
      "active_users": 5,
      "company": "Company Name"
    }
  }'
```

## Reports

Use the report API to get summaries:

```python
import frappe
from sass_manager.api.reports import get_site_summary, get_package_statistics

# Get overall summary
summary = get_site_summary()

# Get package statistics
package_stats = get_package_statistics()
```

## Troubleshooting

### Sites Not Syncing

1. Check client site configuration (`site_config.json`)
2. Verify API key is correct
3. Check Error Log on both main and client sites
4. Ensure main app is accessible from client site

### User Limits Not Working

1. Verify hooks are configured on client site
2. Check subscription package has `max_users` set
3. Verify subscription is active
4. Check Error Log for limit check errors

### Subscription Not Updating

1. Check subscription dates in Site Registration
2. Verify daily scheduled job is running
3. Manually update subscription status if needed

## Support

For issues or questions:
- Email: akingbolahan12@gmail.com
- Check Error Log in ERPNext
- Review API documentation in README.md
