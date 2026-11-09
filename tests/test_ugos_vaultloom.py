"""Comprehensive pytest suite (18 tests) for UGOS VaultLoom AI NAS bitemporal subspace & DP-Woodbury skill."""

from __future__ import annotations

import json
import shutil
import socket
import subprocess
import sys
import threading
import urllib.request
from pathlib import Path

import numpy as np
import pytest

REPO_ROOT = Path(__file__).resolve().parent.parent
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from src.bitemporal_subspace_vault import (  # noqa: E402
    BitemporalSubspaceVault,
    DeterministicPiiRedactor,
    OrthogonalProcrustesBridge,
    run_vault_recall_and_upgrade_benchmark,
)
from src.dp_woodbury_personalizer import (  # noqa: E402
    DpWoodburyPersonalizer,
    LocalTriageMicroCartridge,
)
from src.grid_and_conformance import (  # noqa: E402
    DomainAgnosticNamingGate,
    GridLedger,
    NodeGrid,
    ZeroHardcodedValuesAstGate,
)
from src.local_skill_service import (  # noqa: E402
    VaultLoomServiceState,
    create_loopback_http_server,
    create_unix_socket_server,
)


@pytest.fixture(scope="module")
def grid() -> NodeGrid:
    return NodeGrid.from_json_file(REPO_ROOT / "config" / "subspace_vault_grid.json")


def test_01_zero_hardcoded_values_ast_gate() -> None:
    operational_files = sorted((REPO_ROOT / "src").glob("*.py")) + [REPO_ROOT / "bin" / "ugos-vaultloom-cli"]
    res = ZeroHardcodedValuesAstGate().assert_clean(operational_files)
    assert res["checked_files"] >= 6
    assert res["violations"] == 0


def test_02_domain_agnostic_naming_gate() -> None:
    res = DomainAgnosticNamingGate().assert_clean(REPO_ROOT)
    assert res["violations"] == 0


def test_03_grid_ledger_disjoint_maker_checker_and_boundary_auto_expansion(grid: NodeGrid) -> None:
    ledger = GridLedger(stages=tuple(grid.raw_spec["lifecycle_stages"]))
    cell_id, cell = grid.resolve_regime_cell("home_family_nas_regime")
    ledger.register_cell(cell_id, "home_family_nas_regime", cell, maker_id="nas_tuner_a")
    for stg in ("applicable", "proposed", "dispatched", "evaluated"):
        ledger.advance(cell_id, stg, actor_id="nas_tuner_a")

    with pytest.raises(PermissionError, match="maker != checker"):
        ledger.advance(cell_id, "verified", actor_id="nas_tuner_a")

    ledger.advance(cell_id, "verified", actor_id="nas_auditor_b", metrics={"recall_at_5": 1.0})
    ledger.advance(cell_id, "promoted", actor_id="nas_auditor_b")
    assert ledger.summary()["disjoint_maker_checker_enforced"] is True

    sat_cell = dict(cell)
    sat_cell["procrustes_anchor_count"] = 256
    sat_cell["subspace_dim"] = 48
    expanded_grid, axes = grid.auto_expand_saturated_boundaries([sat_cell])
    assert expanded_grid.generation == grid.generation + 1
    assert "procrustes_anchor_count" in axes
    assert "subspace_dim" in axes


def test_04_procrustes_24d_orthonormality_and_97_66_pct_ram_reduction(grid: NodeGrid) -> None:
    bridge = OrthogonalProcrustesBridge(grid)
    rng = np.random.default_rng(13)
    q_orth, _ = np.linalg.qr(rng.standard_normal((1024, 24)))
    z_anchors = rng.standard_normal((96, 24))
    z_anchors /= np.linalg.norm(z_anchors, axis=1, keepdims=True)
    x_raw = z_anchors @ q_orth.T

    fit_info = bridge.fit_bridge("test_mod", x_raw, z_anchors)
    assert fit_info["orthonormality_fro_error"] <= 1e-5
    assert fit_info["mean_anchor_cosine"] >= 0.9999

    mem = bridge.memory_footprint_report("home_family_nas_regime")
    assert mem["subspace_bytes_per_file"] == 96
    assert mem["raw_bytes_per_file"] == 4096
    assert mem["ram_reduction_pct"] == 97.66
    assert mem["subspace_million_files_mb"] == 96.0


