# UGOS VaultLoom (`v1.1.0`)

**Zero-Cloud Bitemporal `SQLite WAL + FTS5`, `24-d` Orthogonal `Procrustes` Subspace (`-97.66%` Vector RAM) & `(epsilon, delta)`-DP Woodbury Personalization Skill for `UGOS Pro` AI NAS**

[![License: MIT](https://img.shields.io/badge/License-MIT-141413.svg)](LICENSE)
[![Uliya Skill](https://img.shields.io/badge/Uliya_Skill-Markdown_Standard_v1.1.0-0f766e.svg)](SKILL.md)
[![Target OS](https://img.shields.io/badge/Target-UGOS%20Pro%20Linux%20(x86__64%20%2F%20ARM64)-1d4ed8.svg)](skill_manifest.json)

> **UGREEN AI NAS 2026 Challenge — Round-1 Submission (`v1.1.0`)**
> - **Official Round-1 Deadline:** **Sun Nov 15, 2026, 11:45 PM PT**
> - **Primary Deliverable 1 (`ugos_vaultloom_round1_proposal_500w.pdf`):** Short Project Proposal answering all `10` required substantive areas in strictly **`< 500` English words** plus a separated `Excluded Administrative & License Disclosures Appendix`.
> - **Primary Deliverable 2 (`ugos-vaultloom-uliya-skill-v1.1.0.zip`):** Strictly compliant **Uliya Skill Development Standard** Markdown-only skill package (`SKILL.md` + `references/*.md`, `< 10 MB` total, `< 1 MB` per file, configuration placeholders only, `0` executable binaries or unrequested scripts inside the ZIP).
> - **Repository Local Reference CLI Prototype (`src/`, `bin/ugos-vaultloom-cli`, `tests/`):** Runnable MIT-licensed local Linux reference CLI implementation and `19/19` automated `pytest` verification suite accompanying the Uliya Markdown skill specification.

Home, creator-studio, and SMB NAS appliances face three painful bottlenecks when running local AI search and organization:
1. **Vector RAM Bloat & Re-Indexing Lock-In:** Storing standard `1024-d` float32 embeddings (`4,096 B/file`) consumes **`4.09 GB` of vector RAM per `1,000,000` files** — starving ZFS/Btrfs cache, Docker containers, and media transcoding — while upgrading a local embedding model normally forces days of full-disk re-indexing.
2. **Stale-Version Hallucinations:** Overwriting flat index rows destroys document revision history, causing local assistants to surface obsolete configs, drafts, or tax spreadsheets.
3. **Multi-Account Privacy Leakage:** Shared family and SMB NAS boxes lack mathematical isolation when learning folder/tag preferences across accounts or sanitizing outbound share links.

**UGOS VaultLoom** is a zero-cloud `UGOS Pro` skill (`SKILL.md`) paired with a runnable Debian Linux reference CLI prototype engineered for **UGREEN `UGOS Pro` (`NASync iDX6011 Pro` & `DXP` series)** that eliminates all three bottlenecks.

---

## Local Linux Unit Benchmarks & Honest Hardware Status

> **Honest Status Disclosure:** Every metric below was measured deterministically on local `x86_64` Linux (`19/19` passing `pytest` tests in `tests/test_ugos_vaultloom.py`). Physical **`UGREEN NASync iDX6011 Pro`** hardware testing, live `UGOS Pro` AI Album hooks, and million-file RAID/NVMe I/O benchmarks have **not** occurred yet and are scheduled for Round 2 upon finalist hardware access.

| Capability | Architectural Primitive | Local Linux Result | Exact Local Test Condition |
| :--- | :--- | :--- | :--- |
| **Ultra-Compact NAS Vector Index** | `24-d` Orthogonal `Procrustes` float32 subspace | **`96 B/file` (`-97.66%` RAM)** | Exact byte footprint: **`96.0 MB`** vs `4,096.0 MB` (`1024-d` float32) per `1,000,000` vectors |
| **Bitemporal Hybrid Search** | `SQLite WAL + FTS5 BM25` + `24-d` cosine `RRF` | **`1.0000` `Recall@5`** | Simulated corpus: `16` topics $\times$ `3` modalities (`48` active items + `16` superseded drafts), `0` stale leaks |
| **Zero-Reindex Model Upgrade** | SVD Orthogonal `Procrustes` query bridge | **`1.0000` `Recall@5` (`0` re-indexed)** | Simulated `Encoder v1 (1024-d)` $\to$ `Encoder v2 (1024-d)` swap via `96` calibration anchors |
| **Sub-Microsecond Local Triage** | In-memory **`256 B` `.wasm`** + `C99` + `#![no_std]` `Rust` | **`0.047 us` (WASM) / `0.0044 us` (Rust)** | Local `x86_64` 4-way IEEE-754 parity (`0.0` max logit diff across Python/Node V8/`gcc -O3`/`rustc`) |
| **Private Multi-User Learning** | `(\epsilon, \delta)`-DP Recursive Woodbury solver | **`+67.71%` accuracy uplift** | Simulated `4`-account NAS workload (`75.00%` vs `7.29%`, $\epsilon=2.0, \delta=10^{-5}$, RDP $\epsilon=1.4086$, `0` filenames leaked) |
| **Safe Outbound Share Gate** | Deterministic local PII & host sanitizer | **`100%` structured token stripping** | Local UTF-8 test strings: SSNs, payment cards, IPv4 hosts, phone numbers & `ACCT-*` refs |

---

## Primary Uliya Skill Package Structure (`SKILL.md` + `references/`)

- [`SKILL.md`](SKILL.md) — Root Uliya Skill specification (`name: ugos-vaultloom`, YAML frontmatter `< 1,024` chars, configuration placeholders, CLI contracts, 6-step orchestration loop, structured error codes, and explicit license/AI disclosures).
- [`references/cli-reference.md`](references/cli-reference.md) — Exact JSON stdout contracts and exit codes for `healthcheck`, `triage`, `index`, `search`, `redact`, and loopback `127.0.0.1` / `AF_UNIX` IPC.
- [`references/orchestration-and-failure-modes.md`](references/orchestration-and-failure-modes.md) — Multi-step agent orchestration flows and deterministic failure/fallback matrix.
- [`references/ugos-pro-permissions-and-privacy.md`](references/ugos-pro-permissions-and-privacy.md) — `UGOS Pro` shared-folder ACL scoping, `zero_cloud_loopback_only` isolation, `(\epsilon, \delta)`-DP bounds, and raster-image OCR caveats.
- [`references/test-cases-and-disclosures.md`](references/test-cases-and-disclosures.md) — Honest Round-1 local verification vs. Round-2 `NASync iDX6011 Pro` hardware test plan (`2` core cases + `1` edge case) and third-party license table.

---

## Local Reference CLI Prototype Quickstart (Linux)

```bash
# 1. Run the standalone Linux reference prototype self-test
./install_and_selftest.sh

# 2. Run the full 19-test pytest conformance, Uliya standard & cross-runtime parity suite
pytest -v

# 3. Exercise the local reference CLI directly
./bin/ugos-vaultloom-cli healthcheck
./bin/ugos-vaultloom-cli benchmark

# 4. Open the Paper & Ink Interactive NAS Studio in any browser
python3 -m http.server 8090
# Open http://localhost:8090/web/ugos-nas-vaultloom.html
```

---

## Release Assets (`v1.1.0`)

Both Round-1 primary submission deliverables are attached to [GitHub Release `v1.1.0`](https://github.com/aidonerightcorp/ugos-vaultloom/releases/tag/v1.1.0):
1. `ugos-vaultloom-uliya-skill-v1.1.0.zip` — Markdown-only Uliya Skill package (`SKILL.md` + `references/*.md`, `< 10 MB` total, `< 1 MB` per file, `0` binaries/scripts).
2. `ugos_vaultloom_round1_proposal_500w.pdf` — Strict `< 500`-word Paper & Ink Round-1 Short Project Proposal covering all `10` required substantive areas + Excluded Administrative & License Disclosures Appendix.

## License

MIT License — see [LICENSE](LICENSE).
