# Trifecta Document Generator & SharePoint Integration

## Overview
This skill provides Claude with the ability to generate professional contracts and invoices for Trifecta Addiction and Mental Health Services, then automatically store them in SharePoint. This skill handles template selection, data population, document generation, and SharePoint file management.

## When to Use This Skill
Use this skill when:
- Generating client contracts (14-Day Inpatient, 28-Day Inpatient, 28-Day Virtual Boot Camp)
- Creating invoices for clients (program fees, aftercare sessions, individual sessions)
- Storing generated documents in SharePoint
- Retrieving documents from SharePoint for client access
- Updating existing documents with new information
- Creating custom payment schedules or installment plans

## SharePoint Configuration

### SharePoint Site Information
- **Site URL**: https://netorgft5726606.sharepoint.com/sites/Intakeandcontracts
- **List ID**: 4eed6790-f702-47b2-a363-59637f0d1663
- **Site Name**: Intake and Contracts
- **Primary Use**: Document storage for client contracts and invoices

### SharePoint Document Library Structure

```
/sites/Intakeandcontracts/
├── Contracts/
│   ├── 2025/
│   │   ├── January/
│   │   ├── February/
│   │   └── [Month]/
│   ├── 2026/
│   └── Templates/
│       ├── 14_Day_Inpatient_Template.html
│       ├── 28_Day_Inpatient_Template.html
│       └── 28_Day_Virtual_Template.html
├── Invoices/
│   ├── 2025/
│   │   ├── January/
│   │   ├── February/
│   │   └── [Month]/
│   ├── 2026/
│   └── Paid/
│       └── [Year]/[Month]/
└── Client_Records/
    └── [Client_ID]/
        ├── Contract/
        ├── Invoices/
        └── Documentation/
```

### File Naming Conventions

**Contracts:**
```
[ClientLastName]_[ClientFirstName]_[ProgramType]_Contract_[Date].html
Example: Willigar_Max_28Day_Virtual_Contract_2025-09-20.html
```

**Invoices:**
```
[ClientLastName]_[ClientFirstName]_Invoice_[InvoiceNumber]_[Date].html
Example: Willigar_Max_Invoice_1413_2025-11-08.html
```

**Receipts:**
```
[ClientLastName]_[ClientFirstName]_Receipt_Invoice_[InvoiceNumber]_[Status].html
Example: Willigar_Max_Receipt_Invoice_1337_PaidInFull_FINAL.html
```

## Document Templates

### Contract Templates

#### 1. 14-Day Private Inpatient Boot Camp Contract

**Program Details:**
- Duration: 14 consecutive days
- Total Fee: $13,777 CAD
- Deposit: $3,777 CAD (non-refundable)
- Balance: $10,000 CAD (due on intake day)

**Template Structure:**
```html
<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="utf-8" />
  <title>14-Day Inpatient Contract - [Client Name]</title>
  [CSS STYLING - Trifecta brand colors and professional layout]
</head>
<body>
  <div class="brandbar"></div>
  <div class="wrap">
    <!-- LOGOS -->
    <div class="masthead">
      <img src="[Trifecta Logo]" />
      <img src="[Illuminate Logo]" />
    </div>
    
    <!-- TITLE -->
    <h1>14-Day Private Inpatient Boot Camp Program Agreement</h1>
    
    <!-- CLIENT INFO -->
    <div class="client-info">
      <div>Client Name: [CLIENT_NAME]</div>
      <div>Program Start Date: [START_DATE]</div>
      <div>Total Program Fee: $13,777 CAD</div>
    </div>
    
    <!-- SECTIONS -->
    <div class="section">
      <h2>1) Program Description</h2>
      <p>Private accommodations, 24/7 care, CBT/DBT therapy, wellness activities, meals, personalized relapse prevention plan, lifetime guarantee.</p>
      <div class="initial-line">Please initial: _______</div>
    </div>
    
    <div class="section">
      <h2>2) Payment Terms</h2>
      <p>Deposit: $3,777 (non-refundable)</p>
      <p>Balance: $10,000 due on intake day</p>
      <div class="initial-line">Please initial: _______</div>
    </div>
    
    <div class="section">
      <h2>3) No Cancellation & No Refund Policy</h2>
      <p>Non-refundable program. Cancellation fee: 25% or $2,500 minimum.</p>
      <div class="initial-line">Please initial: _______</div>
    </div>
    
    <div class="section">
      <h2>4) Client Commitment & Facility Policies</h2>
      <p>Full participation, follow rules, abstain from substances, remain on-site.</p>
      <p>One-strike expulsion policy.</p>
      <div class="initial-line">Please initial: _______</div>
    </div>
    
    <div class="section">
      <h2>5) Aftercare & Relapse Prevention</h2>
      <p>12 months aftercare included. One-time free 2-week relapse prevention session.</p>
      <div class="initial-line">Please initial: _______</div>
    </div>
    
    <div class="section">
      <h2>6) Lifetime Guarantee</h2>
      <p>One-time return for relapse prevention session at any point in life.</p>
      <div class="initial-line">Please initial: _______</div>
    </div>
    
    <div class="section">
      <h2>7) Inclusions & Exclusions</h2>
      <p>Includes: Private accommodations, 24/7 care, all meals, therapy, aftercare</p>
      <p>Excludes: Medications, travel, personal expenses</p>
      <div class="initial-line">Please initial: _______</div>
    </div>
    
    <div class="section">
      <h2>8) Insurance & Billing</h2>
      <p>Client responsible for insurance reimbursement. Private pay facility.</p>
      <div class="initial-line">Please initial: _______</div>
    </div>
    
    <!-- SIGNATURES -->
    <div class="signatures">
      <div class="sig-block">
        <div>Client Name: [CLIENT_NAME]</div>
        <div class="sig-line">Signature: _______________________</div>
        <div class="sig-line">Date: _______________________</div>
      </div>
      <div class="sig-block">
        <div>Trifecta Representative: Danielle Claughton</div>
        <div class="sig-line">Signature: _______________________</div>
        <div class="sig-line">Date: _______________________</div>
      </div>
    </div>
    
    <!-- FOOTER -->
    <div class="footer">
      Trifecta Addiction & Mental Health Services • Illuminate AMHS<br/>
      Calgary, AB • info@trifectaaddictionservices.com • 403-907-0996<br/>
      www.trifectaaddictionservices.com
    </div>
  </div>
</body>
</html>
```

