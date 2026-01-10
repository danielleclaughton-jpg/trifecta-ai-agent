# Trifecta AI Agent Dashboard Testing & Optimization

## Overview
This skill provides Claude with comprehensive knowledge for testing, optimizing, and deploying the Trifecta AI Agent dashboard. The dashboard runs at `http://localhost:3015/` during development and will be deployed to Azure for production. This skill includes go-live checklists, testing protocols, optimization strategies, and deployment procedures.

## When to Use This Skill
Use this skill when:
- Testing dashboard functionality and components
- Identifying missing or incomplete features
- Optimizing dashboard performance
- Preparing for production deployment
- Troubleshooting dashboard issues
- Adding new features or modules
- Conducting user acceptance testing
- Performing security audits

## Dashboard Architecture Context

Based on your Flow Chart and AI Agent Orchestration skill, the Trifecta AI Agent dashboard should include:

### Core Modules (from Flow Chart)

1. **Client Intake & Onboarding**
   - Forms submission and tracking
   - Lead scoring
   - Treatment matching recommendations

2. **Program Delivery & Scheduling**
   - Calendar view with upcoming sessions
   - Session reminders status
   - Progress tracking by client

3. **Marketing & Sales**
   - Oil & Gas campaign performance
   - Lead tracking by source
   - Conversion funnel visualization

4. **Finance & Invoicing**
   - Payment tracking
   - Revenue by program
   - Outstanding balances

5. **Alumni & Family Engagement**
   - Follow-up schedule
   - Relapse tracking alerts
   - Engagement metrics

6. **AI Agent Support**
   - Chat assistant activity log
   - Automation status
   - Error tracking

7. **Reporting & Analytics**
   - KPI dashboard
   - Export capabilities

8. **Settings & Integrations**
   - API connection status
   - System health monitoring

---

## Go-Live Readiness Checklist

### CRITICAL (Must Be Complete Before Launch)

#### 1. Core Functionality ✓

- [ ] **User Authentication**
  - [ ] Login page functional
  - [ ] Password reset working
  - [ ] Session management (30-minute timeout)
  - [ ] Multi-factor authentication (optional but recommended)
  - [ ] Role-based access control (Admin, Staff, Read-Only)

- [ ] **Dashboard Home Page**
  - [ ] Displays key metrics (leads, clients, revenue)
  - [ ] Shows recent activity feed
  - [ ] Alerts and notifications visible
  - [ ] Quick action buttons working
  - [ ] Responsive design (mobile, tablet, desktop)

- [ ] **Lead Management**
  - [ ] New leads displayed in real-time
  - [ ] Lead details viewable
  - [ ] Status updates functional (new → contacted → consulting → enrolled)
  - [ ] Assignment to Danielle/staff working
  - [ ] Search and filter capabilities

- [ ] **Client Portal Integration**
  - [ ] Session documents uploaded successfully
  - [ ] Client access working
  - [ ] Download links functional
  - [ ] Real-time sync with SharePoint

#### 2. Integration Health ✓

- [ ] **Microsoft Teams**
  - [ ] Meeting scheduling API connected
  - [ ] Recording retrieval working
  - [ ] Calendar sync functional
  - [ ] Test: Schedule a meeting → verify it appears

- [ ] **Microsoft Graph API**
  - [ ] Email sending working (Outlook)
  - [ ] Calendar read/write permissions
  - [ ] File upload to SharePoint/OneDrive
  - [ ] Test: Send email → verify delivery

- [ ] **Dialpad**
  - [ ] SMS sending functional
  - [ ] Call logs accessible
  - [ ] Webhook receiving messages
  - [ ] Test: Send SMS → verify delivery

- [ ] **QuickBooks**
  - [ ] Invoice creation working
  - [ ] Payment tracking syncing
  - [ ] Customer data retrievable
  - [ ] Test: Create invoice → verify in QB

- [ ] **Social Media APIs**
  - [ ] Facebook/Instagram connected
  - [ ] LinkedIn authenticated
  - [ ] Post scheduling functional
  - [ ] Test: Schedule post → verify it posts

- [ ] **Adobe Sign**
  - [ ] Contract sending working
  - [ ] Signature tracking functional
  - [ ] Webhook for completion notifications
  - [ ] Test: Send contract → verify receipt

