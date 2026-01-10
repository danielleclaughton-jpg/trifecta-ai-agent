# Trifecta Session Documentation & Teams Integration

## Overview
This skill enables Claude to automatically process Microsoft Teams meeting recordings, generate session documentation (pre-session outlines and post-session reports), and store all materials in the appropriate client folders. The system integrates with Microsoft Teams, Microsoft Graph API, Azure Blob Storage, and the Trifecta client portal.

## When to Use This Skill
Use this skill when:
- Scheduling client sessions in Microsoft Teams
- Generating pre-session outlines before appointments
- Processing completed Teams meeting recordings
- Creating post-session clinical reports
- Organizing session documentation in client folders
- Preparing materials for client portal upload
- Tracking session completion and homework assignments

## System Architecture

### Integration Points

```
Microsoft Teams Recording
    ↓
Azure Media Services (transcription)
    ↓
Claude AI Processing (summary, analysis, report generation)
    ↓
Document Generator (PDF creation)
    ↓
Storage Layer (Azure Blob Storage + SharePoint)
    ↓
Client Portal (session materials available to client)
    ↓
CRM Update (session logged, next session scheduled)
```

### Technology Stack

**Microsoft Teams API**
- Meeting scheduling
- Recording access
- Participant information
- Meeting metadata

**Microsoft Graph API**
- Calendar integration
- User authentication
- File storage (OneDrive/SharePoint)
- Notification system

**Azure Media Services**
- Audio/video transcription
- Speaker identification
- Timestamp extraction

**Azure Blob Storage**
- Raw recording storage
- Transcription file storage
- Generated document storage
- Archived session materials

**Client Portal API (Google AI Studio)**
- Session outline delivery
- Session report publishing
- Client access management
- Progress tracking

## Storage Structure

### Azure Blob Storage Organization

```
trifecta-session-recordings/
├── raw-recordings/
│   ├── 2025/
│   │   ├── January/
│   │   │   ├── Willigar_Max_2025-01-15_Session.mp4
│   │   │   └── Claughton_Derek_2025-01-16_Session.mp4
│   │   └── February/
│   └── 2026/
├── transcriptions/
│   ├── 2025/
│   │   ├── January/
│   │   │   ├── Willigar_Max_2025-01-15_Transcript.json
│   │   │   └── Claughton_Derek_2025-01-16_Transcript.json
│   │   └── February/
│   └── 2026/
├── session-outlines/
│   ├── 2025/
│   │   ├── January/
│   │   │   ├── Willigar_Max_2025-01-15_Outline.pdf
│   │   │   └── Claughton_Derek_2025-01-16_Outline.pdf
│   │   └── February/
│   └── 2026/
└── session-reports/
    ├── 2025/
    │   ├── January/
    │   │   ├── Willigar_Max_2025-01-15_Report.pdf
    │   │   └── Claughton_Derek_2025-01-16_Report.pdf
    │   └── February/
    └── 2026/
```

### SharePoint Client Portal Organization

```
/sites/ClientPortal/
├── Client_Records/
│   ├── Willigar_Max/
│   │   ├── Sessions/
│   │   │   ├── 2025-01-15_Session_01/
│   │   │   │   ├── Session_Outline.pdf
│   │   │   │   ├── Session_Report.pdf
│   │   │   │   └── Homework_Assignment.pdf
│   │   │   ├── 2025-01-16_Session_02/
│   │   │   └── 2025-01-17_Session_03/
│   │   ├── Treatment_Plan/
│   │   ├── Progress_Reports/
│   │   └── Completed_Homework/
│   └── Winnicki_Derek/
│       └── Sessions/
└── Templates/
    ├── Session_Outline_Template.pdf
    └── Session_Report_Template.pdf
```

### File Naming Conventions

**Format:** `[LastName]_[FirstName]_[Date]_[Type].[extension]`

**Examples:**
- Raw Recording: `Willigar_Max_2025-01-15_Session.mp4`
- Transcription: `Willigar_Max_2025-01-15_Transcript.json`
- Session Outline: `Willigar_Max_2025-01-15_Outline.pdf`
- Session Report: `Willigar_Max_2025-01-15_Report.pdf`

