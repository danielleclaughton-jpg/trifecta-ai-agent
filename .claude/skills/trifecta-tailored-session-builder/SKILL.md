# Trifecta Tailored Session Builder

## Overview
This skill enables Claude to automatically generate personalized session plans and interactive recovery toolkits for Trifecta clients based on post-session recaps. Using established patterns from Derek's and Max's toolkits, Claude creates HTML-based, interactive tools that integrate DBT skills, neuroplasticity principles, and CBT techniques tailored to each client's specific needs and session focus.

## When to Use This Skill
Use this skill when:
- Client completes a therapy session
- Post-session recap is available
- Danielle requests a tailored session plan
- Creating follow-up homework assignments
- Building interactive recovery toolkits
- Designing emergency response plans
- Generating decision-tree worksheets
- Preparing for high-risk situations (holidays, triggers, etc.)

## System Integration Flow

```
Client Session (Teams) → Post-Session Recap Generated
    ↓
Session Recap Analysis (Claude identifies themes, skills practiced, homework)
    ↓
Toolkit Generation (HTML with interactive DBT/CBT tools)
    ↓
Upload to Client Portal (SharePoint /Client_Records/[Name]/Sessions/[Date]/)
    ↓
Client Access & Engagement (interactive tools, emergency plans, skill practice)
```

## Toolkit Template Library

### Template 1: Recovery Toolkit (Derek V9 Pattern)

**Use Case**: General recovery support with comprehensive DBT skill coverage

**Structure**:
```html
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>[Client Name]'s Recovery Toolkit</title>
    <style>
        /* Trifecta brand colors and professional styling */
        :root {
            --primary-teal: #02B6BE;
            --dark-charcoal: #2E3033;
            --light-sky: #E8F7F8;
            --accent-blue: #325C7A;
        }
        /* Responsive card-based layout */
    </style>
</head>
<body>
    <header>
        <h1>[Client Name]'s Recovery Toolkit</h1>
        <p>Session Date: [Date] | Focus: [Session Theme]</p>
    </header>

    <section id="session-recap">
        <h2>Today's Session Highlights</h2>
        <div class="card">
            <h3>What We Covered</h3>
            <ul>
                <li>[Topic 1 from recap]</li>
                <li>[Topic 2 from recap]</li>
                <li>[Topic 3 from recap]</li>
            </ul>
        </div>
        <div class="card">
            <h3>Key Insights</h3>
            <p>[Personalized insight from session]</p>
        </div>
    </section>

    <section id="dbt-skills">
        <h2>Your DBT Skills Practice</h2>
        
        <!-- Skill 1: Customized to session -->
        <div class="skill-card">
            <h3>[Skill Name, e.g., "Radical Acceptance"]</h3>
            <p><strong>What it is:</strong> [Brief definition]</p>
            <p><strong>When to use it:</strong> [Client-specific scenario from session]</p>
            <div class="practice-exercise">
                <h4>Try This Now:</h4>
                <ol>
                    <li>[Step 1 tailored to client's situation]</li>
                    <li>[Step 2]</li>
                    <li>[Step 3]</li>
                </ol>
            </div>
        </div>

        <!-- Interactive Check-In -->
        <div class="interactive-checkin">
            <h4>Daily Emotional Check-In</h4>
            <form>
                <label>How am I feeling right now?</label>
                <select name="emotion">
                    <option>Calm</option>
                    <option>Anxious</option>
                    <option>Sad</option>
                    <option>Angry</option>
                    <option>Overwhelmed</option>
                </select>
                <label>Intensity (1-10):</label>
                <input type="range" min="1" max="10" name="intensity">
                <button type="button" onclick="logEmotion()">Log It</button>
            </form>
        </div>
    </section>

    <section id="neuroplasticity">
        <h2>Brain Training: Neuroplasticity Exercises</h2>
        <div class="card">
            <h3>The Science Behind Your Recovery</h3>
            <p>[Personalized explanation connecting session theme to neuroplasticity]</p>
            <p><strong>Your Brain's Reward System:</strong> [Dopamine balance explanation specific to client's pattern]</p>
        </div>
        
        <div class="daily-practice">
            <h3>Daily Neuroplasticity Workout</h3>
            <ul>
                <li>✅ Morning: [Specific practice, e.g., "5-minute mindful breathing"]</li>
                <li>✅ Afternoon: [Specific practice, e.g., "STOP skill when craving hits"]</li>
                <li>✅ Evening: [Specific practice, e.g., "Gratitude journal - 3 items"]</li>
            </ul>
        </div>
    </section>

    <section id="emergency-plan">
        <h2>🚨 Emergency Response Plan</h2>
        <div class="emergency-card">
            <h3>When Cravings Hit Hard</h3>
            <ol>
                <li><strong>PAUSE:</strong> [Client-specific grounding technique]</li>
                <li><strong>CALL:</strong> [Emergency contact from session]</li>
                <li><strong>USE SKILL:</strong> [Primary DBT skill for this client]</li>
                <li><strong>DISTRACT:</strong> [Personalized distraction list]</li>
            </ol>
            
            <div class="crisis-contacts">
                <h4>Crisis Resources</h4>
                <p>988 Suicide & Crisis Lifeline</p>
                <p>Danielle: +1 (403) 907-0996</p>
                <p>[Client's support person]: [Phone]</p>
            </div>
        </div>
    </section>

    <section id="homework">
        <h2>This Week's Homework</h2>
        <div class="homework-card">
            <h3>[Homework Assignment 1 Title]</h3>
            <p><strong>Task:</strong> [Detailed instructions from session recap]</p>
            <p><strong>Why it matters:</strong> [Connects to client's specific goal]</p>
            <p><strong>Due:</strong> Before next session on [Date]</p>
            <label><input type="checkbox"> Mark complete when done</label>
        </div>
    </section>

    <footer>
        <p>Trifecta Addiction & Mental Health Services</p>
        <p>Questions? Email info@trifectaaddictionservices.com</p>
    </footer>

    <script>
        // Interactive functionality
        function logEmotion() {
            const emotion = document.querySelector('[name="emotion"]').value;
            const intensity = document.querySelector('[name="intensity"]').value;
            alert(`Logged: ${emotion} at intensity ${intensity}/10. Great job checking in!`);
        }
    </script>
</body>
</html>
```

