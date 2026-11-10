# Expert Agent Orchestration & Failure Handling (`ugos-vaultloom`)

This document specifies the decision rules, multi-step orchestration flows, and failure recovery behaviors required by [SKILL.md](../SKILL.md).

---

## 1. End-to-End Orchestration Flows

### Flow A — New or Modified NAS File Intake
1. Receive file event or user indexing request under `UGOS_VOLUME_ROOT`.
2. Resolve canonical path (`realpath`) and verify it resides strictly inside the authorized `UGOS_VOLUME_ROOT` share. If not, emit `ERR_OUTSIDE_VOLUME_ROOT` and stop.
3. Compute lightweight local modality ratios (`text_ratio`, `exif_ratio`, `code_ratio`) and invoke `triage` (`256 B` cartridge) to assign default organizational metadata.
4. Obtain raw embedding from `LOCAL_EMBED_ENDPOINT` (`127.0.0.1`) if configured, project via `OrthogonalProcrustesBridge` (`1024-d -> 24-d` float32, `96 B`), and invoke `index` with `--valid-from <EVENT_EPOCH>`.
5. Confirm `revision_num >= 1` and `subspace_bytes == 96`.

### Flow B — Current vs. Historical Time-Travel Search
1. Parse user intent for temporal qualifiers:
   - **Current truth** (e.g., *"Find my current UPS shutdown policy"*): invoke `search --query "..."` with `--as-of` omitted (`valid_to IS NULL`).
   - **Historical audit** (e.g., *"What was our UPS threshold before last week's edit?"*): convert target date to Unix epoch seconds and invoke `search --query "..." --as-of <EPOCH>`.
2. Cite both `logical_path` and `revision_num` in the response so the user always sees exact provenance.

### Flow C — Zero-Reindex Local Embedding Model Upgrade
1. When `UGOS Pro` updates a local text/vision encoder (`Encoder v1 -> Encoder v2`), select `N = 96` representative anchor items already present in the vault.
2. Embed only those `96` anchors with `Encoder v2` to form `X_v2` (`96 x d_raw`) against stored `24-d` subspace targets `Z` (`96 x 24`).
3. Solve compact SVD `U, _, V^T = svd(X_v2^T Z)` and register `Q_v2 = U V^T` (`||Q_v2^T Q_v2 - I_24||_F <= 1e-5`).
4. Route future queries through `Q_v2` with **`0` stored NAS files re-indexed**.

### Flow D — Shared-NAS `(\epsilon, \delta)`-DP Folder Personalization
1. When user `<LOCAL_UGOS_USER_PLACEHOLDER>` files or re-tags items, clip each `24-d` vector to L2 norm `clip_norm` (`1.0`).
2. Calibrate Gaussian noise scales `(\sigma_gram, \sigma_rhs)` under the active regime's `(dp_epsilon, dp_delta)` budget using the Rényi DP accountant.
3. Apply PSD-projected rank-1 Sherman-Morrison-Woodbury updates to the shared routing prior without storing or transmitting raw filenames across accounts.

---

## 2. Deterministic Failure & Fallback Matrix

| Failure Scenario | Detection Signal | Required Recovery Action |
| :--- | :--- | :--- |
| Local embedding model offline or GPU/NPU saturated | `ERR_EMBED_ENDPOINT_OFFLINE` or HTTP timeout on `127.0.0.1` | Continue serving exact `SQLite FTS5 BM25` lexical results immediately; mark new revisions for deferred dense projection once idle |
| Malformed binary / corrupted EXIF header | Local parser raises decode warning | Index filename + path tokens in `FTS5` with empty EXIF body; never crash batch intake |
| Concurrent SMB file writes | `sqlite3.OperationalError` busy lock | Respect `SQLite WAL` busy timeout and serialized mutex lock; retry idempotently |
| Unredacted sensitive tokens in outbound share note | `redact` reports `total_redactions > 0` | Replace raw text with `redacted_text` before presenting share snippet; warn user that raster images/PDF scans require separate visual/OCR review |
| Privacy budget exhausted on shared SMB regime | Composed Rényi `epsilon >= target_epsilon` | Stop accumulating new noisy sufficient statistics for the epoch; keep inference active on frozen weights |