**Variables to Replace:**
- `[CLIENT_NAME]` → Full client name
- `[START_DATE]` → Program start date (format: "Monday, January 15, 2026")
- `[Trifecta Logo]` → Base64 encoded logo or URL
- `[Illuminate Logo]` → Base64 encoded logo or URL

---

#### 2. 28-Day Private Inpatient Boot Camp Contract

**Program Details:**
- Duration: 28 consecutive days
- Total Fee: $23,777 CAD
- Deposit: $3,777 CAD (non-refundable)
- Balance: $20,000 CAD (due on intake day)

**Template Structure:** [Same structure as 14-Day, with pricing adjustments]

**Variables to Replace:**
- `[CLIENT_NAME]`
- `[START_DATE]`
- Total fee: $23,777 CAD
- Balance: $20,000 CAD

---

#### 3. 28-Day Virtual Intensive Boot Camp Contract

**Program Details:**
- Duration: 28 consecutive days (daily 1:1 sessions)
- Total Fee: $3,777 CAD
- Payment Options:
  - Full payment: $3,777 CAD (on/before start)
  - Two installments: $1,888.50 × 2 (Day 1 & Day 2)

**Template Structure:**
```html
<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="utf-8" />
  <title>28-Day Virtual Program Agreement - [Client Name]</title>
  [CSS STYLING]
</head>
<body>
  <div class="brandbar"></div>
  <div class="wrap">
    <!-- LOGOS -->
    <div class="masthead">
      <div class="brand-lockup">
        <img src="[Trifecta Logo]" />
        <div class="divider"></div>
        <img src="[Illuminate Logo]" />
      </div>
    </div>
    
    <!-- TITLE -->
    <h1>Individual Treatment Agreement</h1>
    <p class="sub">Elite, evidence-based recovery—empowering one life at a time.</p>
    
    <!-- CLIENT INFO GRID -->
    <div class="grid two">
      <div class="kv">
        <div class="k">Client Name</div>
        <div class="v">[CLIENT_NAME]</div>
      </div>
      <div class="kv">
        <div class="k">Program Start Date</div>
        <div class="v">[START_DATE]</div>
      </div>
      <div class="kv">
        <div class="k">Program</div>
        <div class="v">28-Day Virtual Individual Program (CBT • DBT • Neuroplasticity)</div>
      </div>
      <div class="kv">
        <div class="k">Total Program Fee</div>
        <div class="v">$3,777 CAD</div>
      </div>
    </div>
    
    <!-- PROGRAM DESCRIPTION -->
    <div class="card">
      <h2>1) Program Description</h2>
      <div class="phase">
        <strong>Phase One – Days 1–14 (Consecutive)</strong>
        <ul>
          <li>Daily 60-minute 1:1 virtual sessions (recommended: [PREFERRED_TIME]).</li>
          <li>Customized program materials delivered in stages.</li>
          <li>Weekly couple session (if applicable).</li>
        </ul>
      </div>
      <div class="phase">
        <strong>Phase Two – Week After First 14 Days</strong>
        <ul>
          <li>Five (5) 60-minute 1:1 sessions throughout the week.</li>
        </ul>
      </div>
      <div class="phase">
        <strong>Phase Three – Final Week</strong>
        <ul>
          <li>Five (5) 60-minute 1:1 sessions throughout the week.</li>
        </ul>
      </div>
      <h3>Program Includes</h3>
      <ul>
        <li>Customized rehabilitation plan</li>
        <li>CBT/DBT skills, neuroplasticity tools</li>
        <li>Couple/family involvement (when appropriate)</li>
        <li>Personalized YouTube playlist (psychoeducation)</li>
      </ul>
      <div class="initial">Please initial: _______</div>
    </div>
    
    <!-- PAYMENT TERMS -->
    <div class="card">
      <h2>2) Payment Terms</h2>
      <table>
        <thead>
          <tr><th>Payment Option</th><th>Amount</th><th>Due</th></tr>
        </thead>
        <tbody>
          <tr><td>Full Payment</td><td>$3,777 CAD</td><td>Before or on program start</td></tr>
          <tr><td>First Installment</td><td>$1,888.50 CAD</td><td>Before or on program start</td></tr>
          <tr><td>Second Installment</td><td>$1,888.50 CAD</td><td>By Day 2 of program</td></tr>
        </tbody>
      </table>
      <p class="note">E-transfer: info@trifectaaddictionservices.com. No cancellations or refunds.</p>
      <div class="initial">Please initial: _______</div>
    </div>
    
    <!-- SESSION POLICIES -->
    <div class="card">
      <h2>3) Session Policies</h2>
      <ul>
        <li>Sessions scheduled in advance—arrive on time.</li>
        <li>24-hour notice required for cancellations.</li>
        <li>Missed sessions without notice: not rescheduled/refunded.</li>
        <li>Secure, confidential virtual platform.</li>
      </ul>
      <div class="initial">Please initial: _______</div>
    </div>
    
    <!-- NO CANCELLATION -->
    <div class="card">
      <h2>4) No Cancellation Policy</h2>
      <p>Once enrolled, fully committed. <strong>No refunds or cancellations</strong> after payment.</p>
      <div class="initial">Please initial: _______</div>
    </div>
    
    <!-- CLIENT COMMITMENT -->
    <div class="card">
      <h2>5) Client Commitment & Liability Waiver</h2>
      <ul>
        <li>Active participation in all sessions and assignments.</li>
        <li>Follow program policies and safety guidelines.</li>
        <li>Provider not responsible for unforeseen circumstances.</li>
      </ul>
      <div class="initial">Please initial: _______</div>
    </div>
    
    <!-- CONFIDENTIALITY -->
    <div class="card">
      <h2>6) Confidentiality & Privacy</h2>
      <ul>
        <li>All information confidential per laws and ethical standards.</li>
        <li>Client respects confidentiality of couple/family sessions.</li>
      </ul>
      <div class="initial">Please initial: _______</div>
    </div>
    
    <!-- AFTERCARE -->
    <div class="card">
      <h2>7) Aftercare</h2>
      <p>12 months aftercare support included: virtual check-ins and ongoing resources.</p>
      <div class="initial">Please initial: _______</div>
    </div>
    
    <!-- SIGNATURES -->
    <div class="card">
      <h2>Agreement Signatures</h2>
      <div class="sig-row">
        <div class="sig">
          <div><strong>Client:</strong> [CLIENT_NAME]</div>
          <div class="line"></div>
          <div class="muted">Signature</div>
          <div class="line"></div>
          <div class="muted">Date</div>
        </div>
        <div class="sig">
          <div><strong>Clinician:</strong> Danielle Claughton</div>
          <div class="line"></div>
          <div class="muted">Signature</div>
          <div class="line"></div>
          <div class="muted">Date</div>
        </div>
      </div>
    </div>
    
    <!-- FOOTER -->
    <div class="footer">
      Trifecta Addiction & Mental Health Services • Illuminate AMHS<br/>
      Calgary, AB • info@trifectaaddictionservices.com • 403-907-0996<br/>
      www.trifectaaddictionservices.com
    </div>
  </div>
</body>
</html>
```