**Key Pattern Elements from Derek V9:**
- Card-based layout for each skill/concept
- Interactive check-ins and logging
- Emergency response section
- Neuroplasticity education
- Daily practice schedule
- Homework tracking

---

### Template 2: Boundaries Toolkit (Max Pattern)

**Use Case**: Interpersonal effectiveness, relationship skills, communication

**Structure**:
```html
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <title>[Client Name]'s Boundaries & Communication Toolkit</title>
    <style>
        /* Decision tree styling, accordion menus */
        .decision-tree {
            border-left: 3px solid var(--primary-teal);
            padding-left: 20px;
            margin: 20px 0;
        }
        .choice {
            cursor: pointer;
            padding: 10px;
            background: var(--light-sky);
            margin: 5px 0;
            border-radius: 8px;
        }
    </style>
</head>
<body>
    <header>
        <h1>[Client Name]'s Boundaries Toolkit</h1>
        <p>Session Focus: [e.g., "Setting boundaries with family"]</p>
    </header>

    <section id="wise-mind">
        <h2>🧠 Wise Mind Decision Tree</h2>
        <div class="decision-tree">
            <h3>When faced with: [Client's specific scenario from session]</h3>
            
            <div class="choice" onclick="showEmotion()">
                <strong>What does my EMOTION MIND say?</strong>
            </div>
            <div id="emotion-response" style="display:none;">
                <p>[Emotional response from session discussion]</p>
                <p>Example: "I feel guilty saying no to my mom."</p>
            </div>
            
            <div class="choice" onclick="showReason()">
                <strong>What does my REASON MIND say?</strong>
            </div>
            <div id="reason-response" style="display:none;">
                <p>[Logical response from session discussion]</p>
                <p>Example: "I need to protect my recovery time."</p>
            </div>
            
            <div class="choice" onclick="showWise()">
                <strong>What does my WISE MIND say?</strong>
            </div>
            <div id="wise-response" style="display:none;">
                <p>[Integrated Wise Mind response]</p>
                <p>Example: "I can love my mom AND set a boundary. I'll say: 'I can't this week, but let's plan for next weekend.'"</p>
            </div>
        </div>
    </section>

    <section id="dear-man">
        <h2>DEAR MAN Communication Script</h2>
        <div class="card">
            <h3>For: [Client's specific situation, e.g., "Asking partner for alone time"]</h3>
            
            <p><strong>D - Describe:</strong> [Client's situation]<br>
            "When you [specific behavior], I notice [observation]."</p>
            
            <p><strong>E - Express:</strong> [Client's feeling]<br>
            "I feel [emotion] because [reason]."</p>
            
            <p><strong>A - Assert:</strong> [Client's request]<br>
            "I need [specific request]."</p>
            
            <p><strong>R - Reinforce:</strong> [Positive outcome]<br>
            "This will help us [positive result]."</p>
            
            <p><strong>M - Mindful:</strong> Stay focused on your goal<br>
            "If they bring up [distraction], I'll say: 'I hear you, but right now I need [request].'"</p>
            
            <p><strong>A - Appear Confident:</strong> [Body language reminder]<br>
            Eye contact, calm tone, upright posture</p>
            
            <p><strong>N - Negotiate:</strong> [Compromise option]<br>
            "If [request] doesn't work, I'm willing to [alternative]."</p>
        </div>

        <div class="practice-script">
            <h4>Your Exact Script to Practice:</h4>
            <blockquote>
                [Full scripted conversation based on session work]
            </blockquote>
        </div>
    </section>

    <section id="fast">
        <h2>FAST: Self-Respect Effectiveness</h2>
        <div class="card">
            <h3>Keeping Your Integrity in: [Client's scenario]</h3>
            
            <p><strong>F - Fair:</strong> Be fair to yourself AND others<br>
            ✅ [What's fair for client]<br>
            ❌ [What's not fair - giving in too much]</p>
            
            <p><strong>A - Apologies (no excessive):</strong><br>
            ✅ Say: "[Appropriate acknowledgment]"<br>
            ❌ Don't say: "I'm so sorry for being a burden..."</p>
            
            <p><strong>S - Stick to values:</strong><br>
            Your value: [Client's core value from session]<br>
            Action: [How to honor that value]</p>
            
            <p><strong>T - Truthful:</strong><br>
            Tell the truth: [Client's honest statement]<br>
            Don't minimize: [What to avoid saying]</p>
        </div>
    </section>

    <section id="give">
        <h2>GIVE: Maintaining Relationships</h2>
        <div class="card">
            <h3>While Setting Your Boundary</h3>
            
            <p><strong>G - Gentle:</strong> [Gentle approach for client's situation]</p>
            <p><strong>I - Interested:</strong> [Show interest in other person]</p>
            <p><strong>V - Validate:</strong> [Acknowledge their feelings]</p>
            <p><strong>E - Easy Manner:</strong> [Smile, stay calm]</p>
        </div>
    </section>

    <section id="practice-scenarios">
        <h2>🎯 This Week's Practice Scenarios</h2>
        <div class="scenario-card">
            <h3>Scenario 1: [Client-specific upcoming situation]</h3>
            <p><strong>What might happen:</strong> [Prediction from session]</p>
            <p><strong>Your prepared response:</strong> [DEAR MAN script]</p>
            <p><strong>If they push back:</strong> [Backup plan]</p>
            <label><input type="checkbox"> Practice this script 3 times out loud</label>
        </div>
    </section>

    <footer>
        <p>Trifecta Addiction & Mental Health Services</p>
    </footer>

    <script>
        function showEmotion() {
            document.getElementById('emotion-response').style.display = 'block';
        }
        function showReason() {
            document.getElementById('reason-response').style.display = 'block';
        }
        function showWise() {
            document.getElementById('wise-response').style.display = 'block';
        }
    </script>
</body>
</html>
```

