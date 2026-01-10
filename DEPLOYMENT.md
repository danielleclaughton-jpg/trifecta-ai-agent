# Trifecta AI Agent - Production Deployment Guide

**Generated:** 2026-01-10 | **Version:** 1.0.0

---

## 1-Week Production Rollout Timeline

### Day 0 (Today - Jan 10): Local Validation
```bash
# 1. Install new dependencies
pip install -r requirements.txt

# 2. Create local .env with real keys (copy from .env, add actual values)
cp .env .env.local
# Edit .env.local with your actual API keys for testing

# 3. Test local server
python app.py

# 4. Test endpoints
curl http://localhost:5000/health
curl http://localhost:5000/api/skills
curl -X POST http://localhost:5000/api/chat \
  -H "Content-Type: application/json" \
  -d '{"message":"generate contract for new 28-day virtual bootcamp enrollment"}'
```

### Day 1 (Jan 11): Azure Key Vault Setup
```bash
# 1. Create Azure Key Vault (if not exists)
az keyvault create \
  --name trifecta-keyvault \
  --resource-group TrifectaRG \
  --location canadacentral

# 2. Add secrets to Key Vault
az keyvault secret set --vault-name trifecta-keyvault --name "ANTHROPIC-API-KEY" --value "<your-key>"
az keyvault secret set --vault-name trifecta-keyvault --name "MS-CLIENT-ID" --value "<your-id>"
az keyvault secret set --vault-name trifecta-keyvault --name "MS-CLIENT-SECRET" --value "<your-secret>"
az keyvault secret set --vault-name trifecta-keyvault --name "MS-TENANT-ID" --value "<your-tenant>"
az keyvault secret set --vault-name trifecta-keyvault --name "DIALPAD-API-KEY" --value "<your-key>"
az keyvault secret set --vault-name trifecta-keyvault --name "QUICKBOOKS-CLIENT-ID" --value "<your-id>"
az keyvault secret set --vault-name trifecta-keyvault --name "QUICKBOOKS-CLIENT-SECRET" --value "<your-secret>"
az keyvault secret set --vault-name trifecta-keyvault --name "AZURE-SPEECH-KEY" --value "<your-key>"
az keyvault secret set --vault-name trifecta-keyvault --name "FLASK-SECRET-KEY" --value "$(openssl rand -hex 32)"

# 3. Grant App Service access to Key Vault
az webapp identity assign --name trifecta-agent --resource-group TrifectaRG
az keyvault set-policy --name trifecta-keyvault \
  --object-id <app-service-principal-id> \
  --secret-permissions get list
```

### Day 2 (Jan 12): Azure App Service Deployment
```bash
# 1. Create App Service (if not exists)
az webapp create \
  --name trifecta-agent \
  --resource-group TrifectaRG \
  --plan TrifectaPlan \
  --runtime "PYTHON:3.11"

# 2. Configure startup command
az webapp config set \
  --name trifecta-agent \
  --resource-group TrifectaRG \
  --startup-file "gunicorn --bind=0.0.0.0:8000 --workers=4 --threads=2 --timeout=120 app:app"

# 3. Set environment variables (Key Vault references)
az webapp config appsettings set --name trifecta-agent --resource-group TrifectaRG --settings \
  ANTHROPIC_API_KEY="@Microsoft.KeyVault(SecretUri=https://trifecta-keyvault.vault.azure.net/secrets/ANTHROPIC-API-KEY/)" \
  MS_CLIENT_ID="@Microsoft.KeyVault(SecretUri=https://trifecta-keyvault.vault.azure.net/secrets/MS-CLIENT-ID/)" \
  MS_CLIENT_SECRET="@Microsoft.KeyVault(SecretUri=https://trifecta-keyvault.vault.azure.net/secrets/MS-CLIENT-SECRET/)" \
  MS_TENANT_ID="@Microsoft.KeyVault(SecretUri=https://trifecta-keyvault.vault.azure.net/secrets/MS-TENANT-ID/)" \
  DIALPAD_API_KEY="@Microsoft.KeyVault(SecretUri=https://trifecta-keyvault.vault.azure.net/secrets/DIALPAD-API-KEY/)" \
  SECRET_KEY="@Microsoft.KeyVault(SecretUri=https://trifecta-keyvault.vault.azure.net/secrets/FLASK-SECRET-KEY/)" \
  SKILL_DIR="Assets/skills" \
  FLASK_ENV="production"

# 4. Deploy code
az webapp deployment source config-local-git --name trifecta-agent --resource-group TrifectaRG
git remote add azure <deployment-url>
git push azure main

# OR use ZIP deploy:
zip -r deploy.zip . -x ".git/*" -x ".venv/*" -x "__pycache__/*"
az webapp deployment source config-zip --name trifecta-agent --resource-group TrifectaRG --src deploy.zip
```

