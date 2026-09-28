# Iris compatibility replay with 2022 synapse defaults

Fresh clone of the original `SpikeIrisClassifier` model and parameters. It uses the post-fix Release console and the same trainer settings as `SpikeIrisClassifier_TrainerCrossingFix_20260927`; only the test executable's `NPulseSynapse::ADefault()` values are temporarily built to match the library between commits `5f3f06d` and `0be546f` (`Resistance=100e6`, `SecretionTC=0.002`, `DissociationTC=0.002`).

This isolates the historical new-synapse defaults documented in the Iris report. The stored neuron model, trainer settings, `SynapseResistanceStep`, pulse parameters, and stopping horizon remain unchanged. Do not treat these historical defaults as current production defaults. Run/result: pending.