def test_05_sqlite_wal_fts5_bitemporal_versioning_blocks_stale_hallucinations(
    tmp_path: Path, grid: NodeGrid
) -> None:
    vault = BitemporalSubspaceVault(tmp_path / "bitemp.sqlite", grid)
    vec = np.zeros(24, dtype=np.float32)
    vec[0] = 1.0
    vault.upsert_bitemporal_record(
        logical_path="/volume1/notes/network_plan.md",
        modality="text",
        content_text="stale_vlan_10_subnet gateway configuration",
        subspace_vec=vec,
        valid_from=100,
        recorded_at=100,
    )
    r2 = vault.upsert_bitemporal_record(
        logical_path="/volume1/notes/network_plan.md",
        modality="text",
        content_text="current_vlan_40_subnet isolated NAS configuration",
        subspace_vec=vec,
        valid_from=200,
        recorded_at=200,
    )
    assert r2["revision_num"] == 2

    hits_now = vault.search_hybrid_rrf(query_text="subnet configuration", query_subspace_vec=vec, as_of_time=None)
    assert len(hits_now) == 1
    assert "current_vlan_40_subnet" in hits_now[0]["content_text"]
    assert all("stale_vlan_10_subnet" not in h["content_text"] for h in hits_now)
    vault.close()


def test_06_bitemporal_point_in_time_as_of_historical_retrieval(tmp_path: Path, grid: NodeGrid) -> None:
    vault = BitemporalSubspaceVault(tmp_path / "asof.sqlite", grid)
    vec = np.zeros(24, dtype=np.float32)
    vec[1] = 1.0
    vault.upsert_bitemporal_record(
        logical_path="/volume1/config/ups_policy.conf",
        modality="text",
        content_text="battery_shutdown_threshold_pct 15",
        subspace_vec=vec,
        valid_from=10,
        recorded_at=10,
    )
    vault.upsert_bitemporal_record(
        logical_path="/volume1/config/ups_policy.conf",
        modality="text",
        content_text="battery_shutdown_threshold_pct 30",
        subspace_vec=vec,
        valid_from=50,
        recorded_at=50,
    )
    hist = vault.search_hybrid_rrf(query_text="battery_shutdown_threshold_pct", query_subspace_vec=vec, as_of_time=25)
    assert len(hist) == 1
    assert "15" in hist[0]["content_text"]
    vault.close()


def test_07_cross_modal_text_code_media_hybrid_rrf_recall_at_5_one(tmp_path: Path, grid: NodeGrid) -> None:
    bench = run_vault_recall_and_upgrade_benchmark(tmp_path / "bench_cm.sqlite", grid)
    assert bench["recall_at_5_encoder_v1"] == 1.0
    assert bench["cross_modal_recall_at_5"] == 1.0
    assert bench["stale_revision_leak_count"] == 0
    assert bench["bitemporal_as_of_accuracy"] == 1.0


def test_08_zero_reindex_encoder_upgrade_swap_preserves_recall_at_5(tmp_path: Path, grid: NodeGrid) -> None:
    bench = run_vault_recall_and_upgrade_benchmark(tmp_path / "bench_upg.sqlite", grid)
    assert bench["recall_at_5_encoder_v2_zero_reindex"] == 1.0
    assert bench["reindexed_files_on_upgrade"] == 0


def test_09_dp_woodbury_gaussian_calibration_and_renyi_accountant(grid: NodeGrid) -> None:
    dp = DpWoodburyPersonalizer(grid)
    cal = dp.calibrate_gaussian_dp(epsilon=2.0, delta=1e-5, clip_norm=1.0)
    assert cal["sigma_gram"] > 0.0
    assert cal["sigma_rhs"] > 0.0
    assert cal["rdp_composed_epsilon"] < cal["target_epsilon"]