#### 3. Data & Security ✓

- [ ] **Data Storage**
  - [ ] Database connection stable
  - [ ] Data persists between sessions
  - [ ] Backup system configured
  - [ ] Data retention policies implemented

- [ ] **Security Measures**
  - [ ] HTTPS enabled (production)
  - [ ] API keys stored in Azure Key Vault (not hardcoded)
  - [ ] Input validation on all forms
  - [ ] SQL injection prevention
  - [ ] XSS (cross-site scripting) protection
  - [ ] CSRF (cross-site request forgery) tokens

- [ ] **HIPAA Compliance**
  - [ ] PHI encrypted at rest
  - [ ] PHI encrypted in transit
  - [ ] Access logs maintained
  - [ ] Session timeout enforced
  - [ ] No PHI in URL parameters or logs

#### 4. Monitoring & Alerts ✓

- [ ] **System Health Dashboard**
  - [ ] API connection status indicators
  - [ ] Error rate tracking
  - [ ] Response time monitoring
  - [ ] Uptime percentage displayed

- [ ] **Alert System**
  - [ ] High-risk client flags (crisis language detected)
  - [ ] Failed API calls notification
  - [ ] System errors alert to admin
  - [ ] Daily summary email to Danielle

- [ ] **Kill Switch**
  - [ ] Emergency shutdown button accessible
  - [ ] Fallback to basic email responder
  - [ ] Notification sent on activation

#### 5. User Experience ✓

- [ ] **Performance**
  - [ ] Page load time <2 seconds
  - [ ] API responses <1 second
  - [ ] No lag in UI interactions
  - [ ] Optimized images and assets

- [ ] **Usability**
  - [ ] Intuitive navigation
  - [ ] Clear labels and instructions
  - [ ] Error messages helpful
  - [ ] Success confirmations visible
  - [ ] Help documentation accessible

- [ ] **Accessibility**
  - [ ] Keyboard navigation working
  - [ ] Screen reader compatible
  - [ ] Color contrast meets WCAG standards
  - [ ] Alt text for images

---

## Dashboard Component Checklist

### Component 1: Lead Dashboard

**Required Features:**
- [ ] Lead list table (sortable, filterable)
- [ ] Lead detail modal/page
- [ ] Lead source tracking
- [ ] Lead score display
- [ ] Quick actions (email, call, schedule consultation)
- [ ] Activity timeline per lead
- [ ] Status change dropdown
- [ ] Notes section
- [ ] File attachment capability

**Data Displayed:**
- Name, email, phone
- Inquiry date and time
- Lead source (webchat, email, phone, social)
- Lead score (0-21 points)
- Risk flags (if any)
- Current status
- Last contact date
- Next action due

**Test Scenarios:**
1. Create new lead manually
2. Receive lead from webchat (simulate webhook)
3. Update lead status
4. Add notes to lead
5. Schedule consultation from lead detail
6. Filter leads by source
7. Sort leads by date
8. Export leads to CSV

### Component 2: Client Management

**Required Features:**
- [ ] Active clients list
- [ ] Client profile pages
- [ ] Program assignment display
- [ ] Session schedule view
- [ ] Progress tracking
- [ ] Homework completion status
- [ ] Payment status
- [ ] Document access (contracts, invoices, reports)

**Data Displayed:**
- Client name and contact info
- Program type and start date
- Sessions completed vs. total
- Next session date/time
- Homework status
- Payment status (paid, partial, outstanding)
- Risk level
- Recent activity

**Test Scenarios:**
1. View client profile
2. Schedule new session
3. Mark session as complete
4. Upload session report
5. Send reminder manually
6. Update payment status
7. View client documents
8. Generate progress report

### Component 3: Calendar & Scheduling

**Required Features:**
- [ ] Monthly/weekly/daily calendar views
- [ ] Session blocks with client names
- [ ] Color coding by program type
- [ ] Click to view session details
- [ ] Drag-and-drop rescheduling
- [ ] Availability blocking
- [ ] Integration with Teams meeting creation
- [ ] Reminder preview

**Data Displayed:**
- All scheduled sessions
- Danielle's availability
- Session type (inpatient, virtual, outpatient)
- Session status (scheduled, completed, cancelled)
- Recording status (recorded, transcribing, complete)

