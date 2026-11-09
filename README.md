# UGOS VaultLoom (`v1.0.0`)

**Zero-Cloud Bitemporal `SQLite WAL + FTS5`, `24-d` Orthogonal `Procrustes` Subspace (`-97.66%` Vector RAM) & `(epsilon, delta)`-DP Woodbury Personalization Skill for `UGOS Pro` AI NAS**

[![License: MIT](https://img.shields.io/badge/License-MIT-141413.svg)](LICENSE)
[![Python 3.10+](https://img.shields.io/badge/Python-3.10%2B-0f766e.svg)](pyproject.toml)
[![Target OS](https://img.shields.io/badge/Target-UGOS%20Pro%20Linux%20(x86__64%20%2F%20ARM64)-1d4ed8.svg)](skill_manifest.json)

Home, creator-studio, and SMB NAS appliances face three painful bottlenecks when running local AI search and organization:
1. **Vector RAM Bloat:** Storing standard `1024-d` float32 embeddings (`4,096 B/file`) consumes **`4.09 GB` of RAM per `1,000,000` files** — starving ZFS/Btrfs cache, Docker containers, and media transcoding — and upgrading the local embedding model forces days of full-disk re-indexing.
2. **Stale-Version Hallucinations:** Overwriting index rows destroys document revision history, causing local assistants to surface obsolete configs, drafts, or tax spreadsheets.
3. **Multi-Account Privacy Leakage:** Shared family and SMB NAS boxes lack mathematical isolation when learning folder/tag preferences across accounts or sanitizing outbound share links.

**UGOS VaultLoom** is a drop-in, zero-cloud Debian Linux skill engineered for **UGREEN `UGOS Pro` (`NASync iDX6011 Pro` & `DXP` series)** that eliminates all three bottlenecks.

---

## Key Capabilities & Measured Benchmarks

| Capability | Architectural Primitive | Measured Result | Test Condition |
| :--- | :--- | :--- | :--- |
| **Ultra-Compact NAS Vector Index** | `24-d` Orthogonal `Procrustes` float32 subspace | **`96 B/file` (`-97.66%` RAM)** | **`96.0 MB`** vs `4,096.0 MB` (`1024-d`) per `1,000,000` files |
| **Bitemporal Hybrid Search** | `SQLite WAL + FTS5 BM25` + `24-d` cosine `RRF` | **`1.0000` `Recall@5`** | 16 topics $\times$ 3 modalities (`text`, `code`, `media_exif`), `0` stale leaks |
| **Zero-Reindex Model Upgrade** | SVD Orthogonal `Procrustes` query bridge | **`1.0000` `Recall@5` (`0` re-indexed)** | `Encoder v1 (1024-d)` $\to$ `Encoder v2 (1024-d)` via 96 anchors |
| **Sub-Microsecond Local Triage** | In-memory **`256 B` `.wasm`** + `C99` + `#![no_std]` `Rust` | **`0.047 us` (WASM) / `0.0044 us` (Rust)** | 4-way IEEE-754 parity (`0.0` max logit diff across Python/WASM/C99/Rust) |
| **Private Multi-User Learning** | `(\epsilon, \delta)`-DP Recursive Woodbury solver | **`+67.71%` accuracy uplift** | 4 NAS accounts ($\epsilon=2.0, \delta=10^{-5}$, RDP $\epsilon=1.4086$, `0` filenames leaked) |
| **Safe Outbound Share Gate** | Deterministic local PII & host sanitizer | **`100%` token stripping** | Strips SSNs, payment cards, IPv4 hosts, phone numbers & account refs locally |

---

## Quickstart on `UGOS Pro` / Any Linux Host

```bash
# 1. Run the standalone Linux skill installer & end-to-end self-test
./install_and_selftest.sh

# 2. Run the full 18-test pytest conformance & cross-runtime parity suite
pytest -v

# 3. Use the UGOS VaultLoom CLI directly
./bin/ugos-vaultloom-cli healthcheck
./bin/ugos-vaultloom-cli benchmark

# 4. Open the Paper & Ink Interactive NAS Studio in any browser
python3 -m http.server 8090
# Open http://localhost:8090/web/ugos-nas-vaultloom.html
```

---

## Repository & Skill Structure

- `skill_manifest.json` — Standard `UGOS Pro` Linux skill manifest (`zero_cloud_loopback_only`, CLI + loopback HTTP / Unix-socket IPC).
- `install_and_selftest.sh` — Self-contained POSIX/bash verification script for pre-test archive validation.
- `config/subspace_vault_grid.json` — `NodeGrid` configuration regimes (`home_family_nas_regime`, `studio_creator_pro_nas_regime`, `smb_team_compliance_nas_regime`), `ParameterBounds`, and `256 B` WASM triage weights.
- `src/bitemporal_subspace_vault.py` — `SQLite WAL + FTS5` bitemporal store (`valid_from`, `valid_to`, `recorded_at`), `24-d` Orthogonal `Procrustes` bridge, hybrid `RRF` search, and deterministic PII redactor.
- `src/dp_woodbury_personalizer.py` — `(\epsilon, \delta)`-DP Sherman-Morrison-Woodbury multi-account personalizer and `256 B` `.wasm` / `C99` / `#![no_std]` `Rust` local file-triage micro-cartridge compiler.
- `src/local_skill_service.py` & `bin/ugos-vaultloom-cli` — Loopback `127.0.0.1` HTTP + Unix-domain socket service and CLI entrypoint.
- `web/ugos-nas-vaultloom.html` — Light-mode Paper & Ink (`#f5f2ea`) interactive NAS studio running real in-browser `256 B` `WebAssembly.instantiate` file triage.
- `tests/test_ugos_vaultloom.py` — 18 automated behavioral, mathematical, and AST conformance tests.

## Release Assets (`v1.0.0`)

Both Round-1 deliverables are attached to [GitHub Release `v1.0.0`](https://github.com/aidonerightcorp/ugos-vaultloom/releases/tag/v1.0.0):
1. `ugos-vaultloom-skill-v1.0.0.zip` — Self-contained Linux pre-test skill archive (`./install_and_selftest.sh` -> `PASS`).
2. `ugos_vaultloom_proposal.pdf` — Camera-ready 6-page Paper & Ink Round-1 technical proposal & Round-2 `iDX6011 Pro` hardware validation plan.

## License

MIT License — see [LICENSE](LICENSE).