**Key Pattern Elements from Max Boundaries Toolkit:**
- Wise Mind decision tree with interactive reveals
- DEAR MAN scripted conversations
- FAST self-respect checklist
- GIVE relationship maintenance
- Practice scenarios with checkbox tracking

---

### Template 3: High-Risk Situation Planner (Max November 25 Pattern)

**Use Case**: Holiday planning, trigger situations, relapse prevention

**Structure**:
```html
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <title>[Client Name]'s [Situation] Survival Plan</title>
</head>
<body>
    <header>
        <h1>[Client Name]'s [Event/Holiday] Survival Plan</h1>
        <p>Prepared: [Date] | Event Date: [Upcoming Date]</p>
    </header>

    <section id="trigger-map">
        <h2>🎯 Your Trigger Map</h2>
        <div class="card">
            <h3>Known Triggers at [Event]</h3>
            <ul>
                <li>🔴 <strong>[Trigger 1 from session]:</strong> [How it shows up]</li>
                <li>🔴 <strong>[Trigger 2]:</strong> [How it shows up]</li>
                <li>🔴 <strong>[Trigger 3]:</strong> [How it shows up]</li>
            </ul>
        </div>
    </section>

    <section id="before-event">
        <h2>BEFORE the Event</h2>
        <div class="checklist">
            <h3>Preparation Checklist</h3>
            <label><input type="checkbox"> [Specific prep task 1, e.g., "Call support person"]</label>
            <label><input type="checkbox"> [Specific prep task 2, e.g., "Pack emergency kit"]</label>
            <label><input type="checkbox"> [Specific prep task 3, e.g., "Practice Wise Mind script"]</label>
        </div>

        <div class="card">
            <h3>Your Intention for This Event</h3>
            <p>[Client's stated intention from session]</p>
            <p><strong>Success looks like:</strong> [Measurable outcome]</p>
        </div>
    </section>

    <section id="during-event">
        <h2>DURING the Event</h2>
        
        <div class="if-then-plan">
            <h3>If-Then Plans</h3>
            
            <p><strong>IF</strong> [Trigger 1 happens]<br>
            <strong>THEN</strong> I will: [Specific coping action from session]</p>
            
            <p><strong>IF</strong> [Trigger 2 happens]<br>
            <strong>THEN</strong> I will: [Specific coping action]</p>
            
            <p><strong>IF</strong> I feel overwhelmed<br>
            <strong>THEN</strong> I will: [Exit strategy from session]</p>
        </div>

        <div class="emergency-card">
            <h3>🚨 Emergency Exit Plan</h3>
            <ol>
                <li><strong>Notice:</strong> [Warning signs for this client]</li>
                <li><strong>Excuse:</strong> [Pre-planned reason to leave]</li>
                <li><strong>Leave:</strong> [Specific exit action]</li>
                <li><strong>Call:</strong> [Support person + phone number]</li>
                <li><strong>Use Skill:</strong> [Primary DBT skill]</li>
            </ol>
        </div>
    </section>

    <section id="after-event">
        <h2>AFTER the Event</h2>
        <div class="card">
            <h3>Debrief Questions</h3>
            <ol>
                <li>Did I honor my intention? [Yes/No/Mostly]</li>
                <li>What went well? [Write it down]</li>
                <li>What was challenging? [Note it]</li>
                <li>What skill helped most? [Identify for next time]</li>
                <li>What would I do differently? [Learn and adjust]</li>
            </ol>
        </div>

        <div class="self-compassion">
            <h3>💙 Self-Compassion Reminder</h3>
            <p>[Personalized self-compassion message from Danielle]</p>
        </div>
    </section>

    <section id="support-network">
        <h2>📞 Your Support Team</h2>
        <div class="contacts">
            <p><strong>Primary Support:</strong> [Name] - [Phone]</p>
            <p><strong>Backup Support:</strong> [Name] - [Phone]</p>
            <p><strong>Danielle:</strong> +1 (403) 907-0996</p>
            <p><strong>Crisis Line:</strong> 988</p>
        </div>
    </section>

    <footer>
        <p>You've got this. You've prepared. You're not alone.</p>
        <p>Trifecta Addiction & Mental Health Services</p>
    </footer>
</body>
</html>
```

