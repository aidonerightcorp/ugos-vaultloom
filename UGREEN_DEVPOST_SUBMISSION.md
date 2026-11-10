# UGREEN AI NAS Developer Challenge 2026 — Ready-to-Paste Devpost Entry (`UGOS VaultLoom v1.1.0`)

- **Official Round-1 Submission Deadline:** **Sun Nov 15, 2026, 11:45 PM PT**
- **Repository (`MIT`):** `https://github.com/aidonerightcorp/ugos-vaultloom` (`Release v1.1.0`)

## Project Title
**UGOS VaultLoom — Zero-Cloud Bitemporal `24-d` Procrustes Brain & Privacy Skill for UGREEN AI NAS**

## Tagline
Cut NAS vector RAM by **`97.66%` (`96 B/file`)** on `UGOS Pro` with bitemporal `SQLite FTS5` search, zero-reindex local model upgrades, `(epsilon, delta)`-DP multi-user folder routing, and outbound PII share redaction.

---

## Problem Statement: Why Current "AI on NAS" Breaks Down
Putting AI on a private NAS promises data ownership, yet standard local RAG and vector-index stacks fail home, creator-studio, and SMB `NASync` owners in three ways:
1. **RAM Exhaustion & Re-Indexing Lock-In:** Standard `1024-d` float32 embeddings consume `4,096 B/file` (**`4.09 GB` vector RAM per `1,000,000` files**), competing directly with `UGOS Pro` filesystem cache, Docker containers, and 4K media workflows. Worse, upgrading a local embedding model normally forces multi-day full-disk re-indexing.
2. **Stale-File Confusion:** Overwriting flat vector rows destroys document revision history, causing local assistants to mix superseded configs, old drafts, or prior spreadsheets with active files.
3. **Shared-NAS Privacy Exposure:** Multi-account family and SMB NAS volumes lack mathematical isolation when learning folder/tag routing preferences across users — and external share captions risk leaking SSNs, IPv4 hosts, or account tokens.

---

## Proposed Solution: `UGOS VaultLoom` (`v1.1.0`)
**UGOS VaultLoom** is an Uliya Skill package (`SKILL.md` + `references/*.md`) backed by an open-source Debian Linux reference CLI prototype engineered for **UGREEN `UGOS Pro` (`NASync iDX6011 Pro`)**:

1. **`24-d` Orthogonal `Procrustes` Cross-Modal Subspace (`96 B/file`, `-97.66%` Vector RAM):**
   - Projects `1024-d` text, code, and photo/EXIF embeddings into a shared orthonormal `24-d` float32 subspace via compact SVD (`Q^T Q = I_24`), shrinking storage from `4,096 B/file` to **`96 B/file`** (`96.0 MB` vs `4,096.0 MB` per `1,000,000` vectors).
   - **Zero-Reindex Encoder Upgrades:** Upgrading a local encoder (`v1 -> v2`) fits a `96`-anchor Procrustes bridge in milliseconds with **`0` stored NAS files re-indexed** (`1.0000` `Recall@5` on our `48`-item simulated tri-modal benchmark).
2. **Bitemporal `SQLite WAL + FTS5` Hybrid Index (`valid_from`, `valid_to`, `recorded_at`):**
   - Fuses `FTS5 BM25` lexical ranks with `24-d` Procrustes cosine similarity via Reciprocal Rank Fusion (`RRF`), returning **`0` stale revisions** on active queries while supporting exact `as_of` point-in-time historical queries.
3. **`256 B` Local File-Triage Micro-Cartridge + `(epsilon, delta)`-DP Woodbury Routing + PII Share Gate:**
   - Synthesizes an in-memory `256 B` IEEE-754 WebAssembly v1 file-triage module (`0.047 us/call` locally in Node V8), learns shared-NAS folder preferences via Rényi-accounted `(epsilon, delta)`-DP Sherman-Morrison-Woodbury updates (`+67.71%` routing lift across a `4`-account local simulation with `0` filenames leaked), and strips structured PII tokens before external sharing.

---

## Honest Development Status (Round 1 Local vs. Round 2 Physical Hardware)
- **Built & Tested Locally Today (`x86_64` Linux, `19/19` `pytest` passing):** Complete Uliya Markdown Skill (`SKILL.md` + 4 `references/*.md` guides), local reference CLI + loopback `127.0.0.1` / `AF_UNIX` service, `NodeGrid` configuration governance, bitemporal `SQLite WAL + FTS5` + `24-d` Procrustes engine, `256 B` WASM triage synthesizer, DP-Woodbury personalizer, PII redactor, and interactive Paper & Ink browser studio (`web/ugos-nas-vaultloom.html`).
- **Pending Physical UGREEN Hardware Testing in Round 2 (`NASync iDX6011 Pro`):** Physical UGREEN NAS testing has **not** occurred yet. In Round 2 we will validate live `UGOS Pro` File Manager / AI Album event triggers, local Intel iGPU/NPU encoder throughput, multi-user SMB ACL boundaries, and `100k–1M` file NVMe + RAID latency on a physical `NASync iDX6011 Pro`.

---

## Round-1 Submission Deliverables (`Release v1.1.0`)
1. **Short Project Proposal PDF (`ugos_vaultloom_round1_proposal_500w.pdf`):** Answers all `10` required Round-1 substantive areas in strictly **`< 500` English words** (`< 1 MB`, light Paper & Ink layout), followed by a clearly separated `Excluded Administrative & License Disclosures Appendix`.
2. **Uliya Pre-Test Skill Package (`ugos-vaultloom-uliya-skill-v1.1.0.zip`):** Strictly compliant **Markdown-only** Uliya Skill archive (`SKILL.md` + `references/cli-reference.md` + `references/orchestration-and-failure-modes.md` + `references/ugos-pro-permissions-and-privacy.md` + `references/test-cases-and-disclosures.md`, `< 10 MB` total, `< 1 MB` per file, configuration placeholders only, `0` executable binaries or unrequested scripts).
3. **Optional Companion Local Reference CLI Repository (`https://github.com/aidonerightcorp/ugos-vaultloom`):** Full MIT Python/SQLite/WASM reference prototype (`19/19` automated `pytest` tests) and interactive browser studio.
