---
title: Agentic Documentation System – Technical Guide  
archetype: technical-doc  
status: stable  
owner: Shailesh Rawat  
maintainer: self  
version: 1.0  
tags: [Docs-as-Code, Agentic System, AI Workflows, Portfolio]  
last_reviewed: 2025-08-25  
---

# Agentic Documentation System – Technical Guide

This document explains how to **set up, run, and extend** the Agentic Documentation System.  
The system turns structured inputs (briefs, API specs, feedback data) into validated, publishable outputs (API references, user guides, release notes, KB articles, and in-app guidance).

---

## Why It Matters

This guide helps developers, documentation engineers, and technical communicators:

- Understand the folder structure and role-based architecture  
- Run end-to-end pipelines or packet-specific workflows  
- Customize governance policies for style and compliance  
- Contribute new roles or extend outputs safely  

---

## Audience, Scope & Personas

- **Technical Writers / Docs Engineers** – to understand Docs-as-Code pipelines  
- **Developers** – to extend roles or integrate with CI/CD  
- **Comms / Support Teams** – to use feedback-driven KB updates  
- **Researchers** – to study modular, agentic workflows  

---

## Prerequisites

- **Python 3.11+**  
- Optional: `pip install pyyaml` (used for YAML parsing)  
- GitHub (for CI/CD workflows)

> Recommended: set up a virtual environment

```bash
python -m venv .venv
source .venv/bin/activate   # macOS/Linux
.venv\Scripts\Activate.ps1  # Windows
pip install -U pip pyyaml
````

---

## System Architecture

```
engine/
├─ run.py                  # CLI entrypoint
├─ graph.py                # Orchestration flow
├─ roles/                  # Modular agent roles
│  ├─ intake_router.py
│  ├─ researcher.py
│  ├─ writer_tech.py
│  ├─ writer_support.py
│  ├─ writer_inapp.py
│  ├─ editor_style.py
│  ├─ editor_factual.py
│  ├─ compliance_guard.py
│  └─ publisher.py
├─ policies/               # Governance rules
│  ├─ style.yml
│  ├─ compliance.yml
│  └─ risk.yml
├─ logs/                   # Execution logs
└─ metrics/                # Run-time metrics
```

> Role Flow: Intake → Research → Writers → Editors → Compliance → Publisher

All roles use deterministic inputs/outputs and log results to `/engine/logs`.

---

## Tasks & Step-by-Step Instructions

### Clone the Repository

```bash
git clone <repo-url>
cd agentic-id-portfolio
```

### Prepare Intake Files

Edit files inside `/intake/`:

* `tech-docs/brief.md` – summary of release or feature
* `tech-docs/openapi.yaml` – valid OpenAPI 3.0 spec
* `support/feedback.csv` – table of common queries
* `inapp/hints.md` – notes for tooltips and walkthroughs

### Run the Full Pipeline

```bash
python -m engine.run --all
```

### Run Specific Packets

**Tech Release Packet:**

```bash
python -m engine.run --packet tech-release
```

**KB Update Packet:**

```bash
python -m engine.run --packet kb-update
```

### Outputs

Generated files are stored in `/docs/samples/`, including:

* `api-reference/` → OpenAPI + human-readable reference
* `user-guide/` → Task-based user documentation
* `release-notes/` → Highlights, fixes, API changes
* `kb-articles/` → Issue → Cause → Resolution → Prevention
* `in-app-guidance/` → `tooltips.json` and `walkthrough.yaml`
* `evidence/` → Metrics and logs

---

## Access Control & Permissions

* **Writers** → update briefs, specs, and feedback
* **Editors** → style and factual checks
* **Compliance** → PII, sourcing, and policy enforcement
* **Publisher** → generates final docs in `/docs/samples/`

---

## Practical Examples & Templates

### API Spec (`intake/tech-docs/openapi.yaml`)

```yaml
openapi: 3.0.3
info:
  title: Backup Service API
  version: "1.0.0"
paths:
  /v1/backups:
    get:
      summary: List backups
      parameters:
        - in: query
          name: tenantId
          schema:
            type: string
      responses:
        "200":
          description: OK
  /v1/restores:
    post:
      summary: Start restore job
      requestBody:
        required: true
        content:
          application/json:
            schema:
              type: object
              properties:
                backupId: { type: string }
                targetPath: { type: string }
      responses:
        "202":
          description: Accepted
```

### Feedback CSV (`intake/support/feedback.csv`)

```csv
url,query,ticket_tag,frequency
/docs/restore,restore alternate path failed,restore,53
/docs/backup-policy,retention vs immutability,policy,19
```

---

## Known Issues & Friction Points

* Intake quality directly affects output quality
* Feedback CSV must use consistent fields
* In-app JSON/YAML must pass schema validation

---

## Tips & Best Practices

* Start small: minimal, valid OpenAPI spec works best
* Keep `feedback.csv` fresh to simulate real iteration
* Customize `style.yml` to enforce your tone and voice
* Use `--update` mode to re-run only impacted outputs

---

## Troubleshooting Guidance

* `KeyError in publisher` → Check writer output structure
* `No changes on re-run` → Ensure `/intake/` files were updated
* `Invalid YAML/JSON` → Use `yamllint`, `jq`, or IDE validators

---

## Dependencies, Risks & Escalation Path

* **Dependencies**: Python 3.11+, PyYAML (optional)
* **Risks**: Low-quality input → generic, unhelpful docs
* **Escalation**:

  * Intake issues → `intake_router.py`
  * Factual/Style issues → Editors
  * Compliance issues → `compliance_guard.py`

---

## Success Metrics & Outcomes

* Consistent content generation speed
* API → Docs automation
* Feedback-loop → KB updates
* Enforced governance and traceability

---

## Resources & References

* `/engine/policies/style.yml`
* `/engine/policies/compliance.yml`
* `/docs/evidence/metrics.md`

---

## Last Reviewed / Last Updated

2025-08-25

```
