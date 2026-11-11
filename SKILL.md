---
name: ugos-vaultloom
description: Zero-cloud bitemporal NAS search, 24-d Procrustes cross-modal indexing, differentially private multi-user folder routing, and outbound PII redaction skill for UGREEN UGOS Pro AI NAS.
---

# UGOS VaultLoom — Local Bitemporal Subspace & Privacy Skill for UGREEN AI NAS

## 1. User Goal & Problem Solved

UGREEN NAS owners store personal photos, creator studio assets, codebases, and business documents locally to preserve data ownership. Standard AI search stacks undermine that goal in four ways:
1. **Vector RAM Bloat:** Conventional `1024-d` float32 embeddings consume `4,096 B` per file (`~4.1 GB` vector RAM per `1,000,000` files before graph overhead), competing with `UGOS Pro` filesystem caches, Docker services, and media workflows.
2. **Re-Indexing Lock-In:** Upgrading a local text or vision embedding model normally invalidates stored vectors and forces multi-day disk re-indexing across RAID pools.
3. **Stale-Revision Confusion:** Overwriting flat index entries erases document history and surfaces outdated drafts alongside active files.
4. **Shared-NAS Privacy Exposure:** Multi-user family and SMB volumes risk leaking private folder habits across accounts or exposing personal identifiers in external share links.

**UGOS VaultLoom** gives the Uliya agent a strictly local, zero-cloud workflow that projects multi-modal embeddings into a shared `24-d` float32 Orthogonal Procrustes subspace (`96 B/file`, `-97.66%` vector RAM vs `1024-d`), tracks bitemporal revisions in `SQLite WAL + FTS5`, upgrades local encoders via `96` calibration anchors with `0` stored files re-indexed, learns per-account folder preferences under `(\epsilon, \delta)`-Differential Privacy, and strips sensitive tokens before external sharing.

---

## 2. Required Inputs & Configuration Placeholders

Never hardcode credentials, personal paths, or external API keys. Configure all runtime bindings via local placeholders:

| Placeholder Variable | Default / Example Placeholder | Required Permission / Scope |
| :--- | :--- | :--- |
| `UGOS_VOLUME_ROOT` | `/volume1/<SHARED_FOLDER_PLACEHOLDER>` | Read-only access to user-authorized `UGOS Pro` share |
| `VAULTLOOM_DB_PATH` | `/volume1/@appdata/ugos-vaultloom/vault.sqlite` | Read/write local `0600` SQLite WAL + FTS5 file |
| `VAULTLOOM_GRID_CONFIG` | `./config/subspace_vault_grid.json` | Read-only `NodeGrid` regime & bounds JSON |
| `VAULTLOOM_REGIME_ID` | `home_family_nas_regime` | One of `home_family_nas_regime`, `studio_creator_pro_nas_regime`, `smb_team_compliance_nas_regime` |
| `LOCAL_EMBED_ENDPOINT` | `http://127.0.0.1:<LOCAL_EMBED_PORT>/v1/embeddings` | Optional loopback-only local encoder endpoint (`0` WAN egress) |
| `VAULTLOOM_SOCKET_PATH` | `/run/ugos-vaultloom/vaultloom.sock` | Optional local `AF_UNIX` IPC socket (`0600` owner-only) |
| `VAULTLOOM_DP_ACCOUNT_ID` | `<LOCAL_UGOS_USER_PLACEHOLDER>` | Pseudonymous local account token for DP preference updates |

See [references/ugos-pro-permissions-and-privacy.md](references/ugos-pro-permissions-and-privacy.md) for least-privilege ACL and loopback isolation rules.

---

## 3. Supported CLI Capabilities & Exact Command Contracts

The Uliya agent invokes the local reference CLI (`ugos-vaultloom-cli`) using deterministic JSON stdout contracts. Full flag schemas and sample payloads are documented in [references/cli-reference.md](references/cli-reference.md).

1. **Readiness & Resource Envelope Check (`healthcheck`):**
   ```bash
   ugos-vaultloom-cli --db "${VAULTLOOM_DB_PATH}" --regime "${VAULTLOOM_REGIME_ID}" healthcheck
   ```
   Returns `status: "healthy"`, `network_egress: "zero_cloud_loopback_only"`, `subspace_bytes_per_file: 96`, `ram_reduction_pct: 97.66`, and `triage_wasm_bytes: 256`.