**Date Format:** `YYYY-MM-DD` (ISO 8601)

## Pre-Session Workflow

### 1. Session Scheduling (24 Hours Before)

When a session is scheduled in Microsoft Teams:

```python
def schedule_session(
    client_name: str,
    session_datetime: datetime,
    session_number: int,
    program_type: str,
    previous_session_notes: str = None
):
    """
    Schedule session and trigger pre-session outline generation
    
    Args:
        client_name: Full client name (e.g., "Max Willigar")
        session_datetime: Date and time of session
        session_number: Sequential session number
        program_type: "28_day_virtual" | "14_day_inpatient" | "outpatient"
        previous_session_notes: Notes from previous session for continuity
    
    Returns:
        dict: Session details and outline generation status
    """
    
    # Step 1: Create Teams meeting
    meeting = create_teams_meeting(
        subject=f"{client_name} - Session {session_number}",
        start_time=session_datetime,
        duration_minutes=60,
        attendees=[client_email],
        enable_recording=True
    )
    
    # Step 2: Generate pre-session outline
    outline = generate_session_outline(
        client_name=client_name,
        session_number=session_number,
        program_type=program_type,
        previous_notes=previous_session_notes
    )
    
    # Step 3: Upload outline to client portal
    upload_to_client_portal(
        client_name=client_name,
        file_content=outline,
        file_type="session_outline",
        session_date=session_datetime.date()
    )
    
    # Step 4: Send notification to client
    send_session_notification(
        client_email=client_email,
        session_datetime=session_datetime,
        teams_link=meeting["join_url"],
        outline_link=outline["portal_url"]
    )
    
    return {
        "meeting_id": meeting["id"],
        "outline_url": outline["portal_url"],
        "status": "scheduled"
    }
```

### 2. Pre-Session Outline Generation

**Template Structure:**

```markdown
# Session Outline - Session [NUMBER]

**Client:** [Client Name]
**Date:** [Session Date]
**Session Number:** [Number] of [Total Sessions]
**Program:** [Program Type]

---

## Today's Session Focus

### Primary Objectives
1. [Objective 1 - based on program phase]
2. [Objective 2 - based on previous session progress]
3. [Objective 3 - addressing current client needs]

### Topics to Cover
- **[Topic 1]**: [Brief description]
- **[Topic 2]**: [Brief description]
- **[Topic 3]**: [Brief description]

---

## CBT/DBT Skills Practice

### Skill of the Day: [Skill Name]
**Definition:** [Brief explanation of the skill]

**Why This Skill Matters:**
[1-2 sentences on relevance to client's recovery]

**Practice Exercise:**
[Specific exercise we'll do during session]

---

## Review from Last Session

### Homework Review
- [Homework item 1 from previous session]
- [Homework item 2 from previous session]

### Progress Check-In
- Mental wellness (mood, anxiety)
- Physical health
- Spiritual practices
- Social connections

---

## Today's Homework Assignment

### Task 1: [Homework Title]
**Instructions:** [Detailed instructions]
**Time Required:** [Estimated time]
**Due:** Before next session

### Task 2: [Homework Title]
**Instructions:** [Detailed instructions]
**Time Required:** [Estimated time]
**Due:** Before next session

---

## Resources for This Session

### Reading Materials
- [Resource 1 - article/chapter]
- [Resource 2 - worksheet]

### YouTube Playlist
- [Video 1 - psychoeducation topic]
- [Video 2 - skill demonstration]

---

## Preparing for This Session

### What to Bring
- Completed homework from last session
- Your recovery journal
- Any questions or concerns that came up this week

### What to Expect
This session will be approximately 60 minutes and will include:
- Check-in and progress review (10 min)
- Skills training and practice (30 min)
- Homework review and assignment (10 min)
- Questions and next steps (10 min)

---

**Remember:** This outline is a guide. We'll adjust based on what you need most today.

---

*Trifecta Addiction & Mental Health Services*
*Elite, evidence-based recovery, empowering one life at a time*
```

**Generation Logic:**