**Variables to Replace:**
- `[CLIENT_NAME]` → Full client name
- `[START_DATE]` → Program start date (format: "Saturday, September 20")
- `[PREFERRED_TIME]` → Client's preferred session time (e.g., "7:00 PM")

---

### Invoice Templates

#### 1. Program Fee Invoice (Full Payment)

**Use Cases:**
- Initial program enrollment
- Full payment upfront
- Deposit invoice

**Template Structure:**
```html
<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="utf-8" />
  <title>Invoice #[INVOICE_NUMBER] - [Client Name]</title>
  [CSS STYLING]
</head>
<body>
  <div class="brandbar"></div>
  <div class="wrap">
    <!-- HEADER -->
    <div class="masthead">
      <div class="lockup">
        <img src="[Trifecta Logo]" />
        <div class="title">
          <h1>Invoice</h1>
          <div class="sub">Invoice #[INVOICE_NUMBER] • [CLIENT_NAME] • [PROGRAM_TYPE] • Method: [PAYMENT_METHOD]</div>
        </div>
      </div>
      <img src="[Illuminate Logo]" />
    </div>
    
    <!-- KEY DETAILS -->
    <div class="card grid two">
      <div class="kv">
        <div class="k">Bill To</div>
        <div class="v">[CLIENT_NAME]</div>
      </div>
      <div class="kv">
        <div class="k">Issued By</div>
        <div class="v">Trifecta Recovery Services / Illuminate AMHS</div>
      </div>
      <div class="kv">
        <div class="k">Program / Service</div>
        <div class="v">[PROGRAM_TYPE]</div>
      </div>
      <div class="kv">
        <div class="k">Program Dates</div>
        <div class="v">[START_DATE] to [END_DATE]</div>
      </div>
      <div class="kv">
        <div class="k">Status</div>
        <div class="v">[STATUS]</div>
      </div>
      <div class="kv">
        <div class="k">Currency</div>
        <div class="v">CAD</div>
      </div>
    </div>
    
    <!-- LINE ITEMS -->
    <div class="card">
      <table>
        <thead>
          <tr><th>Description</th><th>Rate</th><th>Amount (CAD)</th></tr>
        </thead>
        <tbody>
          <tr>
            <td>
              <strong>[PROGRAM_NAME]</strong><br/>
              Duration: [DURATION]<br/>
              Includes: [INCLUSIONS]
            </td>
            <td>$[PROGRAM_FEE]</td>
            <td>$[PROGRAM_FEE]</td>
          </tr>
        </tbody>
      </table>
      <div class="total">
        <div class="label">Total Due (GST Exempt)</div>
        <div class="amount">$[TOTAL_AMOUNT]</div>
      </div>
    </div>
    
    <!-- PAYMENT NOTE -->
    <div class="card note">
      This invoice reflects the full program fee for <strong>[CLIENT_NAME]</strong>'s enrollment in the <strong>[PROGRAM_NAME]</strong>.
      <br/><br/>
      <strong>Payment Instructions:</strong><br/>
      E-transfer to: <strong>info@trifectaaddictionservices.com</strong><br/>
      E-Transfer Password: <strong>Trifecta 2025</strong><br/>
      Payment due: <strong>[DUE_DATE]</strong>
      <br/><br/>
      Services are <strong>GST exempt</strong> per Canadian tax regulations.
    </div>
    
    <!-- FOOTER -->
    <div class="footer">
      <strong>Danielle Claughton</strong>, Founding Director & CEO<br/>
      Trifecta Recovery Services | Illuminate AMHS<br/>
      info@trifectaaddictionservices.com | +1 (403) 907-0996 • +1 (403) 907-1034<br/>
      www.trifectaaddictionservices.com<br/>
      <em>Elite, evidence-based Recovery, empowering one life at a time.</em>
    </div>
  </div>
</body>
</html>
```

