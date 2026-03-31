# CERN Application Portal Configuration Guide

## Finding the Right Settings for Client Credentials

The error "Client not enabled to retrieve service account" means your OIDC application needs to be configured to support the **Client Credentials Grant** flow. Here's how to find and enable it:

### Step 1: Navigate to Your Application
1. Go to https://application-portal.web.cern.ch
2. Find your `cds-mcp` application
3. Click on it to open the application details

### Step 2: Look for SSO Registration Tab
1. Look for tabs like:
   - **SSO Registration**
   - **Authentication**
   - **OIDC Configuration**
   - **Single Sign-On**

### Step 3: Find OIDC Settings
Once in the SSO/OIDC configuration section, look for these settings:

#### Option A: Grant Types Section
Look for a section called "Grant Types" or "Allowed Grant Types":
- ☐ Authorization Code
- ☐ Implicit
- ☐ **Client Credentials** ← **ENABLE THIS**
- ☐ Resource Owner Password

#### Option B: Client Type Settings
Look for "Client Type" or "Application Type":
- ☐ Public Client
- ☐ **Confidential Client** ← **SELECT THIS**

#### Option C: Advanced Settings
Look for advanced or additional settings:
- ☐ **Service Account Enabled** ← **ENABLE THIS**
- ☐ **Direct Access Grants Enabled**
- ☐ **Standard Flow Enabled**

#### Option D: Authentication Flow Settings
Look for authentication flow options:
- ☐ **Client Credentials Flow** ← **ENABLE THIS**
- ☐ Authorization Code Flow
- ☐ Implicit Flow

### Step 4: Client Authentication Method
Ensure the client authentication is set to:
- **Client Secret (Post)** or **Client Secret (Basic)**

### Step 5: Save and Apply
1. Save the configuration
2. The changes might need approval
3. Wait a few minutes for the changes to propagate

## Alternative: Check Application Description

When you registered the application, you should have seen a checkbox or option like:
- "My application will need to get tokens using its own client ID and secret"
- "Enable service-to-service authentication"
- "Client Credentials Grant"

If you didn't check this during registration, you might need to:
1. Edit the application
2. Look for these options in the basic settings
3. Or re-register the application with the correct settings

## What to Look For in the Interface

The CERN Application Portal interface might show:
- **Capabilities** section
- **OAuth 2.0 / OIDC Settings**
- **Grant Types** dropdown or checkboxes
- **Client Features** section

## If You Can't Find These Options

If none of these options are visible:
1. Your application might not be approved yet
2. You might need to contact CERN IT support
3. The application might need to be re-registered with different initial settings

## Testing After Configuration

Once you enable Client Credentials:
1. Wait 5-10 minutes for changes to propagate
2. Run the debug script again:
   ```bash
   CERN_CLIENT_ID=cds-mcp CERN_CLIENT_SECRET=ODDdttkBE9KXs0vMnbQa3HOse2rqmM5o uv run python debug_auth.py
   ```
3. You should see a successful token acquisition instead of the "unauthorized_client" error

## Contact Information

If you still can't find these settings:
- CERN Service Portal: https://cern.service-now.com
- Search for "Application Portal" or "SSO" support
- Or email the Authentication Service team
