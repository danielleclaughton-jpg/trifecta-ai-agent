# Microsoft Graph / Azure AD Setup Guide
# Enable Outlook Email Sending for Trifecta AI Agent

## Why You Need This

The Flask API (`/api/leads/{id}/approve-send`) sends program-info emails to leads via
Microsoft Graph on behalf of info@trifectaaddictionservices.com. Without these credentials,
email sending fails with "Microsoft Graph credentials not configured."

## What's Missing (from .env.local)

```
MS_CLIENT_ID=        <-- EMPTY — needs Azure App Registration Client ID
MS_CLIENT_SECRET=    <-- EMPTY — needs Azure App Registration Secret
MS_TENANT_ID=        <-- EMPTY — needs your Azure AD Tenant ID
GRAPH_CLIENT_SECRET= <-- EMPTY — same as MS_CLIENT_SECRET (legacy alias)
```

---

## Step-by-Step: Get Credentials from Azure Portal

### Step 1: Sign in to Azure Portal
1. Go to: https://portal.azure.com
2. Sign in with your Microsoft 365 / Trifecta account

### Step 2: Create an App Registration
1. Search for **"App registrations"** in the top search bar
2. Click **"New registration"**
3. Fill in:
   - **Name:** `Trifecta AI Agent`
   - **Supported account types:** `Accounts in this organizational directory only`
   - **Redirect URI:** Leave blank (we use client credentials, no user login)
4. Click **Register**

### Step 3: Copy the IDs
After registration, you'll see the app overview page. Copy:
- **Application (client) ID** → this is `MS_CLIENT_ID`
- **Directory (tenant) ID** → this is `MS_TENANT_ID`

### Step 4: Create a Client Secret
1. In your app registration, click **"Certificates & secrets"** in the left menu
2. Click **"New client secret"**
3. Description: `Trifecta Agent Secret`
4. Expiry: 24 months
5. Click **Add**
6. **IMMEDIATELY copy the "Value"** (you can only see it once) → this is `MS_CLIENT_SECRET`

### Step 5: Add API Permissions
1. Click **"API permissions"** in the left menu
2. Click **"Add a permission"**
3. Select **"Microsoft Graph"**
4. Select **"Application permissions"** (NOT Delegated — we're running as a background service)
5. Add these permissions:
   - `Mail.Send` — to send emails as info@trifectaaddictionservices.com
   - `User.Read.All` — to look up Azure AD users (optional, for client list)
6. Click **"Grant admin consent for [your org]"** (requires Global Admin role)
7. Confirm — the Status column should turn green with a checkmark

### Step 6: Update .env.local
```
MS_CLIENT_ID=<paste Application client ID here>
MS_CLIENT_SECRET=<paste client secret Value here>
MS_TENANT_ID=<paste Directory tenant ID here>
GRAPH_CLIENT_SECRET=<same as MS_CLIENT_SECRET>
```

### Step 7: Update Azure App Service Environment Variables
In Azure Portal > App Services > trifecta-agent > Configuration > Application settings,
add the same four variables so production also works.

---

## Cost / Licensing

- App registrations are **free** in Azure AD
- Email sending via Graph counts against your Microsoft 365 mailbox limits
- No additional Azure credits needed

## Verification

Once configured, test with:
```
POST http://localhost:5000/api/leads/{lead_id}/approve-send
Body: {"approved_by": "danielle"}
```

Expected response: `{"status": "sent", ...}` instead of 502 error.

---

## Support

If you don't have Global Admin access, ask your Microsoft 365 admin to:
1. Create the app registration
2. Grant admin consent for Mail.Send
3. Share the Client ID, Secret, and Tenant ID with you

Contact: Ralph (builder agent) or Pulse (ops agent) to wire it in once you have the values.
