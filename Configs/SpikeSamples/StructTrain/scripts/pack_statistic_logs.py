#!/usr/bin/env python3
"""Pack StatisticLog / EventsLog dirs into tar.gz, then remove sources.

Does not touch SelectivityLog. Archives go under --arch-dir with a MANIFEST.tsv.
"""
from __future__ import annotations

import argparse
import os
import shutil
import subprocess
import sys
from pathlib import Path


def dir_size_bytes(path: Path) -> int:
    total = 0
    for root, _dirs, files in os.walk(path):
        for name in files:
            fp = Path(root) / name
            try:
                total += fp.stat().st_size
            except OSError:
                pass
    return total


def safe_name(rel: str) -> str:
    # SelectivityAsymRm/EXP_x/Train/StatisticLog -> AsymRm__EXP_x__Train__StatisticLog
    parts = Path(rel).parts
    if not parts:
        return "empty"
    family = parts[0]
    short = {
        "SelectivityAsymRm": "AsymRm",
        "SelectivityBranch": "Branch",
        "SelectivityLtzCalibrate": "LtzCal",
        "SelectivityPresynapticInhib": "PSI",
        "SelectivityPhaseA": "PhaseA",
        "SelectivityFastResponse": "FastResponse",
        "SelectivityFastSpan": "FastSpan",
        "TimeNeuronTimeLearner": "TL",
        "TimeNeuronTimeLearnerBranch": "TLBranch",
        "TimeNeuronTimeLearnerBranch_PreInh250": "TLBranchPreInh250",
        "TimeNeuronTimeLearnerBranch_NextSegInh": "TLBranchNextSeg",
    }.get(family, family)
    rest = "__".join(parts[1:]) if len(parts) > 1 else "root"
    name = f"{short}__{rest}".replace(" ", "_")
    return name[:200]


def free_bytes(path: Path) -> int:
    st = os.statvfs(path)
    return st.f_bavail * st.f_frsize


def find_targets(root: Path, min_bytes: int) -> list[Path]:
    out: list[Path] = []
    for dirpath, dirnames, _files in os.walk(root):
        # prune archives and VCS
        base = Path(dirpath)
        rel = base.relative_to(root).as_posix() if base != root else ""
        if "/archives/" in f"/{rel}/" or rel.startswith("archives"):
            dirnames[:] = []
            continue
        if ".git" in dirnames:
            dirnames.remove(".git")
        for name in ("StatisticLog", "EventsLog"):
            if name in dirnames:
                cand = base / name
                # don't descend into the log dirs for further walk of same names
                try:
                    sz = dir_size_bytes(cand)
                except OSError:
                    continue
                if sz >= min_bytes:
                    out.append(cand)
        # prevent walking into StatisticLog/EventsLog themselves
        dirnames[:] = [d for d in dirnames if d not in ("StatisticLog", "EventsLog")]
    # largest first (free space sooner)
    out.sort(key=lambda p: dir_size_bytes(p), reverse=True)
    return out


def pack_one(src: Path, root: Path, arch_dir: Path, dry_run: bool) -> tuple[str, int, str, str]:
    rel = src.relative_to(root).as_posix()
    size = dir_size_bytes(src)
    archive_name = safe_name(rel) + ".tar.gz"
    tar_path = arch_dir / archive_name
    parent = src.parent
    basename = src.name

    if dry_run:
        return rel, size, archive_name, "dry_run"

    # Need room for gzip output (approx size; compressed usually smaller, but
    # peak before rm can approach size + compressed). Require free > size.
    avail = free_bytes(arch_dir)
    if avail < size:
        return rel, size, archive_name, f"fail_space_need_{size}_have_{avail}"

    if tar_path.exists():
        # unique suffix
        stem = tar_path.stem  # ends with .tar
        # archive_name is foo.tar.gz -> stem foo.tar
        n = 1
        while tar_path.exists():
            tar_path = arch_dir / f"{safe_name(rel)}_{n}.tar.gz"
            n += 1
        archive_name = tar_path.name

    # gzip -1: much faster on multi‑GB StatisticLog; still reclaimable after rm
    cmd = [
        "tar",
        "--use-compress-program=gzip -1",
        "-cf",
        str(tar_path),
        "-C",
        str(parent),
        basename,
    ]
    try:
        subprocess.run(cmd, check=True, capture_output=True)
    except subprocess.CalledProcessError as e:
        err = (e.stderr or b"").decode("utf-8", errors="replace")[:200]
        if tar_path.exists():
            tar_path.unlink(missing_ok=True)
        return rel, size, archive_name, f"fail_tar:{err}"

    if not tar_path.exists() or tar_path.stat().st_size <= 0:
        return rel, size, archive_name, "fail_empty_archive"

    # light verify
    try:
        listing = subprocess.run(
            ["tar", "-tzf", str(tar_path)],
            check=True,
            capture_output=True,
            text=True,
        )
        if not listing.stdout.strip():
            tar_path.unlink(missing_ok=True)
            return rel, size, archive_name, "fail_empty_listing"
    except subprocess.CalledProcessError:
        tar_path.unlink(missing_ok=True)
        return rel, size, archive_name, "fail_verify"

    shutil.rmtree(src)
    return rel, size, archive_name, "ok"


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--root", type=Path, required=True)
    ap.add_argument("--arch-dir", type=Path, required=True)
    ap.add_argument("--min-bytes", type=int, default=209715200)
    ap.add_argument("--dry-run", action="store_true")
    args = ap.parse_args()

    root = args.root.resolve()
    arch_dir = args.arch_dir.resolve()
    arch_dir.mkdir(parents=True, exist_ok=True)
    man = arch_dir / "MANIFEST.tsv"
    if not man.exists():
        man.write_text("rel_path\tsize_bytes\tarchive\tstatus\n", encoding="utf-8")

    targets = find_targets(root, args.min_bytes)
    print(f"found {len(targets)} dirs >= {args.min_bytes} under {root}", flush=True)

    ok = 0
    fail = 0
    for i, src in enumerate(targets, 1):
        print(f"[{i}/{len(targets)}] packing {src.relative_to(root)} ...", flush=True)
        rel, size, archive_name, status = pack_one(src, root, arch_dir, args.dry_run)
        with man.open("a", encoding="utf-8") as f:
            f.write(f"{rel}\t{size}\t{archive_name}\t{status}\n")
        print(f"  -> {status} archive={archive_name} size={size}", flush=True)
        if status == "ok" or status == "dry_run":
            ok += 1
        else:
            fail += 1
            if status.startswith("fail_space"):
                print("abort: not enough free space for next large pack", flush=True)
                break

    print(f"done ok={ok} fail={fail} manifest={man}", flush=True)
    return 1 if fail else 0


if __name__ == "__main__":
    sys.exit(main())
