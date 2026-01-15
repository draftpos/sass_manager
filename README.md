# SaaS Manager

Main SaaS management app for managing multiple ERPNext client sites. This app should be installed on your main server to manage all client instances.

## Features

- **Site Registration**: Register and manage all client ERPNext sites
- **Subscription Packages**: Define subscription packages with user limits and pricing
- **Site Data Sync**: Receive and store synced data from client sites
- **User Deposits**: Track payments and deposits from clients
- **Reports**: Generate reports on site usage, subscriptions, and revenue

## Installation

### Step 1: Install the App

```bash
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
- **Daily**: Check subscription expiry
- **Weekly**: Optional cleanup tasks

## Client App Setup

Client sites should install the **sass_client** app. See the [sass_client documentation](../sass_client/README.md) for client-side setup.

## API Endpoints

The app provides the following API endpoints for client sites:

- `/api/method/sass_manager.api.site_api.register_site` - Register a new client site
- `/api/method/sass_manager.api.site_api.sync_site_data` - Sync site data from client
- `/api/method/sass_manager.api.site_api.get_subscription_status` - Get subscription status
- `/api/method/sass_manager.api.site_api.update_subscription` - Update subscription details

## Usage

### Register a Client Site

Client sites will automatically register on first sync, or you can manually register them in the Site Registration doctype.

### Activate Subscription

1. Go to **SaaS Manager > Site Registration**
2. Find the registered site
3. Set:
   - Subscription Package
   - Subscription Start Date
   - Subscription End Date
   - Subscription Status: Active
   - Is Active: ✓

### Monitor Site Data

1. Go to **SaaS Manager > Site Data Sync**
2. View synced data from client sites
3. Create custom reports using the data

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

## DocTypes

1. **Subscription Package**: Define subscription packages
2. **Site Registration**: Register and manage client sites
3. **Site Data Sync**: Store synced data from client sites
4. **User Deposit**: Track payments and deposits
5. **Package Feature**: Define features for packages

## Security

- API key authentication for all client connections
- Guest access with API key validation
- Permission-based access control
- Secure API key generation

## License

MIT

## Support

For issues or questions:
- Email: akingbolahan12@gmail.com
- Check Error Log in ERPNext
- Review API documentation
