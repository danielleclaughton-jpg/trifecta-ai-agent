# Trifecta Asset Management, Investor Portal & Marketing Automation

## Overview
This skill provides Claude with comprehensive knowledge of Trifecta's marketing asset management system, investor portal architecture, and campaign automation workflows. It includes integration with SharePoint for asset storage, NotebookLM for research aggregation, Google Gemini for content generation, and a KPI dashboard for performance tracking.

## When to Use This Skill
Use this skill when:
- Organizing and storing marketing assets (photos, videos, graphics, documents)
- Running marketing campaigns across multiple platforms
- Creating investor materials (pitch decks, reports, updates)
- Aggregating research and competitive intelligence
- Generating performance reports and KPI dashboards
- Managing brand assets and maintaining consistency
- Coordinating with marketing team or agencies

## Recommended Storage Architecture

### **RECOMMENDATION: SharePoint as Primary Asset Hub**

**Why SharePoint:**
1. **Already Integrated**: You have Microsoft Graph API access and existing SharePoint infrastructure
2. **Version Control**: Automatic versioning for all assets
3. **Metadata Tagging**: Rich metadata for searchability (campaign, date, asset type, usage rights)
4. **Collaboration**: Easy sharing with team, agencies, contractors
5. **Permissions**: Granular control (staff, investors, public)
6. **AI Integration**: Microsoft AI services can analyze assets (image recognition, transcription)
7. **Cost-Effective**: Included in existing Microsoft 365 licensing
8. **Compliance**: HIPAA-compliant for any client-related materials

**Alternative: Azure Blob Storage**
- Use for: Large video files (>100MB), raw footage, archived campaigns
- Benefits: Lower cost for storage, better for CDN delivery
- Drawback: Less user-friendly for team collaboration

**Not Recommended: Google Drive**
- Reason: Adds another authentication layer, less integrated with your Azure ecosystem

---

## SharePoint Asset Library Structure

### Complete Folder Hierarchy

```
/sites/TrifectaAssets/
├── Brand_Assets/
│   ├── Logos/
│   │   ├── Trifecta_Logo_Primary.png
│   │   ├── Trifecta_Logo_White.png
│   │   ├── Trifecta_Logo_Black.png
│   │   ├── Illuminate_Logo_Primary.png
│   │   └── Combined_Lockup.png
│   ├── Colors/
│   │   └── Brand_Color_Palette.pdf
│   ├── Fonts/
│   │   ├── Playfair_Display.ttf
│   │   └── Inter.ttf
│   ├── Templates/
│   │   ├── Social_Media_Templates/
│   │   ├── Email_Templates/
│   │   └── Presentation_Templates/
│   └── Brand_Guidelines.pdf
├── Photography/
│   ├── Professional_Headshots/
│   │   ├── Danielle_Headshot_2025_01.jpg
│   │   └── Staff_Headshots/
│   ├── Facility_Photos/
│   │   ├── Exterior/
│   │   ├── Interior/
│   │   └── Treatment_Spaces/
│   ├── Lifestyle_Stock/
│   │   ├── Recovery_Journey/
│   │   ├── Wellness_Activities/
│   │   └── Nature_Healing/
│   └── Event_Photos/
│       └── 2025/
├── Video_Assets/
│   ├── Testimonials/
│   │   ├── Client_A_Testimonial_2025.mp4
│   │   └── Alumni_Success_Stories/
│   ├── Educational_Content/
│   │   ├── DBT_Skills_Series/
│   │   └── Neuroplasticity_Explainers/
│   ├── Promotional_Videos/
│   │   ├── 28_Day_Virtual_Promo.mp4
│   │   └── Inpatient_Program_Overview.mp4
│   ├── Social_Media_Clips/
│   │   ├── Instagram_Reels/
│   │   ├── TikTok/
│   │   └── YouTube_Shorts/
│   └── Raw_Footage/
│       └── Archived_Projects/
├── Graphics_Design/
│   ├── Social_Media_Posts/
│   │   ├── 2025/
│   │   │   ├── January/
│   │   │   │   ├── Radical_Acceptance_Post.png
│   │   │   │   └── Wise_Mind_Post.png
│   │   │   └── February/
│   │   └── 2024/
│   ├── Infographics/
│   │   ├── DBT_Skills_Infographic.png
│   │   └── Neuroplasticity_Process.png
│   ├── Email_Headers/
│   ├── Website_Graphics/
│   └── Print_Materials/
├── Marketing_Campaigns/
│   ├── 2025_Q1_Executive_Campaign/
│   │   ├── Assets/
│   │   ├── Copy/
│   │   ├── Performance_Reports/
│   │   └── Campaign_Brief.pdf
│   ├── 2025_Oil_Gas_Outreach/
│   └── 2024_Campaigns_Archive/
├── Investor_Materials/
│   ├── Pitch_Decks/
│   │   ├── Trifecta_Pitch_Deck_2025.pptx
│   │   └── Executive_Summary.pdf
│   ├── Financial_Reports/
│   │   ├── 2024_Revenue_Report.pdf
│   │   └── Q1_2025_Projections.xlsx
│   ├── Market_Research/
│   │   ├── Competitive_Analysis.pdf
│   │   └── Industry_Trends_Report.pdf
│   ├── Case_Studies/
│   │   └── Client_Outcomes_Anonymized.pdf
│   └── Due_Diligence/
│       └── Data_Room/
├── Content_Library/
│   ├── Blog_Posts/
│   │   ├── Published/
│   │   └── Drafts/
│   ├── Email_Campaigns/
│   │   ├── Welcome_Series/
│   │   ├── Educational_Series/
│   │   └── Nurture_Sequences/
│   ├── Website_Copy/
│   └── Social_Media_Content_Calendar.xlsx
└── Research_Aggregation/
    ├── NotebookLM_Exports/
    ├── Competitive_Intelligence/
    ├── Industry_Research/
    └── Clinical_Studies/
```

