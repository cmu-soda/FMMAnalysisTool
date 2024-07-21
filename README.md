# FMMFSM_simulator
There are three folders in this FMMFSM simulator: FMMFSM_tester, FMMFSM_analyzer, and FMMFSM_analyzer_Tl.
There are three code files respectively for each folder.
- FMMFSM.py: Code for calculating the degree of membership of an FMMFSM.
- discreteSystemModel.py: Code for simulating the state transitions of a system model.
- outputChecker.py: Code for checking for mode confusions by comparing the FMMFSM and the system model.
The usage and code is different for each directory as detailed below.

## FMMFSM_tester
FMMFSM_tester is the minimal tester you can use to analyze a single pair of FMMFSM and system model.
For FMMFSM, you need to specify:
- "initial_state_memberships": m_0 vector
- "input_fuzzified": alpha
- "transition_probabilities": phi
- "action_schedule"

For system model, you need to specify:
- "initial_state": m_0
- "transitions"
- "action_schedule"

"action_schedule" should be the same for a pair of FMMFSM and system model.
Please refer to the FMMFSM paper to more information about how to specify a FMMFSM and system model. Examples can be found in FMMFSM_tester/use_cases

## FMMFSM_analyzer & FMMFSM_analyzer_Tl
FMMFSM_analyzer and FMMFSM_analyzer_Tl together make the FMMFSM analysis tool. FMMFSM_analyzer includes scripts that does not handle task labels, while FMMFSM_analyzer_Tl handle task labels.

Input for FMMFSM_analyzer is the same as for the FMMFSM_tester expect the user should not include "action_schedule". FMMFSM_analyzer handles the random generatioin of action schedule.

Input for FMMFSM_analyzer_Tl is the same as for the FMMFSM_analyzer expect the user need to specify "task_labels" for both FMMFSM and system model. You could find an example in the FMMFSM_analyzer_Tl/config directory.

To use the FMMFSM analysis tool, you first run the run.py:

```bat
python run.py PATH_TO_FMMFSM_CONFIG_FILE PATH_TO_SYSTEM_CONFIG_FILE --num NUM_OF_ACTIONS --iter NUM_OF_ITERATIONS
```

PATH_TO_FMMFSM_CONFIG_FILE and PATH_TO_SYSTEM_CONFIG_FILE need to be in the FMMFSM_analyzer/config or FMMFSM_analyzer_Tl (if includes task labels) directory, and the corresponding output would be saved in the corresponding experiment folder (with time stamp) in the corresponding output folder.

NUM_OF_ACTIONS is the number of actions you want the simulator to randomly generate for a single file.

NUM_OF_ITERATIONS is the number of files you want the simulator to run for a single experiment.

Use --postp flag to save both the original results and the post-processed results (disregard all following errors identified after a blocking state).

Use --tl flag to use FMMFSM_analyzer_Tl instead of FMMFSM_analyzer.

An output from run.py includes:
- A computed directory, which includes one file for the FMMFSM simulation result (end with FMMFSM_Result.json) two files for he system simulation result (Sys_Binary.json: binary result; Sys_Readable.json: For readability), and a result file that includes the analysis result from outputChecker.py.
- A config directory, which includes all config files with the randomly generated action schedules.

After you run the run.py, you can run the analyze.py to summarize findings from the analysis results:

```bat
python analyze.py PATH_TO_EXPERIMENT_FOLDER
```

Use flag --postp to save the summarization for post-processed results.

Use flag --all to save the summarization for pre-processed results.

Use flag --save to save the summarization to a file in the output folder: we recommand you do this every time since the summarization could be too long to read in the terminal.

Use flag --tl if you include task labels in the analysis.