# StatisticLog / EventsLog archives (PHASE10 S0)

- Stamp: `20260914T161650Z`
- Packer: `scripts/pack_statistic_logs.py` (gzip -1)
- Entries: 111 ok / 0 fail (see MANIFEST.tsv)
- df before: 142G avail (69% used)
- df after: 308G avail (31% used)
- StructTrain: 201G → 35G

Restore one log:

```bash
tar -xzf ARCHIVE.tar.gz -C path/to/Train_or_Test/
```

SelectivityLog / ltz_sweep were **not** packed.