### Day 3 (Jan 13): Application Insights + Monitoring
```bash
# 1. Create Application Insights
az monitor app-insights component create \
  --app trifecta-agent-insights \
  --location canadacentral \
  --resource-group TrifectaRG \
  --application-type web

# 2. Get connection string and add to Key Vault
CONN_STRING=$(az monitor app-insights component show --app trifecta-agent-insights --resource-group TrifectaRG --query connectionString -o tsv)
az keyvault secret set --vault-name trifecta-keyvault --name "APPINSIGHTS-CONNECTION-STRING" --value "$CONN_STRING"

# 3. Add to App Service
az webapp config appsettings set --name trifecta-agent --resource-group TrifectaRG --settings \
  APPLICATIONINSIGHTS_CONNECTION_STRING="@Microsoft.KeyVault(SecretUri=https://trifecta-keyvault.vault.azure.net/secrets/APPINSIGHTS-CONNECTION-STRING/)"

# 4. Set up alerts
az monitor metrics alert create \
  --name "trifecta-high-response-time" \
  --resource-group TrifectaRG \
  --scopes /subscriptions/<sub-id>/resourceGroups/TrifectaRG/providers/Microsoft.Web/sites/trifecta-agent \
  --condition "avg ResponseTime > 5000" \
  --description "Alert when response time exceeds 5 seconds"
```

### Day 4 (Jan 14): Microsoft Graph + SharePoint Testing
```bash
# Azure Portal Steps:
# 1. Go to Azure Active Directory > App registrations
# 2. Create or select "Trifecta Agent" app
# 3. Add API permissions:
#    - Microsoft Graph > Application permissions:
#      - User.Read.All
#      - Sites.ReadWrite.All
#      - Files.ReadWrite.All
#      - Calendars.ReadWrite
# 4. Grant admin consent

# Test Graph integration
curl https://trifecta-agent.azurewebsites.net/api/graph/clients

# Test SharePoint upload
curl -X POST https://trifecta-agent.azurewebsites.net/api/sharepoint/upload \
  -H "Content-Type: application/json" \
  -d '{
    "client_name": "Test_Client",
    "document_type": "invoice",
    "content": "<html><body>Test</body></html>",
    "filename": "test_invoice.html"
  }'
```

### Day 5 (Jan 15): Dialpad + QuickBooks Integration
```bash
# Dialpad Setup:
# 1. Go to Dialpad Admin > API
# 2. Generate API key
# 3. Configure webhook URL: https://trifecta-agent.azurewebsites.net/api/dialpad/webhook
# 4. Enable events: call.ended, voicemail.received

# QuickBooks Setup:
# 1. Go to developer.intuit.com
# 2. Create/select app
# 3. Get Client ID, Client Secret
# 4. Configure OAuth redirect: https://trifecta-agent.azurewebsites.net/api/quickbooks/callback
# 5. Complete OAuth flow to get refresh token

# Test Dialpad
curl https://trifecta-agent.azurewebsites.net/api/dialpad/calls?limit=10

# Test contract generation
curl -X POST https://trifecta-agent.azurewebsites.net/api/contract/test-client \
  -H "Content-Type: application/json" \
  -d '{"program": "28_DAY_VIRTUAL", "client_name": "Test User", "email": "test@example.com"}'
```