```python
def generate_session_outline(
    client_name: str,
    session_number: int,
    program_type: str,
    previous_notes: str = None
):
    """
    Generate personalized session outline based on program phase
    
    Uses:
    - Client's current program phase (Days 1-14, 15-21, 22-28)
    - Previous session notes and progress
    - Assigned DBT/CBT skill rotation
    - Client's specific treatment goals
    """
    
    # Determine session focus based on program phase
    if program_type == "28_day_virtual":
        if session_number <= 14:
            phase = "intensive_foundation"
            focus_areas = [
                "Building therapeutic alliance",
                "Crisis management skills",
                "Daily structure and routine"
            ]
            skills = ["Radical Acceptance", "Wise Mind", "STOP Skill"]
        elif session_number <= 21:
            phase = "skills_integration"
            focus_areas = [
                "Practicing core skills",
                "Identifying triggers",
                "Building coping strategies"
            ]
            skills = ["Emotion Regulation", "Distress Tolerance", "DEAR MAN"]
        else:
            phase = "relapse_prevention"
            focus_areas = [
                "Long-term planning",
                "Relapse prevention",
                "Building support network"
            ]
            skills = ["Relapse Prevention Plan", "HALT", "Continuing Care"]
    
    # Select today's CBT/DBT skill (rotate through curriculum)
    todays_skill = get_skill_for_session(session_number, program_type)
    
    # Extract previous session homework (if available)
    previous_homework = extract_homework_from_notes(previous_notes)
    
    # Generate outline using template
    outline = populate_outline_template(
        client_name=client_name,
        session_number=session_number,
        total_sessions=get_total_sessions(program_type),
        program_type=format_program_name(program_type),
        phase=phase,
        focus_areas=focus_areas,
        todays_skill=todays_skill,
        previous_homework=previous_homework
    )
    
    # Convert to PDF
    pdf_content = markdown_to_pdf(outline)
    
    # Generate filename
    date_str = datetime.now().strftime("%Y-%m-%d")
    last_name = client_name.split()[-1]
    first_name = client_name.split()[0]
    filename = f"{last_name}_{first_name}_{date_str}_Outline.pdf"
    
    return {
        "content": pdf_content,
        "filename": filename,
        "phase": phase
    }
```

## Post-Session Workflow

### 1. Recording Retrieval (Automatic)

After Teams meeting ends:

```python
def retrieve_recording(meeting_id: str):
    """
    Retrieve recording from Microsoft Teams
    
    Args:
        meeting_id: Teams meeting identifier
    
    Returns:
        dict: Recording metadata and download URL
    """
    
    # Wait for recording to be processed (usually 5-10 minutes)
    wait_for_recording_processing(meeting_id)
    
    # Get recording details from Microsoft Graph API
    recording_url = f"https://graph.microsoft.com/v1.0/users/{user_id}/onlineMeetings/{meeting_id}/recordings"
    
    response = requests.get(recording_url, headers=auth_headers)
    recording_data = response.json()
    
    # Download recording to Azure Blob Storage
    recording_blob_path = download_to_blob_storage(
        download_url=recording_data["contentUrl"],
        storage_path=f"raw-recordings/{year}/{month}/"
    )
    
    return {
        "recording_id": recording_data["id"],
        "blob_path": recording_blob_path,
        "duration_seconds": recording_data["duration"],
        "participants": recording_data["participants"]
    }
```

### 2. Transcription Processing

