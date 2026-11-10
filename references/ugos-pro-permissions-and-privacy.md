# UGOS Pro Permissions, Loopback Isolation & Privacy Boundaries

This reference details how `ugos-vaultloom` integrates with `UGOS Pro` storage permissions, network isolation, and multi-account privacy controls referenced in [SKILL.md](../SKILL.md).

---

## 1. Filesystem & Shared-Folder ACL Boundaries on `UGOS Pro`

1. **Explicit Share Scoping (`UGOS_VOLUME_ROOT`):**
   - VaultLoom operates strictly inside user-authorized `UGOS Pro` volume paths (placeholder: `/volume1/<SHARED_FOLDER_PLACEHOLDER>`).
   - Path traversal (`..`) and symlinks resolving outside `UGOS_VOLUME_ROOT` are rejected before file metadata or text is read.
2. **Respecting SMB / Family Account ACLs:**
   - On multi-user `NASync` appliances, each household member or SMB department has distinct `UGOS Pro` POSIX/ACL permissions.
   - Index and search queries execute under the requesting account's authorized share scope so User A cannot query files stored in User B's private home volume.
3. **Database Storage Hygiene:**
   - The `SQLite WAL + FTS5` database (`VAULTLOOM_DB_PATH`) and optional Unix socket (`VAULTLOOM_SOCKET_PATH`) must be created with `0600` owner-only permissions under `/volume1/@appdata/ugos-vaultloom/`.
   - VaultLoom never deletes, moves, or overwrites user source files on the NAS volume; bitemporal updates modify only VaultLoom's own metadata catalog.

---

## 2. Zero-Cloud Loopback Network Policy (`zero_cloud_loopback_only`)

- **Zero External API Keys or Cloud Telemetry:** VaultLoom requires `0` external API keys and opens `0` WAN sockets.
- **Strict Loopback Binding:** When running as a local service (`serve-http`), the HTTP listener binds exclusively to `127.0.0.1` (never `0.0.0.0`), and local encoder calls (`LOCAL_EMBED_ENDPOINT`) are restricted to `127.0.0.1` or `AF_UNIX` sockets.

---

## 3. Multi-User Differential Privacy & Outbound Share Limits

1. **Formal `(\epsilon, \delta)`-DP Collaborative Preference Learning:**
   - Shared NAS households and SMB teams benefit from collaborative folder/tag suggestions (e.g., routing invoices, RAW photos, or build scripts) without revealing who owns which filename.
   - Each account clips its `24-d` feature vectors (`||x||_2 <= 1.0`) and adds calibrated Gaussian noise to sufficient statistics (`G = X^T X`, `R = X^T Y`) tracked by a Rényi Differential Privacy Moments Accountant (`epsilon = 1.0..4.0`, `delta = 1e-6..1e-5` per `NodeGrid` regime). Raw filenames never enter the personalization state.
2. **Deterministic Outbound PII Redaction & Honest Scope:**
   - Before text notes or file excerpts leave the NAS via an external share caption, `DeterministicPiiRedactor` strips structured patterns (`SSN`, payment cards, phone numbers, IPv4 addresses, mailboxes, and `ACCT-*` tokens).
   - **Known Limitation:** Regex redaction operates on UTF-8 text and EXIF strings; sensitive text embedded inside un-OCRed raster images or handwritten scans requires local OCR preprocessing or manual user confirmation prior to public sharing.
