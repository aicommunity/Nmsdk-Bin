#!/usr/bin/env bash
set -euo pipefail
ROOT="$(cd "$(dirname "$0")/.." && pwd)"
COPY="$ROOT/../scripts/copy_cell.sh"

CELLS=(
  "A_C25e12_R1e7_S86e6|2.5e-11|1e7|8.6e7|238.09524|ISI~4.2ms"
  "B_C1e11_R1e7_S5e7|1e-11|1e7|5e7|238.09524|ISI~4.2ms"
  "C_C5e12_R5e6_S4e7|5e-12|5e6|4e7|238.09524|ISI~4.2ms"
  "A_C25e12_R1e7_S86e6_ISI50|2.5e-11|1e7|8.6e7|119.04762|ISI~8.4ms"
  "A_C25e12_R1e7_S86e6_ISI100|2.5e-11|1e7|8.6e7|59.52381|ISI~16.8ms"
  "sweep_C1e11_R5e6_S86e6|1e-11|5e6|8.6e7|238.09524|ISI~4.2ms"
  "sweep_C25e12_R5e6_S86e6|2.5e-11|5e6|8.6e7|238.09524|ISI~4.2ms"
  "ctrl_C25e11_R1e7_S86e6|2.5e-10|1e7|8.6e7|238.09524|FastResponse_C"
)

mkdir -p "$ROOT/cells"
for cell in "${CELLS[@]}"; do
  IFS='|' read -r id C Rm Rsyn Freq note <<<"$cell"
  dst="$ROOT/cells/$id"
  rm -rf "$dst"
  bash "$COPY" "$ROOT/template" "$dst"
  python3 - "$dst" "$C" "$Rm" "$Rsyn" "$Freq" "$id" <<'PY'
import re, sys
from pathlib import Path
dst, C, Rm, Rsyn, Freq, cid = Path(sys.argv[1]), sys.argv[2], sys.argv[3], sys.argv[4], sys.argv[5], sys.argv[6]
def set_in_block(text, block, tag, value):
    def repl(m):
        b = m.group(0)
        return re.sub(rf"(<{tag}\b[^>]*>)[^<]*(</{tag}>)", rf"\g<1>{value}\2", b, count=0)
    return re.sub(rf"<{block}\b[^>]*>.*?</{block}>", repl, text, count=1, flags=re.S)
def set_tag(text, tag, value, count=1):
    return re.sub(rf"(<{tag}\b[^>]*>)[^<]*(</{tag}>)", rf"\g<1>{value}\2", text, count=count)
for name in ("Parameters_00.xml", "Model_00.xml"):
    p = dst/name
    t = p.read_text(encoding="utf-8")
    t = set_in_block(t, "ChannelUnderTest", "Capacity", C)
    t = set_in_block(t, "ChannelUnderTest", "Resistance", Rm)
    t = set_in_block(t, "ChannelUnderTest", "RestingResistance", Rm)
    t = set_in_block(t, "ChannelUnderTest", "FBResistance", Rm)
    t = set_in_block(t, "SynapseDrive", "Resistance", Rsyn)
    t = set_in_block(t, "SynapseDrive", "DissociationTC", "0.001")
    t = set_in_block(t, "SynapseDrive", "SecretionTC", "0.001")
    t = set_tag(t, "Frequency", Freq, 1)
    p.write_text(t)
ini = (dst/"project.ini").read_text()
ini = re.sub(r"<ProjectName>[^<]*</ProjectName>", f"<ProjectName>AsymRmSettle_{cid}</ProjectName>", ini)
(dst/"project.ini").write_text(ini)
print("cell", cid, "C", C, "Rm", Rm, "Rsyn", Rsyn, "F", Freq)
PY
done
echo "setup done: $(ls "$ROOT/cells" | wc -l) cells"
