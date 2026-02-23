# Trifecta AI Agent - Claude Code Context

> This file provides Claude Code with essential context about the Trifecta AI Agent project.

## Project Overview

**Trifecta Addiction and Mental Health Services** is a HIPAA-compliant practice management platform run by Danielle Claughton (Founding Director & CEO, CACCF-certified addiction counselor).

This repository contains the **Trifecta AI Agent** - a Flask-based API that orchestrates:
- Client intake and onboarding automation
- Document generation (contracts, invoices, session reports)
- Microsoft Graph integration (Teams, SharePoint, Outlook)
- Dialpad communication management
- QuickBooks financial integration
- Claude AI-powered chat with skill matching

## Tech Stack

| Layer | Technology |
|-------|------------|
| **Backend** | Python 3.11, Flask 3.0 |
| **AI** | Anthropic Claude 3.5 Sonnet |
| **Cloud** | Azure App Service, Azure Key Vault, Azure Blob Storage |
| **Auth** | Azure AD, Microsoft Graph API |
| **Integrations** | SharePoint, Teams, Dialpad, QuickBooks, Adobe Sign |
| **PDF Generation** | WeasyPrint, Jinja2 |
| **Monitoring** | Azure Application Insights |

## Project Structure

```
trifecta-ai-agent/
├── app.py                 # Main Flask application
├── requirements.txt       # Python dependencies
├── DEPLOYMENT.md          # Azure deployment guide
├── CLAUDE.md              # This file (Claude Code context)
├── Assets/
│   ├── skills/            # Claude Code skill files (markdown)
│   └── seo/               # SEO strategy documents
├── dashboard_assets/      # Dashboard UI components
└── templates/             # Jinja2 templates for documents
```

## Key Files

| File | Purpose |
|------|---------|
| `app.py` | Flask API with all endpoints, skill loader, integrations |
| `Assets/skills/*.md` | 9 skill files loaded at runtime for Claude context |
| `DEPLOYMENT.md` | Step-by-step Azure deployment instructions |
| `.env.example` | Environment variable template |

## API Endpoints

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/health` | GET | Health check |
| `/api/skills` | GET | List loaded skills |
| `/api/chat` | POST | Chat with Claude (skill-matched) |
| `/api/graph/clients` | GET | Get clients from Microsoft Graph |
| `/api/sharepoint/upload` | POST | Upload document to SharePoint |
| `/api/contract/<client_id>` | POST | Generate contract + invoice |
| `/api/dialpad/webhook` | POST | Dialpad event webhook |

## Environment Variables

Required secrets (stored in Azure Key Vault for production):
- `ANTHROPIC_API_KEY` - Claude API key
- `MS_CLIENT_ID`, `MS_CLIENT_SECRET`, `MS_TENANT_ID` - Azure AD app registration
- `DIALPAD_API_KEY` - Dialpad API access
- `QUICKBOOKS_CLIENT_ID`, `QUICKBOOKS_CLIENT_SECRET` - QuickBooks OAuth
- `AZURE_SPEECH_KEY`, `AZURE_SPEECH_REGION` - Azure Cognitive Services

## Skills System

Skills are markdown files in `Assets/skills/` that provide Claude with domain knowledge:

1. **trifecta-ai-agent-orchestration** - Central workflow automation
2. **trifecta-practice-system** - Complete practice management reference
3. **trifecta-document-generator** - Contract/invoice generation
4. **trifecta-session-documentation** - Teams recording + report generation
5. **trifecta-tailored-session-builder** - Interactive HTML toolkit generation
6. **trifecta-lead-intake-workflow** - Client onboarding automation
7. **trifecta-marketing-seo** - Marketing and SEO strategies
8. **trifecta-asset-management** - File/folder organization
9. **trifecta-dashboard-testing** - Dashboard testing protocols

## Coding Standards

- **Python Style**: PEP 8, type hints encouraged
- **Error Handling**: Use try/except with logging, return JSON error responses
- **API Responses**: Always return `{'success': bool, 'data': ..., 'error': ...}`
- **Logging**: Use `logger.info()` for requests, `logger.error()` for failures
- **Security**: Never log API keys, use Key Vault references in production
- **HIPAA**: No PHI in logs, file names, or error messages

## Development Commands

```bash
# Install dependencies
pip install -r requirements.txt

# Run locally
python app.py

# Test endpoints
curl http://localhost:5000/health
curl http://localhost:5000/api/skills
curl -X POST http://localhost:5000/api/chat -H "Content-Type: application/json" -d '{"message":"test"}'

# Reload skills
curl -X POST http://localhost:5000/api/skills/reload
```

## Deployment

See `DEPLOYMENT.md` for full Azure deployment guide. Quick reference:
- **Production URL**: https://trifecta-agent.azurewebsites.net
- **Custom Domain**: api.trifectaaddictionservices.com (pending)
- **Runtime**: Python 3.11 on Azure App Service
- **Startup**: `gunicorn --bind=0.0.0.0:8000 --workers=4 app:app`

## Business Context

- **Target Markets**: Oil & Gas workers, professionals with demanding schedules
- **Programs**: 28-Day Virtual Boot Camp, Inpatient (14-day), Outpatient
- **Unique Approach**: Neuroplasticity-based, self-empowerment focused, DBT/CBT integration
- **Contact**: Danielle Claughton - +1 (403) 907-0996 - info@trifectaaddictionservices.com
