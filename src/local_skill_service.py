"""Loopback HTTP and Unix-domain socket local skill service for UGOS Pro Linux AI NAS."""

from __future__ import annotations

import hashlib
import json
import socketserver
from http.server import BaseHTTPRequestHandler, HTTPServer
from pathlib import Path
from typing import Any

import numpy as np

from src.bitemporal_subspace_vault import BitemporalSubspaceVault
from src.dp_woodbury_personalizer import LocalTriageMicroCartridge
from src.grid_and_conformance import NodeGrid


def deterministic_text_to_subspace(text: str, subspace_dim: int, eps: float) -> np.ndarray:
    """Deterministic zero-cloud local feature hashing into unit-normalized float32 subspace for standalone CLI/API calls."""
    acc = np.zeros(subspace_dim, dtype=np.float64)
    tokens = [tok for tok in text.lower().split() if tok]
    if not tokens:
        acc[0] = 1.0
        return acc.astype(np.float32)
    for tok in tokens:
        digest = hashlib.blake2b(tok.encode("utf-8"), digest_size=subspace_dim).digest()
        for idx in range(subspace_dim):
            sign = 1.0 if (int(digest[idx]) & 1) == 0 else -1.0
            acc[idx] += sign
    norm = max(float(np.linalg.norm(acc)), eps)
    return (acc / norm).astype(np.float32)


class VaultLoomServiceState:
    """Shared local runtime state for loopback HTTP and Unix-socket requests."""

    def __init__(self, db_path: str | Path, grid: NodeGrid, regime_id: str = "home_family_nas_regime") -> None:
        self.grid = grid
        self.regime_id = regime_id
        self.scfg = grid.raw_spec["service_constants"]
        self.num = grid.raw_spec["numerical_constants"]
        self.vault = BitemporalSubspaceVault(db_path=db_path, grid=grid)
        self.triage = LocalTriageMicroCartridge(grid=grid)
        self.compiled_triage = self.triage.compile_256b_wasm()

    def handle_action(self, route: str, payload: dict[str, Any]) -> tuple[int, dict[str, Any]]:
        _, cell = self.grid.resolve_regime_cell(self.regime_id)
        d_sub = int(cell["subspace_dim"])
        eps = float(self.num["eps"])
        ok_code = int(self.scfg["http_ok"])
        created_code = int(self.scfg["http_created"])

        if route == "/v1/health":
            mem_rep = self.vault.bridge.memory_footprint_report(self.regime_id)
            return ok_code, {
                "status": "healthy",
                "skill": "ugos-vaultloom",
                "network_egress": "zero_cloud_loopback_only",
                "triage_wasm_bytes": self.compiled_triage["wasm_byte_size"],
                "subspace_bytes_per_file": mem_rep["subspace_bytes_per_file"],
                "ram_reduction_pct": mem_rep["ram_reduction_pct"],
            }

        if route == "/v1/index":
            content = str(payload["content_text"])
            vec = (
                np.asarray(payload["subspace_vec"], dtype=np.float32)
                if "subspace_vec" in payload
                else deterministic_text_to_subspace(content, d_sub, eps)
            )
            res = self.vault.upsert_bitemporal_record(
                logical_path=str(payload["logical_path"]),
                modality=str(payload.get("modality", "text")),
                content_text=content,
                subspace_vec=vec,
                valid_from=int(payload.get("valid_from", 1)),
                recorded_at=int(payload.get("recorded_at", 1)),
                metadata=dict(payload.get("metadata", {})),
                regime_id=self.regime_id,
            )
            return created_code, res

        if route == "/v1/search":
            q_text = str(payload["query_text"])
            q_vec = (
                np.asarray(payload["query_subspace_vec"], dtype=np.float32)
                if "query_subspace_vec" in payload
                else deterministic_text_to_subspace(q_text, d_sub, eps)
            )
            hits = self.vault.search_hybrid_rrf(
                query_text=q_text,
                query_subspace_vec=q_vec,
                as_of_time=payload.get("as_of_time"),
                regime_id=self.regime_id,
            )
            return ok_code, {"results": hits, "count": len(hits)}

        if route == "/v1/triage":
            feats = np.asarray(payload["features_3d"], dtype=np.float32)
            logits, preds = self.triage.evaluate_python_f32(feats)
            cat_idx = int(preds[0])
            cats = self.compiled_triage["categories"]
            return ok_code, {
                "category_index": cat_idx,
                "category": str(cats[cat_idx]),
                "logits": [float(v) for v in logits[0]],
                "wasm_cartridge_bytes": self.compiled_triage["wasm_byte_size"],
            }

        if route == "/v1/redact":
            red = self.vault.redactor.redact_text(str(payload["text"]))
            return ok_code, red

        return int(self.scfg["http_not_found"]), {"error": f"Unknown route: {route}"}


def create_loopback_http_server(state: VaultLoomServiceState, port: int = 0) -> HTTPServer:
    """Create a 127.0.0.1 loopback-only HTTP JSON server for UGOS Pro local daemon integration."""
    host = str(state.scfg["loopback_host"])
    max_bytes = int(state.scfg["max_body_bytes"])

    class _Handler(BaseHTTPRequestHandler):
        def log_message(self, fmt: str, *args: Any) -> None:
            return

        def _send_json(self, status_code: int, body: dict[str, Any]) -> None:
            encoded = json.dumps(body).encode("utf-8")
            self.send_response(status_code)
            self.send_header("Content-Type", "application/json")
            self.send_header("Content-Length", str(len(encoded)))
            self.end_headers()
            self.wfile.write(encoded)

        def do_GET(self) -> None:  # noqa: N802
            code, resp = state.handle_action(self.path, {})
            self._send_json(code, resp)

        def do_POST(self) -> None:  # noqa: N802
            length = min(int(self.headers.get("Content-Length", "0")), max_bytes)
            raw = self.rfile.read(length).decode("utf-8") if length > 0 else "{}"
            payload = json.loads(raw) if raw.strip() else {}
            code, resp = state.handle_action(self.path, payload)
            self._send_json(code, resp)

    return HTTPServer((host, port), _Handler)


def create_unix_socket_server(state: VaultLoomServiceState, socket_path: str | Path) -> socketserver.UnixStreamServer:
    """Create a local Unix-domain socket newline-delimited JSON server for zero-TCP UGOS Pro IPC."""
    sock_file = Path(socket_path)
    if sock_file.exists():
        sock_file.unlink()

    class _UnixHandler(socketserver.StreamRequestHandler):
        def handle(self) -> None:
            line = self.rfile.readline().decode("utf-8").strip()
            if not line:
                return
            req = json.loads(line)
            route = str(req.get("route", "/v1/health"))
            payload = dict(req.get("payload", {}))
            code, resp = state.handle_action(route, payload)
            out = json.dumps({"status_code": code, "body": resp}) + "\n"
            self.wfile.write(out.encode("utf-8"))

    return socketserver.UnixStreamServer(str(sock_file), _UnixHandler)
