# Trifecta AI Agent - Quick Start Guide

## ✅ Current Status

| Service | Port | Status |
|---------|------|--------|
| Flask API | 5000 | Running |
| Dashboard | 3015 | Running |

---

## 🚀 Quick Start Commands

### 1. Start Flask API (if not running)
```powershell
cd C:\Users\TrifectaAgent\trifecta-ai-agent
.\.venv\Scripts\Activate.ps1
python app.py
```

### 2. Start Dashboard (if not running)
```powershell
cd C:\Users\TrifectaAgent\trifecta-ai-agent
python dashboard_dev.py
```

### 3. Open Dashboard
👉 **http://localhost:3015/**

---

## 🔑 Required Environment Variables (.env file)

Create or edit `.env` in the project root:

```env
# ===== REQUIRED FOR CLAUDE AI =====
ANTHROPIC_API_KEY=sk-ant-api03-xxxxxxxxxxxx

# ===== OPTIONAL - MICROSOFT GRAPH =====
MS_CLIENT_ID=your-azure-app-client-id
MS_CLIENT_SECRET=your-azure-app-secret
MS_TENANT_ID=your-azure-tenant-id

# ===== OPTIONAL - DIALPAD =====
DIALPAD_API_KEY=your-dialpad-api-key

# ===== OPTIONAL - GODADDY WEBCHAT =====
GODADDY_WEBCHAT_API_KEY=your-godaddy-key

# ===== APP SETTINGS =====
PORT=5000
FLASK_DEBUG=0
SECRET_KEY=change-this-in-production
```

---

## 📋 Checklist to Get Running

### Minimum (Claude Chat Only)
- [ ] Set `ANTHROPIC_API_KEY` in `.env`
- [ ] Start Flask API: `python app.py`
- [ ] Start Dashboard: `python dashboard_dev.py`
- [ ] Open http://localhost:3015/
- [ ] Test chat in the "AI Chat (Claude)" card

### Full Features
- [ ] Set all environment variables above
- [ ] Configure Azure App registration for Graph API
- [ ] Set up Dialpad API credentials
- [ ] Set up GoDaddy WebChat API

---

## 🧪 Test Commands

### Test Claude Chat (PowerShell)
```powershell
$body = '{"message": "What services does Trifecta offer?"}'
Invoke-RestMethod -Uri "http://localhost:5000/api/chat" -Method POST -Body $body -ContentType "application/json"
```

### Test Health Endpoint
```powershell
Invoke-RestMethod -Uri "http://localhost:5000/health"
```

### Test Skills
```powershell
Invoke-RestMethod -Uri "http://localhost:5000/api/skills"
```

---

## 🔧 Troubleshooting

### "API Offline" in Dashboard
1. Check if Flask is running: `netstat -ano | findstr :8000`
2. If not, start it: `python app.py`

### "AI service not configured"
1. Check `.env` has `ANTHROPIC_API_KEY`
2. Verify the key is valid at https://console.anthropic.com/

### Dashboard not loading
1. Check if running: `netstat -ano | findstr :3015`
2. If not, start it: `python dashboard_dev.py`
3. Hard refresh browser: `Ctrl + Shift + R`

---

## 📁 Project Structure

```
trifecta-ai-agent/
├── app.py                 # Flask API (main backend)
├── dashboard_dev.py       # Dashboard HTTP server
├── dashboard_index.html   # Dashboard UI
├── .env                   # Environment variables (create this!)
├── requirements.txt       # Python dependencies
├── Assets/
│   └── skills/           # AI skill files (.md)
└── START_HERE.md         # This file
```
