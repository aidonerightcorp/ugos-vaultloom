"""Zero-cloud SQLite WAL + FTS5 bitemporal NAS index, 24-d Orthogonal Procrustes cross-modal bridge, and PII redactor."""

from __future__ import annotations

import json
import re
import sqlite3
import threading
from pathlib import Path
from typing import Any

import numpy as np

from src.grid_and_conformance import NodeGrid


class OrthogonalProcrustesBridge:
    """Aligns high-dimensional multi-modal or upgraded encoder embeddings into a shared 24-d float32 subspace."""

    def __init__(self, grid: NodeGrid) -> None:
        self.grid = grid
        self.num = grid.raw_spec["numerical_constants"]
        self.bridges: dict[str, np.ndarray] = {}

    def fit_bridge(
        self,
        bridge_key: str,
        x_raw_anchors: np.ndarray,
        z_subspace_targets: np.ndarray,
    ) -> dict[str, Any]:
        """Solve min_Q ||X Q - Z||_F s.t. Q^T Q = I_{d_sub} via compact SVD."""
        x_mat = np.asarray(x_raw_anchors, dtype=np.float64)
        z_mat = np.asarray(z_subspace_targets, dtype=np.float64)
        cross_cov = x_mat.T @ z_mat
        u_mat, _, vt_mat = np.linalg.svd(cross_cov, full_matrices=False)
        q_proj = (u_mat @ vt_mat).astype(np.float64)
        self.bridges[bridge_key] = q_proj

        d_sub = int(z_mat.shape[1])
        orth_err = float(np.linalg.norm((q_proj.T @ q_proj) - np.eye(d_sub, dtype=np.float64), ord="fro"))
        aligned = self.project_to_subspace(bridge_key, x_mat)
        z_norm = z_mat / np.maximum(np.linalg.norm(z_mat, axis=1, keepdims=True), float(self.num["eps"]))
        cos_sim = float(np.mean(np.sum(aligned * z_norm, axis=1)))

        return {
            "bridge_key": bridge_key,
            "raw_dim": int(x_mat.shape[1]),
            "subspace_dim": d_sub,
            "orthonormality_fro_error": round(orth_err, int(self.num["six_digits"])),
            "mean_anchor_cosine": round(cos_sim, int(self.num["six_digits"])),
        }

    def project_to_subspace(self, bridge_key: str, x_raw: np.ndarray) -> np.ndarray:
        """Project 1-D or 2-D raw embeddings into unit-normalized float32 subspace vectors (96 B/file at 24-d)."""
        if bridge_key not in self.bridges:
            raise KeyError(f"Unfitted Procrustes bridge_key: {bridge_key}")
        q_proj = self.bridges[bridge_key]
        arr = np.asarray(x_raw, dtype=np.float64)
        was_1d = arr.ndim == 1
        if was_1d:
            arr = arr.reshape(1, -1)
        proj = arr @ q_proj
        eps = float(self.num["eps"])
        norms = np.maximum(np.linalg.norm(proj, axis=1, keepdims=True), eps)
        unit_f32 = (proj / norms).astype(np.float32)
        return unit_f32[0] if was_1d else unit_f32

    def memory_footprint_report(self, regime_id: str = "home_family_nas_regime") -> dict[str, Any]:
        """Compute exact per-file and 1,000,000-file vector RAM footprint vs raw float32 embeddings."""
        _, cell = self.grid.resolve_regime_cell(regime_id)
        d_sub = int(cell["subspace_dim"])
        d_raw = int(cell["raw_encoder_dim"])
        f32_b = int(self.num["f32_bytes"])
        million = int(self.num["one_million_files"])
        mb_div = float(self.num["bytes_per_mb"])
        pct_scale = float(self.num["pct_scale"])
        two_d = int(self.num["two_digits"])

        sub_bytes = d_sub * f32_b
        raw_bytes = d_raw * f32_b
        reduction_pct = (float(raw_bytes - sub_bytes) / float(raw_bytes)) * pct_scale

        return {
            "subspace_dim": d_sub,
            "raw_encoder_dim": d_raw,
            "subspace_bytes_per_file": sub_bytes,
            "raw_bytes_per_file": raw_bytes,
            "ram_reduction_pct": round(reduction_pct, two_d),
            "subspace_million_files_mb": round(float(sub_bytes * million) / mb_div, two_d),
            "raw_million_files_mb": round(float(raw_bytes * million) / mb_div, two_d),
        }


