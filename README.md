# FMMFSM_simulator
There are three folders in this FMMFSM simulator tool: FMMFSM_tester, FMMFSM_analyzer, and FMMFSM_analyzer_Tl.
There are three code files respectively for each folder.
- FMMFSM.py: Code for calculating the degree of membership of an FMMFSM.
- discreteSystemModel.py: Code for simulating the state transitions of a system model.
- outputChecker.py: Code for checking for mode confusions by comparing the FMMFSM and the system model.
The usage and code is different for each directory as detailed below.

## FMMFSM_tester
FMMFSM_tester is the minimal tester you can use to analyze a single pair of FMMFSM and system model.
For FMMFSM, you need to specify:
- "initial_state_memberships"
- "input_fuzzified"
- "transition_probabilities"
- "action_schedule"

For system model, you need to specify:
- "initial_state"
- "transitions"
- "action_schedule"

"action_schedule" should be the same for a pair of FMMFSM and system model.
