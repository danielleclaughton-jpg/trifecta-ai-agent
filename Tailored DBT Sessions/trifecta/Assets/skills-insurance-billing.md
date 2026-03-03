# Trifecta Insurance Verification & Billing Skill

## Overview
This skill provides Claude with complete knowledge of Trifecta's insurance verification, billing, and claims submission processes. It includes verification protocols, common insurance payers, billing procedures, and collection workflows for addiction and mental health services.

## When to Use This Skill
Use this skill when:
- Verifying client insurance benefits
- Determining coverage for addiction treatment services
- Explaining out-of-network benefits to clients
- Processing claims submission
- Handling insurance denials and appeals
- Collecting client responsibility portions
- Creating Superbills for HSA/FSA reimbursement
- Explaining deductible, copay, and coinsurance concepts

## Insurance Verification Process

### Step 1: Gather Client Information
Before calling insurance, collect:
- Client full name (as it appears on insurance card)
- Date of birth
- Insurance company name
- Member ID number
- Group number (if applicable)
- Policy holder name and relationship (if not self)
- Type of plan (PPO, HMO, EPO, POS)

### Step 2: Verify Benefits
Contact insurance company or use electronic verification (Availity, Change Healthcare):

**Key Questions to Ask:**
1. "What are the benefits for outpatient mental health/addiction treatment?"
2. "Is prior authorization required for treatment?"
3. "What is the deductible amount and how much has been met?"
4. "What is the copay per session?"
5. "What is the coinsurance percentage after deductible?"
6. "What is the out-of-pocket maximum?"
7. "How many sessions are covered per calendar year?"
8. "Is telehealth covered?"
9. "What diagnosis codes are covered for addiction treatment?"
10. "Are there any exclusions or limitations?"

### Step 3: Document Verification
Record all information in client file:
```
Insurance Verification Date: [Date]
Verified By: [Staff Name]
Insurance Representative: [Name/ID]
Reference Number: [Call Reference #]
Benefits Confirmed:
- Outpatient MH/SA Treatment: [Yes/No]
- Prior Auth Required: [Yes/No]
- Deductible: $[X] (Remaining: $[Y])
- Copay: $[X] per session
- Coinsurance: [X]%
- Out-of-Pocket Max: $[X] (Remaining: $[Y])
- Sessions Covered: [X] per [year/month]
- Telehealth: [Covered/Not Covered]
- Effective Date: [Date]
```

## Common Insurance Payers

### Major Commercial Payers
| Payer | Phone | Website | Notes |
|-------|-------|---------|-------|
| Blue Cross Blue Shield | 1-800-262-2583 | bcbs.com | Often best benefits |
| Aetna | 1-800-872-3862 | aetna.com | May require precertification |
| Cigna | 1-800-244-6224 | cigna.com | Out-of-network friendly |
| UnitedHealthcare | 1-800-328-5979 | uhc.com | Large provider network |
| Humana | 1-800-448-6262 | humana.com | Check network status |
| Kaiser Permanente | 1-800-464-4000 | kp.org | HMO - limited access |
| Oscar Health | 1-800-300-5448 | hioscar.com | Growing payer |
| Medicare | 1-800-MEDICARE | medicare.gov | For 65+ or disabled |
| Medicaid | State-specific | State website | Income-based |

### Behavioral Health Specific
| Payer | Phone | Notes |
|-------|-------|-------|
| Beacon Health Options | 1-800-249-0028 | Behavioral health carve-out |
| Magellan Healthcare | 1-800-424-2589 | Behavioral health specialist |
| ComPsych | 1-800-272-2827 | EAP and behavioral health |

## Insurance Terminology

### Key Terms Every Staff Should Know

**Deductible:**
The amount clients must pay out-of-pocket before insurance begins paying. Example: $1,500 deductible means client pays first $1,500, then insurance kicks in.

**Copay:**
A fixed amount client pays per visit (e.g., $30 copay per session). Usually applies after deductible is met.

**Coinsurance:**
A percentage client pays after deductible is met. Example: 20% coinsurance means client pays 20% of allowed amount, insurance pays 80%.

**Out-of-Pocket Maximum (OOPM):**
The most client will pay in a calendar year including deductible, copays, and coinsurance. After reaching this, insurance pays 100%.

**Allowed Amount:**
The maximum amount insurance will pay for a service. Also called "Usual and Customary Rate" (UCR) or "Negotiated Rate."

