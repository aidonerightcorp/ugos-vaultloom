"""(epsilon, delta)-DP Recursive Woodbury NAS Personalizer and 256 B .wasm / C99 / #![no_std] Rust Triage Cartridges."""

from __future__ import annotations

import base64
import ctypes
import json
import math
import shutil
import struct
import subprocess
import tempfile
import time
from pathlib import Path
from typing import Any

import numpy as np

from src.grid_and_conformance import NodeGrid


class LocalTriageMicroCartridge:
    """Emits an exact 256-byte IEEE-754 WebAssembly v1 triage cartridge + C99 and #![no_std] Rust twins."""

    def __init__(self, grid: NodeGrid) -> None:
        self.grid = grid
        self.tspec = grid.raw_spec["triage_cartridge_spec"]
        self.wspec = grid.raw_spec["wasm_compact_constants"]
        self.num = grid.raw_spec["numerical_constants"]

    def _uleb(self, val: int) -> bytes:
        cont = int(self.wspec["leb_cont"])
        mask = int(self.wspec["leb_mask"])
        shift = int(self.wspec["leb_shift"])
        out = bytearray()
        rem = int(val)
        while rem >= cont:
            out.append((rem & mask) | cont)
            rem >>= shift
        out.append(rem & mask)
        return bytes(out)

    def _sleb(self, val: int) -> bytes:
        cont = int(self.wspec["leb_cont"])
        mask = int(self.wspec["leb_mask"])
        sign = int(self.wspec["leb_sign"])
        shift = int(self.wspec["leb_shift"])
        out = bytearray()
        rem = int(val)
        more = True
        while more:
            byte = rem & mask
            rem >>= shift
            done_pos = rem == 0 and (byte & sign) == 0
            done_neg = rem == -1 and (byte & sign) != 0
            if done_pos or done_neg:
                more = False
            else:
                byte |= cont
            out.append(byte)
        return bytes(out)

    def _sec(self, sid: int, payload: bytes) -> bytes:
        return bytes([sid]) + self._uleb(len(payload)) + payload

    def _nm(self, text: str) -> bytes:
        raw = text.encode("utf-8")
        return self._uleb(len(raw)) + raw

    def compile_256b_wasm(self) -> dict[str, Any]:
        """Emit the exact 256-byte IEEE-754 float32 WebAssembly v1 local file-triage module in memory."""
        ws = self.wspec
        in_dim = int(self.tspec["in_dim"])
        out_dim = int(self.tspec["out_dim"])
        in_off = int(self.tspec["input_offset_bytes"])
        out_off = int(self.tspec["output_offset_bytes"])
        b_off = int(self.tspec["bias_offset_bytes"])

        w_mat = np.asarray(self.tspec["weights_4x3"], dtype="<f4")
        b_vec = np.asarray(self.tspec["bias_4"], dtype="<f4")
        data_blob = w_mat.tobytes() + b_vec.tobytes()

        sec_type = self._sec(int(ws["sec_type"]), self._uleb(1) + bytes([int(ws["type_func"]), 0, 1, int(ws["val_i32"])]))
        sec_func = self._sec(int(ws["sec_function"]), self._uleb(1) + bytes([0]))
        sec_mem = self._sec(int(ws["sec_memory"]), self._uleb(1) + bytes([0, 1]))
        exp = (
            self._uleb(int(self.num["two"]))
            + self._nm("memory")
            + bytes([int(ws["export_memory"]), 0])
            + self._nm("eval")
            + bytes([int(ws["export_func"]), 0])
        )
        sec_exp = self._sec(int(ws["sec_export"]), exp)

        locals_enc = (
            self._uleb(int(ws["local_groups"]))
            + self._uleb(int(ws["local_i32_cnt"]))
            + bytes([int(ws["val_i32"])])
            + self._uleb(int(ws["local_f32_cnt"]))
            + bytes([int(ws["val_f32"])])
        )

        op_iconst = int(ws["op_iconst"])
        op_fconst = int(ws["op_fconst"])
        op_lget = int(ws["op_lget"])
        op_lset = int(ws["op_lset"])
        op_block = int(ws["op_block"])
        op_loop = int(ws["op_loop"])
        op_if = int(ws["op_if"])
        op_end = int(ws["op_end"])
        op_br = int(ws["op_br"])
        op_br_if = int(ws["op_br_if"])
        op_fload = int(ws["op_fload"])
        op_fstore = int(ws["op_fstore"])
        op_ige = int(ws["op_ige"])
        op_fgt = int(ws["op_fgt"])
        op_iadd = int(ws["op_iadd"])
        op_imul = int(ws["op_imul"])
        op_ishl = int(ws["op_ishl"])
        op_fadd = int(ws["op_fadd"])
        op_fmul = int(ws["op_fmul"])
        b_void = int(ws["block_void"])
        shl_two = int(ws["f32_shift_log2"])

        loc_r = int(ws["loc_r"])
        loc_c = int(ws["loc_c"])
        loc_best_idx = int(ws["loc_best_idx"])
        loc_acc = int(ws["loc_acc"])
        loc_best_val = int(ws["loc_best_val"])

        code = bytearray()
        code += bytes([op_iconst]) + self._sleb(0) + bytes([op_lset, loc_best_idx])
        code += bytes([op_fconst]) + struct.pack("<f", float(self.tspec["init_neg_inf_f32"])) + bytes([op_lset, loc_best_val])
        code += bytes([op_iconst]) + self._sleb(0) + bytes([op_lset, loc_r])

        code += bytes([op_block, b_void, op_loop, b_void])
        code += bytes([op_lget, loc_r, op_iconst]) + self._sleb(out_dim) + bytes([op_ige, op_br_if, 1])
        code += bytes([op_lget, loc_r, op_iconst, shl_two, op_ishl, op_fload, shl_two]) + self._uleb(b_off) + bytes([op_lset, loc_acc])

        code += bytes([op_iconst]) + self._sleb(0) + bytes([op_lset, loc_c])
        code += bytes([op_block, b_void, op_loop, b_void])
        code += bytes([op_lget, loc_c, op_iconst]) + self._sleb(in_dim) + bytes([op_ige, op_br_if, 1])

        code += bytes([op_lget, loc_acc])
        code += bytes([op_lget, loc_r, op_iconst]) + self._sleb(in_dim) + bytes([op_imul, op_lget, loc_c, op_iadd, op_iconst, shl_two, op_ishl, op_fload, shl_two]) + self._uleb(0)
        code += bytes([op_lget, loc_c, op_iconst, shl_two, op_ishl, op_fload, shl_two]) + self._uleb(in_off)
        code += bytes([op_fmul, op_fadd, op_lset, loc_acc])

        code += bytes([op_lget, loc_c, op_iconst, 1, op_iadd, op_lset, loc_c, op_br, 0, op_end, op_end])

        code += bytes([op_lget, loc_r, op_iconst, shl_two, op_ishl, op_lget, loc_acc, op_fstore, shl_two]) + self._uleb(out_off)
        code += bytes([op_lget, loc_acc, op_lget, loc_best_val, op_fgt, op_if, b_void, op_lget, loc_acc, op_lset, loc_best_val, op_lget, loc_r, op_lset, loc_best_idx, op_end])
        code += bytes([op_lget, loc_r, op_iconst, 1, op_iadd, op_lset, loc_r, op_br, 0, op_end, op_end])
        code += bytes([op_lget, loc_best_idx, op_end])

        body = locals_enc + bytes(code)
        sec_code = self._sec(int(ws["sec_code"]), self._uleb(1) + self._uleb(len(body)) + body)
        sec_data = self._sec(int(ws["sec_data"]), self._uleb(1) + bytes([0, op_iconst, 0, op_end]) + self._uleb(len(data_blob)) + data_blob)

        wasm_bytes = bytes(ws["magic_and_version"]) + sec_type + sec_func + sec_mem + sec_exp + sec_code + sec_data
        return {
            "wasm_bytes": wasm_bytes,
            "wasm_byte_size": len(wasm_bytes),
            "wasm_base64": base64.b64encode(wasm_bytes).decode("ascii"),
            "in_dim": in_dim,
            "out_dim": out_dim,
            "input_offset": in_off,
            "output_offset": out_off,
            "categories": list(self.tspec["categories"]),
        }

    def evaluate_python_f32(self, x_batch: np.ndarray) -> tuple[np.ndarray, np.ndarray]:
        """Exact IEEE-754 float32 left-to-right forward evaluation matching 256B WASM, C99, and #![no_std] Rust."""
        x_f32 = np.ascontiguousarray(x_batch, dtype=np.float32)
        if x_f32.ndim == 1:
            x_f32 = x_f32.reshape(1, -1)
        w_mat = np.asarray(self.tspec["weights_4x3"], dtype=np.float32)
        b_vec = np.asarray(self.tspec["bias_4"], dtype=np.float32)
        in_dim = int(self.tspec["in_dim"])
        out_dim = int(self.tspec["out_dim"])
        n_rows = int(x_f32.shape[0])

        logits = np.zeros((n_rows, out_dim), dtype=np.float32)
        for s_i in range(n_rows):
            for r_i in range(out_dim):
                acc = np.float32(b_vec[r_i])
                for c_i in range(in_dim):
                    acc = np.float32(acc + np.float32(w_mat[r_i, c_i] * x_f32[s_i, c_i]))
                logits[s_i, r_i] = acc
        preds = np.argmax(logits, axis=1).astype(np.int64)
        return logits, preds

    def render_c99_source(self) -> str:
        w_flat = np.asarray(self.tspec["weights_4x3"], dtype=np.float32).ravel()
        b_flat = np.asarray(self.tspec["bias_4"], dtype=np.float32).ravel()
        in_dim = int(self.tspec["in_dim"])
        out_dim = int(self.tspec["out_dim"])
        w_str = ", ".join(f"{float(v):.8e}f" for v in w_flat)
        b_str = ", ".join(f"{float(v):.8e}f" for v in b_flat)
        return f"""#include <stdint.h>

static const float W[{in_dim * out_dim}] = {{{w_str}}};
static const float B[{out_dim}] = {{{b_str}}};

int32_t vaultloom_triage_c99(const float* in_vec, float* out_vec) {{
    int32_t best_idx = 0;
    float best_val = -1.0e30f;
    for (int32_t r = 0; r < {out_dim}; ++r) {{
        float acc = B[r];
        for (int32_t c = 0; c < {in_dim}; ++c) {{
            acc = acc + (W[r * {in_dim} + c] * in_vec[c]);
        }}
        out_vec[r] = acc;
        if (acc > best_val) {{
            best_val = acc;
            best_idx = r;
        }}
    }}
    return best_idx;
}}

int32_t vaultloom_triage_c99_bench(const float* in_vec, float* out_vec, uint32_t loops) {{
    int32_t sink = 0;
    float local_in[{in_dim}];
    for (int32_t j = 0; j < {in_dim}; ++j) local_in[j] = in_vec[j];
    for (uint32_t k = 0; k < loops; ++k) {{
        sink += vaultloom_triage_c99(local_in, out_vec);
    }}
    return sink;
}}
"""

    def render_nostd_rust_source(self) -> str:
        w_flat = np.asarray(self.tspec["weights_4x3"], dtype=np.float32).ravel()
        b_flat = np.asarray(self.tspec["bias_4"], dtype=np.float32).ravel()
        in_dim = int(self.tspec["in_dim"])
        out_dim = int(self.tspec["out_dim"])
        w_str = ", ".join(f"{float(v):.8e}_f32" for v in w_flat)
        b_str = ", ".join(f"{float(v):.8e}_f32" for v in b_flat)
        return f"""#![no_std]

#[panic_handler]
fn panic(_info: &core::panic::PanicInfo) -> ! {{
    loop {{}}
}}

static W: [f32; {in_dim * out_dim}] = [{w_str}];
static B: [f32; {out_dim}] = [{b_str}];

#[no_mangle]
pub unsafe extern "C" fn vaultloom_triage_rs(in_ptr: *const f32, out_ptr: *mut f32) -> i32 {{
    let mut best_idx: i32 = 0;
    let mut best_val: f32 = -1.0e30_f32;
    let mut r = 0;
    while r < {out_dim} {{
        let mut acc = B[r];
        let mut c = 0;
        while c < {in_dim} {{
            acc += W[r * {in_dim} + c] * (*in_ptr.add(c));
            c += 1;
        }}
        *out_ptr.add(r) = acc;
        if acc > best_val {{
            best_val = acc;
            best_idx = r as i32;
        }}
        r += 1;
    }}
    best_idx
}}

#[no_mangle]
pub unsafe extern "C" fn vaultloom_triage_rs_bench(in_ptr: *const f32, out_ptr: *mut f32, loops: u32) -> i32 {{
    let mut sink: i32 = 0;
    let mut k: u32 = 0;
    while k < loops {{
        sink = sink.wrapping_add(vaultloom_triage_rs(in_ptr, out_ptr));
        k += 1;
    }}
    sink
}}
"""

    def verify_cross_runtime_parity(self, x_test: np.ndarray) -> dict[str, Any]:
        """Verify 4-way IEEE-754 parity (Python == 256B WASM == C99 == #![no_std] Rust) and <0.5us latency."""
        compiled = self.compile_256b_wasm()
        wasm_bytes = compiled["wasm_bytes"]
        in_dim = int(compiled["in_dim"])
        out_dim = int(compiled["out_dim"])
        in_off = int(compiled["input_offset"])
        out_off = int(compiled["output_offset"])
        py_logits, py_preds = self.evaluate_python_f32(x_test)

        node_bin = shutil.which("node") or "node"
        gcc_bin = shutil.which("gcc") or "gcc"
        rustc_bin = shutil.which("rustc") or str(Path.home() / ".local/bin/rustc")
        timeout_s = int(self.num["subprocess_timeout_sec"])
        warmup = int(self.num["wasm_warmup_loops"])
        w_loops = int(self.num["wasm_bench_loops"])
        n_loops = int(self.num["native_bench_loops"])
        ns_per_us = float(self.num["ns_per_us"])

        mjs_code = f"""import fs from 'node:fs';
const wasmBytes = fs.readFileSync(process.argv[2]);
const payload = JSON.parse(fs.readFileSync(process.argv[3], 'utf8'));
const {{ instance }} = await WebAssembly.instantiate(wasmBytes);
const exp = instance.exports;
const inView = new Float32Array(exp.memory.buffer, {in_off}, {in_dim});
const outView = new Float32Array(exp.memory.buffer, {out_off}, {out_dim});
const logits = [];
const preds = [];
for (const row of payload.vectors) {{
  inView.set(row);
  preds.push(exp.eval());
  logits.push(Array.from(outView));
}}
let sink = 0;
for (let w = 0; w < {warmup}; w += 1) sink += exp.eval();
const t0 = process.hrtime.bigint();
for (let r = 0; r < payload.loops; r += 1) {{
  sink += exp.eval();
}}
const elapsedNs = Number(process.hrtime.bigint() - t0);
process.stdout.write(JSON.stringify({{ logits, preds, elapsed_ns: elapsedNs, sink }}));
"""
        with tempfile.TemporaryDirectory() as tmp_str:
            work = Path(tmp_str)
            wasm_p = work / "triage_256b.wasm"
            pay_p = work / "payload.json"
            mjs_p = work / "run.mjs"
            wasm_p.write_bytes(wasm_bytes)
            pay_p.write_text(
                json.dumps(
                    {
                        "loops": w_loops,
                        "vectors": np.ascontiguousarray(x_test, dtype=np.float32).tolist(),
                    }
                ),
                encoding="utf-8",
            )
            mjs_p.write_text(mjs_code, encoding="utf-8")
            proc_w = subprocess.run(
                [node_bin, str(mjs_p), str(wasm_p), str(pay_p)],
                check=True,
                capture_output=True,
                text=True,
                timeout=timeout_s,
            )
            w_parsed = json.loads(proc_w.stdout)
            wasm_logits = np.asarray(w_parsed["logits"], dtype=np.float32)
            wasm_preds = np.asarray(w_parsed["preds"], dtype=np.int64)
            wasm_us = (float(w_parsed["elapsed_ns"]) / ns_per_us) / float(w_loops)

            # Compile C99 cartridge
            c_file = work / "triage.c"
            c_so = work / "libtriage_c99.so"
            c_file.write_text(self.render_c99_source(), encoding="utf-8")
            subprocess.run(
                [gcc_bin, "-std=c99", "-O3", "-fno-fast-math", "-shared", "-fPIC", str(c_file), "-o", str(c_so)],
                check=True,
                capture_output=True,
                text=True,
                timeout=timeout_s,
            )
            c_lib = ctypes.CDLL(str(c_so))
            c_eval = c_lib.vaultloom_triage_c99
            c_eval.argtypes = [ctypes.POINTER(ctypes.c_float), ctypes.POINTER(ctypes.c_float)]
            c_eval.restype = ctypes.c_int32
            c_bench = c_lib.vaultloom_triage_c99_bench
            c_bench.argtypes = [ctypes.POINTER(ctypes.c_float), ctypes.POINTER(ctypes.c_float), ctypes.c_uint32]
            c_bench.restype = ctypes.c_int32

            # Compile #![no_std] Rust cartridge
            rs_file = work / "triage.rs"
            rs_so = work / "libtriage_rs.so"
            rs_file.write_text(self.render_nostd_rust_source(), encoding="utf-8")
            subprocess.run(
                [rustc_bin, "--edition=2021", "--crate-type", "cdylib", "-C", "opt-level=3", "-C", "panic=abort", str(rs_file), "-o", str(rs_so)],
                check=True,
                capture_output=True,
                text=True,
                timeout=timeout_s,
            )
            rs_lib = ctypes.CDLL(str(rs_so))
            rs_eval = rs_lib.vaultloom_triage_rs
            rs_eval.argtypes = [ctypes.POINTER(ctypes.c_float), ctypes.POINTER(ctypes.c_float)]
            rs_eval.restype = ctypes.c_int32
            rs_bench = rs_lib.vaultloom_triage_rs_bench
            rs_bench.argtypes = [ctypes.POINTER(ctypes.c_float), ctypes.POINTER(ctypes.c_float), ctypes.c_uint32]
            rs_bench.restype = ctypes.c_int32

            x_contig = np.ascontiguousarray(x_test, dtype=np.float32)
            n_rows = int(x_contig.shape[0])
            c_logits = np.zeros((n_rows, out_dim), dtype=np.float32)
            rs_logits = np.zeros((n_rows, out_dim), dtype=np.float32)
            c_preds = np.zeros(n_rows, dtype=np.int64)
            rs_preds = np.zeros(n_rows, dtype=np.int64)
            out_buf = (ctypes.c_float * out_dim)()

            for idx in range(n_rows):
                in_buf = (ctypes.c_float * in_dim)(*x_contig[idx].tolist())
                c_preds[idx] = int(c_eval(in_buf, out_buf))
                for o_i in range(out_dim):
                    c_logits[idx, o_i] = float(out_buf[o_i])
                rs_preds[idx] = int(rs_eval(in_buf, out_buf))
                for o_i in range(out_dim):
                    rs_logits[idx, o_i] = float(out_buf[o_i])

            bench_in = (ctypes.c_float * in_dim)(*x_contig[0].tolist())
            t0_c = time.perf_counter_ns()
            sink_c = int(c_bench(bench_in, out_buf, ctypes.c_uint32(n_loops)))
            c99_us = (float(time.perf_counter_ns() - t0_c) / ns_per_us) / float(n_loops)

            t0_rs = time.perf_counter_ns()
            sink_rs = int(rs_bench(bench_in, out_buf, ctypes.c_uint32(n_loops)))
            rust_us = (float(time.perf_counter_ns() - t0_rs) / ns_per_us) / float(n_loops)

        max_diff = float(
            max(
                np.max(np.abs(py_logits - wasm_logits)),
                np.max(np.abs(py_logits - c_logits)),
                np.max(np.abs(py_logits - rs_logits)),
            )
        )
        tol = float(self.num["logit_parity_tol"])
        six_d = int(self.num["six_digits"])
        sub_us_cap = float(self.num["max_sub_microsecond_us"])

        return {
            "wasm_byte_size": int(compiled["wasm_byte_size"]),
            "expected_wasm_bytes": int(self.tspec["expected_wasm_bytes"]),
            "wasm_per_call_us": round(wasm_us, six_d),
            "c99_per_call_us": round(c99_us, six_d),
            "rust_nostd_per_call_us": round(rust_us, six_d),
            "max_four_way_logit_diff": round(max_diff, six_d),
            "four_way_parity_ok": bool(max_diff <= tol),
            "exact_class_agreement": bool(
                np.array_equal(py_preds, wasm_preds)
                and np.array_equal(py_preds, c_preds)
                and np.array_equal(py_preds, rs_preds)
            ),
            "sub_microsecond_verified": bool(wasm_us < sub_us_cap and c99_us < sub_us_cap and rust_us < sub_us_cap),
            "sink_guard": sink_c + sink_rs,
        }


