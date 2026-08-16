# HardwareCatalog

Canonical catalog for boards / shields / modules / firmwares (JSON + SVG + reference PDFs).

**Runtime mirror:** `Bin/HardwareCatalog` via:

```bash
python Scripts/sync_hardware_catalog.py
python Scripts/validate_hardware_catalog.py
python Scripts/validate_hardware_catalog.py --root Bin/HardwareCatalog
```

NeuroModeler resolves the catalog through `UHardwareCatalogPaths` (`RDK_HARDWARE_CATALOG_DIR` or relative work-dir path).

Edit sources here only; re-sync before shipping Bin.