**Explanation of Benefits (EOB):**
Document from insurance showing how claim was processed, what was paid, and client responsibility.

**Prior Authorization (Precertification):**
Approval required from insurance before treatment begins. Common for inpatient, PHP, and intensive outpatient.

**Medical Necessity:**
Insurance requirement that treatment must be clinically appropriate and essential.

## Billing Codes

### CPT Codes for Mental Health Services

| Code | Description | Typical Rate Range |
|------|-------------|-------------------|
| 90791 | Psychiatric diagnostic evaluation (no medical) | $150-$250 |
| 90792 | Psychiatric diagnostic evaluation (with medical) | $175-$300 |
| 90832 | Psychotherapy, 30 minutes | $75-$125 |
| 90834 | Psychotherapy, 45 minutes | $100-$175 |
| 90837 | Psychotherapy, 60 minutes | $125-$225 |
| 90846 | Family psychotherapy (without patient) | $100-$175 |
| 90847 | Family psychotherapy (with patient) | $110-$200 |
| 90853 | Group psychotherapy | $50-$100 per person |
| 90862 | Medication management | $75-$150 |
| 96127 | Brief emotional/behavioral assessment | $15-$40 |

### Add-On Codes
| Code | Description |
|------|-------------|
| 90839 | Psychotherapy for crisis (first 60 min) |
| 90840 | Psychotherapy for crisis (each additional 30 min) |
| 99354 | Prolonged service (first hour) |
| 99355 | Prolonged service (each additional 30 min) |

### HCPCS Codes for Special Services
| Code | Description |
|------|-------------|
| G0449 | Alcohol and/or drug use assessment |
| G0451 | Alcohol and/or drug use treatment planning |
| G0506 | Comprehensive assessment, treatment planning |
| H0001 | Alcohol and/or drug assessment |
| H0004 | Alcohol and/or drug treatment planning |
| H0015 | Alcohol and/or drug intensive outpatient |
| H2010 | Comprehensive medication services |

### ICD-10 Diagnosis Codes (Addiction)

**F10 Series - Alcohol Use Disorders**
| Code | Description |
|------|-------------|
| F10.20 | Alcohol use disorder, uncomplicated |
| F10.21 | Alcohol use disorder, in remission |
| F10.220 | Alcohol use disorder with intoxication, uncomplicated |
| F10.921 | Alcohol use disorder, unspecified, in remission |

**F11 Series - Opioid Use Disorders**
| Code | Description |
|------|-------------|
| F11.20 | Opioid use disorder, uncomplicated |
| F11.21 | Opioid use disorder, in remission |
| F11.220 | Opioid use disorder with intoxication |

**F12 Series - Cannabis Use Disorders**
| Code | Description |
|------|-------------|
| F12.20 | Cannabis use disorder, uncomplicated |
| F12.21 | Cannabis use disorder, in remission |

**F13 Series - Sedative/Hypnotic Use Disorders**
| Code | Description |
|------|-------------|
| F13.20 | Sedative use disorder, uncomplicated |
| F13.21 | Sedative use disorder, in remission |

**F14 Series - Cocaine Use Disorders**
| Code | Description |
|------|-------------|
| F14.20 | Cocaine use disorder, uncomplicated |
| F14.21 | Cocaine use disorder, in remission |

**F15 Series - Other Stimulant Use Disorders**
| Code | Description |
|------|-------------|
| F15.20 | Other stimulant use disorder, uncomplicated |
| F15.21 | Other stimulant use disorder, in remission |

**F16 Series - Hallucinogen Use Disorders**
| Code | Description |
|------|-------------|
| F16.20 | Hallucinogen use disorder, uncomplicated |

**F18 Series - Inhalant Use Disorders**
| Code | Description |
|------|-------------|
| F18.20 | Inhalant use disorder, uncomplicated |

**F19 Series - Multiple Substance Use Disorders**
| Code | Description |
|------|-------------|
| F19.20 | Other psychoactive substance use disorder, uncomplicated |
| F19.21 | Other psychoactive substance use disorder, in remission |

### ICD-10 Diagnosis Codes (Mental Health)

**F32-F33 - Depression**
| Code | Description |
|------|-------------|
| F32.0 | Major depressive disorder, single episode, mild |
| F32.1 | Major depressive disorder, single episode, moderate |
| F32.2 | Major depressive disorder, single episode, severe |
| F32.9 | Major depressive disorder, single episode, unspecified |
| F33.0 | Major depressive disorder, recurrent, mild |
| F33.1 | Major depressive disorder, recurrent, moderate |
| F33.2 | Major depressive disorder, recurrent, severe |

