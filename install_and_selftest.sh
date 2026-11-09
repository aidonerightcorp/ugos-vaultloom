#!/usr/bin/env bash
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
CLI_BIN="${SCRIPT_DIR}/bin/ugos-vaultloom-cli"

echo "[1/5] Checking Python 3.10+ & SQLite FTS5 availability on Linux..."
python3 -c 'import sqlite3, sys, numpy; assert sys.version_info >= (3, 10); con = sqlite3.connect(":memory:"); con.execute("CREATE VIRTUAL TABLE t USING fts5(body);"); con.close(); print("Runtime prerequisites OK")'

chmod +x "${CLI_BIN}"

TMP_VAULT_DIR="$(mktemp -d)"
trap 'rm -rf "${TMP_VAULT_DIR}"' EXIT
DB_PATH="${TMP_VAULT_DIR}/ugos_selftest_vault.sqlite"

echo "[2/5] Running UGOS VaultLoom CLI healthcheck..."
HEALTH_JSON="$("${CLI_BIN}" --db "${DB_PATH}" healthcheck)"
echo "      ${HEALTH_JSON}"
python3 -c "import json, sys; d = json.loads(sys.argv[1]); assert d['status'] == 'healthy' and d['triage_wasm_bytes'] == 256 and d['subspace_bytes_per_file'] == 96" "${HEALTH_JSON}"

echo "[3/5] Indexing bitemporal revisions (v1 @ t=10 -> v2 @ t=20) & querying SQLite WAL + FTS5..."
"${CLI_BIN}" --db "${DB_PATH}" index --path "/volume1/docs/raid_topology.md" --modality "text" --text "RAID topology draft v1 legacy layout" --valid-from 10 > /dev/null
"${CLI_BIN}" --db "${DB_PATH}" index --path "/volume1/docs/raid_topology.md" --modality "text" --text "RAID topology active v2 NVMe cache layout" --valid-from 20 > /dev/null

NOW_JSON="$("${CLI_BIN}" --db "${DB_PATH}" search --query "RAID topology layout")"
HIST_JSON="$("${CLI_BIN}" --db "${DB_PATH}" search --query "RAID topology layout" --as-of 12)"
python3 -c "import json, sys; now_r = json.loads(sys.argv[1])['results']; hist_r = json.loads(sys.argv[2])['results']; assert 'active v2' in now_r[0]['content_text']; assert 'draft v1' in hist_r[0]['content_text']" "${NOW_JSON}" "${HIST_JSON}"

echo "[4/5] Verifying 256 B local file-triage cartridge & deterministic PII redaction..."
TRI_JSON="$("${CLI_BIN}" --db "${DB_PATH}" triage --features "0.94,0.05,0.04")"
RED_JSON="$("${CLI_BIN}" --db "${DB_PATH}" redact --text "Share NAS note for SSN 123-45-6789 on host 192.168.1.40")"
python3 -c "import json, sys; t = json.loads(sys.argv[1]); r = json.loads(sys.argv[2]); assert t['category'] == 'engineering_code'; assert '[REDACTED-SSN]' in r['redacted_text'] and '[REDACTED-IPV4]' in r['redacted_text']" "${TRI_JSON}" "${RED_JSON}"

echo "[5/5] Running full 24-d Procrustes Recall@5 (-97.66% RAM), Zero-Reindex Upgrade & DP-Woodbury benchmark..."
BENCH_JSON="$("${CLI_BIN}" benchmark)"
python3 -c "import json, sys; b = json.loads(sys.argv[1]); vb = b['vault_benchmark']; dpb = b['dp_woodbury_benchmark']; assert vb['recall_at_5_encoder_v1'] == 1.0 and vb['recall_at_5_encoder_v2_zero_reindex'] == 1.0 and vb['memory_footprint']['ram_reduction_pct'] == 97.66 and dpb['accuracy_uplift'] > 0.4 and dpb['raw_filenames_leaked'] == 0" "${BENCH_JSON}"

echo "UGOS_VAULTLOOM_SELFTEST=PASS"