**Variables to Replace:**
- `[INVOICE_NUMBER]` → Sequential invoice number (e.g., 1413, 1450)
- `[CLIENT_NAME]` → Full client name
- `[PROGRAM_TYPE]` → "14-Day Inpatient" / "28-Day Inpatient" / "28-Day Virtual Boot Camp"
- `[PAYMENT_METHOD]` → "e-Transfer" / "Credit Card" / "Wire Transfer"
- `[STATUS]` → "OUTSTANDING" / "PAID" / "PARTIAL PAYMENT RECEIVED"
- `[START_DATE]` → Program start date
- `[END_DATE]` → Program end date
- `[PROGRAM_NAME]` → Full program name
- `[DURATION]` → "14 days" / "28 days"
- `[INCLUSIONS]` → Brief list of what's included
- `[PROGRAM_FEE]` → Dollar amount (e.g., 13777.00)
- `[TOTAL_AMOUNT]` → Total amount due
- `[DUE_DATE]` → Payment due date

---

#### 2. Session-Based Invoice (Aftercare/Individual Sessions)

**Use Cases:**
- Aftercare sessions ($60/hour)
- Individual counseling sessions
- Partial payments

**Template Structure:**
```html
[Same header structure as program invoice]

<!-- LINE ITEMS - SESSION BASED -->
<div class="card">
  <table>
    <thead>
      <tr><th>Description</th><th>Rate</th><th>Amount (CAD)</th></tr>
    </thead>
    <tbody>
      [SESSION_ROWS]
      <!-- Example row: -->
      <tr>
        <td>
          <strong>Virtual Session – 60 Minutes</strong><br/>
          Date: <strong>[SESSION_DATE]</strong><br/>
          Focus: [SESSION_FOCUS]
        </td>
        <td>$60.00</td>
        <td>$60.00</td>
      </tr>
    </tbody>
  </table>
  <div class="total">
    <div class="label">Outstanding Balance (GST Exempt)</div>
    <div class="amount">$[OUTSTANDING_BALANCE]</div>
  </div>
</div>

<!-- PAYMENT NOTE WITH PARTIAL PAYMENT INFO -->
<div class="card note">
  This invoice reflects <strong>[SESSION_COUNT]</strong> 60-minute virtual counselling sessions for <strong>[CLIENT_NAME]</strong> on [SESSION_DATES_LIST].
  <br/><br/>
  Professional fee is <strong>$60/hour</strong>, for a total of <strong>$[TOTAL_FEE] CAD</strong>. Services are <strong>GST exempt</strong>.
  <br/><br/>
  <strong>Payment Status:</strong> $[AMOUNT_PAID] has been received. <strong>Outstanding balance: $[OUTSTANDING_BALANCE]</strong>
  <br/><br/>
  Please remit the remaining payment by e-transfer to <strong>info@trifectaaddictionservices.com</strong> due upon receipt.
  <br/><br/>
  <strong>E-Transfer Password: Trifecta 2025</strong>
</div>
```

**Variables to Replace:**
- `[SESSION_ROWS]` → Multiple `<tr>` rows, one per session
- `[SESSION_DATE]` → Individual session date (e.g., "Saturday, November 8, 2025")
- `[SESSION_FOCUS]` → Session topic (e.g., "CBT techniques and coping strategies")
- `[SESSION_COUNT]` → Number of sessions (e.g., "three")
- `[SESSION_DATES_LIST]` → Comma-separated list of dates
- `[TOTAL_FEE]` → Total of all sessions (e.g., "180.00")
- `[AMOUNT_PAID]` → Amount already paid (e.g., "120.00")
- `[OUTSTANDING_BALANCE]` → Remaining balance (e.g., "60.00")

---

#### 3. Receipt (Paid in Full)

**Use Cases:**
- Confirmation of full payment
- Record for client's insurance reimbursement
- Final accounting record

**Template Structure:**
```html
[Same header as invoice, but title: "Receipt"]

<!-- STATUS BADGE -->
<div class="status-badge paid">PAID IN FULL</div>

<!-- KEY DETAILS -->
<div class="card grid two">
  <div class="kv">
    <div class="k">Receipt For</div>
    <div class="v">[CLIENT_NAME]</div>
  </div>
  <div class="kv">
    <div class="k">Payment Date</div>
    <div class="v">[PAYMENT_DATE]</div>
  </div>
  <div class="kv">
    <div class="k">Payment Method</div>
    <div class="v">[PAYMENT_METHOD]</div>
  </div>
  <div class="kv">
    <div class="k">Original Invoice</div>
    <div class="v">#[INVOICE_NUMBER]</div>
  </div>
</div>

<!-- LINE ITEMS -->
[Same table structure as invoice]

<div class="total">
  <div class="label">Amount Paid</div>
  <div class="amount paid">$[AMOUNT_PAID]</div>
</div>

<!-- CONFIRMATION NOTE -->
<div class="card note success">
  <strong>Payment Received:</strong> This receipt confirms full payment of <strong>$[AMOUNT_PAID] CAD</strong> received on <strong>[PAYMENT_DATE]</strong> via <strong>[PAYMENT_METHOD]</strong> for services rendered.
  <br/><br/>
  This receipt may be used for insurance reimbursement purposes. Trifecta Addiction & Mental Health Services is a private pay facility and does not bill insurance directly.
  <br/><br/>
  Thank you for your payment.
</div>
```

**Variables to Replace:**
- `[PAYMENT_DATE]` → Date payment received
- `[PAYMENT_METHOD]` → e-Transfer / Credit Card / Wire Transfer
- `[AMOUNT_PAID]` → Total amount paid

---

## SharePoint Integration

### Microsoft Graph API Configuration

**Required Permissions:**
- `Files.ReadWrite.All` - Read and write files in all site collections
- `Sites.ReadWrite.All` - Edit or delete items in all site collections
- `User.Read` - Sign in and read user profile