```python
def transcribe_recording(recording_blob_path: str):
    """
    Transcribe recording using Azure Media Services
    
    Args:
        recording_blob_path: Path to recording in Azure Blob Storage
    
    Returns:
        dict: Transcription data with timestamps and speaker identification
    """
    
    # Submit transcription job to Azure Media Services
    transcription_job = azure_media_services.create_transcription(
        input_blob=recording_blob_path,
        language="en-US",
        enable_speaker_diarization=True,
        enable_sentiment_analysis=True
    )
    
    # Wait for transcription to complete
    wait_for_job_completion(transcription_job.id)
    
    # Retrieve transcription results
    transcription = transcription_job.get_results()
    
    # Parse transcription into structured format
    parsed_transcript = {
        "full_text": transcription.text,
        "segments": [],
        "speakers": {
            "clinician": [],
            "client": []
        },
        "key_moments": []
    }
    
    for segment in transcription.segments:
        parsed_transcript["segments"].append({
            "start_time": segment.start,
            "end_time": segment.end,
            "speaker": segment.speaker,
            "text": segment.text,
            "confidence": segment.confidence
        })
        
        # Categorize by speaker
        if segment.speaker == "Speaker 1":  # Clinician
            parsed_transcript["speakers"]["clinician"].append(segment.text)
        else:  # Client
            parsed_transcript["speakers"]["client"].append(segment.text)
    
    # Identify key moments (homework mentions, skill practice, crisis moments)
    parsed_transcript["key_moments"] = identify_key_moments(transcription.text)
    
    # Save transcription to blob storage
    transcript_filename = recording_blob_path.replace(".mp4", "_Transcript.json")
    save_to_blob_storage(parsed_transcript, transcript_filename)
    
    return parsed_transcript
```

### 3. Session Report Generation

**Template Structure:**

```markdown
# Clinical Session Report - Session [NUMBER]

**Client:** [Client Name]
**Date:** [Session Date]
**Session Number:** [Number] of [Total Sessions]
**Duration:** [Duration in minutes]
**Clinician:** Danielle Claughton, CACCF

---

## Session Summary

### Session Focus
[2-3 sentences summarizing the main focus of the session]

### Topics Covered
- [Topic 1]
- [Topic 2]
- [Topic 3]

### Client Engagement
**Engagement Level:** [High / Moderate / Low]
**Participation:** [Active / Responsive / Reluctant]
**Mood/Affect:** [Description of client's presentation]

---

## Progress Notes

### Wins & Strengths Observed
- [Win/strength 1]
- [Win/strength 2]
- [Win/strength 3]

### Challenges Discussed
- [Challenge 1 and how addressed]
- [Challenge 2 and how addressed]

### Skills Practiced
**Skill:** [CBT/DBT skill name]
**Practice Exercise:** [What we did]
**Client Understanding:** [Assessment of client's grasp of skill]
**Areas for Continued Practice:** [What needs more work]

### Clinical Observations
[Clinical notes on client's progress, patterns, concerns, or areas requiring attention]

---

## Homework Assigned

### Task 1: [Homework Title]
**Instructions:** [Detailed instructions]
**Purpose:** [Why this homework supports recovery]
**Due:** Before next session ([Date])

### Task 2: [Homework Title]
**Instructions:** [Detailed instructions]
**Purpose:** [Why this homework supports recovery]
**Due:** Before next session ([Date])

---

## Next Session Goals

### Primary Objectives for Session [Next Session Number]
1. [Objective 1]
2. [Objective 2]
3. [Objective 3]

### Topics to Address
- [Topic 1]
- [Topic 2]

### Skills to Practice
- [Skill 1]
- [Skill 2]

---

## Risk Assessment

### Current Risk Level: [Low / Moderate / High]

**Substance Use Risk:** [Assessment]
**Suicide/Self-Harm Risk:** [Assessment]
**Crisis Indicators:** [None / Describe if present]

**Action Taken (if applicable):** [Crisis intervention steps if needed]

---

## Treatment Plan Updates

### Progress Toward Treatment Goals
- **Goal 1:** [Progress description]
- **Goal 2:** [Progress description]
- **Goal 3:** [Progress description]

### Treatment Plan Adjustments (if any)
[Note any modifications to treatment approach or goals]

---

## Next Session Information

**Scheduled Date:** [Next session date and time]
**Session Focus:** [Brief preview]
**Preparation:** [What client should do to prepare]

---

**Clinician Notes:** [Any additional observations, consultation notes, or reminders]

---

*This report is confidential and protected under HIPAA regulations.*

*Trifecta Addiction & Mental Health Services*
*Danielle Claughton, CACCF - Founding Director & CEO*
```

**Generation Logic:**

