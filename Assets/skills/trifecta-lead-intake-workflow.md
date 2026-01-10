# Trifecta Lead Intake & Follow-Up Workflow

## Overview
This skill provides Claude with complete knowledge of Trifecta's lead management system across GoDaddy Conversations (web chat), Outlook (contact forms & emails), and Dialpad. It includes all response templates, tracking procedures, signature rules, and follow-up protocols for converting website visitors into enrolled clients.

## When to Use This Skill
Use this skill when:
- Monitoring and responding to GoDaddy web chat inquiries
- Processing contact form submissions from Outlook
- Tracking leads in Google Sheets
- Sending detailed program information emails
- Following up with leads who provided contact information
- Managing B2B referral partnerships
- Updating lead status and conversion tracking

## Platform Access & URLs

### GoDaddy Conversations (Web Chat)
- **URL**: https://conversations.godaddy.com/conversations/[conversation-id]
- **Purpose**: Real-time website chat inquiries
- **Total Conversations**: 704
- **Filters**: Inbox, Status, Labels, Channels, Has Reminder
- **Message Types**:
  - "Chatbot:" = Automated bot responses
  - "You:" = Human responses from Danielle/assistant
  - "Talk to a human" button = High-priority lead

### Outlook Email
- **Account**: info@trifectaaddictionservices.com
- **URL**: https://outlook.office.com
- **Folders**: Inbox, Sent Items
- **Purpose**: Send detailed program information, respond to contact forms

### Google Sheets Lead Tracker
- **URL**: https://docs.google.com/spreadsheets/d/1aV55LlDzyfqVu4maXLxfN55cb_NPBnU21BjeqVbqnL0/edit#gid=0
- **Sheet Name**: "Trifecta Addiction Services - Leads Tracker"
- **Columns**:
  - A: Date Contacted
  - B: Name/Identifier
  - C: Email Address
  - D: Phone Number
  - E: Source
  - F: Initial Question/Interest
  - G: Date Responded
  - H: Status
  - I: Follow-up Sent
  - J: Program Interest Notes

### Dialpad
- **Purpose**: Phone and SMS tracking (integrated with lead workflow)

## Complete Workflow Process

### Phase 1: Monitoring & Initial Identification

**Daily Monitoring Protocol:**
1. Access GoDaddy Conversations inbox
2. Review conversations from last 10 days
3. Identify conversations requiring human response

**Decision Criteria - RESPOND If:**
- ✅ Visitor clicked "Talk to a human"
- ✅ Visitor asked a specific question
- ✅ Contact form submitted with inquiry
- ✅ Named lead (not Guest User) with question

**Decision Criteria - DO NOT Respond If:**
- ❌ Only "Chatbot:" messages visible (no human question)
- ❌ Only chatbot follow-up "We haven't heard from you..."
- ❌ Already has "You:" response and awaiting reply

**Lead Types:**
1. **Named Leads**: Lori-Ann Crain, Valerii Tatianich, angie
2. **Guest Users**: Guest User 1767710374
3. **Contact Forms**: Louise.Chalupiak@shaw.ca
4. **Professional Referrers**: Celene from Inii Healing House

### Phase 2: Initial Response in GoDaddy Chat

**For General Leads (Guest Users & Chat Inquiries):**

```
Hi there!

Thank you so much for your interest in Trifecta Addiction & Mental Health Services. I'd love to provide you with more detailed information about our programs.

To send you our comprehensive program overview and pricing details directly, would you mind sharing your best email address with me?

I'm here to answer any questions you may have, and I look forward to supporting you.

Warmly,
Trifecta's Virtual Assistant
```

**For Named Leads with Specific Questions:**

```
Hi [Name],

Thank you for reaching out and for your interest in [specific program/question]. I'm glad to connect with you.

To provide you with detailed [pricing/program] information and help you understand which option would be the best fit, would you mind sharing your best email address with me?

I'm here to answer any questions you have, and I look forward to supporting you.

Warmly,
Trifecta's Virtual Assistant
```

**For Professional/B2B Referrers:**

```
Hi [Name],

Thank you for reaching out from [Organization]!

Yes, absolutely - you can send admissions packages to info@trifectaaddictionservices.com. We'd be happy to review them and explore potential collaboration opportunities.

If you'd like to connect directly to discuss referral processes or partnership opportunities, please feel free to call us at +1 (403) 907-0996.

Warmly,
Trifecta's Virtual Assistant
📧 Email: info@trifectaaddictionservices.com
📞 Phone: +1 (403) 907-0996
```