**Authentication:**
```python
from msal import ConfidentialClientApplication
import requests

# Azure AD App Registration
CLIENT_ID = "[Your Azure AD App Client ID]"
CLIENT_SECRET = "[Your Azure AD App Client Secret]"
TENANT_ID = "[Your Tenant ID]"
AUTHORITY = f"https://login.microsoftonline.com/{TENANT_ID}"
SCOPE = ["https://graph.microsoft.com/.default"]

# Authenticate
app = ConfidentialClientApplication(
    CLIENT_ID,
    authority=AUTHORITY,
    client_credential=CLIENT_SECRET
)

# Get access token
result = app.acquire_token_for_client(scopes=SCOPE)
access_token = result.get("access_token")

# Headers for API calls
headers = {
    "Authorization": f"Bearer {access_token}",
    "Content-Type": "application/json"
}
```

### SharePoint File Operations

#### 1. Upload Document to SharePoint

```python
def upload_document_to_sharepoint(
    file_content: str,
    file_name: str,
    folder_path: str,
    site_id: str = "netorgft5726606.sharepoint.com,<site_guid>,<web_guid>"
):
    """
    Upload HTML document to SharePoint
    
    Args:
        file_content: HTML content as string
        file_name: Name of file (e.g., "Willigar_Max_Contract_2025-09-20.html")
        folder_path: Path within SharePoint (e.g., "Contracts/2025/September")
        site_id: SharePoint site identifier
    
    Returns:
        dict: Upload result with file URL and metadata
    """
    
    # Microsoft Graph API endpoint
    upload_url = (
        f"https://graph.microsoft.com/v1.0/sites/{site_id}"
        f"/drive/root:/{folder_path}/{file_name}:/content"
    )
    
    # Upload file
    response = requests.put(
        upload_url,
        headers={
            "Authorization": f"Bearer {access_token}",
            "Content-Type": "text/html"
        },
        data=file_content.encode('utf-8')
    )
    
    if response.status_code in [200, 201]:
        result = response.json()
        return {
            "success": True,
            "file_id": result["id"],
            "web_url": result["webUrl"],
            "download_url": result["@microsoft.graph.downloadUrl"]
        }
    else:
        return {
            "success": False,
            "error": response.text
        }
```

**Usage Example:**
```python
# Generate contract HTML
contract_html = generate_contract(
    client_name="Max Willigar",
    program_type="28_day_virtual",
    start_date="September 20, 2025"
)

# Upload to SharePoint
result = upload_document_to_sharepoint(
    file_content=contract_html,
    file_name="Willigar_Max_28Day_Virtual_Contract_2025-09-20.html",
    folder_path="Contracts/2025/September"
)

if result["success"]:
    print(f"Contract uploaded: {result['web_url']}")
else:
    print(f"Upload failed: {result['error']}")
```

#### 2. Retrieve Document from SharePoint

```python
def get_document_from_sharepoint(
    file_path: str,
    site_id: str
):
    """
    Retrieve document from SharePoint
    
    Args:
        file_path: Full path to file (e.g., "Contracts/2025/September/Willigar_Max_Contract.html")
        site_id: SharePoint site identifier
    
    Returns:
        dict: File content and metadata
    """
    
    # Get file metadata
    metadata_url = (
        f"https://graph.microsoft.com/v1.0/sites/{site_id}"
        f"/drive/root:/{file_path}"
    )
    
    response = requests.get(metadata_url, headers=headers)
    
    if response.status_code == 200:
        metadata = response.json()
        
        # Download file content
        download_url = metadata["@microsoft.graph.downloadUrl"]
        content_response = requests.get(download_url)
        
        return {
            "success": True,
            "content": content_response.text,
            "metadata": metadata
        }
    else:
        return {
            "success": False,
            "error": "File not found"
        }
```

#### 3. Create Folder Structure

```python
def create_folder_structure(
    folder_path: str,
    site_id: str
):
    """
    Create folder structure in SharePoint
    
    Args:
        folder_path: Path to create (e.g., "Contracts/2026/January")
        site_id: SharePoint site identifier
    
    Returns:
        dict: Creation result
    """
    
    folders = folder_path.split('/')
    current_path = ""
    
    for folder in folders:
        current_path = f"{current_path}/{folder}" if current_path else folder
        
        # Check if folder exists
        check_url = (
            f"https://graph.microsoft.com/v1.0/sites/{site_id}"
            f"/drive/root:/{current_path}"
        )
        
        check_response = requests.get(check_url, headers=headers)
        
        # Create folder if doesn't exist
        if check_response.status_code == 404:
            parent_path = "/".join(current_path.split('/')[:-1])
            create_url = (
                f"https://graph.microsoft.com/v1.0/sites/{site_id}"
                f"/drive/root:/{parent_path}:/children"
            )
            
            create_response = requests.post(
                create_url,
                headers=headers,
                json={
                    "name": folder,
                    "folder": {},
                    "@microsoft.graph.conflictBehavior": "rename"
                }
            )
    
    return {"success": True}
```

#### 4. List Documents in Folder

```python
def list_documents_in_folder(
    folder_path: str,
    site_id: str,
    filter_by: str = None
):
    """
    List all documents in a SharePoint folder
    
    Args:
        folder_path: Path to folder (e.g., "Contracts/2025/September")
        site_id: SharePoint site identifier
        filter_by: Optional filter (e.g., "startswith(name, 'Willigar')")
    
    Returns:
        list: List of files with metadata
    """
    
    list_url = (
        f"https://graph.microsoft.com/v1.0/sites/{site_id}"
        f"/drive/root:/{folder_path}:/children"
    )
    
    if filter_by:
        list_url += f"?$filter={filter_by}"
    
    response = requests.get(list_url, headers=headers)
    
    if response.status_code == 200:
        files = response.json().get("value", [])
        return [
            {
                "name": file["name"],
                "web_url": file["webUrl"],
                "created": file["createdDateTime"],
                "modified": file["lastModifiedDateTime"],
                "size": file["size"]
            }
            for file in files
            if "file" in file  # Exclude folders
        ]
    else:
        return []
```

### Document Generation Workflow

#### Complete Workflow: Contract Generation → SharePoint Storage