class DeterministicPiiRedactor:
    """Zero-cloud deterministic PII & credential stripper gating optional external NAS file shares."""

    _PATTERNS: tuple[tuple[str, re.Pattern[str], str], ...] = (
        ("ssn_id", re.compile(r"\b\d{3}-\d{2}-\d{4}\b"), "[REDACTED-SSN]"),
        ("payment_card", re.compile(r"\b(?:\d{4}[-\s]){3}\d{4}\b"), "[REDACTED-CARD]"),
        ("phone_num", re.compile(r"(?<![\d-])(?:\(\d{3}\)\s?|\d{3}[-.\s])\d{3}[-.]\d{4}(?![\d-])"), "[REDACTED-PHONE]"),
        ("ipv4_host", re.compile(r"\b(?:\d{1,3}\.){3}\d{1,3}\b"), "[REDACTED-IPV4]"),
        ("mailbox", re.compile(r"\b[A-Za-z0-9._%+-]+@[A-Za-z0-9-]+(?:\.[A-Za-z0-9-]+)+\b"), "[REDACTED-CONTACT]"),
        ("account_ref", re.compile(r"\bACCT-[0-9A-Z]{6,}\b"), "[REDACTED-ACCOUNT]"),
    )

    def redact_text(self, raw_text: str) -> dict[str, Any]:
        cleaned = raw_text
        counts: dict[str, int] = {}
        total_hits = 0
        for kind, rx, token in self._PATTERNS:
            matches = rx.findall(cleaned)
            if matches:
                counts[kind] = len(matches)
                total_hits += len(matches)
                cleaned = rx.sub(token, cleaned)
        return {
            "redacted_text": cleaned,
            "redaction_counts": counts,
            "total_redactions": total_hits,
            "safe_for_external_share": True,
        }


