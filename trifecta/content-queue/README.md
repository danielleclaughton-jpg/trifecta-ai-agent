# Content Queue

Drop `.md` files here to queue content for Danielle's approval.

## Format

Each file should include frontmatter:

```markdown
---
platform: linkedin|instagram|facebook|blog|email
date: 2026-04-01
priority: normal|high|urgent
title: Short title for approval UI
---

Content body here...
```

Files are scanned by `/api/brief` and surfaced in the daily brief.
Approved content moves to `trifecta/content/approved/`.