```python
def generate_and_store_contract(
    client_data: dict,
    program_type: str
):
    """
    Complete workflow: Generate contract and upload to SharePoint
    
    Args:
        client_data: {
            "name": "Max Willigar",
            "start_date": "September 20, 2025",
            "preferred_time": "7:00 PM",
            "email": "max@example.com"
        }
        program_type: "14_day_inpatient" | "28_day_inpatient" | "28_day_virtual"
    
    Returns:
        dict: Result with SharePoint URL
    """
    
    # Step 1: Select template
    template = get_contract_template(program_type)
    
    # Step 2: Populate template with client data
    contract_html = populate_template(template, client_data)
    
    # Step 3: Generate file name
    date_str = datetime.now().strftime("%Y-%m-%d")
    last_name = client_data["name"].split()[-1]
    first_name = client_data["name"].split()[0]
    
    program_name_map = {
        "14_day_inpatient": "14Day_Inpatient",
        "28_day_inpatient": "28Day_Inpatient",
        "28_day_virtual": "28Day_Virtual"
    }
    program_name = program_name_map[program_type]
    
    file_name = f"{last_name}_{first_name}_{program_name}_Contract_{date_str}.html"
    
    # Step 4: Determine folder path
    year = datetime.now().strftime("%Y")
    month = datetime.now().strftime("%B")
    folder_path = f"Contracts/{year}/{month}"
    
    # Step 5: Create folder structure if needed
    create_folder_structure(folder_path, SITE_ID)
    
    # Step 6: Upload to SharePoint
    upload_result = upload_document_to_sharepoint(
        file_content=contract_html,
        file_name=file_name,
        folder_path=folder_path
    )
    
    # Step 7: Log to CRM
    if upload_result["success"]:
        log_document_to_crm(
            client_email=client_data["email"],
            document_type="contract",
            document_url=upload_result["web_url"],
            program_type=program_type
        )
    
    return upload_result
```

#### Complete Workflow: Invoice Generation → SharePoint Storage

```python
def generate_and_store_invoice(
    client_data: dict,
    invoice_data: dict,
    invoice_type: str
):
    """
    Complete workflow: Generate invoice and upload to SharePoint
    
    Args:
        client_data: {
            "name": "Max Willigar",
            "email": "max@example.com"
        }
        invoice_data: {
            "invoice_number": "1413",
            "program_type": "28-Day Virtual Boot Camp",
            "sessions": [
                {"date": "Nov 8, 2025", "focus": "Initial assessment"},
                {"date": "Nov 15, 2025", "focus": "CBT techniques"}
            ],
            "total_fee": 180.00,
            "amount_paid": 120.00,
            "outstanding": 60.00
        }
        invoice_type: "program_fee" | "session_based" | "receipt"
    
    Returns:
        dict: Result with SharePoint URL
    """
    
    # Step 1: Select template
    template = get_invoice_template(invoice_type)
    
    # Step 2: Populate template
    invoice_html = populate_invoice_template(template, client_data, invoice_data)
    
    # Step 3: Generate file name
    date_str = datetime.now().strftime("%Y-%m-%d")
    last_name = client_data["name"].split()[-1]
    first_name = client_data["name"].split()[0]
    invoice_num = invoice_data["invoice_number"]
    
    if invoice_type == "receipt":
        file_name = f"{last_name}_{first_name}_Receipt_Invoice_{invoice_num}_PaidInFull_{date_str}.html"
    else:
        file_name = f"{last_name}_{first_name}_Invoice_{invoice_num}_{date_str}.html"
    
    # Step 4: Determine folder path
    year = datetime.now().strftime("%Y")
    month = datetime.now().strftime("%B")
    
    if invoice_type == "receipt" or invoice_data.get("status") == "PAID":
        folder_path = f"Invoices/Paid/{year}/{month}"
    else:
        folder_path = f"Invoices/{year}/{month}"
    
    # Step 5: Upload to SharePoint
    upload_result = upload_document_to_sharepoint(
        file_content=invoice_html,
        file_name=file_name,
        folder_path=folder_path
    )
    
    # Step 6: Log to CRM and QuickBooks
    if upload_result["success"]:
        log_document_to_crm(
            client_email=client_data["email"],
            document_type="invoice",
            document_url=upload_result["web_url"],
            invoice_number=invoice_num
        )
        
        sync_to_quickbooks(invoice_data)
    
    return upload_result
```

## CSS Styling (Trifecta Brand)

### Universal Stylesheet for All Documents