### Day 6 (Jan 16): End-to-End Testing
```bash
# Full workflow test
# 1. Chat with skill matching
curl -X POST https://trifecta-agent.azurewebsites.net/api/chat \
  -H "Content-Type: application/json" \
  -d '{"message": "I need to onboard a new executive client for the 28-day program"}'

# 2. Portal sync with Claude analysis
curl "https://trifecta-agent.azurewebsites.net/api/portal-sync?risk=high"

# 3. Contract generation + SharePoint + QuickBooks
curl -X POST https://trifecta-agent.azurewebsites.net/api/contract/new-client-123 \
  -H "Content-Type: application/json" \
  -d '{"program": "28_DAY_VIRTUAL"}'

# 4. Verify Application Insights logs
az monitor app-insights query \
  --app trifecta-agent-insights \
  --analytics-query "requests | where timestamp > ago(1h) | summarize count() by name"
```

### Day 7 (Jan 17): Go-Live + Documentation
```bash
# 1. Enable custom domain (if needed)
az webapp config hostname add --webapp-name trifecta-agent --resource-group TrifectaRG --hostname api.trifectaaddictionservices.com

# 2. Add SSL certificate
az webapp config ssl bind --certificate-thumbprint <thumbprint> --ssl-type SNI --name trifecta-agent --resource-group TrifectaRG

# 3. Final health check
curl https://api.trifectaaddictionservices.com/health

# 4. Update GoDaddy DNS (A record or CNAME)
# Point api.trifectaaddictionservices.com → trifecta-agent.azurewebsites.net
```

---

## API Endpoints Summary

| Endpoint | Method | Description | Skills Used |
|----------|--------|-------------|-------------|
| `/` | GET | Health check | - |
| `/health` | GET | Service status | - |
| `/api/skills` | GET | List skills | - |
| `/api/skills/<name>` | GET | Get skill | - |
| `/api/skills/reload` | POST | Reload skills | - |
| `/api/chat` | POST | Chat with AI | All (matched) |
| `/api/graph/clients` | GET | Get clients | lead-intake, practice-system |
| `/api/graph/clients/<id>` | GET/PATCH | Client detail | lead-intake, practice-system |
| `/api/sharepoint/upload` | POST | Upload document | document-generator, session-documentation |
| `/api/dialpad/calls` | GET | Get calls | tailored-session-builder |
| `/api/dialpad/transcription/<id>` | GET | Get transcription | tailored-session-builder |
| `/api/dialpad/webhook` | POST | Dialpad events | tailored-session-builder |
| `/api/portal-sync` | GET/POST | Sync + analyze | ai-agent-orchestration |
| `/api/contract/<client_id>` | GET/POST | Generate contract | document-generator |

---

## Troubleshooting

### Common Issues

**1. Key Vault access denied**
```bash
# Verify managed identity
az webapp identity show --name trifecta-agent --resource-group TrifectaRG

# Check Key Vault policy
az keyvault show --name trifecta-keyvault --query "properties.accessPolicies"
```

**2. Skills not loading**
```bash
# Check SKILL_DIR path
az webapp config appsettings list --name trifecta-agent --resource-group TrifectaRG | grep SKILL_DIR

# Verify files deployed
az webapp ssh --name trifecta-agent --resource-group TrifectaRG
ls -la Assets/skills/
```

**3. Graph API 401 errors**
```bash
# Verify app registration permissions
# Azure Portal > Azure AD > App registrations > Trifecta Agent > API permissions
# Ensure admin consent granted
```

**4. Anthropic API errors**
```bash
# Test API key directly
curl https://api.anthropic.com/v1/messages \
  -H "x-api-key: $ANTHROPIC_API_KEY" \
  -H "anthropic-version: 2023-06-01" \
  -H "Content-Type: application/json" \
  -d '{"model":"claude-3-5-sonnet-20241022","max_tokens":100,"messages":[{"role":"user","content":"Hello"}]}'
```

---

## Files Created/Modified

| File | Purpose |
|------|---------|
| `.env` | Production environment config with Key Vault refs |
| `requirements.txt` | Updated with Azure, Graph, QuickBooks SDKs |
| `app.py` | Full production app with all integrations |
| `startup.txt` | Gunicorn startup command |
| `host.json` | Azure Functions host config |
| `.deployment` | Azure deployment settings |
| `DEPLOYMENT.md` | This deployment guide |

---

## Contact

**Trifecta AI Agent Support**
- Email: info@trifectaaddictionservices.com
- Phone: +1 (403) 907-0996
