# Synthetic competition dynamics: lateral inhibition On

Clone of the verified 0.006 threshold replay, retaining all four synthetic input patterns. The trained structures and all physical parameters are unchanged. `DataFromFile` is set to 1 in the experiment clone because completed source replays persist it as 0 after EOF. This probe captures the source class LTZone outputs, target somas, input dendrites, inhibitory synapse 1/2 direct inputs (`OutInCopy`) and conductance outputs, and inhibitory channel outputs/inputs. In this wiring, class 1 drives `InhSynapse1` and class 3 drives `InhSynapse2` on class 2.

Run: `NeuroModelerConsole.exe -c Project.ini -s -t 8.01 -x -S`.
