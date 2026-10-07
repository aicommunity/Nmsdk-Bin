# HardwareCatalog

Canonical catalog for boards / shields / modules / firmwares (JSON + SVG + reference PDFs).

**Runtime mirror:** `Bin/HardwareCatalog` via:

```bash
python3 Scripts/import_modules_catalog_xlsx.py   # optional refresh from xlsx
python3 Scripts/sync_hardware_catalog.py
# optional: python3 Scripts/sync_hardware_catalog.py --dest /path/to/Bin/HardwareCatalog
```

Source spreadsheets: [Docs/ArduinoShields/README.md](../Docs/ArduinoShields/README.md).

NeuroModeler resolves the catalog through `UHardwareCatalogPaths` (`RDK_HARDWARE_CATALOG_DIR` or relative work-dir path).

Edit sources here only; re-sync before shipping Bin.
