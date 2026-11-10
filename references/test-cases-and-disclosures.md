# Verification Status, Finalist Test Cases & Mandatory Disclosures

This document records honest current verification boundaries, Round-2 hardware test methodology for `UGREEN NASync iDX6011 Pro`, and mandatory third-party/AI disclosures referenced in [SKILL.md](../SKILL.md).

---

## 1. Honest Current Development & Verification Status (Round 1)

### 1.1 Built & Unit-Verified Locally Today (x86_64 Linux, No Physical NAS Hardware Yet)
All core algorithms and reference CLI workflows are implemented and verified locally via `19` automated `pytest` tests (`tests/test_ugos_vaultloom.py`):
- **Uliya Skill Package (`SKILL.md` + `references/*.md`):** Validated for frontmatter schema, placeholder hygiene, `< 1 MB` per-file limits, and Markdown-only archive structure.
- **24-d Orthogonal Procrustes Subspace (`src/bitemporal_subspace_vault.py`):** Verified exact `96 B/file` float32 storage (`-97.66%` vector RAM vs `4,096 B/file` `1024-d` float32, i.e., `96.0 MB` vs `4,096.0 MB` for `1,000,000` vectors) and orthonormality error `<= 1e-5`.
- **Simulated Tri-Modal Bitemporal Benchmark:** Evaluated across `16` controlled topics $\times$ `3` modalities (`text`, `code`, `media_exif` = `48` active items + `16` superseded drafts) in `SQLite WAL + FTS5`, achieving `1.0000` `Recall@5`, `0` stale-revision leaks on active queries, `1.0000` `as_of` historical recall, and `1.0000` `Recall@5` after swapping simulated `1024-d` `Encoder v1 -> Encoder v2` using `96` calibration anchors (`0` stored items re-indexed).
- **In-Memory `256 B` Local Triage Cartridge (`src/dp_woodbury_personalizer.py`):** Synthesizes a `256 B` IEEE-754 WebAssembly v1 binary in memory (`0.047 us/call` in Node V8; bit-identical `0.0` max logit diff against `C99` and `#![no_std]` Rust).
- **Simulated 4-Account `(\epsilon, \delta)`-DP Woodbury Benchmark:** Achieves `75.00%` folder-routing accuracy vs `7.29%` unpersonalized baseline (`+67.71%` uplift at `epsilon=2.0, delta=1e-5`, Rényi composed `epsilon=1.4086`) with `0` raw filenames shared.

### 1.2 Pending Physical Hardware Validation in Round 2 (`NASync iDX6011 Pro`)
The following items have **not** yet been tested on physical UGREEN hardware and will be validated in Round 2 upon remote/physical access to `NASync iDX6011 Pro`:
- Live `UGOS Pro` filesystem event hooks (`inotify` / File Manager / AI Album metadata triggers).
- Real local text/vision model inference latency on `iDX6011 Pro` Intel iGPU / NPU.
- Multi-hundred-thousand to million-file `SQLite WAL + FTS5` + `96 B/file` mmap latency on physical NVMe cache + RAID pools.
- Live multi-account `UGOS Pro` SMB/POSIX permission enforcement end to end.

---

## 2. Finalist Round-2 Hardware Testing Methodology (2 Core Cases + 1 Edge Case)

1. **Core Test Case 1 — Multi-Modal Corpus Indexing & Resident RAM Ceiling (`100,000` Real Files):**
   - **Setup:** Load `100,000` mixed Markdown/PDF notes, source code files, and `.heic`/`.jpg` EXIF assets onto a `UGOS Pro` shared volume on `NASync iDX6011 Pro`.
   - **Pass Criteria:** Resident RSS of the VaultLoom service stays `< 120 MB`, hybrid bitemporal `RRF` p95 query latency stays `< 25 ms`, and active queries return `0` superseded revisions after `1,000` simulated file edits.
2. **Core Test Case 2 — Zero-Reindex Local Encoder Upgrade:**
   - **Setup:** Index the corpus with local `Encoder A`, then upgrade `LOCAL_EMBED_ENDPOINT` to `Encoder B` and run `96`-anchor Procrustes alignment.
   - **Pass Criteria:** Calibration completes in `< 1 s` on CPU, `0` stored SQLite subspace blobs are rewritten, and post-upgrade `Recall@5` retains `>= 95%` of full re-index quality.
3. **Edge Case — Concurrent SMB Edits + Corrupted EXIF + Unredacted Share Attempt:**
   - **Setup:** Trigger simultaneous edits from two `UGOS Pro` accounts alongside truncated EXIF headers and an outbound share note containing dummy SSN/IPv4/account strings.
   - **Pass Criteria:** `SQLite WAL` serializes revisions cleanly (`0` DB corruption), malformed EXIF degrades gracefully to filename `FTS5` indexing, and the outbound share gate strips `100%` of structured PII tokens before output.

---

## 3. Third-Party Licenses, Competition Scope & AI Tools Disclosure

| Component | Version | License | Source & Usage |
| :--- | :--- | :--- | :--- |
| Python Standard Library | `3.10+` | PSF-2.0 | `sqlite3` (WAL + FTS5), `http.server`, `socketserver`, `ast`, `re` (`https://www.python.org`) |
| NumPy | `>=1.24` | BSD-3-Clause | SVD Procrustes alignment & float32 array ops in optional Python CLI (`https://numpy.org`) |
| Pytest | `>=7.4` | MIT | Local automated unit/conformance testing only (`https://pytest.org`) |

- **Competition Originality Disclosure:** All `ugos-vaultloom` skill definitions, `NodeGrid` schemas, bitemporal `24-d` Procrustes vault logic, `256 B` WASM cartridge generator, DP-Woodbury personalizer, and interactive studio were conceived and authored during the competition window under the MIT License (`aidonerightcorp`).
- **AI Tools Disclosure:** Google Gemini / Antigravity AI coding assistant was used to accelerate code drafting, test authoring, and documentation formatting, with deterministic local execution and human engineering review of all claims and benchmarks.
