# Environment Switching Guide 🔄

## Overview
The Dataverse Web API Studio now supports **multiple environment switching** with a convenient dropdown selector. You can easily switch between DEV, PROD, SANDBOX, UAT, or any custom environments you define.

## Features ✨
- **Dynamic Environment Detection**: Automatically detects all `ORG_URL_*` variables in your `.env` file
- **Easy Switching**: Simple dropdown selector to switch between environments
- **Flexible Configuration**: Add as many environments as you need
- **Secure**: Only the URL changes; credentials remain the same across environments

## How to Configure Environments

### 1. Update Your `.env` File

Instead of a single `ORG_URL` variable, define multiple environment-specific URLs:

```env
# Authentication (same for all environments)
TENANT_ID=your-azure-tenant-id
CLIENT_ID=your-app-registration-client-id
CLIENT_SECRET=your-app-registration-client-secret

# Environment URLs - Add as many as you need
ORG_URL_DEV=https://your-org-dev.crm4.dynamics.com/
ORG_URL_PROD=https://your-org.crm4.dynamics.com/
ORG_URL_SANDBOX=https://your-org-sandbox.crm4.dynamics.com/
ORG_URL_UAT=https://your-org-uat.crm4.dynamics.com/
ORG_URL_TEST=https://your-org-test.crm4.dynamics.com/
```

### 2. Naming Convention

The application extracts environment names from the variable suffix:
- `ORG_URL_DEV` → **DEV**
- `ORG_URL_PROD` → **PROD**
- `ORG_URL_SANDBOX` → **SANDBOX**
- `ORG_URL_UAT` → **UAT**
- `ORG_URL_MYENV` → **MYENV**

You can use **any name** you want after `ORG_URL_`.

## Using the Environment Selector

### In the Application

1. **Launch the application**: `python dataverse_api_gui.py`

2. **Environment Dropdown**: At the top of the authentication panel, you'll see a new "Environment:" dropdown

3. **Select Your Environment**: 
   - Click the dropdown to see all available environments
   - Select the environment you want to connect to (e.g., DEV, PROD)
   - The Org URL field will automatically update

4. **Connect**: Click "🔗 Connect to Dataverse" to authenticate with the selected environment

5. **Switch Anytime**: 
   - You can switch environments before connecting
   - After switching, click "Connect" again to authenticate with the new environment

### Default Environment

The application will default to:
1. **DEV** environment if it exists
2. Otherwise, the **first environment** found in your `.env` file

## Migration from Old Configuration

If you have an existing `.env` file with `ORG_URL`, update it as follows:

### Before:
```env
ORG_URL=https://your-org.crm4.dynamics.com/
```

### After:
```env
ORG_URL_PROD=https://your-org.crm4.dynamics.com/
ORG_URL_DEV=https://your-org-dev.crm4.dynamics.com/
```

## Example Use Cases

### 1. Developer Testing
- Work in **DEV** environment during development
- Switch to **UAT** for user acceptance testing
- Switch to **PROD** for production operations

### 2. Multi-Tenant Setup
- `ORG_URL_CLIENT1` for Client 1's environment
- `ORG_URL_CLIENT2` for Client 2's environment
- `ORG_URL_CLIENT3` for Client 3's environment

### 3. Regional Deployments
- `ORG_URL_US` for US region
- `ORG_URL_EU` for European region
- `ORG_URL_APAC` for Asia-Pacific region

## Best Practices 🎯

1. **Always use meaningful names**: Use clear environment names (DEV, PROD, SANDBOX) rather than generic names

2. **Keep credentials consistent**: Use the same TENANT_ID, CLIENT_ID, and CLIENT_SECRET across environments when possible

3. **Document your environments**: Comment each URL in your `.env` file to explain what it's for:
   ```env
   # Production environment - Live customer data
   ORG_URL_PROD=https://your-org.crm4.dynamics.com/
   
   # Development environment - Gaurav's test data
   ORG_URL_DEV=https://your-org-dev.crm4.dynamics.com/
   ```

4. **Use separate app registrations**: For enhanced security, consider using different app registrations (CLIENT_ID/SECRET) for production vs. non-production environments

5. **Double-check before operations**: Always verify the selected environment before performing operations, especially destructive ones (DELETE, UPDATE)

## Troubleshooting 🔧

### No Environments Showing in Dropdown
- **Cause**: No `ORG_URL_*` variables found in `.env` file
- **Solution**: Add at least one `ORG_URL_*` variable (e.g., `ORG_URL_DEV`)

### Wrong Environment Selected
- **Cause**: Default environment may not be what you expect
- **Solution**: Always verify the selected environment before connecting

### URL Field is Empty
- **Cause**: Environment variable value is empty in `.env`
- **Solution**: Ensure your environment variables have actual URLs assigned

### Can't Connect After Switching
- **Cause**: You're still connected to the previous environment
- **Solution**: Click "🔗 Connect to Dataverse" again after switching environments

## Security Considerations 🔒

1. **Never commit `.env` file**: Keep your `.env` file in `.gitignore`
2. **Use environment-specific secrets**: Consider using different CLIENT_SECRET values for each environment
3. **Verify permissions**: Ensure your app registration has appropriate permissions for each environment
4. **Test in non-prod first**: Always test operations in DEV/UAT before running in PROD

## API Changes

### For Developers Extending the Code

The `DataverseClient` class remains unchanged. The environment switching is handled at the GUI level:

```python
# The GUI now loads all ORG_URL_* variables
self.available_environments = {
    'DEV': 'https://org-dev.crm4.dynamics.com/',
    'PROD': 'https://org.crm4.dynamics.com/',
    # ... more environments
}

# When user selects an environment, the org_url field is updated
# Then authentication proceeds as normal
self.client = DataverseClient(tenant, client_id, secret, org_url)
```

## Files Updated

- **`.env`**: Updated to use `ORG_URL_*` pattern
- **`dataverse_api_gui.py`**: Added environment selector and switching logic
- **`docs/env.example`**: Updated template
- **`docs/setup_guide.md`**: Updated configuration instructions
- **`docs/QUICK_REFERENCE.md`**: Updated usage instructions
- **`README.md`**: Updated quick start guide

## Support

For questions or issues:
1. Check this guide first
2. Review the [setup_guide.md](docs/setup_guide.md)
3. Check the [QUICK_REFERENCE.md](docs/QUICK_REFERENCE.md)

---

**Happy Environment Switching! 🚀**