### Metadata Tagging Schema

Every asset should have the following metadata tags:

| Field | Type | Purpose | Example |
|-------|------|---------|---------|
| **Asset Type** | Choice | Categorize asset | Photo, Video, Graphic, Document |
| **Campaign** | Text | Link to campaign | "2025 Q1 Executive Campaign" |
| **Platform** | Multi-choice | Where it's used | LinkedIn, Instagram, Email, Website |
| **Date Created** | Date | When asset was created | 2025-01-15 |
| **Usage Rights** | Choice | Legal usage | Full Rights, Limited, Stock |
| **Status** | Choice | Asset status | Active, Archived, Deprecated |
| **Keywords** | Text | Searchability | "DBT, recovery, executive, neuroplasticity" |
| **Created By** | Person | Who created it | Danielle, Marketing Agency, Freelancer |
| **File Size** | Automatic | Storage tracking | 2.4 MB |
| **Dimensions** | Text | For images/videos | 1920x1080, 1080x1080 |

---

## Marketing Campaign Automation Workflows

### Campaign Lifecycle Management

```python
def create_marketing_campaign(
    campaign_name: str,
    campaign_type: str,
    target_audience: str,
    platforms: list,
    start_date: date,
    end_date: date
):
    """
    Create and organize new marketing campaign
    
    Args:
        campaign_name: Descriptive campaign name
        campaign_type: "awareness" | "lead_gen" | "conversion" | "retention"
        target_audience: "executives" | "oil_gas" | "families" | "general"
        platforms: ["linkedin", "instagram", "facebook", "email", "google_ads"]
        start_date: Campaign start date
        end_date: Campaign end date
    
    Returns:
        dict: Campaign structure and asset requirements
    """
    
    # Step 1: Create campaign folder structure in SharePoint
    campaign_folder = f"Marketing_Campaigns/{campaign_name}"
    
    create_sharepoint_folders([
        f"{campaign_folder}/Assets/Photos",
        f"{campaign_folder}/Assets/Videos",
        f"{campaign_folder}/Assets/Graphics",
        f"{campaign_folder}/Copy",
        f"{campaign_folder}/Performance_Reports",
        f"{campaign_folder}/Ad_Creative"
    ])
    
    # Step 2: Generate campaign brief using Claude AI
    campaign_brief = generate_campaign_brief(
        campaign_name=campaign_name,
        campaign_type=campaign_type,
        target_audience=target_audience,
        platforms=platforms
    )
    
    # Upload campaign brief
    upload_to_sharepoint(
        content=campaign_brief,
        filename="Campaign_Brief.pdf",
        folder_path=campaign_folder
    )
    
    # Step 3: Create content calendar
    content_calendar = create_content_calendar(
        campaign_name=campaign_name,
        platforms=platforms,
        start_date=start_date,
        end_date=end_date
    )
    
    # Step 4: Define asset requirements
    asset_requirements = define_asset_needs(
        platforms=platforms,
        campaign_type=campaign_type
    )
    
    # Step 5: Set up KPI tracking
    create_kpi_dashboard(
        campaign_name=campaign_name,
        platforms=platforms,
        goals=campaign_brief["objectives"]
    )
    
    return {
        "campaign_folder": campaign_folder,
        "campaign_brief": campaign_brief,
        "content_calendar": content_calendar,
        "asset_requirements": asset_requirements,
        "kpi_dashboard_url": f"https://powerbi.com/campaigns/{campaign_name}"
    }
```

