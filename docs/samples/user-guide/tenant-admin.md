---
title: Tenant Admin Guide
owner: docs-team
status: active
tags: [user-guide, public-docs]
last_reviewed: 2025-08-24
risk_band: L2
approvals:
  pm: true
  engineering: true
---
## Configure backup policy
1. Open **Policies**.
2. Define scope and schedule (set retention days and window).
3. Save and verify next run time.

## Run backup
1. Open **Backups**.
2. Select tenant.
3. Click **Run Now** and confirm.

## Restore data
1. Open **Restores**.
2. Choose the latest backup.
3. Provide an alternate `targetPath`.
4. Submit and verify output.

**Verification:** Files appear at `targetPath` and pass integrity checks.

**Rollback:** Re-run backup with prior policy settings.

Source: intake/tech-docs/brief.md