```css
:root {
  --brand-teal: #02B6BE;
  --brand-ink: #2E3033;
  --brand-sky: #E8F7F8;
  --brand-accent: #325C7A;
  --card: #ffffff;
  --muted: #6C737F;
  --border: #E6EAEE;
  --ring: rgba(2,182,190,.25);
  --radius: 14px;
  --shadow: 0 6px 22px rgba(24,39,75,.06), 0 2px 6px rgba(24,39,75,.06);
}

* {
  box-sizing: border-box;
}

body {
  margin: 0;
  background: #F7FAFC;
  color: var(--brand-ink);
  font-family: Inter, system-ui, -apple-system, Segoe UI, Roboto, sans-serif;
  line-height: 1.5;
}

.brandbar {
  height: 6px;
  background: linear-gradient(90deg, var(--brand-teal), var(--brand-accent));
}

.wrap {
  max-width: 980px;
  margin: 42px auto;
  padding: 0 20px;
}

/* LOGOS & MASTHEAD */
.masthead {
  display: flex;
  align-items: center;
  gap: 18px;
  flex-wrap: wrap;
  margin-bottom: 18px;
}

.masthead img {
  height: 72px;
  width: auto;
}

.brand-lockup {
  display: flex;
  align-items: center;
  gap: 14px;
  flex-wrap: wrap;
  padding: 14px 16px;
  background: var(--brand-sky);
  border-radius: 12px;
}

.brand-lockup .divider {
  width: 2px;
  height: 44px;
  background: linear-gradient(180deg, #b7e9ec, #9adfe3);
}

/* TYPOGRAPHY */
h1 {
  font-family: "Playfair Display", serif;
  font-weight: 700;
  margin: 10px 0 6px;
  letter-spacing: .2px;
  font-size: 28px;
}

h2 {
  font-family: "Playfair Display", serif;
  font-weight: 700;
  font-size: 22px;
  margin: 0 0 10px;
  letter-spacing: .2px;
}

.sub {
  color: var(--muted);
  font-size: 15px;
}

/* CARDS */
.card {
  background: var(--card);
  border-radius: var(--radius);
  box-shadow: var(--shadow);
  padding: 22px;
  margin: 18px 0;
  border: 1px solid var(--border);
}

/* GRID LAYOUT */
.grid {
  display: grid;
  gap: 14px;
}

@media (min-width: 820px) {
  .grid.two {
    grid-template-columns: 1fr 1fr;
  }
}

/* KEY-VALUE PAIRS */
.kv {
  padding: 14px 16px;
  border-radius: 12px;
  background: #fff;
  border: 1px solid var(--border);
}

.kv .k {
  font-size: 12px;
  letter-spacing: .12em;
  text-transform: uppercase;
  color: var(--muted);
}

.kv .v {
  font-size: 17px;
  font-weight: 600;
}

/* BADGES */
.badge {
  display: inline-block;
  padding: 6px 10px;
  border-radius: 999px;
  background: rgba(2,182,190,.10);
  color: var(--brand-teal);
  font-weight: 600;
  font-size: 12px;
  letter-spacing: .06em;
  text-transform: uppercase;
}

/* LISTS */
.list {
  margin: 0;
  padding-left: 18px;
}

.list li {
  margin: 6px 0;
}

/* PHASE SECTIONS */
.phase {
  border-left: 4px solid var(--brand-teal);
  padding-left: 14px;
  margin: 10px 0 8px;
}

/* TABLES */
table {
  width: 100%;
  border-collapse: separate;
  border-spacing: 0;
  overflow: hidden;
  border-radius: 12px;
  border: 1px solid var(--border);
}

th, td {
  padding: 12px 14px;
  border-bottom: 1px solid var(--border);
  text-align: left;
}

th {
  background: #F4FAFB;
  font-weight: 600;
  font-size: 13px;
  color: #405463;
}

tr:last-child td {
  border-bottom: none;
}

/* NOTES */
.note {
  background: #fff;
  border: 1px dashed #bcdde0;
  color: #35565b;
  padding: 14px 16px;
  border-radius: 12px;
  font-size: 14px;
}

.note.success {
  border-color: #4ade80;
  background: #f0fdf4;
  color: #166534;
}

/* INITIAL LINES */
.initial {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 10px;
  margin-top: 8px;
}

.initial label {
  color: var(--muted);
  font-size: 13px;
}

.initial .line {
  flex: 1;
  border-bottom: 1px solid var(--border);
  height: 24px;
}

/* SIGNATURES */
.sig-row {
  display: grid;
  gap: 10px;
}

@media (min-width: 680px) {
  .sig-row {
    grid-template-columns: 1fr 1fr;
  }
}

.sig {
  border: 1px solid var(--border);
  border-radius: 12px;
  padding: 14px 16px;
  background: #fff;
}

.sig .line {
  border-bottom: 1px solid var(--border);
  height: 28px;
  margin: 8px 0;
}

/* FOOTER */
.footer {
  text-align: center;
  color: var(--muted);
  font-size: 13px;
  margin-top: 12px;
}

.contact {
  font-size: 14px;
  color: var(--muted);
}

.contact a {
  color: var(--brand-accent);
  text-decoration: none;
}

/* TOTALS */
.total {
  display: flex;
  justify-content: flex-end;
  gap: 18px;
  align-items: center;
  margin-top: 10px;
}

.total .label {
  color: var(--muted);
  font-weight: 600;
}

.total .amount {
  font-size: 22px;
  font-weight: 800;
}

.total .amount.paid {
  color: #16a34a;
}

/* STATUS BADGES */
.status-badge {
  display: inline-block;
  padding: 8px 16px;
  border-radius: 999px;
  font-weight: 700;
  font-size: 14px;
  letter-spacing: .08em;
  text-transform: uppercase;
  margin: 12px 0;
}

.status-badge.paid {
  background: #dcfce7;
  color: #166534;
}

.status-badge.outstanding {
  background: #fef3c7;
  color: #92400e;
}

.status-badge.partial {
  background: #dbeafe;
  color: #1e40af;
}

/* PRINT STYLES */
@media print {
  body {
    background: #fff;
  }
  .card {
    box-shadow: none;
  }
  .no-print {
    display: none;
  }
}
```

## Best Practices & Usage Guidelines

### 1. When to Generate Contracts

**Trigger Conditions:**
- Client completes intake consultation
- Client confirms program enrollment
- Payment (deposit or full) is received
- Program start date is confirmed

**Workflow:**
1. Collect all required client information
2. Select appropriate contract template
3. Populate template with client data
4. Generate HTML contract
5. Upload to SharePoint in appropriate folder
6. Send download link to client via email
7. Log contract creation in CRM
8. Set reminder for signature collection

### 2. When to Generate Invoices

**Trigger Conditions:**
- Contract is signed (generate program fee invoice)
- Session is completed (generate session invoice)
- Payment plan installment is due
- Aftercare sessions are scheduled

**Workflow:**
1. Determine invoice type (program fee vs. session-based)
2. Assign sequential invoice number
3. Populate invoice template with line items
4. Calculate totals and outstanding balances
5. Generate HTML invoice
6. Upload to SharePoint
7. Send to client via email
8. Log invoice in QuickBooks
9. Set payment reminder if outstanding balance

### 3. When to Generate Receipts

**Trigger Conditions:**
- Full payment is received
- Final installment is paid
- Client requests receipt for insurance

