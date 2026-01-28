# Trifecta AI Agent

AI Agent for Trifecta Addiction and Mental Health Services - Flask-based API with Azure cognitive services integration.

## Overview

This repository contains the backend API that powers Trifecta's practice management automation, including:

- Client intake and onboarding workflows
- Document generation (contracts, invoices, session reports)
- Microsoft Graph integration (Teams, SharePoint, Outlook)
- Dialpad communication management
- QuickBooks financial integration
- Claude AI-powered chat with skill matching

## Tech Stack

| Layer | Technology |
|-------|------------|
| Backend | Python 3.11, Flask 3.0 |
| AI | Anthropic Claude 3.5 Sonnet |
| Cloud | Azure App Service, Key Vault, Blob Storage |
| Auth | Azure AD, Microsoft Graph API |
| Integrations | SharePoint, Teams, Dialpad, QuickBooks |

## Project Structure

```
trifecta-ai-agent/
├── app.py                 # Main Flask application
├── requirements.txt       # Python dependencies
├── CLAUDE.md              # Claude Code context file
├── DEPLOYMENT.md          # Azure deployment guide
├── .claude/
│   └── skills/            # Claude Code skills (9 skills)
├── Assets/
│   ├── skills/            # Flask API skill files
│   └── seo/               # SEO strategy documents
├── dashboard_assets/      # Dashboard UI components
└── templates/             # Jinja2 document templates
```

## Quick Start

```bash
# Install dependencies
pip install -r requirements.txt

# Copy environment template
cp .env.example .env
# Edit .env with your API keys

# Run locally (Windows or Linux)
python app.py

# Test health endpoint
curl http://localhost:5000/health
```

## API Key Authentication (Recommended)

If you set `TRIFECTA_API_KEY` in your environment, all endpoints except `/`, `/health`,
and `/api-docs` will require an API key. Send it via:

- Header: `X-API-Key: <your_key>`
- Or: `Authorization: Bearer <your_key>`

Add it locally in `.env` and in Azure App Service settings or Key Vault.

## Claude Code Skills

Skills are available as slash commands:

| Command | Description |
|---------|-------------|
| `/trifecta-document-generator` | Generate contracts and invoices |
| `/trifecta-practice-system` | Practice management reference |
| `/trifecta-lead-intake-workflow` | Client onboarding automation |
| `/trifecta-session-documentation` | Session reports and Teams integration |
| `/trifecta-tailored-session-builder` | Interactive recovery toolkits |
| `/trifecta-marketing-seo` | Marketing and SEO strategies |
| `/trifecta-ai-agent-orchestration` | Central workflow automation |
| `/trifecta-asset-management` | File and folder organization |
| `/trifecta-dashboard-testing` | Dashboard testing protocols |

## Deployment

This repo is configured for **Windows App Service (wfastcgi)** via `web.config`.
If you deploy to Windows, ignore `startup.txt` (Linux/gunicorn only).

See [DEPLOYMENT.md](DEPLOYMENT.md) for full Azure deployment instructions.

## Contact

**Trifecta Addiction and Mental Health Services**
- Danielle Claughton, Founding Director & CEO
- Phone: +1 (403) 907-0996
- Email: info@trifectaaddictionservices.com