**Key Pattern Elements from Max November 25 Plan:**
- Trigger mapping specific to event
- Before/During/After structure
- If-Then contingency plans
- Emergency exit strategy
- Post-event debrief prompts
- Self-compassion messaging

---

## Session Recap to Toolkit Generation Process

### Step 1: Analyze Session Recap

**Extract Key Elements:**
1. **Session Theme**: What was the primary focus?
2. **DBT/CBT Skills Covered**: Which skills were discussed/practiced?
3. **Client's Specific Challenges**: What struggles did they share?
4. **Homework Assigned**: What tasks did Danielle assign?
5. **Upcoming Triggers**: Any identified high-risk situations?
6. **Support System**: Who are their emergency contacts?
7. **Wins/Strengths**: What progress was noted?

**Example Session Recap Input:**
```
Client: Derek
Date: January 10, 2026
Theme: Managing work stress and cravings during shift work

Skills Covered:
- Radical Acceptance (accepting can't change schedule)
- STOP skill (when craving hits on shift)
- Distress Tolerance (TIPP technique)

Client Challenges:
- 12-hour shifts trigger exhaustion and cravings
- Isolation during night shifts
- Difficulty reaching out for support

Homework:
- Practice STOP skill 3x when craving arises
- Daily emotional check-in at end of shift
- Call support person 2x this week

Upcoming Triggers:
- Night shift rotation starts Tuesday
- Alone time in truck during breaks

Support: 
- Wife Sarah: (403) XXX-XXXX
- Coworker Mike: (403) XXX-XXXX
```