**CRITICAL SIGNATURE RULE:**
- **NEVER** sign as "Danielle Claughton" in GoDaddy chat
- **ALWAYS** use "Trifecta's Virtual Assistant" or "Trifecta's Agent"
- Exception: Outlook emails use Danielle's full signature

### Phase 3: Obtaining Contact Information

**For Named Leads:**
1. Click on contact name at top of GoDaddy conversation
2. Look for email address in contact details panel
3. Copy email if present

**For Contact Forms:**
- Email address already visible in conversation

**For Guest Users:**
- Must wait for them to reply with email in chat
- No contact info available until they provide it

**Documentation Decision:**
- If email found: Proceed to Phase 4 (send program info)
- If no email: Log in Sheet as "Awaiting Email" and monitor for reply

### Phase 4: Send Detailed Program Information via Outlook

**Pre-Send Verification:**
1. Navigate to Outlook: https://outlook.office.com
2. Check "Sent Items" to verify email hasn't already been sent
3. **CRITICAL**: Never send duplicate program emails

**Subject Lines:**
- "Trifecta Addiction Services - Program Information & Pricing"
- "Trifecta Addiction Services - 28-Day Boot Camp Program Information"
- "Trifecta Addiction Services - Inpatient Program Information"

**Email Template Structure:**

**1. Greeting:**
```
Dear [Name],

Thank you for reaching out to Trifecta Addiction & Mental Health Services. [Personalized acknowledgment of their situation/question].
```

**2. Program Overview:**
```
Based on what you've shared—[reference their question]—let me walk you through our most comprehensive option:

**28-Day Virtual Intensive One-on-One Boot Camp**
⚡ Immediate availability — one opening now

This is our most robust program and delivers the clinical intensity of inpatient residential treatment, privately and virtually.

You receive:
• One-hour private 1:1 sessions every day for 28 consecutive days
• A personalized Empowerment Workbook Binder, mailed to you, designed to guide your daily recovery work
• Evidence-based treatment using CBT, DBT, and trauma-informed approaches, tailored specifically to your needs
• Flexible session scheduling, including lunch-hour or after-4 PM options to fit your life

This is not a generic program. Every session is customized to your specific needs and circumstances, with one goal: sustainable recovery.
```

**3. Why Daily Sessions Matter:**
```
**Why Daily Sessions Make the Difference**

[Condition] changes the brain—recovery requires neuroplastic change, which means your brain needs consistent, daily support to interrupt old patterns and build new, healthier ones. Daily sessions for 28 consecutive days create the foundation for lasting transformation.
```

**4. Inpatient Option (if relevant):**
```
**Inpatient Residential Option**

If you're also considering our Calgary-based inpatient program, the next intake availability is late January 2026. This includes:
• 24/7 structured environment with on-site support
• Daily individual and group therapy sessions
• Evidence-based treatment using CBT, DBT, and neuroplasticity-focused approaches
• Comprehensive aftercare planning and transition support
```

**5. Pricing & Investment:**
```
**Pricing & Investment**

Detailed pricing information for both programs is available on our website at www.trifectaaddictionservices.com. I'm also happy to discuss investment details directly during a consultation to ensure you have complete clarity.
```

**6. Next Steps:**
```
**Next Steps**

I'd like to connect with you briefly to [learn more about your situation/answer questions]. Here's how to move forward:

1. Review program details and pricing: www.trifectaaddictionservices.com

2. Book a complimentary consultation: https://outlook.office.com/bookwithme/user/fb9a2dc9e8cb43ca92cc90d034210d7f@trifectaaddictionservices.com

[Personalized closing statement referencing their situation]

Please reach out anytime—I'm here to help.
```

**7. Signature (ALWAYS use in Outlook):**
```
Warmly,

Danielle Claughton
Founding Director & CEO
Trifecta Addiction and Mental Health Services

📧 Email: info@trifectaaddictionservices.com
🌐 Website: www.trifectaaddictionservices.com
📞 Phone: +1 (403) 907-0996 | +1 (403) 907-1034
📍 Calgary, Alberta, Canada

"Empowering recovery, one step at a time."

⚕️ Evidenced-Based Neuroplasticity Model | Holistic, Hands-On Treatment
```

### Phase 5: Notify Lead in GoDaddy Chat

**After Sending Program Email:**

Return to GoDaddy conversation and send:

```
Great news, [Name]! I've just sent you a comprehensive email with detailed [program type] information and pricing to [email@address.com]. Please check your inbox (and spam folder just in case). Looking forward to connecting with you!
```

**Purpose**: Ensures the lead knows to check their email and provides transparency about next steps.

### Phase 6: Update Google Sheets Tracker