**F40-F48 - Anxiety and Stressor-Related**
| Code | Description |
|------|-------------|
| F40.10 | Social anxiety disorder |
| F41.0 | Panic disorder |
| F41.1 | Generalized anxiety disorder |
| F42.0 | Obsessive-compulsive disorder |
| F43.10 | Post-traumatic stress disorder, unspecified |
| F43.12 | Post-traumatic stress disorder, acute |
| F43.20 | Adjustment disorder, unspecified |
| F43.21 | Adjustment disorder with depressed mood |
| F43.25 | Adjustment disorder with mixed anxiety |

**F60-F69 - Personality Disorders**
| Code | Description |
|------|-------------|
| F60.9 | Personality disorder, unspecified |
| F60.3 | Borderline personality disorder |

## Superbill Creation

### Superbill Template for Clients
```
TRIFECTA ADDICTION AND MENTAL HEALTH SERVICES
Superbill for Insurance Claims

Patient Name: ____________________
Date of Birth: ____________________
Member ID: ____________________

Date of Service | CPT Code | Diagnosis Code | Description | Amount
----------------|----------|----------------|-------------|--------
                |          |                |             |
                |          |                |             |
                |          |                |             |
                |          |                |             |

Total: $____________________

Provider: Trifecta Addiction and Mental Health Services
NPI: [Your NPI Number]
Tax ID: [Your Tax ID]
License: [License Number - State]

Submit this superbill to your insurance company for reimbursement.
```

## Collections Workflow

### Step 1: Generate Statement
Send itemized statement showing:
- Date of service
- Service description
- Charge amount
- Insurance payment (if any)
- Adjustments
- Client responsibility

### Step 2: Payment Plan Options
For clients unable to pay in full:
- 3-month payment plan (no interest)
- 6-month payment plan (no interest)
- Sliding scale based on income (document)
- Financial hardship application

### Step 3: Collections Sequence
| Day | Action |
|-----|--------|
| Day 0 | Service rendered |
| Day 1-7 | Insurance claim submitted |
| Day 30 | First statement to client (after EOB) |
| Day 45 | First reminder call/email |
| Day 60 | Second reminder (more urgent) |
| Day 75 | Final notice before collections |
| Day 90 | Send to collections (if policy) |

## Out-of-Network Benefits

### Explaining OON Benefits to Clients
"When your insurance says we're 'out-of-network,' it means we don't have a contracted rate with them. However, most PPO plans still provide coverage:

1. You pay the full session fee at the time of service
2. We provide a superbill with diagnosis and treatment codes
3. You submit the superbill to your insurance
4. Insurance reimburses you directly based on their 'usual and customary rate'
5. Typical reimbursement: 50-80% of the session fee"

### Calculating Estimated Client Cost
```
Session Fee: $175
Insurance Allows: $140
Reimbursement Rate: 60%
Expected Reimbursement: $84
Your Net Cost: $91

OR using copay method:
Copay: $40 per session
Your Cost: $40 (regardless of session fee)
```

## Common Insurance Denials and Appeals

### Denial Codes
| Code | Meaning | Action |
|------|---------|--------|
| CO-4 | Contracted provider disallowed | Verify network status |
| CO-11 | Diagnosis not covered | Submit medical necessity |
| CO-18 | Duplicate claim | Resubmit with corrected info |
| CO-22 | Care provider denied | Verify NPI/Tax ID |
| CO-29 | Time limit expired | Appeal with documentation |
| CO-31 | Patient not eligible | Verify coverage date |
| CO-50 | Not medically necessary | Submit clinical notes |
| CO-97 | Payment included in allowance | Accept as final |

### Appeal Process
1. Review denial letter carefully
2. Gather clinical documentation
3. Write letter of medical necessity
4. Include relevant research/guidelines
5. Submit within 60-day deadline
6. Follow up on status weekly
7. Escalate to supervisor if denied again