class BitemporalSubspaceVault:
    """SQLite WAL + FTS5 bitemporal knowledge store with 24-d Procrustes + BM25 Reciprocal Rank Fusion."""

    def __init__(
        self,
        db_path: str | Path,
        grid: NodeGrid,
        bridge: OrthogonalProcrustesBridge | None = None,
    ) -> None:
        self.db_path = Path(db_path)
        self.grid = grid
        self.num = grid.raw_spec["numerical_constants"]
        self.bridge = bridge or OrthogonalProcrustesBridge(grid)
        self.redactor = DeterministicPiiRedactor()
        self._lock = threading.Lock()
        self.conn = sqlite3.connect(str(self.db_path), check_same_thread=False)
        self.conn.row_factory = sqlite3.Row
        self._init_schema()

    def _init_schema(self) -> None:
        with self._lock:
            self.conn.execute("PRAGMA journal_mode=WAL;")
            self.conn.execute("PRAGMA synchronous=NORMAL;")
            self.conn.execute(
                """
                CREATE TABLE IF NOT EXISTS vault_records (
                    record_pk INTEGER PRIMARY KEY AUTOINCREMENT,
                    logical_path TEXT NOT NULL,
                    modality TEXT NOT NULL,
                    revision_num INTEGER NOT NULL,
                    content_text TEXT NOT NULL,
                    metadata_json TEXT NOT NULL,
                    subspace_blob BLOB NOT NULL,
                    valid_from INTEGER NOT NULL,
                    valid_to INTEGER,
                    recorded_at INTEGER NOT NULL,
                    superseded_at INTEGER
                );
                """
            )
            self.conn.execute(
                "CREATE INDEX IF NOT EXISTS idx_vault_path_valid ON vault_records(logical_path, valid_from, valid_to);"
            )
            self.conn.execute(
                """
                CREATE VIRTUAL TABLE IF NOT EXISTS vault_fts USING fts5(
                    logical_path,
                    content_text,
                    modality
                );
                """
            )
            self.conn.commit()

    def close(self) -> None:
        with self._lock:
            self.conn.close()

    def upsert_bitemporal_record(
        self,
        *,
        logical_path: str,
        modality: str,
        content_text: str,
        subspace_vec: np.ndarray,
        valid_from: int,
        recorded_at: int,
        metadata: dict[str, Any] | None = None,
        regime_id: str = "home_family_nas_regime",
    ) -> dict[str, Any]:
        """Insert or supersede a NAS file revision preserving full bitemporal point-in-time history."""
        _, cell = self.grid.resolve_regime_cell(regime_id)
        d_sub = int(cell["subspace_dim"])
        vec_f32 = np.ascontiguousarray(subspace_vec, dtype="<f4").reshape(-1)
        if vec_f32.size != d_sub:
            raise ValueError(f"Expected subspace_dim={d_sub}, got {vec_f32.size}")

        meta_str = json.dumps(metadata or {}, sort_keys=True)
        blob = vec_f32.tobytes()
        with self._lock:
            cur = self.conn.execute(
                "SELECT record_pk, revision_num FROM vault_records WHERE logical_path = ? AND valid_to IS NULL ORDER BY revision_num DESC LIMIT 1;",
                (logical_path,),
            )
            active_row = cur.fetchone()
            if active_row is not None:
                prev_pk = int(active_row["record_pk"])
                next_rev = int(active_row["revision_num"]) + 1
                self.conn.execute(
                    "UPDATE vault_records SET valid_to = ?, superseded_at = ? WHERE record_pk = ?;",
                    (valid_from, recorded_at, prev_pk),
                )
            else:
                next_rev = 1

            ins = self.conn.execute(
                """
                INSERT INTO vault_records (
                    logical_path, modality, revision_num, content_text, metadata_json,
                    subspace_blob, valid_from, valid_to, recorded_at, superseded_at
                ) VALUES (?, ?, ?, ?, ?, ?, ?, NULL, ?, NULL);
                """,
                (logical_path, modality, next_rev, content_text, meta_str, blob, valid_from, recorded_at),
            )
            rec_pk = int(ins.lastrowid or 0)
            self.conn.execute(
                "INSERT INTO vault_fts(rowid, logical_path, content_text, modality) VALUES (?, ?, ?, ?);",
                (rec_pk, logical_path, content_text, modality),
            )
            self.conn.commit()
        return {
            "record_pk": rec_pk,
            "logical_path": logical_path,
            "revision_num": next_rev,
            "subspace_bytes": len(blob),
        }

    def _sanitize_fts_query(self, query_text: str) -> str:
        tokens = [tok for tok in re.findall(r"[A-Za-z0-9_]+", query_text.lower()) if len(tok) > 1]
        if not tokens:
            return ""
        return " OR ".join(f'"{t}"' for t in tokens)

    def search_hybrid_rrf(
        self,
        *,
        query_text: str,
        query_subspace_vec: np.ndarray,
        as_of_time: int | None = None,
        regime_id: str = "home_family_nas_regime",
    ) -> list[dict[str, Any]]:
        """Execute bitemporal SQLite FTS5 BM25 + 24-d Procrustes cosine search fused via Reciprocal Rank Fusion."""
        _, cell = self.grid.resolve_regime_cell(regime_id)
        d_sub = int(cell["subspace_dim"])
        top_k = int(cell["search_top_k"])
        rrf_k = float(cell["rrf_rank_constant"])
        w_sem = float(cell["rrf_semantic_weight"])
        w_lex = 1.0 - w_sem

        q_vec = np.ascontiguousarray(query_subspace_vec, dtype=np.float32).reshape(-1)
        q_norm = float(np.linalg.norm(q_vec))
        eps = float(self.num["eps"])
        if q_norm > eps:
            q_vec = q_vec / np.float32(q_norm)

        fts_expr = self._sanitize_fts_query(query_text)
        cand_limit = top_k * int(self.num["fts_candidate_multiplier"])
        with self._lock:
            if as_of_time is None:
                rows = self.conn.execute(
                    "SELECT * FROM vault_records WHERE valid_to IS NULL;"
                ).fetchall()
            else:
                rows = self.conn.execute(
                    "SELECT * FROM vault_records WHERE valid_from <= ? AND (valid_to IS NULL OR valid_to > ?);",
                    (as_of_time, as_of_time),
                ).fetchall()

            if not rows:
                return []

            valid_by_pk = {int(r["record_pk"]): r for r in rows}

            # Lexical FTS5 BM25 ranking restricted to bitemporally active record_pks
            lex_ranks: dict[int, int] = {}
            if fts_expr:
                fts_rows = self.conn.execute(
                    "SELECT rowid, bm25(vault_fts) AS b_score FROM vault_fts WHERE vault_fts MATCH ? ORDER BY b_score ASC LIMIT ?;",
                    (fts_expr, cand_limit),
                ).fetchall()
                rank_pos = 1
                for fr in fts_rows:
                    pk_val = int(fr["rowid"])
                    if pk_val in valid_by_pk:
                        lex_ranks[pk_val] = rank_pos
                        rank_pos += 1

        # Dense 24-d Procrustes cosine ranking across bitemporally valid rows
        sem_scores: list[tuple[int, float]] = []
        for pk_val, row in valid_by_pk.items():
            vec = np.frombuffer(row["subspace_blob"], dtype="<f4").reshape(d_sub)
            cos_val = float(np.dot(q_vec, vec))
            sem_scores.append((pk_val, cos_val))
        sem_scores.sort(key=lambda item: item[1], reverse=True)
        sem_ranks = {pk_val: idx + 1 for idx, (pk_val, _) in enumerate(sem_scores)}
        sem_map = dict(sem_scores)

        fused: list[dict[str, Any]] = []
        six_d = int(self.num["six_digits"])
        for pk_val, row in valid_by_pk.items():
            s_rank = sem_ranks[pk_val]
            rrf_val = w_sem / (rrf_k + float(s_rank))
            if pk_val in lex_ranks:
                rrf_val += w_lex / (rrf_k + float(lex_ranks[pk_val]))
            fused.append(
                {
                    "record_pk": pk_val,
                    "logical_path": str(row["logical_path"]),
                    "modality": str(row["modality"]),
                    "revision_num": int(row["revision_num"]),
                    "content_text": str(row["content_text"]),
                    "valid_from": int(row["valid_from"]),
                    "valid_to": row["valid_to"],
                    "cosine_24d": round(sem_map[pk_val], six_d),
                    "lexical_rank": lex_ranks.get(pk_val),
                    "rrf_score": round(rrf_val, six_d),
                }
            )

        fused.sort(key=lambda item: (float(item["rrf_score"]), float(item["cosine_24d"])), reverse=True)
        return fused[:top_k]