```python
def generate_session_report(
    client_name: str,
    session_date: datetime,
    session_number: int,
    transcription: dict,
    pre_session_outline: dict
):
    """
    Generate comprehensive session report from transcription
    
    Uses Claude AI to analyze transcription and extract:
    - Session summary
    - Progress notes
    - Homework completion
    - New homework assignments
    - Next session goals
    - Risk assessment
    """
    
    # Prepare context for Claude AI analysis
    analysis_prompt = f"""
    You are a clinical documentation assistant for Danielle Claughton, CACCF, 
    at Trifecta Addiction & Mental Health Services.
    
    Analyze this therapy session transcription and generate a comprehensive 
    clinical session report.
    
    CLIENT: {client_name}
    SESSION DATE: {session_date.strftime("%B %d, %Y")}
    SESSION NUMBER: {session_number}
    PROGRAM: {get_program_type(client_name)}
    
    TRANSCRIPTION:
    {transcription["full_text"]}
    
    PRE-SESSION OUTLINE (for context):
    {pre_session_outline["content"]}
    
    Generate a session report that includes:
    
    1. SESSION SUMMARY (2-3 sentences)
       - Main focus of the session
       - Topics covered
       - Client engagement level
    
    2. PROGRESS NOTES
       - Wins & strengths observed (3 specific examples)
       - Challenges discussed and how addressed
       - Skills practiced and client's understanding
       - Clinical observations (patterns, concerns, areas requiring attention)
    
    3. HOMEWORK ASSIGNED
       - Specific tasks with detailed instructions
       - Purpose of each homework item
    
    4. NEXT SESSION GOALS
       - Primary objectives for next session
       - Topics to address
       - Skills to practice
    
    5. RISK ASSESSMENT
       - Current risk level (Low/Moderate/High)
       - Substance use risk
       - Suicide/self-harm risk
       - Crisis indicators (if any)
    
    Use the session report template format. Be specific, clinical, and evidence-based.
    Focus on observable behaviors and client statements.
    """
    
    # Call Claude AI for analysis
    claude_response = anthropic_client.messages.create(
        model="claude-sonnet-4-20250514",
        max_tokens=4000,
        messages=[{
            "role": "user",
            "content": analysis_prompt
        }]
    )
    
    session_report_markdown = claude_response.content[0].text
    
    # Convert to PDF
    pdf_content = markdown_to_pdf(session_report_markdown)
    
    # Generate filename
    date_str = session_date.strftime("%Y-%m-%d")
    last_name = client_name.split()[-1]
    first_name = client_name.split()[0]
    filename = f"{last_name}_{first_name}_{date_str}_Report.pdf"
    
    return {
        "content": pdf_content,
        "markdown": session_report_markdown,
        "filename": filename
    }
```

### 4. Document Upload to Client Portal

```python
def upload_to_client_portal(
    client_name: str,
    session_date: date,
    session_outline: dict = None,
    session_report: dict = None
):
    """
    Upload session documents to client portal
    
    Args:
        client_name: Full client name
        session_date: Date of session
        session_outline: Pre-session outline (optional)
        session_report: Post-session report (optional)
    
    Returns:
        dict: Upload results with portal URLs
    """
    
    # Determine client folder path
    last_name = client_name.split()[-1]
    first_name = client_name.split()[0]
    client_folder = f"{last_name}_{first_name}"
    
    # Create session subfolder
    session_folder = session_date.strftime("%Y-%m-%d") + f"_Session_{get_session_number(client_name, session_date)}"
    
    folder_path = f"Client_Records/{client_folder}/Sessions/{session_folder}"
    
    # Create folder structure in SharePoint
    create_sharepoint_folder(folder_path)
    
    results = {}
    
    # Upload session outline (if provided)
    if session_outline:
        outline_result = upload_to_sharepoint(
            file_content=session_outline["content"],
            filename="Session_Outline.pdf",
            folder_path=folder_path
        )
        results["outline_url"] = outline_result["web_url"]
    
    # Upload session report (if provided)
    if session_report:
        report_result = upload_to_sharepoint(
            file_content=session_report["content"],
            filename="Session_Report.pdf",
            folder_path=folder_path
        )
        results["report_url"] = report_result["web_url"]
    
    # Notify client via client portal API
    notify_client_portal(
        client_name=client_name,
        session_date=session_date,
        documents_available=results
    )
    
    return results
```

### 5. CRM Update & Next Session Scheduling