**Workflow:**
1. Verify payment received in QuickBooks
2. Pull original invoice data
3. Generate receipt with "PAID IN FULL" status
4. Upload to SharePoint in "Paid" folder
5. Send receipt to client via email
6. Update CRM status to "Paid"

### 4. SharePoint Folder Organization

**Best Practices:**
- Create folders by year, then month
- Use consistent naming conventions
- Separate "Paid" invoices from "Outstanding"
- Create client-specific folders for easy access
- Archive old documents annually

### 5. Error Handling

**Common Issues & Solutions:**

| Issue | Solution |
|-------|----------|
| SharePoint authentication fails | Refresh access token, verify Azure AD app permissions |
| File already exists | Use conflict behavior "rename" or check for existing file first |
| Folder doesn't exist | Call `create_folder_structure()` before upload |
| Template variable missing | Validate client data before generation, use default values |
| HTML rendering issues | Test templates in multiple browsers, validate HTML |

### 6. Quality Assurance Checklist

**Before Generating Documents:**
- [ ] Verify client name spelling
- [ ] Confirm program start date
- [ ] Double-check pricing and payment terms
- [ ] Validate all required fields are populated
- [ ] Preview generated HTML in browser
- [ ] Test SharePoint upload connection
- [ ] Verify email delivery of download link

**After Document Generation:**
- [ ] Confirm file uploaded successfully to SharePoint
- [ ] Verify download link works
- [ ] Check document renders correctly in browser
- [ ] Log document creation in CRM
- [ ] Send notification to client
- [ ] Set follow-up reminders

## Integration with Existing Systems

### CRM Integration

When documents are generated, log the event in the CRM:

```python
def log_document_to_crm(
    client_email: str,
    document_type: str,
    document_url: str,
    **metadata
):
    """
    Log document creation to CRM
    
    Args:
        client_email: Client's email address
        document_type: "contract" | "invoice" | "receipt"
        document_url: SharePoint URL to document
        **metadata: Additional document metadata
    """
    
    crm_entry = {
        "timestamp": datetime.now().isoformat(),
        "client_email": client_email,
        "document_type": document_type,
        "document_url": document_url,
        "metadata": metadata
    }
    
    # Log to CRM database
    # (Implementation depends on CRM system)
```

### QuickBooks Integration

Sync invoice data to QuickBooks:

```python
def sync_to_quickbooks(invoice_data: dict):
    """
    Create invoice in QuickBooks
    
    Args:
        invoice_data: Invoice details including line items and totals
    """
    
    qb_invoice = {
        "Line": [{
            "Amount": invoice_data["total_fee"],
            "DetailType": "SalesItemLineDetail",
            "SalesItemLineDetail": {
                "ItemRef": {"value": invoice_data["program_item_id"]}
            }
        }],
        "CustomerRef": {"value": invoice_data["client_qb_id"]},
        "BillEmail": {"Address": invoice_data["client_email"]}
    }
    
    # Send to QuickBooks API
    # (Implementation depends on QuickBooks setup)
```

### Email Notification Integration

Send download links to clients:

```python
def send_document_email(
    client_email: str,
    document_type: str,
    document_url: str,
    client_name: str
):
    """
    Send document download link to client via email
    
    Args:
        client_email: Client's email address
        document_type: "contract" | "invoice" | "receipt"
        document_url: SharePoint download URL
        client_name: Client's full name
    """
    
    if document_type == "contract":
        subject = "Your Trifecta Treatment Agreement"
        body = f"""
        Dear {client_name},
        
        Your treatment agreement is ready for review. Please click the link below to view and sign:
        
        {document_url}
        
        If you have any questions, please don't hesitate to reach out.
        
        Warm regards,
        Danielle Claughton
        Trifecta Addiction & Mental Health Services
        """
    
    elif document_type == "invoice":
        subject = "Invoice from Trifecta Addiction Services"
        body = f"""
        Dear {client_name},
        
        Your invoice is ready. Please click the link below to view and process payment:
        
        {document_url}
        
        Payment can be made via e-transfer to info@trifectaaddictionservices.com
        E-Transfer Password: Trifecta 2025
        
        Thank you,
        Danielle Claughton
        Trifecta Addiction & Mental Health Services
        """
    
    # Send via Microsoft Graph API (Outlook)
    # (Implementation depends on email setup)
```

## Security & Compliance

### Data Protection

**Encryption:**
- All documents encrypted at rest in SharePoint
- All API communications use TLS 1.3
- Access tokens refreshed every 60 minutes
- No sensitive data stored in logs

**Access Control:**
- Role-based permissions in SharePoint
- Client-specific folders with restricted access
- Audit logs for all document access
- Multi-factor authentication for staff

**HIPAA Compliance:**
- Business Associate Agreements with Microsoft
- PHI handling procedures documented
- Breach notification protocols in place
- 7-year retention policy, automatic deletion after

### Audit Trail

Log all document operations:

```python
def log_audit_event(
    event_type: str,
    user: str,
    document_id: str,
    action: str
):
    """
    Log audit event for compliance
    
    Args:
        event_type: "create" | "access" | "modify" | "delete"
        user: User performing action
        document_id: SharePoint document ID
        action: Description of action taken
    """
    
    audit_log = {
        "timestamp": datetime.now().isoformat(),
        "event_type": event_type,
        "user": user,
        "document_id": document_id,
        "action": action,
        "ip_address": request.remote_addr
    }
    
    # Store in secure audit database
```

## Conclusion

This skill provides comprehensive document generation and SharePoint integration capabilities for Trifecta Addiction and Mental Health Services. By automating contract and invoice creation while maintaining brand consistency, security, and compliance, the system enables efficient client onboarding and financial management.

**Key Features:**
- Professional, branded HTML templates
- Automated SharePoint storage and organization
- CRM and QuickBooks integration
- HIPAA-compliant security measures
- Complete audit trail

Use this skill in combination with the Trifecta Practice Management System, Marketing & SEO Strategy, and AI Agent Orchestration skills for complete ecosystem knowledge.
