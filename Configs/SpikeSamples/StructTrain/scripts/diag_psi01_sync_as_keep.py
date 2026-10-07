#!/usr/bin/env python3
"""Diag Inv2: SoftCold psi01_050 with SyncTol/EstDelay patched to asym50-keep values.

Does NOT mutate production archives. SKIP registry. SoftCold Need→0 gate unchanged.
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))

import posttune_verify as pv  # noqa: E402
from repro_cold_lib import set_tag_all, soft_cold_reset_train as _soft_cold_orig  # noqa: E402

SYNC_KEEP = "0.00208333"
EST_KEEP = "0.002"
DIAG_NOTE = ROOT / "_repro" / "diag" / "psi01_sync_as_keep"
DIAG_NOTE.mkdir(parents=True, exist_ok=True)


def _patch_sync_est(train: Path) -> list[str]:
    patched: list[str] = []
    for rel in ("Parameters_00.xml", "Model_00.xml"):
        p = train / rel
        if not p.exists():
            continue
        t = p.read_text(encoding="utf-8")
        t2 = set_tag_all(t, "SyncTolerance", SYNC_KEEP)
        t2 = set_tag_all(t2, "EstDelayPerSeg", EST_KEEP)
        if t2 != t:
            p.write_text(t2, encoding="utf-8")
            patched.append(rel)
    return patched


def soft_cold_then_patch(train: Path, *, autosave_model_s: int = 10) -> None:
    """Soft-cold first; Sync/EstDelay re-applied after run_case's sync_estdelay_from_gold."""
    _soft_cold_orig(train, autosave_model_s=autosave_model_s)
    # Tentative patch (may be overwritten by sync_estdelay_from_gold if gold forces EstDelay).
    _patch_sync_est(train)


def main() -> int:
    pv.soft_cold_reset_train = soft_cold_then_patch  # type: ignore[attr-defined]
    _orig_run_case = pv.run_case

    def run_case_repatch(name: str, **kwargs):
        # Intercept: after soft_cold+sync inside run_case we cannot hook mid-flight easily;
        # re-patch Train XML immediately after soft_cold via wrapping is incomplete.
        # Instead wrap at start and also patch once run_case returns Train still on disk —
        # too late for Train. So: patch again by wrapping the post-soft_cold section via
        # monkeypatch of sync_estdelay_from_gold.
        return _orig_run_case(name, **kwargs)

    import repro_cold_lib as rcl

    _sync_orig = rcl.sync_estdelay_from_gold

    def sync_then_repatch(train: Path, gold_train: Path) -> None:
        _sync_orig(train, gold_train)
        patched = _patch_sync_est(train)
        meta = {
            "case": "psi01_050",
            "diag": "sync_as_keep",
            "SyncTolerance": SYNC_KEEP,
            "EstDelayPerSeg": EST_KEEP,
            "patched_train_rels": patched,
            "workdir": str(train.parent),
            "after_sync_estdelay": True,
        }
        (DIAG_NOTE / "last_patch.json").write_text(
            json.dumps(meta, indent=2) + "\n", encoding="utf-8"
        )
        print(
            f"  DIAG patch (post-sync) SyncTolerance={SYNC_KEEP} "
            f"EstDelayPerSeg={EST_KEEP} rels={patched} work={train.parent}"
        )

    rcl.sync_estdelay_from_gold = sync_then_repatch  # type: ignore[attr-defined]
    # run_case imports sync_estdelay_from_gold locally inside the function — must patch
    # at module used by that import. It does `from repro_cold_lib import ... sync_estdelay_from_gold`
    # INSIDE run_case, so patching rcl is enough if done before that import executes.
    row = run_case_repatch(
        "psi01_050",
        snap_every=20,
        autosave_model_s=10,
        stall_autosave_n=8,
        keep_slog=False,
    )
    # SoftCold-style print (mirrors parallel runner)
    need = (row.get("after") or {}).get("IsNeedToTrain", "?")
    tipr = (row.get("after") or {}).get("TipSynapseResistance", "")
    L = (row.get("after") or {}).get("DendriteLength", "")
    ok = not row.get("row_fail", True)
    print(
        f"DIAG_PSI01_SYNC_AS_KEEP ok={int(ok)} Need={need} tipr={tipr} L={L} "
        f"fail_notes={row.get('fail_notes')} mid_source={row.get('mid_source')} "
        f"gate_ok={row.get('gate_ok')} run_dir={row.get('run_dir')}"
    )
    (DIAG_NOTE / "last_result.json").write_text(
        json.dumps(
            {
                "ok": ok,
                "Need": need,
                "tipr": tipr,
                "L": L,
                "fail_notes": row.get("fail_notes"),
                "mid_source": row.get("mid_source"),
                "gate_ok": row.get("gate_ok"),
                "gate_rc": row.get("gate_rc"),
                "run_dir": row.get("run_dir"),
                "failure_class": row.get("failure_class"),
            },
            indent=2,
        )
        + "\n",
        encoding="utf-8",
    )
    return 0 if ok else 1


if __name__ == "__main__":
    raise SystemExit(main())