### Asset Requirements by Platform

**LinkedIn (Professional/Executive Audience)**
- Image Posts: 1200x627px (horizontal), 1080x1080px (square)
- Video: 1080x1920px (vertical for feed), 1920x1080px (horizontal)
- Carousel: 1080x1080px (up to 10 images)
- Tone: Professional, evidence-based, authority-building
- Frequency: 3-5 posts per week

**Instagram (Lifestyle/Wellness Focus)**
- Feed Posts: 1080x1080px (square), 1080x1350px (portrait)
- Stories: 1080x1920px (vertical)
- Reels: 1080x1920px (vertical, 15-90 seconds)
- Tone: Inspirational, relatable, visual storytelling
- Frequency: 5-7 posts per week + daily stories

**Facebook (Community/Family Audience)**
- Image Posts: 1200x630px (link preview), 1080x1080px (square)
- Video: 1280x720px (horizontal), 1080x1920px (vertical)
- Tone: Warm, educational, community-focused
- Frequency: 3-5 posts per week

**Email Campaigns**
- Header Image: 600px wide (height varies)
- In-line Graphics: 600px wide max
- Tone: Personal, conversational, value-driven
- Frequency: 1-2 emails per week

**Google Ads**
- Display Ads: 300x250px, 728x90px, 160x600px, 300x600px
- Responsive Search Ads: Text-only (headlines, descriptions)
- Tone: Benefit-driven, clear call-to-action

---

## NotebookLM Integration

### Research Aggregation Workflows

**What is NotebookLM:**
Google's AI-powered research assistant that helps you:
- Upload and analyze multiple sources (PDFs, articles, notes)
- Ask questions across all sources
- Generate summaries and insights
- Create source-cited content

**Trifecta Use Cases:**

#### 1. Competitive Intelligence Workflow

```
STEP 1: Source Collection
→ Upload competitor websites (text export)
→ Upload competitor social media analysis reports
→ Upload industry reports (SAMHSA, NAMI data)
→ Upload local market research

STEP 2: NotebookLM Analysis
→ Query: "What are the top 3 unique value propositions of competitors in Calgary?"
→ Query: "What pricing strategies are competitors using?"
→ Query: "What gaps exist in the executive addiction treatment market?"

STEP 3: Export & Integration
→ Export insights to PDF
→ Store in: Research_Aggregation/Competitive_Intelligence/
→ Use insights to inform campaign strategy
```

#### 2. Investor Materials Workflow

```
STEP 1: Source Collection
→ Upload Trifecta financial reports
→ Upload industry market size data
→ Upload healthcare investment trends reports
→ Upload client outcome data (anonymized)

STEP 2: NotebookLM Analysis
→ Query: "Summarize Trifecta's financial performance vs industry benchmarks"
→ Query: "What are the key market trends supporting growth?"
→ Query: "Generate an executive summary for investors"

STEP 3: Content Generation
→ Use NotebookLM outputs as basis for pitch deck slides
→ Generate investment thesis document
→ Create FAQ for investor due diligence
```

#### 3. Content Research Workflow

