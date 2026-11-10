# CLI & Loopback Service Reference (`ugos-vaultloom-cli`)

This reference defines the exact local command-line and loopback IPC contracts orchestrated by [SKILL.md](../SKILL.md) on `UGOS Pro` (`Debian Linux 12+`, `x86_64` / `ARM64`).

---

## 1. Global Flags & Exit Codes

```bash
ugos-vaultloom-cli [--db <SQLITE_PATH>] [--grid <GRID_JSON_PATH>] [--regime <REGIME_ID>] <subcommand> [options]
```

- `--db`: Path to local SQLite WAL + FTS5 database file (placeholder: `/volume1/@appdata/ugos-vaultloom/vault.sqlite`).
- `--grid`: Path to `NodeGrid` configuration file (default: `./config/subspace_vault_grid.json`).
- `--regime`: Active NAS workload regime:
  - `home_family_nas_regime` (`24-d`, `top_k=5`, `rrf_k=60`, `w_sem=0.65`, `dp_epsilon=2.0`, `dp_delta=1e-5`)
  - `studio_creator_pro_nas_regime` (`24-d`, `top_k=8`, `rrf_k=40`, `w_sem=0.75`, `dp_epsilon=4.0`, `dp_delta=1e-5`)
  - `smb_team_compliance_nas_regime` (`24-d`, `top_k=5`, `rrf_k=60`, `w_sem=0.55`, `dp_epsilon=1.0`, `dp_delta=1e-6`)

| Exit Code | Meaning |
| :--- | :--- |
| `0` | Command succeeded; deterministic JSON written to `stdout`. |
| `2` | Invalid input, missing argument, or policy/path refusal (`ERR_OUTSIDE_VOLUME_ROOT`). |
| `3` | Local storage lock or dependency degraded (`ERR_SQLITE_LOCKED_TIMEOUT`, `ERR_EMBED_ENDPOINT_OFFLINE`). |

---

## 2. Subcommand Contracts

### 2.1 `healthcheck`
Verifies `SQLite WAL + FTS5` readiness, vector byte footprint, and `256 B` local triage cartridge synthesis.

```json
{
  "status": "healthy",
  "skill": "ugos-vaultloom",
  "network_egress": "zero_cloud_loopback_only",
  "triage_wasm_bytes": 256,
  "subspace_bytes_per_file": 96,
  "ram_reduction_pct": 97.66
}
```

### 2.2 `index`
Inserts or supersedes a bitemporal file revision.

- Required flags: `--path <LOGICAL_PATH>`, `--text <EXTRACTED_CONTENT>`
- Optional flags: `--modality <text|code|media_exif>` (default `text`), `--valid-from <EPOCH_INT>`, `--recorded-at <EPOCH_INT>`

```json
{
  "record_pk": 2,
  "logical_path": "/volume1/<SHARED_FOLDER_PLACEHOLDER>/network_plan.md",
  "revision_num": 2,
  "subspace_bytes": 96
}
```

### 2.3 `search`
Executes hybrid `SQLite FTS5 BM25` + `24-d` Procrustes cosine Reciprocal Rank Fusion (`RRF`).

- Required flag: `--query <SEARCH_STRING>`
- Optional flag: `--as-of <EPOCH_INT>` (omitted = active current revisions `valid_to IS NULL`; provided = point-in-time historical snapshot `valid_from <= as_of < valid_to`)

```json
{
  "query": "isolated vlan configuration",
  "as_of": null,
  "count": 1,
  "results": [
    {
      "record_pk": 2,
      "logical_path": "/volume1/<SHARED_FOLDER_PLACEHOLDER>/network_plan.md",
      "modality": "text",
      "revision_num": 2,
      "content_text": "current_vlan_40_subnet isolated NAS configuration",
      "valid_from": 200,
      "valid_to": null,
      "cosine_24d": 0.994102,
      "lexical_rank": 1,
      "rrf_score": 0.016393
    }
  ]
}
```

### 2.4 `triage`
Evaluates normalized 3-feature file ratios (`<TEXT_RATIO>,<EXIF_RATIO>,<CODE_RATIO>` in `[0.0, 1.0]`) through the local `256 B` linear-ReLU cartridge.

```json
{
  "category_id": 2,
  "category": "media_gallery",
  "logits": [-0.051, 0.042, 0.918, -0.019],
  "wasm_bytes": 256
}
```

### 2.5 `redact`
Applies deterministic local regex sanitization prior to external link or note sharing.

```json
{
  "redacted_text": "Host [REDACTED-IPV4] account [REDACTED-ACCOUNT]",
  "redaction_counts": {
    "ipv4_host": 1,
    "account_ref": 1
  },
  "total_redactions": 2,
  "safe_for_external_share": true
}
```

---

## 3. Loopback Daemon & `AF_UNIX` IPC Contracts

For low-latency desktop widget or container calls on `UGOS Pro` without subprocess spawn overhead, `ugos-vaultloom-cli serve-http --port <LOOPBACK_PORT>` binds strictly to `127.0.0.1` (and `AF_UNIX` newline-delimited JSON on `VAULTLOOM_SOCKET_PATH`) exposing `/v1/health`, `/v1/index`, `/v1/search`, `/v1/triage`, and `/v1/redact`.