```python
def update_crm_post_session(
    client_name: str,
    session_date: datetime,
    session_report: dict,
    next_session_date: datetime = None
):
    """
    Update CRM with session completion and schedule next session
    
    Args:
        client_name: Full client name
        session_date: Date of completed session
        session_report: Generated session report
        next_session_date: Optional next session datetime
    """
    
    # Extract key data from session report
    homework_assigned = extract_homework(session_report["markdown"])
    risk_level = extract_risk_level(session_report["markdown"])
    progress_summary = extract_progress_summary(session_report["markdown"])
    
    # Update CRM
    crm_update = {
        "client_name": client_name,
        "session_date": session_date.isoformat(),
        "session_completed": True,
        "homework_assigned": homework_assigned,
        "risk_level": risk_level,
        "progress_summary": progress_summary,
        "report_url": session_report.get("sharepoint_url")
    }
    
    update_crm_record(client_name, crm_update)
    
    # Schedule next session (if provided)
    if next_session_date:
        schedule_next_session(
            client_name=client_name,
            session_datetime=next_session_date,
            session_number=get_session_number(client_name) + 1
        )
    
    # Set homework reminder (2 days before next session)
    if next_session_date:
        reminder_date = next_session_date - timedelta(days=2)
        schedule_homework_reminder(
            client_name=client_name,
            reminder_date=reminder_date,
            homework=homework_assigned
        )
```

## Complete Workflow Orchestration

### End-to-End Session Lifecycle

```python
async def handle_session_lifecycle(
    client_name: str,
    session_datetime: datetime,
    session_number: int,
    program_type: str
):
    """
    Orchestrate complete session lifecycle from scheduling to documentation
    
    PHASE 1: PRE-SESSION (24 hours before)
    - Generate session outline
    - Upload to client portal
    - Send client notification with Teams link
    
    PHASE 2: DURING SESSION
    - Record Teams meeting automatically
    
    PHASE 3: POST-SESSION (within 2 hours)
    - Retrieve recording from Teams
    - Transcribe audio
    - Generate session report using Claude AI
    - Upload report to client portal
    - Update CRM
    - Schedule next session
    """
    
    # PHASE 1: PRE-SESSION (triggered 24 hours before)
    if datetime.now() >= session_datetime - timedelta(hours=24):
        
        # Generate outline
        outline = generate_session_outline(
            client_name=client_name,
            session_number=session_number,
            program_type=program_type
        )
        
        # Create Teams meeting
        meeting = create_teams_meeting(
            subject=f"{client_name} - Session {session_number}",
            start_time=session_datetime,
            duration_minutes=60,
            enable_recording=True
        )
        
        # Upload outline to portal
        upload_to_client_portal(
            client_name=client_name,
            session_date=session_datetime.date(),
            session_outline=outline
        )
        
        # Notify client
        send_session_notification(
            client_name=client_name,
            session_datetime=session_datetime,
            teams_link=meeting["join_url"]
        )
    
    # PHASE 2: DURING SESSION
    # (Recording happens automatically via Teams)
    
    # PHASE 3: POST-SESSION (triggered when meeting ends)
    meeting_ended = await wait_for_meeting_end(meeting["id"])
    
    if meeting_ended:
        
        # Wait for recording to be processed
        await asyncio.sleep(600)  # Wait 10 minutes
        
        # Retrieve recording
        recording = retrieve_recording(meeting["id"])
        
        # Transcribe
        transcription = transcribe_recording(recording["blob_path"])
        
        # Generate report
        report = generate_session_report(
            client_name=client_name,
            session_date=session_datetime,
            session_number=session_number,
            transcription=transcription,
            pre_session_outline=outline
        )
        
        # Upload report to portal
        upload_to_client_portal(
            client_name=client_name,
            session_date=session_datetime.date(),
            session_report=report
        )
        
        # Update CRM
        update_crm_post_session(
            client_name=client_name,
            session_date=session_datetime,
            session_report=report
        )
        
        # Log completion
        log_session_completion(
            client_name=client_name,
            session_number=session_number,
            session_date=session_datetime
        )
```

## CBT/DBT Skills Curriculum

### 28-Day Virtual Boot Camp Skills Rotation