class DpWoodburyPersonalizer:
    """Closed-form (epsilon, delta)-DP Sherman-Morrison-Woodbury multi-account NAS folder/tag personalizer."""

    def __init__(self, grid: NodeGrid) -> None:
        self.grid = grid
        self.dpcfg = grid.raw_spec["dp_constants"]
        self.num = grid.raw_spec["numerical_constants"]

    def calibrate_gaussian_dp(
        self,
        *,
        epsilon: float,
        delta: float,
        clip_norm: float,
    ) -> dict[str, Any]:
        """Calibrate Gaussian mechanism noise scales and Moments / Renyi-DP composed epsilon."""
        c_const = float(self.dpcfg["gaussian_c_const"])
        two_f = float(int(self.num["two"]))
        eps_g = epsilon * float(self.dpcfg["gram_budget_share"])
        eps_r = epsilon * float(self.dpcfg["rhs_budget_share"])
        delta_part = delta * float(self.dpcfg["delta_split_share"])

        sens_gram = clip_norm * clip_norm
        sens_rhs = clip_norm
        sigma_gram = sens_gram * math.sqrt(two_f * math.log(c_const / delta_part)) / eps_g
        sigma_rhs = sens_rhs * math.sqrt(two_f * math.log(c_const / delta_part)) / eps_r

        a_min = int(self.dpcfg["rdp_alpha_min"])
        a_max = int(self.dpcfg["rdp_alpha_max"])
        best_rdp_eps = float("inf")
        best_alpha = a_min
        log_inv_delta = math.log(1.0 / delta)
        for alpha in range(a_min, a_max + 1):
            rdp_g = float(alpha) * (sens_gram * sens_gram) / (two_f * sigma_gram * sigma_gram)
            rdp_r = float(alpha) * (sens_rhs * sens_rhs) / (two_f * sigma_rhs * sigma_rhs)
            cand = (rdp_g + rdp_r) + log_inv_delta / float(alpha - 1)
            if cand < best_rdp_eps:
                best_rdp_eps = cand
                best_alpha = alpha

        six_d = int(self.num["six_digits"])
        return {
            "target_epsilon": epsilon,
            "target_delta": delta,
            "sigma_gram": round(sigma_gram, six_d),
            "sigma_rhs": round(sigma_rhs, six_d),
            "rdp_composed_epsilon": round(best_rdp_eps, six_d),
            "optimal_rdp_alpha": best_alpha,
        }

    def export_account_dp_sufficient_stats(
        self,
        *,
        rng: np.random.Generator,
        x_subspace_events: np.ndarray,
        y_onehot: np.ndarray,
        clip_norm: float,
        dp_calib: dict[str, Any],
    ) -> dict[str, Any]:
        """Clip per-file 24-d vectors and emit PSD-projected (epsilon, delta)-DP sufficient statistics (0 filenames)."""
        x_mat = np.asarray(x_subspace_events, dtype=np.float64)
        y_mat = np.asarray(y_onehot, dtype=np.float64)
        n_ev = int(x_mat.shape[0])
        d_sub = int(x_mat.shape[1])
        k_cls = int(y_mat.shape[1])

        clipped = np.zeros((n_ev, d_sub), dtype=np.float64)
        for idx in range(n_ev):
            norm_v = float(np.linalg.norm(x_mat[idx]))
            scale = max(1.0, norm_v / clip_norm)
            clipped[idx] = x_mat[idx] / scale

        gram_clean = clipped.T @ clipped
        rhs_clean = clipped.T @ y_mat

        raw_g_noise = rng.normal(0.0, float(dp_calib["sigma_gram"]), size=(d_sub, d_sub))
        sym_noise = np.triu(raw_g_noise) + np.triu(raw_g_noise, k=1).T
        eigvals, eigvecs = np.linalg.eigh(gram_clean + sym_noise)
        eigvals_psd = np.maximum(0.0, eigvals)
        gram_dp = (eigvecs * eigvals_psd[None, :]) @ eigvecs.T

        rhs_dp = rhs_clean + rng.normal(0.0, float(dp_calib["sigma_rhs"]), size=(d_sub, k_cls))
        return {
            "gram_dp": gram_dp,
            "rhs_dp": rhs_dp,
            "raw_filenames_exported": 0,
        }

    def fuse_via_woodbury(
        self,
        *,
        account_exports: list[dict[str, Any]],
        ridge_lambda: float,
    ) -> np.ndarray:
        """Closed-form rank-1 Sherman-Morrison-Woodbury fusion over PSD eigen-factors."""
        d_sub = int(account_exports[0]["rhs_dp"].shape[0])
        k_cls = int(account_exports[0]["rhs_dp"].shape[1])
        eps = float(self.num["eps"])

        h_inv = (1.0 / ridge_lambda) * np.eye(d_sub, dtype=np.float64)
        rhs_total = np.zeros((d_sub, k_cls), dtype=np.float64)

        for pkt in account_exports:
            rhs_total = rhs_total + pkt["rhs_dp"]
            eigvals, eigvecs = np.linalg.eigh(pkt["gram_dp"])
            for c_idx in range(d_sub):
                lam = float(eigvals[c_idx])
                if lam > eps:
                    u_vec = math.sqrt(lam) * eigvecs[:, c_idx]
                    hu = h_inv @ u_vec
                    denom = 1.0 + float(u_vec @ hu)
                    h_inv = h_inv - np.outer(hu, hu) / denom

        return (h_inv @ rhs_total).astype(np.float32)

    def run_personalization_benchmark(
        self,
        regime_id: str = "home_family_nas_regime",
    ) -> dict[str, Any]:
        """Measure accuracy uplift of closed-form (epsilon, delta)-DP Woodbury personalization across family/team users."""
        _, cell = self.grid.resolve_regime_cell(regime_id)
        d_sub = int(cell["subspace_dim"])
        eps_target = float(cell["dp_target_epsilon"])
        delta_target = float(cell["dp_target_delta"])
        clip_norm = float(cell["dp_l2_clip_norm"])
        ridge_lam = float(cell["woodbury_ridge_lambda"])

        k_cls = int(self.dpcfg["folder_class_count"])
        n_users = int(self.num["personalization_user_count"])
        n_train = int(self.num["personalization_train_per_user"])
        n_eval = int(self.num["personalization_eval_per_user"])
        seed_idx = int(self.num["two"])
        rng = np.random.default_rng(int(self.grid.raw_spec["seeds"][seed_idx]))

        # Shared household/team folder prototypes in 24-d subspace
        q_proto, _ = np.linalg.qr(rng.standard_normal((d_sub, d_sub)))
        class_centroids = q_proto[:, :k_cls].T  # [4, 24]

        dp_cal = self.calibrate_gaussian_dp(epsilon=eps_target, delta=delta_target, clip_norm=clip_norm)
        exports: list[dict[str, Any]] = []
        eval_x_list: list[np.ndarray] = []
        eval_y_list: list[int] = []

        noise_std = 1.0 / float(int(self.num["five"]))
        for _ in range(n_users):
            labels_tr = rng.integers(0, k_cls, size=n_train)
            x_tr = class_centroids[labels_tr] + rng.normal(0.0, noise_std, size=(n_train, d_sub))
            x_tr = x_tr / np.maximum(np.linalg.norm(x_tr, axis=1, keepdims=True), float(self.num["eps"]))
            y_tr = np.eye(k_cls, dtype=np.float64)[labels_tr]
            exports.append(
                self.export_account_dp_sufficient_stats(
                    rng=rng,
                    x_subspace_events=x_tr,
                    y_onehot=y_tr,
                    clip_norm=clip_norm,
                    dp_calib=dp_cal,
                )
            )

            labels_ev = rng.integers(0, k_cls, size=n_eval)
            x_ev = class_centroids[labels_ev] + rng.normal(0.0, noise_std, size=(n_eval, d_sub))
            x_ev = x_ev / np.maximum(np.linalg.norm(x_ev, axis=1, keepdims=True), float(self.num["eps"]))
            eval_x_list.append(x_ev)
            eval_y_list.extend(int(v) for v in labels_ev)

        x_eval_all = np.vstack(eval_x_list).astype(np.float32)
        y_eval_arr = np.asarray(eval_y_list, dtype=np.int64)

        # Unpersonalized zero-prior baseline vs DP-Woodbury fused classifier
        w_unpersonalized = np.eye(d_sub, k_cls, dtype=np.float32)
        base_preds = np.argmax(x_eval_all @ w_unpersonalized, axis=1)
        base_acc = float(np.mean(base_preds == y_eval_arr))

        w_dp = self.fuse_via_woodbury(account_exports=exports, ridge_lambda=ridge_lam)
        dp_preds = np.argmax(x_eval_all @ w_dp, axis=1)
        dp_acc = float(np.mean(dp_preds == y_eval_arr))

        rd = int(self.num["round_digits"])
        return {
            "regime_id": regime_id,
            "user_accounts_fused": n_users,
            "target_epsilon": eps_target,
            "target_delta": delta_target,
            "rdp_composed_epsilon": dp_cal["rdp_composed_epsilon"],
            "unpersonalized_accuracy": round(base_acc, rd),
            "dp_woodbury_accuracy": round(dp_acc, rd),
            "accuracy_uplift": round(dp_acc - base_acc, rd),
            "raw_filenames_leaked": sum(int(e["raw_filenames_exported"]) for e in exports),
        }