**Test Scenarios:**
1. View today's schedule
2. Schedule new session
3. Reschedule existing session
4. Cancel session
5. Block off personal time
6. Create Teams meeting from calendar
7. View completed sessions
8. Check reminder queue

### Component 4: Analytics Dashboard

**Required Features:**
- [ ] KPI cards (leads, clients, revenue, conversion rate)
- [ ] Line charts (trends over time)
- [ ] Bar charts (performance by program)
- [ ] Funnel chart (lead → client conversion)
- [ ] Date range selector
- [ ] Export to PDF/Excel
- [ ] Comparison vs. previous period

**KPIs to Display:**
- New leads this month
- Consultations scheduled
- New client enrollments
- Revenue this month
- Lead-to-client conversion rate
- Average revenue per client
- Client retention rate
- Program completion rate

**Test Scenarios:**
1. View current month metrics
2. Change date range to last quarter
3. Compare this month vs. last month
4. Export analytics report
5. Drill down into specific metric
6. View revenue by program
7. Check conversion funnel

### Component 5: Conversation Log

**Required Features:**
- [ ] Chronological list of all agent interactions
- [ ] Filter by channel (email, SMS, webchat, social)
- [ ] Search by client name or keyword
- [ ] Conversation detail view
- [ ] Sentiment indicators
- [ ] Escalation flags
- [ ] Export capability

**Data Displayed:**
- Date/time of interaction
- Channel (email, webchat, SMS)
- Client/lead name
- Message preview
- Agent vs. human handled
- Outcome (info sent, consultation booked, escalated)

**Test Scenarios:**
1. View all conversations from today
2. Filter to show only escalated conversations
3. Search for specific client conversation
4. View full conversation thread
5. Export conversation log
6. Mark conversation as resolved

### Component 6: Automation Status

**Required Features:**
- [ ] List of active automations
- [ ] On/off toggles
- [ ] Success/failure counts
- [ ] Last run timestamp
- [ ] Error logs
- [ ] Manual trigger buttons
- [ ] Automation rule editor

**Automations to Display:**
- Welcome email sequence
- Session reminders (24hr, 2hr)
- Payment reminders
- Homework check-ins
- Follow-up sequences
- Birthday messages
- Milestone celebrations

**Test Scenarios:**
1. Turn off automation
2. Manually trigger automation
3. View error log
4. Edit automation rule
5. Test automation with sample data
6. View success rate
7. Restart failed automation

### Component 7: Integration Status

**Required Features:**
- [ ] Connection status indicators (green/yellow/red)
- [ ] Last successful connection timestamp
- [ ] Error messages if disconnected
- [ ] Reconnect buttons
- [ ] API rate limit usage
- [ ] Webhook delivery status

**Integrations to Monitor:**
- Microsoft Graph (Outlook, Teams, SharePoint)
- Dialpad
- QuickBooks
- Adobe Sign
- Facebook/Instagram
- LinkedIn
- Google Analytics

**Test Scenarios:**
1. Check all connection statuses
2. Test reconnect for failed integration
3. View API usage stats
4. Check webhook delivery log
5. Refresh credentials
6. View error history

### Component 8: Settings & Configuration

**Required Features:**
- [ ] User profile management
- [ ] Password change
- [ ] Notification preferences
- [ ] Email templates editor
- [ ] SMS templates editor
- [ ] Business hours configuration
- [ ] Holiday schedule
- [ ] Webhook URLs display
- [ ] API key management (view only, not display)

**Test Scenarios:**
1. Update user profile
2. Change password
3. Edit email template
4. Update business hours
5. Add holiday
6. Save notification preferences
7. View webhook URLs

---

## Testing Protocols

### Manual Testing Checklist

**Daily Testing (During Development):**
1. Load dashboard → verify no errors
2. Create test lead → verify appears in dashboard
3. Send test email → verify delivered
4. Schedule test session → verify in calendar
5. Check integration status → all green

**Weekly Testing:**
1. Full user journey test (lead → consultation → enrollment → session)
2. Test all API integrations
3. Load testing (simulate 10+ concurrent users)
4. Mobile responsiveness check
5. Security scan (OWASP ZAP or similar)

