# Codex Task: Redesign Trifecta Command Center Dashboard

## Goal
Rebuild `dashboard_index.html` to match the founder's mockup design at:
`C:\Users\TrifectaAgent\trifecta-ai-agent\client_portal_mockup\trifecta_dashboard_mockup.PNG`

## Mockup Design Spec

### Layout
- **Dark theme** (already have this, keep it)
- **Left sidebar** with navigation icons + labels:
  - Dashboard, Client Intake, Program Delivery, Progress Monitoring
  - Marketing & Sales, Finance & Invoicing, Compliance
  - Alumni Engagement, AI Support, Analytics, Settings
- **Top bar**: "AI Agention Center" with search bar + user avatar (Danielle C)
- **4 large KPI cards** across the top row:
  - Total Leads (with % change indicator)
  - Qualified HR Leads
  - Monthly Revenue ($)
  - Conversion Rate (%)
- **Client Activity** panel (left-middle): list of recent client actions with avatars, names, timestamps
- **Upcoming Appointments** panel (center): calendar-style list with dates/times
- **Alerts** panel (right): urgent items needing attention
- **Revenue Trend** chart (bottom-center): line chart showing monthly revenue
- **Upcoming Appointments** detail list (bottom-left)

### Data Sources (all on localhost:5000)
These endpoints already exist and return real data:

| Endpoint | Data |
|----------|------|
| `GET /api/kpi/live` | leads_today, leads_total, emails_sent_today, active_clients, conversion_rate |
| `GET /api/leads/board?limit=20` | Lead pipeline with names, emails, status, dates |
| `GET /api/approvals?status=pending` | Content/email items awaiting approval |
| `GET /api/approvals/<id>/approve` | One-tap approve (POST) |
| `GET /api/approvals/<id>/reject` | One-tap reject (POST) |
| `GET /api/calendar/upcoming` | Upcoming appointments from Outlook |
| `GET /api/email-drafts` | Email drafts with counts |
| `GET /api/scheduler/status` | Background job statuses |
| `GET /health` | System health check |
| `GET /api/content/generate-image` | DALL-E 3 image generation (POST) |

### Oil & Gas KPI Dashboard
Also create a second view/tab for Oil & Gas campaign tracking:
- Database: `oil_gas_leads.db` (SQLite, same machine)
- Tables: `oil_gas_leads` (id, name, email, phone, source, platform, enquiry_type, lead_score, status, notes, created_at, updated_at)
- Tables: `oil_gas_events` (id, lead_id, event_type, source, received_at)
- Add Flask endpoint `GET /api/oil-gas/leads` to serve this data
- Show: total oil & gas leads, pipeline by status, recent activity

### Auto-refresh
- KPIs: poll every 15 seconds
- Leads: poll every 30 seconds
- Approvals: poll every 30 seconds
- Calendar: poll every 60 seconds

### Approval Queue
- Show pending items with one-tap Approve / Reject buttons
- Badge count in sidebar nav
- Auto-refresh after approve/reject

### Key Files
- `C:\Users\TrifectaAgent\trifecta-ai-agent\dashboard_index.html` — the file to rewrite
- `C:\Users\TrifectaAgent\trifecta-ai-agent\dashboard_dev.py` — serves it on port 3015
- `C:\Users\TrifectaAgent\trifecta-ai-agent\app.py` — Flask API on port 5000
- `C:\Users\TrifectaAgent\trifecta-ai-agent\client_portal_mockup\trifecta_dashboard_mockup.PNG` — the design mockup
- `C:\Users\TrifectaAgent\trifecta-ai-agent\dashboard_assets\` — logos and brand assets

### Important Notes
- Single HTML file with embedded CSS and JS (no build tools)
- API base URL: `http://localhost:5000` (hardcode or auto-detect)
- Keep the Trifecta teal brand color (#2dced3)
- Mobile-responsive is nice but desktop-first
- Use the existing `fetchJson()` helper pattern from the current dashboard
