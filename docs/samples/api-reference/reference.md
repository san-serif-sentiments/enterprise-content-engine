---
title: Backup & Restore API Reference
owner: docs-team
status: active
tags: [api-reference. public-docs]
last_reviewed: 2025-08-24
risk_band: L2
approvals: pm: true engineering: true
---
## Overview
Authentication uses bearer tokens. Pagination uses `limit` and `offset`. ### List backups ```bash
curl -H "Authorization: Bearer TOKEN" \ "https://api.example.com/v1/backups?tenantId=123"
``` ### Start restore ```bash
curl -X POST -H "Authorization: Bearer TOKEN" \ -H "Content-Type: application/json" \ -d '{"backupId":"b1","targetPath":"/tmp"}' \ "https://api.example.com/v1/restores"
``` Notes: For `tenantId`. use the GUID of the managed tenant. `targetPath` must be writable. Source: intake/tech-docs/openapi.yaml

Source: intake/tech-docs/openapi.yaml