### Step 2: Select Appropriate Template

**Decision Tree:**

```
Is session focused on relationships/boundaries?
    YES → Use Template 2 (Boundaries Toolkit)
    NO → Continue

Is there an upcoming high-risk event (holiday, trigger situation)?
    YES → Use Template 3 (High-Risk Planner)
    NO → Continue

General recovery support needed?
    YES → Use Template 1 (Recovery Toolkit)
```

**For Derek Example Above**: Template 1 (Recovery Toolkit) - focuses on daily coping, shift work triggers

### Step 3: Populate Template with Client-Specific Content

**Customization Rules:**

1. **Replace all [Client Name] placeholders** with actual name
2. **Insert Session Date and Theme** in header
3. **Populate "Today's Session Highlights"** with recap topics
4. **Select DBT Skills** that were covered in session
5. **Write client-specific scenarios** for skill practice
6. **Create personalized If-Then plans** based on identified triggers
7. **Include exact homework assignments** from recap
8. **Add emergency contacts** with real phone numbers
9. **Customize neuroplasticity explanation** to client's pattern
10. **Tailor closing/self-compassion message** from Danielle's voice

**Derek Example - Populated Recovery Toolkit Excerpt:**

```html
<section id="dbt-skills">
    <h2>Your DBT Skills Practice</h2>
    
    <div class="skill-card">
        <h3>STOP Skill (For Cravings On Shift)</h3>
        <p><strong>What it is:</strong> A quick intervention to pause and choose your response when a craving hits.</p>
        <p><strong>When to use it:</strong> During your 12-hour shift when you feel the urge to use, especially during truck breaks alone.</p>
        <div class="practice-exercise">
            <h4>Try This Now:</h4>
            <ol>
                <li><strong>S - Stop:</strong> Physically freeze. Put down your phone. Step out of the truck if safe.</li>
                <li><strong>T - Take a breath:</strong> Deep breath in for 4, hold for 4, out for 6. Repeat 3 times.</li>
                <li><strong>O - Observe:</strong> Notice: "This is a craving. It will peak in 15 minutes and pass. I don't have to act on it."</li>
                <li><strong>P - Proceed mindfully:</strong> Call Sarah or Mike. Eat a snack. Listen to your recovery playlist. Choose ONE action that moves you toward your goal.</li>
            </ol>
        </div>
    </div>

    <div class="skill-card">
        <h3>Radical Acceptance (For Shift Schedule)</h3>
        <p><strong>What it is:</strong> Accepting reality without approval or judgment.</p>
        <p><strong>When to use it:</strong> When you're frustrated about night shifts or feeling resentful about your schedule.</p>
        <div class="practice-exercise">
            <h4>Try This:</h4>
            <p>Say to yourself: "I don't like night shifts, AND I can't change them right now. Fighting reality causes me more suffering. I choose to accept this AND take care of myself within it."</p>
        </div>
    </div>
</section>

<section id="emergency-plan">
    <h2>🚨 Emergency Response Plan for Shift Work</h2>
    <div class="emergency-card">
        <h3>When Craving Hits During Your Shift</h3>
        <ol>
            <li><strong>PAUSE:</strong> Pull over if driving. Use STOP skill.</li>
            <li><strong>CALL:</strong> Sarah (403) XXX-XXXX or Mike (403) XXX-XXXX</li>
            <li><strong>USE SKILL:</strong> TIPP - splash cold water, intense pushups (20), paced breathing</li>
            <li><strong>DISTRACT:</strong> Recovery podcast, text Danielle, drive to Tim Hortons (not alone in truck)</li>
        </ol>
        
        <div class="crisis-contacts">
            <h4>Crisis Resources</h4>
            <p>988 Suicide & Crisis Lifeline</p>
            <p>Danielle: +1 (403) 907-0996</p>
            <p>Sarah: (403) XXX-XXXX</p>
            <p>Mike: (403) XXX-XXXX</p>
        </div>
    </div>
</section>

<section id="homework">
    <h2>This Week's Homework</h2>
    <div class="homework-card">
        <h3>Practice STOP Skill</h3>
        <p><strong>Task:</strong> Use the STOP skill at least 3 times this week when you notice a craving—whether strong or mild. Write down what happened each time.</p>
        <p><strong>Why it matters:</strong> Repetition rewires your brain's automatic response to cravings. Each time you practice, you're strengthening new neural pathways.</p>
        <p><strong>Due:</strong> Before next session on January 17, 2026</p>
        <label><input type="checkbox"> Completed 3 times</label>
    </div>

    <div class="homework-card">
        <h3>Daily Emotional Check-In</h3>
        <p><strong>Task:</strong> At the end of every shift, spend 2 minutes writing: How am I feeling? What went well? What was hard?</p>
        <p><strong>Why it matters:</strong> Self-awareness is the foundation of recovery. Tracking patterns helps you see what works.</p>
        <p><strong>Due:</strong> Before next session</p>
        <label><input type="checkbox"> Completed all 7 days</label>
    </div>
</section>
```