2. **Local File-Triage Classification (`triage`):**
   ```bash
   ugos-vaultloom-cli --db "${VAULTLOOM_DB_PATH}" triage --features "<CODE_SYNTAX_DENSITY>,<MEDIA_EXIF_DENSITY>,<STRUCTURED_RECORD_DENSITY>"
   ```
   Classifies incoming files into `archive_docs`, `engineering_code`, `media_gallery`, or `compliance_records` via a `256 B` local triage cartridge.

3. **Bitemporal File Revision Indexing (`index`):**
   ```bash
   ugos-vaultloom-cli --db "${VAULTLOOM_DB_PATH}" --regime "${VAULTLOOM_REGIME_ID}" index \
     --path "${UGOS_VOLUME_ROOT}/<RELATIVE_FILE_PATH>" \
     --modality "<text|code|media_exif>" \
     --text "<EXTRACTED_LOCAL_TEXT_OR_EXIF>" \
     --valid-from "<UNIX_EPOCH_SECONDS>"
   ```
   Atomically closes any prior active revision (`valid_to = valid_from`) and inserts `revision_num + 1` with its `96 B` `24-d` float32 subspace blob.

4. **Current or Point-in-Time Hybrid Search (`search`):**
   ```bash
   ugos-vaultloom-cli --db "${VAULTLOOM_DB_PATH}" --regime "${VAULTLOOM_REGIME_ID}" search \
     --query "<USER_SEARCH_QUERY>" [--as-of "<UNIX_EPOCH_SECONDS>"]
   ```
   Fuses `SQLite FTS5 BM25` lexical ranks with `24-d` Procrustes cosine similarity via Reciprocal Rank Fusion (`RRF`), filtered strictly by active (`valid_to IS NULL`) or historical (`as_of`) validity.

5. **Outbound External Share PII Redaction (`redact`):**
   ```bash
   ugos-vaultloom-cli --db "${VAULTLOOM_DB_PATH}" redact --text "<OUTBOUND_SNIPPET_OR_NOTE>"
   ```
   Strips SSN, payment card, phone, IPv4, mailbox, and account-reference patterns locally before any external share link or summary is created.

---

## 4. Expert Agent Orchestration Workflow

Follow this deterministic 6-step orchestration loop (detailed decision trees in [references/orchestration-and-failure-modes.md](references/orchestration-and-failure-modes.md)):

1. **Step 1 — Preflight & Scope Guard:** Run `healthcheck` once per session. Reject any target file path outside `UGOS_VOLUME_ROOT` or belonging to a `UGOS Pro` shared folder the requesting user lacks read permission to access.
2. **Step 2 — Intake & Local Triage:** On file creation/modification (or AI Album metadata update), extract plain text, code symbols, or EXIF tags locally and run `triage` to assign the default category without cloud calls.
3. **Step 3 — `24-d` Procrustes Projection & Bitemporal Upsert:** Project raw local embeddings (`1024-d` when `LOCAL_EMBED_ENDPOINT` is active, or deterministic local feature projection offline) through the fitted `OrthogonalProcrustesBridge` (`Q^T Q = I_24`) into `96 B` float32 vectors and execute `index`. When upgrading a local encoder model, fit a new `96`-anchor Procrustes matrix `Q_v2` in milliseconds instead of re-indexing stored files.
4. **Step 4 — Hybrid Bitemporal Retrieval:** For current questions, call `search` without `--as-of` so superseded drafts never leak into answers. For historical audit or recovery questions ("what did our NAS config say last Tuesday?"), pass `--as-of <TIMESTAMP>`.
5. **Step 5 — `(\epsilon, \delta)`-DP Folder Personalization:** When a user moves or tags files on a shared family/SMB NAS, clip the `24-d` feature vector (`||x||_2 <= C`), calibrate Gaussian sufficient-statistic noise via the Rényi DP accountant, and update closed-form Sherman-Morrison-Woodbury routing weights (`0` raw filenames shared across accounts).
6. **Step 6 — Mandatory Outbound Share Gate:** Before generating any external summary or share caption, pass text through `redact` and verify `safe_for_external_share == true`.