### Sample Appeal Letter
```
[Insurance Company Name]
Appeals Department
[Address]

RE: Appeal of Denial for [Patient Name]
DOB: [Date]
Member ID: [ID]
Claim Date: [Date]
Claim Amount: $[Amount]

Dear Appeals Team,

I am writing to appeal the denial of coverage for mental health services
rendered to the above-named patient.

[Patient] has been diagnosed with [Diagnosis] and has been receiving
psychotherapy treatment at Trifecta Addiction and Mental Health Services.

The treatment is medically necessary because:
1. [Clinical reason #1]
2. [Clinical reason #2]
3. [Clinical reason #3]

Enclosed please find:
- Updated treatment plan
- Clinical notes supporting medical necessity
- Relevant practice guidelines

We respectfully request that you reconsider this denial and provide
coverage for the requested treatment.

Thank you for your time and consideration.

Sincerely,
[Provider Name, Credentials]
NPI: [Number]
License: [License Number]
```

## Client Communication Templates

### Initial Benefits Explanation
```
Hi [Client Name],

Thank you for providing your insurance information. I've completed a
benefits verification with your insurance company, [Insurance Name].

Here's what we found:

INSURANCE SUMMARY:
- Deductible: $[X] (You have met $[Y] so far)
- Copay per session: $[X]
- Coinsurance: [X]%
- Out-of-Pocket Maximum: $[X] (You have $[Y] remaining)
- Sessions covered: Unlimited per calendar year

YOUR RESPONSIBILITY:
For each session, you would pay: $[X] (copay)

Please note: This is an estimate based on information provided by your
insurance. Actual amounts may vary based on final claim processing.

Let me know if you have any questions about your coverage!

Warmly,
[Staff Name]
Trifecta Addiction and Mental Health Services
```

### Preauthorization Request
```
Dear [Insurance Name] Utilization Review,

I am writing to request prior authorization for ongoing psychotherapy
services for [Patient Name], DOB: [DOB], Member ID: [ID].

DIAGNOSIS:
- Primary: [ICD-10 Code] - [Description]
- Secondary: [ICD-10 Code] - [Description]

TREATMENT PLAN:
[Patient] is participating in individual psychotherapy [X] times per
week for [X] minutes per session. Treatment focuses on:

1. [Goal #1]
2. [Goal #2]
3. [Goal #3]

CLINICAL INDICATION:
[Patient] presents with [symptoms] which significantly impair
functioning in [areas]. Evidence-based treatment is clinically
indicated to address [presenting concerns].

REQUEST:
I am requesting authorization for [number] sessions of individual
psychotherapy (CPT codes: 90834/90837) for a period of [time period].

Please contact me if you require additional information.

Sincerely,
[Provider Name, Credentials]
NPI: [Number]
Phone: [Number]
Fax: [Number]
```

## Financial Assistance Programs

### Sliding Scale Application
```
TRIFECTA ADDICTION AND MENTAL HEALTH SERVICES
Financial Assistance Application

PATIENT INFORMATION:
Name: ____________________ DOB: ____________________
Address: _______________________________________________
Phone: ____________________ Email: ____________________

HOUSEHOLD INFORMATION:
Number of dependents: _____
Annual household income: $____________________
Source of income: _______________________________________________

REQUESTED REDUCTION:
I am requesting a [X]% reduction in fees based on financial hardship.

CERTIFICATION:
I certify that the information provided is accurate. I understand that
falsifying information may result in termination of services.

Patient Signature: ____________________ Date: ____________________

FOR OFFICE USE:
Approved: [ ] Yes [ ] No
Reduction: [ ] 25% [ ] 50% [ ] 75% [ ] 100%
Staff Reviewer: ____________________ Date: ____________________
```

## Key Contacts

### Insurance Verification Contacts
| Payer | Phone | Hours |
|-------|-------|-------|
| BCBS National | 800-262-2583 | 24/7 |
| Aetna | 800-872-3862 | 7am-7pm CT |
| Cigna | 800-244-6224 | 24/7 |
| UnitedHealthcare | 800-328-5979 | 8am-6pm CT |
| Humana | 800-448-6262 | 7am-7pm CT |

### Internal Contacts
| Role | Name | Extension |
|------|------|-----------|
| Billing Manager | [Name] | [Ext] |
| Insurance Verification | [Name] | [Ext] |
| Collections | [Name] | [Ext] |

## Compliance Notes

- Always verify current benefits before each new authorization period
- Document all insurance conversations with date, time, and representative name
- Maintain confidentiality of all insurance and financial information
- Follow up on pending authorizations within 48-72 hours
- File claims within 5 business days of service
- Keep copies of all submitted claims and correspondence
- Review EOBs within 24 hours of receipt
- Address discrepancies within 30 days