**Pre-Launch Testing:**
1. End-to-end testing with real data
2. User acceptance testing with Danielle
3. Performance testing under load
4. Security penetration testing
5. Backup and recovery testing
6. Documentation review

### Automated Testing

```python
# Example automated test suite structure

import pytest
import requests

BASE_URL = "http://localhost:3015"

def test_dashboard_loads():
    """Test that dashboard home page loads successfully"""
    response = requests.get(f"{BASE_URL}/")
    assert response.status_code == 200
    assert "Trifecta AI Agent Dashboard" in response.text

def test_api_create_lead():
    """Test lead creation via API"""
    lead_data = {
        "name": "Test User",
        "email": "test@example.com",
        "phone": "+14031234567",
        "inquiry_type": "self",
        "program_interest": "28_day_virtual"
    }
    response = requests.post(f"{BASE_URL}/api/leads", json=lead_data)
    assert response.status_code == 201
    assert "lead_id" in response.json()

def test_integration_outlook():
    """Test Outlook email sending integration"""
    email_data = {
        "to": "test@example.com",
        "subject": "Test Email",
        "body": "This is a test"
    }
    response = requests.post(f"{BASE_URL}/api/integrations/outlook/send", json=email_data)
    assert response.status_code == 200
    assert response.json()["sent"] == True

def test_session_scheduling():
    """Test session scheduling"""
    session_data = {
        "client_name": "Test Client",
        "session_date": "2025-01-20",
        "session_time": "14:00",
        "duration_minutes": 60
    }
    response = requests.post(f"{BASE_URL}/api/sessions/schedule", json=session_data)
    assert response.status_code == 201
    assert "meeting_link" in response.json()

def test_dashboard_performance():
    """Test dashboard response time"""
    import time
    start = time.time()
    response = requests.get(f"{BASE_URL}/")
    end = time.time()
    load_time = end - start
    assert load_time < 2.0  # Page should load in under 2 seconds
```

---

## Performance Optimization

### Frontend Optimization

**1. Code Splitting**
```javascript
// Lazy load components that aren't immediately needed
const ClientManagement = React.lazy(() => import('./components/ClientManagement'));
const Analytics = React.lazy(() => import('./components/Analytics'));
```

**2. Image Optimization**
- Compress all images (use WebP format)
- Implement lazy loading for images below the fold
- Use responsive images (different sizes for mobile/desktop)

**3. Caching Strategy**
```javascript
// Cache static assets for 1 year
app.use(express.static('public', {
  maxAge: '1y',
  immutable: true
}));

// Cache API responses for 5 minutes
app.get('/api/leads', cache('5 minutes'), (req, res) => {
  // ... fetch leads
});
```

**4. Minification**
- Minify JavaScript (use Webpack/Vite)
- Minify CSS
- Remove console.log statements in production

### Backend Optimization

**1. Database Indexing**
```sql
-- Add indexes for frequently queried fields
CREATE INDEX idx_leads_status ON leads(status);
CREATE INDEX idx_clients_program ON clients(program_type);
CREATE INDEX idx_sessions_date ON sessions(session_date);
```

**2. Query Optimization**
```javascript
// Bad: N+1 query problem
const clients = await Client.findAll();
for (let client of clients) {
  client.sessions = await Session.findAll({ where: { clientId: client.id } });
}

// Good: Use eager loading
const clients = await Client.findAll({
  include: [{ model: Session }]
});
```

**3. API Rate Limiting**
```javascript
const rateLimit = require('express-rate-limit');

const apiLimiter = rateLimit({
  windowMs: 15 * 60 * 1000, // 15 minutes
  max: 100 // limit each IP to 100 requests per windowMs
});

app.use('/api/', apiLimiter);
```

**4. Async Processing**
```javascript
// Move heavy tasks to background jobs
const Queue = require('bull');
const transcriptionQueue = new Queue('transcription');

// Add job to queue
transcriptionQueue.add({
  recordingPath: '/path/to/recording.mp4',
  clientName: 'John Doe'
});

// Process job in background
transcriptionQueue.process(async (job) => {
  const transcript = await transcribeRecording(job.data.recordingPath);
  return transcript;
});
```

---

## Deployment Checklist

### Pre-Deployment (On Localhost)

