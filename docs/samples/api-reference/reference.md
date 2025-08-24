---
title: Druva Backup & Restore API Reference
owner: docs-team
status: active
tags: [api-reference]
last_reviewed: 2025-08-01
---
Authentication uses bearer tokens.

Pagination uses limit and offset.

### List backups

```bash
curl -H "Authorization: Bearer TOKEN" \
  "https://api.example.com/v1/backups?tenantId=123"
```

### Start restore

```bash
curl -X POST -H "Authorization: Bearer TOKEN" \
  -d '{"backupId":"b1","targetPath":"/tmp"}' \
  "https://api.example.com/v1/restores"
```

Checklist: PM, Eng

Source: intake/tech-docs/openapi.yaml