**Week 1 (Days 1-7): Crisis Management & Foundation**
- Day 1: Program orientation, Radical Acceptance
- Day 2: Wise Mind (emotion + reason balance)
- Day 3: STOP Skill (crisis intervention)
- Day 4: TIPP Skill (temperature, intense exercise, paced breathing, paired muscle relaxation)
- Day 5: Self-Soothe with 5 Senses
- Day 6: IMPROVE the Moment
- Day 7: Week 1 review and integration

**Week 2 (Days 8-14): Emotion Regulation**
- Day 8: Identifying and labeling emotions
- Day 9: Opposite Action
- Day 10: Check the Facts
- Day 11: Problem Solving
- Day 12: ABC PLEASE (vulnerability factors)
- Day 13: Building Positive Experiences
- Day 14: Week 2 review and integration

**Week 3 (Days 15-21): Interpersonal Effectiveness**
- Day 15: DEAR MAN (asking for what you need)
- Day 16: GIVE (maintaining relationships)
- Day 17: FAST (self-respect effectiveness)
- Day 18: Validation skills
- Day 19: Managing conflict
- Day 20: Setting boundaries
- Day 21: Week 3 review and integration

**Week 4 (Days 22-28): Relapse Prevention & Long-Term Planning**
- Day 22: Identifying triggers and warning signs
- Day 23: HALT (hungry, angry, lonely, tired)
- Day 24: Building a support network
- Day 25: Continuing care planning
- Day 26: Relapse prevention plan creation
- Day 27: Emergency response plan
- Day 28: Program completion and next steps

### Skills Reference Library

```python
SKILLS_LIBRARY = {
    "radical_acceptance": {
        "name": "Radical Acceptance",
        "category": "Distress Tolerance",
        "definition": "Accepting reality as it is, without approval or judgment",
        "when_to_use": "When fighting reality causes suffering",
        "practice": "Notice one fact about current situation without judgment",
        "resources": ["radical_acceptance_worksheet.pdf", "acceptance_video.mp4"]
    },
    "wise_mind": {
        "name": "Wise Mind",
        "category": "Mindfulness",
        "definition": "Integration of emotional mind and reasonable mind",
        "when_to_use": "When making decisions or solving problems",
        "practice": "Ask: What does my emotion say? What does my reason say? What feels wise?",
        "resources": ["wise_mind_worksheet.pdf", "wise_mind_meditation.mp3"]
    },
    # ... [additional skills]
}
```

## Client Portal API Integration

### Google AI Studio Integration

```python
def sync_with_client_portal(
    client_name: str,
    document_type: str,
    document_url: str,
    session_date: date
):
    """
    Sync documents with Google AI Studio-powered client portal
    
    Args:
        client_name: Full client name
        document_type: "outline" | "report" | "homework"
        document_url: SharePoint URL to document
        session_date: Date of session
    """
    
    # Client portal API endpoint (built with Google AI Studio)
    portal_api_url = "https://[your-client-portal-api].azurewebsites.net/api/documents"
    
    payload = {
        "client_name": client_name,
        "document_type": document_type,
        "document_url": document_url,
        "session_date": session_date.isoformat(),
        "uploaded_at": datetime.now().isoformat()
    }
    
    response = requests.post(
        portal_api_url,
        headers={
            "Authorization": f"Bearer {portal_api_key}",
            "Content-Type": "application/json"
        },
        json=payload
    )
    
    if response.status_code == 200:
        return {
            "success": True,
            "portal_document_id": response.json()["document_id"]
        }
    else:
        return {
            "success": False,
            "error": response.text
        }
```

## Monitoring & Quality Assurance

### Session Documentation Quality Checks