```
STEP 1: Source Collection
→ Upload Dr. Anna Lembke articles/books
→ Upload Dr. Andrew Huberman podcast transcripts
→ Upload DBT research papers
→ Upload neuroplasticity studies

STEP 2: NotebookLM Analysis
→ Query: "What does research say about neuroplasticity and addiction recovery?"
→ Query: "Summarize key DBT skills for social media content"
→ Query: "What are practical applications of Dr. Lembke's dopamine balance concept?"

STEP 3: Content Creation
→ Generate blog post outlines based on research
→ Create evidence-based social media captions
→ Develop educational video scripts
```

### NotebookLM Integration Code

```python
def create_notebooklm_research_project(
    project_name: str,
    sources: list,
    research_questions: list
):
    """
    Create NotebookLM research project and aggregate insights
    
    Args:
        project_name: Name of research project
        sources: List of file paths to upload as sources
        research_questions: List of questions to query
    
    Returns:
        dict: Research outputs and insights
    """
    
    # Note: NotebookLM API details pending
    # This is a placeholder workflow structure
    
    # Step 1: Create project
    notebook_project = {
        "name": project_name,
        "sources": [],
        "insights": []
    }
    
    # Step 2: Upload sources
    for source_path in sources:
        # Upload each source to NotebookLM
        # (API integration pending)
        source_id = upload_to_notebooklm(source_path)
        notebook_project["sources"].append(source_id)
    
    # Step 3: Query for insights
    for question in research_questions:
        # Query NotebookLM with question
        # (API integration pending)
        insight = query_notebooklm(
            project_id=notebook_project["id"],
            query=question
        )
        notebook_project["insights"].append({
            "question": question,
            "answer": insight["answer"],
            "sources_cited": insight["sources"]
        })
    
    # Step 4: Export and store
    export_path = f"Research_Aggregation/NotebookLM_Exports/{project_name}.pdf"
    export_notebooklm_insights(notebook_project, export_path)
    
    # Step 5: Upload to SharePoint
    upload_to_sharepoint(
        file_path=export_path,
        folder_path="Research_Aggregation/NotebookLM_Exports"
    )
    
    return notebook_project
```

### Recommended Research Projects

**Project 1: Executive Addiction Treatment Market Analysis**
- Sources: Competitor websites, SAMHSA data, industry reports
- Questions:
  - What is the total addressable market for executive addiction treatment in Canada?
  - What are the key differentiators of top competitors?
  - What unmet needs exist in the executive market?

**Project 2: Neuroplasticity Evidence Base**
- Sources: Research papers, Dr. Lembke's work, clinical studies
- Questions:
  - What does science say about neuroplasticity and addiction recovery?
  - How long does neuroplastic change take?
  - What are practical applications for client education?

**Project 3: Oil & Gas Industry Wellness Trends**
- Sources: Industry wellness reports, safety data, worker health studies
- Questions:
  - What are the primary mental health challenges for oil & gas workers?
  - How do rotational schedules impact treatment access?
  - What wellness programs are competitors offering?

---

## KPI Dashboard for Marketing & Content Performance

### Dashboard Architecture

**Platform: Power BI (Recommended)**
- Why: Native integration with Microsoft ecosystem
- Real-time data from: LinkedIn, Instagram, Facebook, Google Analytics, Email platform
- Accessible via web and mobile

**Alternative: Google Data Studio**
- Why: If using Google Ads heavily
- Integration: Connect to Google Analytics, Google Ads, social media APIs

### Dashboard Structure

#### Page 1: Executive Overview

**KPIs Displayed:**
- Total Reach (all platforms combined)
- Total Engagement (likes, comments, shares, clicks)
- Lead Generation (consultation requests, form submissions)
- Conversion Rate (leads → enrolled clients)
- Cost Per Acquisition (CPA)
- Return on Ad Spend (ROAS)

**Visualizations:**
- Line chart: Reach and engagement trends over time
- Funnel chart: Lead → Consultation → Enrollment conversion
- Bar chart: Performance by platform
- KPI cards: Current month vs. previous month

#### Page 2: Platform Performance

**LinkedIn Performance**
- Follower growth
- Post reach (organic vs. paid)
- Engagement rate
- Profile visits
- InMail response rate
- Top performing posts (by engagement)

**Instagram Performance**
- Follower growth
- Post reach (feed vs. stories vs. reels)
- Engagement rate
- Profile visits
- Website clicks
- Top performing content

