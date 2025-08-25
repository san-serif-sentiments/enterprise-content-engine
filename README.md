---
title: Agentic Documentation System – System Overview
owner: Shailesh Rawat
status: draft
version: 1.0
tags: [Agentic Content System, Technical Documentation, Docs-as-Code, AI Workflows]
last_reviewed: 2025-08-25
---

# Overview
This repository showcases a working **agentic documentation system**.  
The system demonstrates how AI-driven roles can generate and maintain high-quality documentation by turning **structured inputs** into **validated, publishable outputs**.  

Instead of static writing samples, this is a **self-maintaining documentation workflow** that runs end-to-end:  
- Intake of structured inputs (briefs, API specs, feedback data)  
- Agentic processing (writer, editor, compliance, publisher)  
- Governed outputs (docs, in-app guidance, release notes, KB)  
- Continuous improvement via data-driven iteration and metrics  

---

# Why It Matters
Modern documentation needs to be:  
- **Continuous**: always up to date with product and customer feedback  
- **Governed**: compliant with style, risk, and factual accuracy policies  
- **User-centric**: task-first, contextual, and available in-app  
- **Measurable**: tied to adoption, support deflection, and engagement metrics  

This system proves how an **agentic workflow** can handle these needs with **Docs-as-Code principles**.

---

# Core Workflows

## 1. Intake → Output (Full Lifecycle)
- **Inputs** in `/intake/`  
  - `brief.md` – high-level release/change summary  
  - `openapi.yaml` – source-of-truth API spec  
  - `feedback.csv` – support or customer query data  
  - `hints.md` – in-app guidance notes  
- **Agent Roles**  
  - Intake Router → Researcher → Writers (tech, support, in-app) → Editors → Compliance Guard → Publisher  
- **Outputs** in `/docs/`  
  - API Reference (OpenAPI + human-readable guide)  
  - User Guide (task-based, role-driven)  
  - Release Notes (highlights, fixes, API changes)  
  - Knowledge Base articles (issue → cause → resolution → prevention)  
  - In-App Guidance (tooltips.json, walkthrough.yaml)  
  - Evidence & Metrics (engagement, ticket deflection, adoption)  

---

## 2. Tech Release Packet
- Trigger: new API spec + feature brief in `/intake/tech-docs/`  
- Outputs:  
  - API reference (`reference.md`)  
  - User guide (`tenant-admin.md`)  
  - Release notes (`2025-08.md`)  
  - In-app tooltips (`tooltips.json`)  
  - Walkthrough (`walkthrough.yaml`)  
- Governance applied: style policy (active voice, clear phrasing), compliance guard (no PII, sources validated).  

---

## 3. KB Update Packet
- Trigger: updated `feedback.csv` showing recurring support queries  
- Outputs:  
  - Refreshed KB articles in `/docs/samples/kb-articles/`  
  - Updated metrics in `/docs/evidence/metrics.md`  
- Governance applied: factual verification against source feedback, Support sign-off simulated.  

---

# Governance & Policies
- **Style Policy (`style.yml`)**  
  - Active voice  
  - Sentence max length  
  - Forbidden phrases (e.g., “cutting-edge”, “we think”)  
- **Compliance Policy (`compliance.yml`)**  
  - PII redaction (email, phone)  
  - Sources required for factual claims  
  - Risk banding (internal vs public content)  

---

# Metrics & Evidence
- Search success rate from queries  
- Top failed queries with frequencies  
- KB deflection estimates  
- Release notes cycle time  
- Walkthrough completion rates  

---

# Usage
From repo root:  

Run full pipeline:  
```bash
python -m engine.run --all

Run a specific packet:

python -m engine.run --packet tech-release
python -m engine.run --packet kb-update


---

Key Takeaways

Inputs drive outputs: docs update automatically when intake specs or feedback change.

Agentic lifecycle: modular roles enforce writing, editing, compliance, and publishing.

Evidence baked-in: metrics track improvements and close the loop with user feedback.


This is a living portfolio system that proves how documentation can be created, governed, and maintained through agentic AI workflows.

---