- [ ] All tests passing
- [ ] No console errors in browser
- [ ] No TypeScript/ESLint errors
- [ ] Environment variables documented
- [ ] Database migrations ready
- [ ] API documentation complete
- [ ] User documentation written

### Azure Deployment Configuration

**1. App Service Setup**
```bash
# Create App Service
az webapp create \
  --resource-group TrifectaResourceGroup \
  --plan TrifectaServicePlan \
  --name trifecta-dashboard \
  --runtime "NODE|18-lts"

# Configure environment variables
az webapp config appsettings set \
  --resource-group TrifectaResourceGroup \
  --name trifecta-dashboard \
  --settings \
    NODE_ENV=production \
    DATABASE_URL=$DATABASE_URL \
    OUTLOOK_CLIENT_ID=$OUTLOOK_CLIENT_ID \
    OUTLOOK_CLIENT_SECRET=$OUTLOOK_CLIENT_SECRET
```

**2. Database Configuration**
- Azure SQL Database or Azure Database for PostgreSQL
- Connection string in Azure Key Vault
- Firewall rules configured
- Backup schedule set (daily)

**3. SSL Certificate**
- Enable HTTPS only
- Force HTTPS redirects
- Auto-renew certificate

**4. Custom Domain**
```bash
# Map custom domain
az webapp config hostname add \
  --resource-group TrifectaResourceGroup \
  --webapp-name trifecta-dashboard \
  --hostname dashboard.trifectaaddictionservices.com
```

### Post-Deployment Verification

- [ ] Dashboard accessible via production URL
- [ ] HTTPS working correctly
- [ ] All integrations functioning
- [ ] Database connections stable
- [ ] Logs streaming properly
- [ ] Monitoring alerts configured
- [ ] Backup tested
- [ ] Load test completed

---

## Monitoring & Maintenance

### Azure Application Insights Setup

```javascript
const appInsights = require('applicationinsights');
appInsights.setup(process.env.APPINSIGHTS_INSTRUMENTATIONKEY)
  .setAutoDependencyCorrelation(true)
  .setAutoCollectRequests(true)
  .setAutoCollectPerformance(true, true)
  .setAutoCollectExceptions(true)
  .setAutoCollectDependencies(true)
  .setAutoCollectConsole(true)
  .setUseDiskRetryCaching(true)
  .start();
```

### Key Metrics to Monitor

**Performance Metrics:**
- Page load time
- API response time
- Database query time
- Error rate
- Request volume

**Business Metrics:**
- New leads per day
- Consultations scheduled
- Client enrollments
- Revenue generated
- Conversion rates

**System Health:**
- CPU usage
- Memory usage
- Disk space
- Network latency
- Database connections

### Alert Configuration

```javascript
// Example alert rules
const alerts = {
  high_error_rate: {
    condition: "error_rate > 5%",
    notification: "email to danielle@trifectaaddictionservices.com",
    severity: "high"
  },
  slow_api_response: {
    condition: "avg_response_time > 2 seconds",
    notification: "slack #tech-alerts",
    severity: "medium"
  },
  database_down: {
    condition: "database_connection_failed",
    notification: "SMS to Danielle",
    severity: "critical"
  }
};
```

---

## Common Issues & Troubleshooting

### Issue 1: Dashboard Won't Load

**Symptoms:**
- Blank white screen
- "Cannot GET /" error
- Infinite loading spinner

**Diagnosis:**
```bash
# Check if server is running
curl http://localhost:3015

# Check server logs
tail -f logs/server.log

# Check for port conflicts
lsof -i :3015
```

**Solutions:**
- Restart server: `npm run dev`
- Check `.env` file exists and has all required variables
- Verify database connection string
- Clear browser cache
- Check for JavaScript errors in console

### Issue 2: API Integration Failing

**Symptoms:**
- "Integration Status: Red"
- "Failed to send email" error
- Webhooks not receiving data

**Diagnosis:**
```javascript
// Test API connection
const testConnection = async () => {
  try {
    const response = await outlookAPI.getProfile();
    console.log("Connection successful:", response);
  } catch (error) {
    console.error("Connection failed:", error.message);
  }
};
```

**Solutions:**
- Refresh access token
- Check API credentials in Azure Key Vault
- Verify network connectivity
- Check API rate limits
- Review webhook URL configuration

