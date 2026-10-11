# Archived TimeLearner audit build metadata

This directory records provenance for local Windows Console variants assembled for the TimeLearner audit from root 4a5b36b, PulseLib 2bb72a3, and Bin 2a55692.

file-manifest.json records sizes and SHA-256 values of artifacts present during consolidation. Executables and .projecthist files are intentionally not committed; the manifest is a checksum record, not a promise that those files are present in a fresh checkout.

The archived NeuroModelerConsole.ini was byte-identical to the canonical Platform/Win/NeuroModelerConsole.ini, so the duplicate was removed. Per-run Console hashes and source pins remain in the provenance bundles under Configs/SpikeSamples/StructTrain/_repro/runs/.