```python
def validate_session_documentation(
    session_report: dict,
    transcription: dict
):
    """
    Quality check for session documentation
    
    Validates:
    - Report completeness (all sections present)
    - Risk assessment included
    - Homework assigned
    - Next session goals defined
    - Clinical observations documented
    """
    
    required_sections = [
        "Session Summary",
        "Progress Notes",
        "Homework Assigned",
        "Next Session Goals",
        "Risk Assessment"
    ]
    
    missing_sections = []
    
    for section in required_sections:
        if section not in session_report["markdown"]:
            missing_sections.append(section)
    
    # Check for risk assessment specifics
    if "Risk Level:" not in session_report["markdown"]:
        missing_sections.append("Risk Level Assessment")
    
    # Check transcription quality
    if transcription["confidence_score"] < 0.85:
        warnings.append("Low transcription confidence - manual review recommended")
    
    return {
        "complete": len(missing_sections) == 0,
        "missing_sections": missing_sections,
        "warnings": warnings
    }
```

## Error Handling & Fallback Procedures

### Transcription Failure Handling

```python
def handle_transcription_failure(
    recording_blob_path: str,
    meeting_id: str
):
    """
    Fallback procedure if automatic transcription fails
    
    Actions:
    1. Notify Danielle of transcription failure
    2. Provide direct link to recording
    3. Create placeholder session report
    4. Set reminder for manual documentation
    """
    
    # Send alert to Danielle
    send_alert(
        recipient="danielle@trifectaaddictionservices.com",
        subject="Session Transcription Failed - Manual Review Needed",
        body=f"""
        Automatic transcription failed for meeting {meeting_id}.
        
        Recording available at: {recording_blob_path}
        
        Please manually create session report or retry transcription.
        
        Client will receive session outline but report is pending.
        """
    )
    
    # Create placeholder report
    placeholder_report = generate_placeholder_report(
        message="Session report pending - recording under review"
    )
    
    # Set reminder for manual follow-up
    create_task(
        assigned_to="Danielle",
        task="Complete session report manually",
        due_date=datetime.now() + timedelta(hours=24),
        priority="high"
    )
```

## Best Practices & Usage Guidelines

### 1. Pre-Session Preparation

**Best Practices:**
- Generate outlines 24 hours in advance
- Review previous session notes before generating outline
- Customize outline based on client's current needs
- Include relevant resources and reading materials
- Set up Teams meeting with recording enabled

### 2. During Session

**Best Practices:**
- Confirm recording has started
- Reference session outline during session
- Take brief notes on key moments
- Practice skills interactively
- Assign homework verbally and in writing

### 3. Post-Session Documentation

**Best Practices:**
- Review transcription for accuracy before generating report
- Use Claude AI for analysis but review clinically
- Document risk assessment accurately
- Be specific with homework instructions
- Upload all materials within 2 hours of session completion

### 4. Client Portal Management

**Best Practices:**
- Ensure all materials uploaded before client notification
- Test download links before sending to client
- Organize folders by session date
- Archive completed session materials monthly
- Maintain 7-year retention per HIPAA

## Integration with Existing Skills

### Trifecta Practice Management System
- Uses client data from CRM
- Follows treatment protocols
- Aligns with program structures

### AI Agent Orchestration
- Automated workflow triggers
- Escalation protocols for high-risk sessions
- Staff notification system

### Document Generator
- Uses same branding and templates
- Consistent file naming conventions
- SharePoint integration methods

## Security & Compliance

### HIPAA Compliance

**Recording Storage:**
- Encrypted at rest in Azure Blob Storage
- Access restricted to authorized personnel
- Audit logs for all access
- Automatic deletion after 7 years

**Transcription Data:**
- No PHI in file names
- Encrypted during processing
- Deleted after report generation (unless retention required)
- Not shared with third parties

**Client Portal Access:**
- Multi-factor authentication
- Client-specific access only
- Session timeout (15 minutes inactive)
- Download tracking and audit logs

### Access Control

**Who Can Access:**
- Danielle: Full access to all recordings and reports
- Staff: Limited access to assigned clients only
- Clients: Access to own session materials only
- Auditors: Read-only access with approval

## Conclusion

This skill provides comprehensive automation for clinical session documentation, from pre-session preparation through post-session reporting. By integrating Microsoft Teams recording, Azure transcription services, Claude AI analysis, and the client portal, the system ensures:

- Consistent, high-quality session documentation
- Reduced administrative burden on clinicians
- Improved client engagement through accessible materials
- HIPAA-compliant data management
- Seamless integration with existing Trifecta systems

Use this skill in combination with other Trifecta skills for complete practice management automation.