### Issue 3: Performance Degradation

**Symptoms:**
- Dashboard slow to load
- API requests taking >2 seconds
- Browser freezing during interactions

**Diagnosis:**
```bash
# Check server performance
top

# Check database queries
EXPLAIN ANALYZE SELECT * FROM leads WHERE status = 'new';

# Check memory usage
free -m
```

**Solutions:**
- Add database indexes
- Implement query caching
- Optimize frontend bundles
- Enable CDN for static assets
- Scale up Azure App Service plan

---

## Security Audit Checklist

### Authentication & Authorization

- [ ] Strong password requirements enforced
- [ ] Session tokens expire after inactivity
- [ ] Multi-factor authentication available
- [ ] Role-based access working correctly
- [ ] Password reset flow secure
- [ ] No credentials in source code

### Data Protection

- [ ] All data encrypted in transit (HTTPS)
- [ ] Sensitive data encrypted at rest
- [ ] PHI not logged in plain text
- [ ] SQL injection prevention implemented
- [ ] XSS prevention implemented
- [ ] CSRF tokens used for forms

### API Security

- [ ] API keys stored in Key Vault
- [ ] Rate limiting configured
- [ ] Input validation on all endpoints
- [ ] Authentication required for sensitive endpoints
- [ ] CORS configured properly
- [ ] API versioning implemented

### Compliance

- [ ] HIPAA compliance documented
- [ ] Privacy policy accessible
- [ ] Terms of service accepted
- [ ] Data retention policy implemented
- [ ] Audit logs maintained
- [ ] Breach notification procedure documented

---

## Dashboard Optimization Priorities

### HIGH PRIORITY (Do First)

1. **Complete Core Functionality**
   - Lead management CRUD operations
   - Client profile pages
   - Session scheduling
   - Integration status monitoring

2. **Fix Critical Bugs**
   - Any authentication issues
   - Database connection errors
   - API integration failures

3. **Implement Security Measures**
   - Move API keys to Azure Key Vault
   - Enable HTTPS
   - Add CSRF protection
   - Implement rate limiting

### MEDIUM PRIORITY (Do Next)

4. **Performance Optimization**
   - Add database indexes
   - Implement caching
   - Optimize large queries
   - Minify frontend assets

5. **User Experience Improvements**
   - Add loading indicators
   - Improve error messages
   - Add success confirmations
   - Implement keyboard shortcuts

6. **Monitoring & Alerts**
   - Set up Application Insights
   - Configure alert rules
   - Add health check endpoint
   - Implement error logging

### LOW PRIORITY (Nice to Have)

7. **Advanced Features**
   - Advanced analytics
   - Custom report builder
   - Bulk operations
   - Export to multiple formats

8. **Polish & Refinement**
   - Dark mode toggle
   - Customizable dashboard
   - Animated transitions
   - Improved mobile experience

---

## Next Steps & Action Plan

### This Week
1. ✅ Review current dashboard code in Claude Code
2. ⬜ Run automated test suite
3. ⬜ Fix critical bugs identified
4. ⬜ Complete missing core features
5. ⬜ Move secrets to Azure Key Vault

### Next Week
6. ⬜ Conduct user acceptance testing with Danielle
7. ⬜ Optimize performance (add indexes, caching)
8. ⬜ Set up Application Insights monitoring
9. ⬜ Deploy to Azure staging environment
10. ⬜ Load test with realistic data

### Week 3
11. ⬜ Final security audit
12. ⬜ Complete documentation
13. ⬜ Train Danielle on dashboard usage
14. ⬜ Deploy to production
15. ⬜ Monitor closely for first 72 hours

---

## Conclusion

This skill provides comprehensive testing protocols, optimization strategies, and deployment procedures for the Trifecta AI Agent dashboard. By following these checklists and guidelines, you can ensure the dashboard is production-ready, secure, performant, and provides excellent user experience.

**Key Success Criteria:**
- All core functionality working
- All integrations connected and stable
- Security measures implemented
- Performance optimized (<2s load time)
- Monitoring and alerts configured
- User acceptance testing passed

Use this skill in combination with the AI Agent Orchestration skill for complete understanding of the dashboard's role in the Trifecta ecosystem.