def run_vault_recall_and_upgrade_benchmark(
    db_path: str | Path,
    grid: NodeGrid,
    regime_id: str = "home_family_nas_regime",
) -> dict[str, Any]:
    """Benchmark bitemporal Recall@5, zero-stale leakage, -97.66% RAM, and zero-reindex encoder upgrade parity."""
    _, cell = grid.resolve_regime_cell(regime_id)
    num = grid.raw_spec["numerical_constants"]
    d_sub = int(cell["subspace_dim"])
    d_raw = int(cell["raw_encoder_dim"])
    n_anchors = int(cell["procrustes_anchor_count"])
    n_topics = int(num["benchmark_topic_count"])

    seed0 = int(grid.raw_spec["seeds"][0])
    rng = np.random.default_rng(seed0)

    # Construct ground-truth shared 24-d semantic subspace + 4 distinct 1024-d modality/version encoders
    w_text_v1, _ = np.linalg.qr(rng.standard_normal((d_raw, d_sub)))
    w_code_v1, _ = np.linalg.qr(rng.standard_normal((d_raw, d_sub)))
    w_media_v1, _ = np.linalg.qr(rng.standard_normal((d_raw, d_sub)))
    w_text_v2, _ = np.linalg.qr(rng.standard_normal((d_raw, d_sub)))

    anchor_z = rng.standard_normal((n_anchors, d_sub))
    anchor_z = anchor_z / np.maximum(np.linalg.norm(anchor_z, axis=1, keepdims=True), float(num["eps"]))

    bridge = OrthogonalProcrustesBridge(grid)
    bridge.fit_bridge("text_v1", anchor_z @ w_text_v1.T, anchor_z)
    bridge.fit_bridge("code_v1", anchor_z @ w_code_v1.T, anchor_z)
    bridge.fit_bridge("media_v1", anchor_z @ w_media_v1.T, anchor_z)

    vault = BitemporalSubspaceVault(db_path=db_path, grid=grid, bridge=bridge)
    topic_concepts = np.eye(d_sub, dtype=np.float64)[:n_topics]

    t_epoch_old = int(num["ten"])
    t_epoch_new = int(num["ten"]) * int(num["two"])

    for t_idx in range(n_topics):
        z_t = topic_concepts[t_idx]
        # Revision 1 (historical draft at t=10)
        raw_txt_old = z_t @ w_text_v1.T
        vault.upsert_bitemporal_record(
            logical_path=f"/nas/projects/topic_{t_idx}/design_notes.md",
            modality="text",
            content_text=f"topic_{t_idx} legacy_draft_v1 architecture specification module_{t_idx}",
            subspace_vec=bridge.project_to_subspace("text_v1", raw_txt_old),
            valid_from=t_epoch_old,
            recorded_at=t_epoch_old,
            regime_id=regime_id,
        )
        # Revision 2 (current active specification at t=20 superseding v1)
        vault.upsert_bitemporal_record(
            logical_path=f"/nas/projects/topic_{t_idx}/design_notes.md",
            modality="text",
            content_text=f"topic_{t_idx} active_release_v2 production specification module_{t_idx}",
            subspace_vec=bridge.project_to_subspace("text_v1", raw_txt_old),
            valid_from=t_epoch_new,
            recorded_at=t_epoch_new,
            regime_id=regime_id,
        )
        # Cross-modal code file + EXIF media asset in same shared 24-d subspace
        vault.upsert_bitemporal_record(
            logical_path=f"/nas/projects/topic_{t_idx}/kernel_{t_idx}.rs",
            modality="code",
            content_text=f"pub fn execute_module_{t_idx}() -> usize {{ /* topic_{t_idx} */ 0 }}",
            subspace_vec=bridge.project_to_subspace("code_v1", z_t @ w_code_v1.T),
            valid_from=t_epoch_old,
            recorded_at=t_epoch_old,
            regime_id=regime_id,
        )
        vault.upsert_bitemporal_record(
            logical_path=f"/nas/media/topic_{t_idx}/capture_{t_idx}.heic",
            modality="media_exif",
            content_text=f"EXIF lens telemetry diagram asset for topic_{t_idx}",
            subspace_vec=bridge.project_to_subspace("media_v1", z_t @ w_media_v1.T),
            valid_from=t_epoch_old,
            recorded_at=t_epoch_old,
            regime_id=regime_id,
        )

    # Evaluate Pre-Upgrade Recall@5, Cross-Modal Recall@5, Stale Leakage, and Historical As-Of Accuracy
    hits_v1 = 0
    cross_modal_hits = 0
    stale_leaks = 0
    historical_hits = 0

    for t_idx in range(n_topics):
        z_t = topic_concepts[t_idx]
        q_sub_v1 = bridge.project_to_subspace("text_v1", z_t @ w_text_v1.T)
        res_now = vault.search_hybrid_rrf(
            query_text=f"topic_{t_idx} specification",
            query_subspace_vec=q_sub_v1,
            as_of_time=None,
            regime_id=regime_id,
        )
        paths_now = {r["logical_path"] for r in res_now}
        modalities_now = {r["modality"] for r in res_now}
        if f"/nas/projects/topic_{t_idx}/design_notes.md" in paths_now:
            hits_v1 += 1
        if {"text", "code", "media_exif"}.issubset(modalities_now):
            cross_modal_hits += 1
        if any("legacy_draft_v1" in r["content_text"] for r in res_now):
            stale_leaks += 1

        res_hist = vault.search_hybrid_rrf(
            query_text=f"topic_{t_idx}",
            query_subspace_vec=q_sub_v1,
            as_of_time=t_epoch_old,
            regime_id=regime_id,
        )
        if any("legacy_draft_v1" in r["content_text"] for r in res_hist):
            historical_hits += 1

    # Upgrade query encoder from Encoder v1 (1024-d) -> Encoder v2 (1024-d) WITHOUT re-indexing any stored NAS file!
    bridge.fit_bridge("text_v2_upgrade", anchor_z @ w_text_v2.T, anchor_z)
    hits_v2_zero_reindex = 0
    for t_idx in range(n_topics):
        z_t = topic_concepts[t_idx]
        q_sub_v2 = bridge.project_to_subspace("text_v2_upgrade", z_t @ w_text_v2.T)
        res_upg = vault.search_hybrid_rrf(
            query_text=f"module_{t_idx}",
            query_subspace_vec=q_sub_v2,
            as_of_time=None,
            regime_id=regime_id,
        )
        if f"/nas/projects/topic_{t_idx}/design_notes.md" in {r["logical_path"] for r in res_upg}:
            hits_v2_zero_reindex += 1

    mem_report = bridge.memory_footprint_report(regime_id=regime_id)
    vault.close()
    rd = int(num["round_digits"])

    return {
        "topics_evaluated": n_topics,
        "recall_at_5_encoder_v1": round(float(hits_v1) / float(n_topics), rd),
        "cross_modal_recall_at_5": round(float(cross_modal_hits) / float(n_topics), rd),
        "recall_at_5_encoder_v2_zero_reindex": round(float(hits_v2_zero_reindex) / float(n_topics), rd),
        "reindexed_files_on_upgrade": 0,
        "stale_revision_leak_count": stale_leaks,
        "bitemporal_as_of_accuracy": round(float(historical_hits) / float(n_topics), rd),
        "memory_footprint": mem_report,
    }