**Access Sheet:**
https://docs.google.com/spreadsheets/d/1aV55LlDzyfqVu4maXLxfN55cb_NPBnU21BjeqVbqnL0/edit#gid=0

**Column Entry Guidelines:**

| Column | Format | Examples |
|--------|--------|----------|
| **A: Date Contacted** | MM/DD/YYYY | 01/06/2026 |
| **B: Name/Identifier** | Full name or Guest User ID | "Lori-Ann Crain", "Guest User (1767710374)" |
| **C: Email Address** | Full email | amelanson1977@gmail.com |
| **D: Phone Number** | If provided | Usually blank for chat/Guest Users |
| **E: Source** | Platform origin | "Chat - GoDaddy", "Contact Form - Contact Us" |
| **F: Initial Question/Interest** | Brief summary | "What types of addiction treatment programs?", "Boot Camp program & cost questions" |
| **G: Date Responded** | MM/DD/YYYY | When first human response sent |
| **H: Status** | Current stage | See Status Definitions below |
| **I: Follow-up Sent** | Yes/No/Awaiting Email | Program email sent status |
| **J: Program Interest Notes** | Program type | "28-Day Boot Camp", "Inpatient Treatment", "Family member inquiry" |

**Status Definitions (Column H):**
- **"Response Sent"** = Initial human reply sent in GoDaddy, awaiting email address
- **"Awaiting Human Response"** = Lead clicked "Talk to a human" but no reply sent yet
- **"Program Info Sent"** = Full program email sent via Outlook
- **"Customer Replied"** = Lead has responded to our message
- **"Business Response Sent"** = Comprehensive contact form email sent

**Follow-up Sent Definitions (Column I):**
- **"Yes"** = Program information email sent via Outlook
- **"No"** = No program email sent yet
- **"Awaiting Email"** = Cannot send until email address provided

**CRITICAL TRACKING RULES:**
- **ALWAYS** update sheet after sending initial response
- **ALWAYS** update sheet after sending program email
- **ALWAYS** update when status changes
- Never skip sheet updates - this is the master tracking system

### Phase 7: Ongoing Monitoring & Follow-Up

**Daily Inbox Check:**
- Frequency: Multiple times per day
- Time Window: Last 10 days
- Look for: Recent activity ("Just now", "2 min", "Today")

**Processing Replies:**

**If They Provided Email:**
1. Extract email address
2. Update Google Sheets Column C
3. Send program info via Outlook (Phase 4)
4. Notify them in chat (Phase 5)
5. Update Sheet Status to "Program Info Sent" and Follow-up to "Yes"

**If They Asked Follow-Up Questions:**
1. Respond to their specific question in GoDaddy chat
2. Continue conversation naturally
3. Update Sheet with any new information
4. If ready to book, provide booking link

**If They Haven't Replied:**
- Monitor for 3-5 days
- No further action needed (chatbot will send automated follow-ups)
- Keep status as "Awaiting Email" or "Response Sent"

**Re-Scan Historical Conversations:**
1. Return to GoDaddy Inbox
2. Review last 10 days of conversations
3. Check for any missed replies
4. Verify all Guest Users with questions have received human responses
5. Update any status changes in Google Sheets

### Phase 8: Special Handling Scenarios

#### Scenario A: Professional/B2B Referrers

**Example**: Celene White Quills from Inii Healing House Treatment Centre

**Response Approach:**
- Professional tone (not client-facing)
- Provide direct contact: info@trifectaaddictionservices.com
- Phone: +1 (403) 907-0996
- Discuss partnership/referral processes
- No program pricing needed
- Sheet Status: "Business Response Sent"

#### Scenario B: Contact Forms with Detailed Information

**Examples**: Louise, Melissa, Michael, Taylor, Braeden

