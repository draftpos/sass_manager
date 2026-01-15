# SaaS Manager - Features Overview

## Core Features

### 1. Site Registration & Management
- Register client ERPNext sites
- Track site information (URL, IP, company, client type)
- Generate unique API keys for each site
- Monitor site status (Active/Expired/Pending)

### 2. Subscription Package Management
- Create subscription packages with:
  - Package name and code
  - Maximum user limits
  - Pricing information
  - Feature lists
- Enable/disable packages
- Track package usage across sites

### 3. Site Data Synchronization
- Automatic data sync from client sites
- Tracks:
  - Sales invoices count
  - Credit notes count
  - Purchase invoices count
  - Stock reconciliations count
  - Active users count
  - Total companies count
  - Subscription status
- Historical sync data for reporting

### 4. User Limit Enforcement
- Enforce user limits based on subscription package
- Automatic validation when creating/enabling users
- Configurable on client sites

### 5. Payment & Deposit Management
- Track user deposits
- Support for multiple payment methods:
  - Manual
  - Payment Gateway
  - Bank Transfer
  - Cash
- Link deposits to subscriptions
- Auto-apply deposits to extend subscriptions

### 6. Reporting & Analytics
- Site summary statistics
- Package usage statistics
- Revenue tracking
- User count per site
- Transaction counts
- Custom reports using Site Data Sync

## Client Types Supported

1. **ERP**: Standard ERPNext instance
2. **Mobile POS**: Mobile Point of Sale
3. **Desktop POS**: Desktop Point of Sale
4. **Fiscalisation**: Fiscal compliance systems

## API Endpoints

### Registration
- `register_site`: Register a new client site
- Returns API key for future authentication

### Data Sync
- `sync_site_data`: Sync site data to main app
- Called automatically by client sites hourly

### Subscription Management
- `get_subscription_status`: Get current subscription status
- `update_subscription`: Update subscription details (admin use)

### Reports
- `get_site_summary`: Get overall statistics
- `get_site_details`: Get detailed site information
- `get_package_statistics`: Get package usage statistics

## Scheduled Tasks

### Main App
- **Daily**: Check and update expired subscriptions
- **Weekly**: Optional cleanup of old sync data

### Client App
- **Hourly**: Sync site data to main app

## Data Flow

```
Client Site → Sync Data → Main App → Store in Site Data Sync
                ↓
         Update Site Registration
                ↓
         Generate Reports
```

## Security Features

- API key authentication
- Guest access for API endpoints (with API key validation)
- Permission-based access control
- Secure API key generation

## Integration Points

### ERPNext Integration
- User limit enforcement hooks
- Automatic data collection
- Scheduled sync jobs

### Payment Gateway Integration
- Ready for payment gateway integration
- Manual payment option available
- Transaction reference tracking

## Customization

- Custom reports using Site Data Sync doctype
- Custom subscription packages
- Configurable sync frequency
- Custom client types

## Future Enhancements

Potential features for future versions:
- Real-time sync via webhooks
- Advanced analytics dashboard
- Automated billing
- Multi-currency support
- Email notifications for expiry
- Usage alerts