### Step 4: Generate HTML File

**File Naming Convention:**
```
[LastName]_[FirstName]_Session_[Date]_Toolkit.html

Examples:
- Winnicki_Derek_Session_2026-01-10_Toolkit.html
- Willigar_Max_Session_2026-01-15_Boundaries_Toolkit.html
```

**File Generation Process:**
1. Populate chosen template with all client-specific content
2. Validate HTML structure (no broken tags)
3. Test interactivity (buttons, checkboxes, decision trees)
4. Verify all placeholders replaced
5. Save as `.html` file

### Step 5: Upload to Client Portal

**SharePoint Path:**
```
/Client_Records/[LastName]_[FirstName]/Sessions/[Date]_Session_[Number]/
    ├── Session_Outline.pdf
    ├── Session_Report.pdf
    └── [Name]_Toolkit.html  ← Upload here
```

**Upload Process:**
1. Connect to SharePoint via Microsoft Graph API
2. Navigate to client's session folder
3. Upload HTML file
4. Set permissions (client access only)
5. Generate shareable link
6. Log upload in CRM

### Step 6: Notify Client

**Email Notification Template:**

```
Subject: Your Personalized Recovery Toolkit from Today's Session

Dear [Client Name],

Great work in today's session! I've created a personalized interactive toolkit based on what we covered.

Your toolkit includes:
• The DBT skills we practiced today ([Skill 1], [Skill 2])
• Step-by-step guides for [specific situation from session]
• Your emergency response plan
• This week's homework with tracking

Access your toolkit here: [SharePoint Link]

This is yours to use anytime—during cravings, tough moments, or just for daily practice.

See you next session on [Date]. You're doing great.

Warmly,

Danielle Claughton
Founding Director & CEO
Trifecta Addiction and Mental Health Services
```