---

## 5. Completion Criteria, Structured Error Codes & Failure/Fallback Handling

A task is complete only when CLI exit status is `0`, JSON output parses cleanly, bitemporal `revision_num` or `results` match the requested time horizon, and any external-facing text reports `safe_for_external_share: true`.

| Error Code | Trigger Condition | Deterministic Agent Fallback |
| :--- | :--- | :--- |
| `ERR_OUTSIDE_VOLUME_ROOT` | Path resolves outside `UGOS_VOLUME_ROOT` or symlink escapes share | Abort immediately; report permission boundary refusal to user |
| `ERR_EMBED_ENDPOINT_OFFLINE` | `LOCAL_EMBED_ENDPOINT` unreachable or busy on NAS | Degrade gracefully to `SQLite FTS5 BM25` + deterministic local hash projection; queue background re-projection |
| `ERR_SQLITE_LOCKED_TIMEOUT` | Concurrent NAS writer holds WAL lock past timeout | Retry up to bounded `NodeGrid` backoff; never corrupt or truncate WAL |
| `ERR_UNFITTED_PROCRUSTES_BRIDGE` | New local encoder activated before `96`-anchor calibration | Run local anchor calibration batch before switching query bridge key |
| `ERR_PII_REDACTION_REQUIRED` | Unredacted text requested for external share preview | Block share preview; re-run `redact` and warn user to inspect raster images manually |
| `ERR_DP_BUDGET_EXHAUSTED` | Account exceeds configured `dp_epsilon` privacy budget | Freeze further cross-account Woodbury updates and serve existing frozen weights |

---

## 6. Explicit Disclosures

Full verification tables and Round-2 test plans appear in [references/test-cases-and-disclosures.md](references/test-cases-and-disclosures.md).

1. **Third-Party Components & Open-Source Licenses:**
   - **Python Standard Library (`sqlite3` WAL + FTS5, `http.server`, `socketserver`, `ast`, `zipfile`):** PSF License v2 (`https://docs.python.org/3/license.html`).
   - **NumPy (`>=1.24`):** BSD-3-Clause License (`https://numpy.org/doc/stable/license.html`) — used in the optional Python reference CLI for compact SVD (`np.linalg.svd`) and float32 vector algebra.
   - **Pytest (`>=7.4`, dev/test only):** MIT License (`https://docs.pytest.org/en/stable/license.html`).
2. **Principal Functionality Developed During the Competition & Honest Status:**
   - Built during the competition (`MIT` open-source): Uliya Skill Markdown specification (`SKILL.md` + `references/*.md`), `NodeGrid` declarative settings schema, bitemporal `SQLite WAL + FTS5` + `24-d` Orthogonal Procrustes engine, in-memory `256 B` WebAssembly triage cartridge synthesizer, `(\epsilon, \delta)`-DP Recursive Woodbury personalizer, outbound PII redactor, loopback CLI/IPC reference prototype, and light-mode browser studio.
   - **Honest Hardware Status:** All current benchmarks (`96 B/file` = `-97.66%` vector RAM vs `1024-d`, `1.0000` `Recall@5` on a `48`-item simulated tri-modal corpus built from made-up vectors on `24` clean topic directions with random-matrix encoders and no live embedding model, `0.047 us` Node V8 WASM triage, and `75.00%` 4-account simulated DP folder-routing accuracy against `25.00%` 4-folder chance and `7.29%` blank identity-matrix start) were measured locally on x86_64 Linux (`19/19` passing `pytest` tests). Physical `UGREEN NASync iDX6011 Pro` hardware testing, live `UGOS Pro` AI Album hooks, and million-file RAID I/O benchmarks have **not** occurred yet and are scheduled for Round 2.
3. **AI Tools Used:**
   - AI coding and documentation assistance (Google Gemini / Antigravity agentic IDE workflow) was used during competition development for code scaffolding, test generation, and documentation formatting; every algorithm, mathematical invariant, word-count check, and automated test was executed and verified deterministically on Linux.