**Requirements:**
1. Personalized, comprehensive email response via Outlook
2. Address their specific situation in detail
3. Tailor program recommendation to their needs
4. Include full program details, pricing reference, next steps
5. DO NOT also reply in GoDaddy chat (contact forms don't have chat interface)
6. Sheet Status: "Business Response Sent", Follow-up: "Yes"

#### Scenario C: Existing Conversations

**Example**: User said "I ALREADY TALKED TO NACE"

**Handling:**
- Do not treat as new lead
- Only respond to new messages in existing thread
- Status should reflect ongoing conversation: "Customer Replied"
- Continue conversation as needed

#### Scenario D: Guest Users with Only Chatbot Messages

**DO NOT respond if:**
- Only chatbot automated messages visible
- No actual question from the visitor
- No "Talk to a human" clicked

**These are NOT active leads and should be ignored.**

## Critical Rules & Guardrails

### Signature Rules

**GoDaddy Chat:**
- ✅ ALWAYS sign as "Trifecta's Virtual Assistant" or "Trifecta's Agent"
- ❌ NEVER sign as "Danielle Claughton"

**Outlook Emails:**
- ✅ ALWAYS use Danielle Claughton's full signature with credentials
- ✅ Include all contact info, website, phone numbers
- ✅ Include tagline: "Empowering recovery, one step at a time."

### Duplicate Prevention

- ✅ ALWAYS check Outlook Sent Items before sending program email
- ✅ ALWAYS check Google Sheets for existing lead before creating new row
- ✅ NEVER send program info twice to same email address

### Message Authorship Recognition

- **"Chatbot:"** = Automated bot response (not human)
- **"You:"** = Human response from Danielle or assistant
- Only respond to conversations without "You:" messages (unless following up)

### Response Timing

- Guest Users who asked questions: Respond immediately
- Named leads: Respond within same day
- Contact forms: Respond within 24 hours
- Monitor inbox multiple times daily

### Email Collection Priority

- Primary goal of initial GoDaddy chat response: **GET EMAIL ADDRESS**
- Cannot send program details without email
- Use contact header click method to find hidden emails in GoDaddy

## Workflow Summary Checklist

**For Each New Lead:**
- [ ] Identify conversation in GoDaddy Inbox
- [ ] Verify it needs human response (not just chatbot)
- [ ] Send initial GoDaddy chat response requesting email
- [ ] Check if email is available in contact info
- [ ] If email available: Send program info via Outlook
- [ ] If email sent: Notify lead in GoDaddy chat
- [ ] Add/update lead in Google Sheets with all details
- [ ] Set correct Status and Follow-up Sent values
- [ ] Monitor for replies and follow up as needed

**Daily Monitoring:**
- [ ] Check GoDaddy Inbox (last 10 days)
- [ ] Look for new conversations needing responses
- [ ] Check for replies to existing conversations
- [ ] Verify all Guest Users with questions have responses
- [ ] Update Google Sheets for any status changes
- [ ] Check Outlook for new contact form submissions

## Key Resources

**GoDaddy Conversations:**
- https://conversations.godaddy.com/conversations/[conversation-id]

**Outlook:**
- Sent Items: https://outlook.office.com/mail/sentitems
- New Mail: https://outlook.office.com

**Google Sheets Tracker:**
- https://docs.google.com/spreadsheets/d/1aV55LlDzyfqVu4maXLxfN55cb_NPBnU21BjeqVbqnL0/edit#gid=0

**Trifecta Resources:**
- Website: www.trifectaaddictionservices.com
- Email: info@trifectaaddictionservices.com
- Phone: +1 (403) 907-0996 | +1 (403) 907-1034
- Booking Link: https://outlook.office.com/bookwithme/user/fb9a2dc9e8cb43ca92cc90d034210d7f@trifectaaddictionservices.com

## Integration with Other Skills

### Trifecta Practice Management System
- Feeds lead data into client onboarding workflow
- Links to consultation scheduling
- Connects to contract generation

### AI Agent Orchestration
- Lead qualification and scoring
- Automated response triggers
- CRM integration

### Marketing & SEO Strategy
- Tracks lead source attribution
- Measures campaign effectiveness
- Informs content strategy based on common questions

## Best Practices

### Response Quality
- Always personalize responses based on the lead's specific question
- Reference details they mentioned in their inquiry
- Match their tone (urgent vs. exploratory)
- Be warm but professional

### Email Personalization
- Acknowledge their specific situation in greeting
- Tailor program recommendation to their needs
- Reference their question/concern in "Based on what you've shared"
- Customize closing statement to their circumstances

### Follow-Up Persistence
- Don't give up after one non-response
- Allow chatbot automated follow-ups to work
- Re-engage if they return to chat
- Update status to reflect current stage

### Data Quality
- Always double-check email addresses before sending
- Verify spelling of names
- Note any special circumstances in Program Interest Notes
- Track B2B inquiries separately

## Conclusion

This skill provides comprehensive guidance for managing the complete lead intake and follow-up workflow across all Trifecta platforms. By following these protocols, Claude can effectively convert website visitors into enrolled clients while maintaining data integrity and providing excellent customer service.

**Key Success Metrics:**
- Response time <24 hours
- Email collection rate >80%
- Lead-to-consultation conversion rate >40%
- Zero duplicate communications
- 100% data accuracy in Google Sheets

Use this skill in combination with other Trifecta skills for complete ecosystem management.