## Advanced Features & Customizations

### Interactive Elements to Include

**1. Emotion Tracking with Charts**
```javascript
function logEmotion() {
    const emotion = document.querySelector('[name="emotion"]').value;
    const intensity = document.querySelector('[name="intensity"]').value;
    const timestamp = new Date().toLocaleString();
    
    // Store in localStorage
    let log = JSON.parse(localStorage.getItem('emotionLog') || '[]');
    log.push({ emotion, intensity, timestamp });
    localStorage.setItem('emotionLog', JSON.stringify(log));
    
    alert(`Logged: ${emotion} at ${intensity}/10 on ${timestamp}`);
    updateChart();
}
```

**2. Skill Practice Counter**
```javascript
function markSkillComplete(skillName) {
    let count = parseInt(localStorage.getItem(skillName) || '0');
    count++;
    localStorage.setItem(skillName, count);
    document.getElementById(`${skillName}-count`).textContent = count;
    
    if (count >= 3) {
        alert(`Great job! You've practiced ${skillName} ${count} times this week!`);
    }
}
```

**3. Decision Tree with Branching Paths**
```javascript
function showPath(choice) {
    // Hide all paths
    document.querySelectorAll('.decision-path').forEach(el => {
        el.style.display = 'none';
    });
    
    // Show selected path
    document.getElementById(`path-${choice}`).style.display = 'block';
}
```

## Integration with Existing Skills

### Trifecta Session Documentation
- Pulls from post-session recap generated by Claude AI analysis
- Uses same client folder structure in SharePoint
- Complements Session Report with interactive tools

### AI Agent Orchestration
- Automated toolkit generation triggered by session completion
- Client notification sent via email automation
- Progress tracking fed back into CRM

### Document Generator
- Uses same Trifecta branding and HTML styling
- Consistent file naming conventions
- SharePoint upload methods

## Quality Assurance Checklist

**Before Uploading Toolkit:**
- [ ] All [Client Name] placeholders replaced
- [ ] Session date and theme accurate
- [ ] DBT skills match what was covered in session
- [ ] Homework assignments match session recap
- [ ] Emergency contacts verified and current
- [ ] Interactive elements tested (buttons, checkboxes)
- [ ] HTML validates (no broken tags)
- [ ] Mobile-responsive design
- [ ] Trifecta branding consistent
- [ ] No PHI in file name or metadata

## Best Practices

### Content Personalization
- Always reference client's specific situation in examples
- Use their exact language/phrasing from session
- Include real names of support people (with permission)
- Tailor skill explanations to their unique challenges
- Make scenarios realistic to their daily life

### Skill Selection
- Match skills to session focus (don't add unrelated skills)
- Prioritize skills client struggled with or wants to improve
- Build on skills from previous sessions
- Introduce max 2-3 new skills per toolkit

### Homework Design
- Make homework specific and measurable
- Provide clear instructions (not vague "practice acceptance")
- Connect homework to client's stated goals
- Include completion checkboxes for accountability

### Emergency Planning
- Always include crisis resources
- Personalize emergency plan to client's triggers
- Provide step-by-step action plan (not general advice)
- Include actual phone numbers (verified and current)

## Conclusion

This skill enables Claude to transform post-session recaps into powerful, personalized recovery tools that extend therapy beyond the session room. By following established patterns from Derek's and Max's toolkits, Claude creates consistent, high-quality, interactive HTML tools that support clients' daily recovery practice.

**Key Success Metrics:**
- Toolkit generated within 2 hours of session completion
- 100% personalization (no generic placeholders)
- Client engagement with interactive elements
- Homework completion rate >80%
- Client satisfaction with toolkit usefulness

Use this skill in combination with Session Documentation skill for complete post-session workflow automation.
