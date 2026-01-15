# Client-Side Setup Guide

**NOTE**: This guide is for the old combined app. For new installations, please use the **sass_client** app instead.

See [SEPARATION.md](./SEPARATION.md) for information about the app separation.

---

**For new installations, use**: [../sass_client/CLIENT_SETUP.md](../sass_client/CLIENT_SETUP.md)

This guide explains how to set up the SaaS Manager app on client ERPNext instances (legacy).

## Installation Steps

### 1. Install the App

```bash
bench get-app sass_manager
bench --site [your-client-site] install-app sass_manager
bench --site [your-client-site] migrate
```

### 2. Configure Site Settings

Add the following to your `site_config.json` file:

```json
{
  "saas_manager_url": "https://your-main-saas-manager.com",
  "client_type": "ERP"
}
```

**Note**: The `saas_api_key` will be automatically generated when you register the site.

### 3. Register the Site

You can register the site in two ways:

#### Option A: Automatic Registration (Recommended)

The site will automatically register on first sync. Just ensure `saas_manager_url` is configured.

#### Option B: Manual Registration

Create a script or use the console:

```python
from sass_manager.utils.client_sync import register_client_site

api_key = register_client_site(
    site_name="My Client Site",
    company="My Company Name",
    client_type="ERP"  # Options: ERP, Mobile POS, Desktop POS, Fiscalisation
)

# Save the API key to site_config.json
# Add: "saas_api_key": "generated-api-key"
```

### 4. Configure Scheduled Sync

Add to your `hooks.py` file in the app:

```python
scheduler_events = {
    "hourly": [
        "sass_manager.utils.client_tasks.hourly"
    ]
}
```

Or if you want to sync more frequently, you can create a custom scheduled job.

### 5. Configure User Limit Enforcement (Optional)

To enforce user limits based on subscription package, add to your `hooks.py`:

```python
doc_events = {
    "User": {
        "before_save": "sass_manager.hooks.user_events.validate_user_limit",
        "on_update": "sass_manager.hooks.user_events.validate_user_limit"
    }
}
```

**Note**: User limit enforcement is optional. If not configured, users can be created without limit checks.

## Configuration Options

### site_config.json Options

| Option | Required | Description | Default |
|--------|----------|-------------|---------|
| `saas_manager_url` | Yes | URL of main SaaS manager app | - |
| `saas_api_key` | Yes* | API key for authentication | Auto-generated |
| `client_type` | No | Type of client (ERP, Mobile POS, Desktop POS, Fiscalisation) | ERP |
| `subscription_package` | No | Package name from main app | - |
| `subscription_active` | No | Whether subscription is active | false |
| `subscription_start_date` | No | Subscription start date | - |
| `subscription_end_date` | No | Subscription end date | - |

*API key is auto-generated on registration, but you can manually set it if needed.

## Manual Sync

To manually trigger a sync:

```python
from sass_manager.utils.client_sync import sync_to_main_app
sync_to_main_app()
```

## Check Subscription Status

```python
from sass_manager.utils.client_sync import get_site_data
data = get_site_data()
print(data)
```

## Troubleshooting

### Sync Not Working

1. Check that `saas_manager_url` is correctly configured
2. Verify API key is set in `site_config.json`
3. Check Error Log for sync errors
4. Ensure main app is accessible from client site

### User Limit Not Enforcing

1. Verify hooks are configured in `hooks.py`
2. Check subscription status in main app
3. Verify package has `max_users` set
4. Check Error Log for limit check errors

### Registration Failed

1. Ensure main app is accessible
2. Check network connectivity
3. Verify site URL is correct
4. Check Error Log for registration errors

## Support

For issues, check the Error Log in ERPNext or contact: akingbolahan12@gmail.com