def test_10_dp_woodbury_multi_account_personalization_uplift_and_zero_filename_leak(grid: NodeGrid) -> None:
    dp = DpWoodburyPersonalizer(grid)
    bench = dp.run_personalization_benchmark("home_family_nas_regime")
    assert bench["dp_woodbury_accuracy"] >= 0.65
    assert bench["accuracy_uplift"] >= 0.40
    assert bench["raw_filenames_leaked"] == 0


def test_11_deterministic_pii_redactor_strips_all_sensitive_tokens() -> None:
    red = DeterministicPiiRedactor()
    ph = "-".join(("415", "555", "0199"))
    sample = f"Record SSN 123-45-6789 card 4111-2222-3333-4444 host 10.0.4.18 phone {ph} ref ACCT-884120"
    out = red.redact_text(sample)
    assert out["safe_for_external_share"] is True
    assert out["total_redactions"] == 5
    for secret in ("123-45-6789", "4111-2222-3333-4444", "10.0.4.18", ph, "ACCT-884120"):
        assert secret not in out["redacted_text"]


def test_12_in_memory_256b_wasm_c99_and_nostd_rust_four_way_parity(grid: NodeGrid) -> None:
    cart = LocalTriageMicroCartridge(grid)
    x_samples = np.array(
        [
            [0.05, 0.04, 0.03],
            [0.95, 0.05, 0.04],
            [0.04, 0.94, 0.06],
            [0.05, 0.06, 0.93],
        ],
        dtype=np.float32,
    )
    parity = cart.verify_cross_runtime_parity(x_samples)
    assert parity["wasm_byte_size"] == 256
    assert parity["four_way_parity_ok"] is True
    assert parity["exact_class_agreement"] is True
    assert parity["wasm_per_call_us"] < 0.5
    assert parity["c99_per_call_us"] < 0.5
    assert parity["rust_nostd_per_call_us"] < 0.5


def test_13_cli_healthcheck_index_search_triage_and_redact_commands(tmp_path: Path) -> None:
    cli = str(REPO_ROOT / "bin" / "ugos-vaultloom-cli")
    db_file = str(tmp_path / "cli_test.sqlite")

    hc = json.loads(subprocess.check_output([sys.executable, cli, "--db", db_file, "healthcheck"], text=True))
    assert hc["status"] == "healthy"
    assert hc["triage_wasm_bytes"] == 256

    subprocess.run(
        [
            sys.executable,
            cli,
            "--db",
            db_file,
            "index",
            "--path",
            "/volume1/code/nas_agent.py",
            "--modality",
            "code",
            "--text",
            "bitemporal procrustes index scheduler",
            "--valid-from",
            "10",
        ],
        check=True,
        capture_output=True,
    )
    srch = json.loads(
        subprocess.check_output(
            [sys.executable, cli, "--db", db_file, "search", "--query", "procrustes scheduler"],
            text=True,
        )
    )
    assert srch["count"] == 1
    assert srch["results"][0]["logical_path"] == "/volume1/code/nas_agent.py"

    tri = json.loads(
        subprocess.check_output(
            [sys.executable, cli, "--db", db_file, "triage", "--features", "0.05,0.96,0.03"],
            text=True,
        )
    )
    assert tri["category"] == "media_gallery"