**Facebook Performance**
- Page likes growth
- Post reach (organic vs. paid)
- Engagement rate
- Click-through rate
- Lead form submissions

**Email Performance**
- List growth
- Open rate by campaign
- Click-through rate
- Conversion rate
- Unsubscribe rate
- Top performing emails

#### Page 3: Content Analysis

**Top Performing Content**
- By engagement (likes, comments, shares)
- By reach (impressions, views)
- By conversion (clicks to website, form submissions)

**Content Type Analysis**
- Image posts vs. video vs. carousel
- Educational vs. promotional vs. inspirational
- Long-form vs. short-form

**Topic Analysis**
- Which DBT/CBT topics get most engagement?
- Executive vs. general audience content performance
- Oil & Gas industry content performance

#### Page 4: Audience Insights

**Demographics**
- Age distribution
- Gender distribution
- Location (Calgary vs. broader Alberta vs. Canada-wide)
- Job titles (for LinkedIn)

**Behavior**
- Time of day for highest engagement
- Day of week for highest engagement
- Device usage (mobile vs. desktop)

**Journey Analysis**
- How do people find Trifecta? (organic search, social media, referral)
- What content do they engage with before converting?
- How long from first touch to consultation request?

#### Page 5: Campaign ROI

**Campaign Performance**
- By campaign: Reach, engagement, leads, conversions, cost
- ROI calculation: (Revenue - Cost) / Cost × 100%
- Cost per lead by campaign
- Cost per acquisition by campaign

**Budget Allocation**
- Spending by platform
- Spending by campaign
- Recommended budget adjustments based on performance

### Data Integration Code

```python
def update_kpi_dashboard(
    date_range: tuple,
    platforms: list = ["linkedin", "instagram", "facebook", "email", "google_analytics"]
):
    """
    Pull data from all marketing platforms and update KPI dashboard
    
    Args:
        date_range: (start_date, end_date) tuple
        platforms: List of platforms to pull data from
    
    Returns:
        dict: Aggregated KPI data
    """
    
    kpi_data = {
        "date_range": date_range,
        "platforms": {},
        "aggregated": {}
    }
    
    # Pull LinkedIn data
    if "linkedin" in platforms:
        linkedin_data = get_linkedin_analytics(date_range)
        kpi_data["platforms"]["linkedin"] = {
            "followers": linkedin_data["follower_count"],
            "reach": linkedin_data["impressions"],
            "engagement": linkedin_data["engagements"],
            "profile_visits": linkedin_data["profile_views"],
            "clicks": linkedin_data["clicks"]
        }
    
    # Pull Instagram data
    if "instagram" in platforms:
        instagram_data = get_instagram_insights(date_range)
        kpi_data["platforms"]["instagram"] = {
            "followers": instagram_data["follower_count"],
            "reach": instagram_data["reach"],
            "engagement": instagram_data["engagement"],
            "profile_visits": instagram_data["profile_views"],
            "website_clicks": instagram_data["website_clicks"]
        }
    
    # Pull Facebook data
    if "facebook" in platforms:
        facebook_data = get_facebook_insights(date_range)
        kpi_data["platforms"]["facebook"] = {
            "page_likes": facebook_data["page_fans"],
            "reach": facebook_data["page_impressions"],
            "engagement": facebook_data["page_engaged_users"],
            "clicks": facebook_data["page_consumptions"]
        }
    
    # Pull Email data
    if "email" in platforms:
        email_data = get_email_campaign_stats(date_range)
        kpi_data["platforms"]["email"] = {
            "list_size": email_data["total_subscribers"],
            "emails_sent": email_data["total_sent"],
            "open_rate": email_data["avg_open_rate"],
            "click_rate": email_data["avg_click_rate"],
            "conversions": email_data["total_conversions"]
        }
    
    # Pull Google Analytics data
    if "google_analytics" in platforms:
        ga_data = get_google_analytics_data(date_range)
        kpi_data["platforms"]["google_analytics"] = {
            "sessions": ga_data["sessions"],
            "users": ga_data["users"],
            "pageviews": ga_data["pageviews"],
            "bounce_rate": ga_data["bounce_rate"],
            "avg_session_duration": ga_data["avg_session_duration"],
            "goal_completions": ga_data["goal_completions"]
        }
    
    # Aggregate cross-platform metrics
    kpi_data["aggregated"] = {
        "total_reach": sum(p.get("reach", 0) for p in kpi_data["platforms"].values()),
        "total_engagement": sum(p.get("engagement", 0) for p in kpi_data["platforms"].values()),
        "total_clicks": sum(p.get("clicks", 0) for p in kpi_data["platforms"].values()),
        "total_conversions": sum(p.get("conversions", 0) for p in kpi_data["platforms"].values())
    }
    
    # Update Power BI dataset
    update_powerbi_dataset("TrifectaMarketingKPI", kpi_data)
    
    return kpi_data
```

