# Google Sheets Lead Logging — Setup Guide

The Flask app can automatically log new leads to a Google Sheet when they come in via webhooks (GoDaddy, Dialpad, Outlook). This is **non-fatal** — if credentials are missing or the API fails, leads still work normally.

## How to Set Up

### 1. Create a Google Cloud Service Account

1. Go to [Google Cloud Console](https://console.cloud.google.com/)
2. Create a project (or use an existing one)
3. Enable the **Google Sheets API** (`APIs & Services > Library > Google Sheets API`)
4. Go to `APIs & Services > Credentials > Create Credentials > Service Account`
5. Name it something like `trifecta-sheets-logger`
6. Click into the service account > **Keys** tab > **Add Key > Create new key > JSON**
7. Download the JSON file

### 2. Place the Credentials File

Rename the downloaded JSON file to:

```
google-credentials.json
```

Place it in the app root directory:

```
C:\Users\TrifectaAgent\trifecta-ai-agent\google-credentials.json
```

> ⚠️ This file contains a private key. **Never commit it to git.** It should already be in `.gitignore`.

### 3. Share the Google Sheet with the Service Account

Open the Google Sheet and share it (Editor access) with the service account email address found in the JSON file. It looks like:

```
trifecta-sheets-logger@your-project.iam.gserviceaccount.com
```

### 4. Environment Variable (Optional)

The sheet ID is already set as a default in code. To override, set in `.env.local`:

```
GOOGLE_SHEETS_ID=1aV55LlDzyfqVu4maXLxfN55cb_NPBnU21BjeqVbqnL0
```

## Without Credentials

If `google-credentials.json` is not present, the app logs a warning and skips Sheets logging. No errors, no crashes — leads still flow into SQLite normally.

## Sheet Columns (A–J)

| Column | Field |
|--------|-------|
| A | Date Contacted |
| B | Name |
| C | Email |
| D | Phone |
| E | Source |
| F | Initial Question |
| G | Date Responded |
| H | Status |
| I | Follow-up Sent |
| J | Notes / Program Interest |