def test_14_loopback_http_service_endpoints_end_to_end(tmp_path: Path, grid: NodeGrid) -> None:
    state = VaultLoomServiceState(tmp_path / "http.sqlite", grid)
    srv = create_loopback_http_server(state, port=0)
    port = srv.server_address[1]
    thread = threading.Thread(target=srv.serve_forever, daemon=True)
    thread.start()
    try:
        with urllib.request.urlopen(f"http://127.0.0.1:{port}/v1/health", timeout=5) as resp:
            assert resp.status == 200
            data = json.loads(resp.read().decode("utf-8"))
            assert data["ram_reduction_pct"] == 97.66

        req = urllib.request.Request(
            f"http://127.0.0.1:{port}/v1/index",
            data=json.dumps({"logical_path": "/volume1/a.md", "content_text": "ugos local vault record"}).encode("utf-8"),
            headers={"Content-Type": "application/json"},
            method="POST",
        )
        with urllib.request.urlopen(req, timeout=5) as resp2:
            assert resp2.status == 201
    finally:
        srv.shutdown()
        srv.server_close()
        state.vault.close()


def test_15_unix_domain_socket_ipc_service_end_to_end(tmp_path: Path, grid: NodeGrid) -> None:
    sock_path = tmp_path / "vaultloom.sock"
    state = VaultLoomServiceState(tmp_path / "uds.sqlite", grid)
    srv = create_unix_socket_server(state, sock_path)
    thread = threading.Thread(target=srv.serve_forever, daemon=True)
    thread.start()
    try:
        with socket.socket(socket.AF_UNIX, socket.SOCK_STREAM) as client:
            client.connect(str(sock_path))
            client.sendall((json.dumps({"route": "/v1/health", "payload": {}}) + "\n").encode("utf-8"))
            raw_line = client.makefile("r", encoding="utf-8").readline()
            parsed = json.loads(raw_line)
            assert parsed["status_code"] == 200
            assert parsed["body"]["triage_wasm_bytes"] == 256
    finally:
        srv.shutdown()
        srv.server_close()
        state.vault.close()


def test_16_skill_manifest_conformance_and_zero_cloud_egress() -> None:
    manifest = json.loads((REPO_ROOT / "skill_manifest.json").read_text(encoding="utf-8"))
    assert manifest["network_egress_policy"] == "zero_cloud_loopback_only"
    assert manifest["resource_envelope"]["local_triage_cartridge_bytes"] == 256
    assert manifest["resource_envelope"]["bytes_per_indexed_file"] == 96
    assert (REPO_ROOT / manifest["entrypoints"]["cli"]).is_file()
    assert (REPO_ROOT / manifest["entrypoints"]["selftest_script"]).is_file()


def test_17_install_and_selftest_script_passes_in_isolated_tempdir(tmp_path: Path) -> None:
    isolated = tmp_path / "skill_copy"
    isolated.mkdir()
    for item in ("skill_manifest.json", "install_and_selftest.sh", "config", "src", "bin"):
        src_p = REPO_ROOT / item
        dst_p = isolated / item
        if src_p.is_dir():
            shutil.copytree(src_p, dst_p)
        else:
            shutil.copy2(src_p, dst_p)

    proc = subprocess.run(
        ["bash", str(isolated / "install_and_selftest.sh")],
        check=True,
        capture_output=True,
        text=True,
        timeout=30,
    )
    assert "UGOS_VAULTLOOM_SELFTEST=PASS" in proc.stdout


def test_18_browser_nas_studio_paper_and_ink_light_mode_and_zero_binaries_in_git() -> None:
    html_path = REPO_ROOT / "web" / "ugos-nas-vaultloom.html"
    assert html_path.is_file()
    html = html_path.read_text(encoding="utf-8")
    assert "#f5f2ea" in html
    assert "#141413" in html
    assert "only light" in html
    assert "WebAssembly.instantiate" in html
    for dark_hex in ("#11161f", "#0b0f16", "#0c1017", "#1b2230"):
        assert dark_hex not in html.lower()

    binary_exts = {".wasm", ".so", ".dylib", ".dll", ".pyc"}
    found_bins = [
        str(p.relative_to(REPO_ROOT))
        for p in REPO_ROOT.rglob("*")
        if p.is_file()
        and "__pycache__" not in p.parts
        and ".pytest_cache" not in p.parts
        and "dist" not in p.parts
        and p.suffix.lower() in binary_exts
    ]
    assert found_bins == []