---

## Investor Portal Architecture

### Portal Structure

```
Trifecta Investor Portal (SharePoint Site)
├── Home (Dashboard)
│   ├── Latest Updates
│   ├── Key Metrics Overview
│   └── Quick Links
├── Company Overview
│   ├── Executive Summary
│   ├── Team Bios
│   ├── Company History
│   └── Vision & Mission
├── Financial Performance
│   ├── Revenue Reports (monthly, quarterly, annual)
│   ├── Expense Breakdown
│   ├── Profitability Analysis
│   ├── Cash Flow Statements
│   └── Financial Projections
├── Market & Opportunity
│   ├── Market Size & TAM
│   ├── Competitive Landscape
│   ├── Industry Trends
│   └── Growth Strategy
├── Programs & Services
│   ├── Program Descriptions
│   ├── Client Outcomes Data
│   ├── Pricing Strategy
│   └── Service Expansion Plans
├── Investment Materials
│   ├── Pitch Deck
│   ├── Investment Thesis
│   ├── Term Sheet Template
│   └── Use of Funds Breakdown
├── Due Diligence
│   ├── Legal Documents
│   ├── Licenses & Certifications
│   ├── Insurance Policies
│   ├── Contracts & Agreements
│   └── Intellectual Property
└── Updates & Communications
    ├── Monthly Investor Updates
    ├── Board Meeting Minutes
    ├── Quarterly Business Reviews
    └── News & Press Releases
```

### Access Control

**Investor Roles:**

| Role | Access Level | Can View | Can Download |
|------|-------------|----------|--------------|
| **Prospective Investor** | Limited | Company Overview, Pitch Deck, Public Financial Summary | Pitch Deck only |
| **Active Investor** | Full | All sections except internal board minutes | All except internal documents |
| **Board Member** | Full + Admin | Everything including board minutes | Everything |
| **Trifecta Admin** | Full + Admin | Everything, can upload/edit | Everything |

**Access Implementation:**
```python
def grant_investor_access(
    investor_email: str,
    investor_role: str,
    investment_date: date
):
    """
    Grant appropriate SharePoint permissions to investor
    
    Args:
        investor_email: Investor's email address
        investor_role: "prospective" | "active" | "board_member"
        investment_date: Date of investment (for active/board)
    
    Returns:
        dict: Access confirmation with portal URL
    """
    
    # Define permission levels
    permissions = {
        "prospective": {
            "folders": ["Company_Overview", "Investment_Materials/Pitch_Deck"],
            "permission_level": "Read"
        },
        "active": {
            "folders": ["Company_Overview", "Financial_Performance", "Market_Opportunity", 
                       "Programs_Services", "Investment_Materials", "Updates_Communications"],
            "permission_level": "Read"
        },
        "board_member": {
            "folders": ["*"],  # All folders
            "permission_level": "Contribute"
        }
    }
    
    # Grant SharePoint permissions
    grant_sharepoint_permissions(
        site_url="https://netorgft5726606.sharepoint.com/sites/TrifectaInvestorPortal",
        user_email=investor_email,
        folders=permissions[investor_role]["folders"],
        permission_level=permissions[investor_role]["permission_level"]
    )
    
    # Send welcome email with portal link
    send_investor_welcome_email(
        investor_email=investor_email,
        investor_role=investor_role,
        portal_url="https://netorgft5726606.sharepoint.com/sites/TrifectaInvestorPortal"
    )
    
    # Log access grant in CRM
    log_investor_access(
        investor_email=investor_email,
        role=investor_role,
        date_granted=datetime.now()
    )
    
    return {
        "access_granted": True,
        "portal_url": "https://netorgft5726606.sharepoint.com/sites/TrifectaInvestorPortal",
        "role": investor_role
    }
```

