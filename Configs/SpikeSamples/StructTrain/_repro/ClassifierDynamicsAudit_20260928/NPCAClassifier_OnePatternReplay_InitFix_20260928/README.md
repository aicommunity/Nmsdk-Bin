# NPCA one-pattern replay after child initialization fix

Release clone from the legacy PCATest example. Initial source/PCA Activities remain 0 in the XML snapshots. `NPCAClassifier::AReset` must now activate and initialize both dependencies before the first step, and park the nested classifier until all 80 PCA windows are collected. The input fixture has 101 scalar samples. Recorder captures source data and nested `NSPNeuronGen` LTZone output/potential. One selected row, not multiclass classification. Run: `NeuroModelerConsole.exe -c Project.ini -s -t 60 -x -S`.