### Monthly Investor Update Template

```markdown
# Trifecta Monthly Investor Update - [Month Year]

**From:** Danielle Claughton, Founding Director & CEO
**Date:** [Date]

---

## Executive Summary

[2-3 sentence overview of the month's performance and key highlights]

---

## Key Metrics

### Financial Performance
- **Revenue:** $[amount] ([+/- %] vs. previous month)
- **New Client Enrollments:** [number] ([+/- %] vs. previous month)
- **Client Retention Rate:** [percentage]
- **Average Revenue Per Client:** $[amount]

### Operational Metrics
- **Active Clients:** [number]
  - Inpatient: [number]
  - Outpatient: [number]
  - Virtual Boot Camp: [number]
- **Program Completion Rate:** [percentage]
- **Client Satisfaction Score:** [score]/5.0

### Marketing Performance
- **Website Traffic:** [number] visits ([+/- %] vs. previous month)
- **Social Media Reach:** [number] impressions
- **Leads Generated:** [number]
- **Lead-to-Client Conversion Rate:** [percentage]

---

## Highlights & Achievements

### Business Development
- [Achievement 1]
- [Achievement 2]
- [Achievement 3]

### Client Outcomes
- [Outcome 1]
- [Outcome 2]

### Team & Operations
- [Update 1]
- [Update 2]

---

## Challenges & Solutions

### Challenge: [Description]
**Impact:** [How it affected operations]
**Solution:** [Steps taken to address]
**Status:** [Resolved / In Progress / Monitoring]

---

## Strategic Initiatives

### Current Focus Areas
1. [Initiative 1] - [Status and progress]
2. [Initiative 2] - [Status and progress]
3. [Initiative 3] - [Status and progress]

### Next Month Priorities
1. [Priority 1]
2. [Priority 2]
3. [Priority 3]

---

## Financial Details

### Revenue Breakdown
- Inpatient Programs: $[amount] ([percentage]% of total)
- Outpatient Programs: $[amount] ([percentage]% of total)
- Virtual Boot Camp: $[amount] ([percentage]% of total)

### Expense Summary
- Personnel: $[amount]
- Marketing: $[amount]
- Facilities: $[amount]
- Operations: $[amount]

### Cash Position
- Beginning Balance: $[amount]
- Ending Balance: $[amount]
- Runway: [months]

---

## Market & Competitive Insights

[Brief update on industry trends, competitive moves, or market opportunities]

---

## Questions & Feedback

We welcome your questions and feedback. Please contact:
- Email: investors@trifectaaddictionservices.com
- Phone: (403) 907-0996

---

*This update is confidential and intended solely for Trifecta investors.*
```

---

## Google Gemini "Banana Slides" Integration

**Note:** Please provide more details about "Banana Slides" tool. Based on the name, I'm assuming it's a Google Gemini-powered presentation generation tool.

**Proposed Integration Workflow:**

```python
def create_presentation_with_gemini(
    presentation_type: str,
    content_source: str,
    slides_count: int,
    template: str = "trifecta_branded"
):
    """
    Generate presentation using Google Gemini
    
    Args:
        presentation_type: "investor_pitch" | "program_overview" | "monthly_update"
        content_source: Path to source content (NotebookLM export, financial report, etc.)
        slides_count: Desired number of slides
        template: Presentation template to use
    
    Returns:
        dict: Generated presentation URL and download link
    """
    
    # Step 1: Prepare content for Gemini
    content = load_content_source(content_source)
    
    # Step 2: Define slide structure based on type
    if presentation_type == "investor_pitch":
        slide_structure = [
            "Title Slide",
            "Problem Statement",
            "Solution",
            "Market Opportunity",
            "Business Model",
            "Traction & Metrics",
            "Competitive Landscape",
            "Team",
            "Financial Projections",
            "Funding Ask & Use of Funds",
            "Contact Information"
        ]
    elif presentation_type == "program_overview":
        slide_structure = [
            "Title Slide",
            "About Trifecta",
            "Program Overview",
            "14-Day Inpatient Program",
            "28-Day Inpatient Program",
            "28-Day Virtual Boot Camp",
            "Treatment Methodology",
            "Client Outcomes",
            "Pricing & Insurance",
            "Next Steps"
        ]
    
    # Step 3: Generate presentation with Gemini
    # (API integration pending - placeholder)
    presentation = gemini_generate_presentation(
        content=content,
        slide_structure=slide_structure,
        template=template,
        branding=TRIFECTA_BRANDING
    )
    
    # Step 4: Upload to SharePoint
    upload_to_sharepoint(
        file=presentation,
        folder_path="Investor_Materials/Pitch_Decks" if presentation_type == "investor_pitch" else "Marketing_Campaigns/Presentations"
    )
    
    return {
        "presentation_url": presentation["sharepoint_url"],
        "download_link": presentation["download_url"]
    }
```

---

## Best Practices & Usage Guidelines

### Asset Management Best Practices

1. **Consistent Naming Conventions**
   - Use descriptive names: `Trifecta_LinkedIn_Post_Radical_Acceptance_2025-01-15.png`
   - Include date in filename for versioning
   - Use underscores (not spaces) for file names

2. **Metadata Tagging**
   - Tag every asset immediately upon upload
   - Use consistent keywords for searchability
   - Update status when assets are deprecated

3. **Version Control**
   - SharePoint automatically versions files
   - Major updates: increment version (v1.0 → v2.0)
   - Minor updates: increment sub-version (v1.0 → v1.1)

4. **Regular Audits**
   - Monthly: Review active campaign assets
   - Quarterly: Archive old campaigns
   - Annually: Delete deprecated assets (with approval)

### Campaign Management Best Practices

1. **Planning Phase**
   - Define clear objectives and KPIs
   - Research audience and competitors
   - Create detailed content calendar
   - Prepare all assets before launch

2. **Execution Phase**
   - Schedule posts in advance using automation tools
   - Monitor performance daily
   - Engage with comments and messages promptly
   - A/B test different creative approaches

3. **Analysis Phase**
   - Review KPIs weekly
   - Identify top-performing content
   - Adjust strategy based on data
   - Document learnings for future campaigns

### Investor Communication Best Practices

1. **Transparency**
   - Share both successes and challenges
   - Provide context for metrics
   - Be proactive about potential issues

2. **Consistency**
   - Send monthly updates on same schedule
   - Use consistent format and structure
   - Maintain professional tone

3. **Responsiveness**
   - Respond to investor questions within 24 hours
   - Provide detailed answers with supporting data
   - Schedule regular investor calls (quarterly)

---

## Integration with Existing Skills

### Trifecta Marketing & SEO Strategy
- Uses same voice and tone guidelines (Lembke/Huberman style)
- Follows content rotation (7-day DBT/CBT cycle)
- Aligns with keyword strategy

### Document Generator
- Uses same branding and templates
- Consistent file naming conventions
- SharePoint integration methods

### Practice Management System
- Client outcome data informs investor materials
- Program performance feeds KPI dashboard
- Treatment methodology showcased in marketing

---

## Next Steps for Implementation

### Immediate Actions (This Week)
1. Set up SharePoint asset library structure
2. Upload existing marketing assets with metadata
3. Create Power BI dashboard (basic version)
4. Set up NotebookLM account and create first research project

### Short-Term (Next 2-4 Weeks)
5. Implement automated KPI data pulls from social media APIs
6. Create first monthly investor update
7. Organize investor portal structure in SharePoint
8. Generate first marketing campaign using this system

### Medium-Term (Next 1-3 Months)
9. Fully automate KPI dashboard updates
10. Launch investor portal with proper access controls
11. Integrate Google Gemini for presentation generation
12. Build out NotebookLM research library

---

## Conclusion

This skill provides comprehensive asset management, investor portal architecture, and marketing automation capabilities for Trifecta. By centralizing all marketing materials in SharePoint, integrating research aggregation with NotebookLM, and tracking performance with a KPI dashboard, the system enables efficient campaign execution and transparent investor communication.

**Key Benefits:**
- Organized, searchable asset library
- Automated campaign workflows
- Data-driven decision making
- Professional investor communications
- Research-backed content creation

Use this skill in combination with other Trifecta skills for complete ecosystem management.
