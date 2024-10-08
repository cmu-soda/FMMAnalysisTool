# FMM Analysis Tool
This branch contains the code version of the FMM Analysis Tool for the paper "Fuzzy Mental Models: A Formalism for Reasoning About Vagueness and Confusion in Human Machine Interaction," and the results of the two case studies in the paper.

There are three code files in the FMM_Analysis_TL repo:
- FMMFSM.py: Code for calculating the degree of membership of an FMMFSM.
- discreteSystemModel.py: Code for simulating the state transitions of a system model.
- outputChecker.py: Code for checking for mode confusions by comparing the FMMFSM and the system model.

## FMM_Analysis_TL
FMM_Analysis_TL handles the random generatioin of action schedule ("action_schedule"). Input for FMM_Analysis_TL that the user need to specify includes:
For FMM, you need to specify:
- "initial_state_memberships": m_0 vector
- "input_fuzzified": alpha
- "transition_probabilities": phi
- "task_labels"

For system model, you need to specify:
- "initial_state": m_0
- "transitions"
- "task_labels"

You can find example inputs in the FMM_Analysis_TL/config directory.

To use the FMM analysis tool, you first run the run.py:

```bat
python run.py PATH_TO_FMM_CONFIG_FILE PATH_TO_SYSTEM_CONFIG_FILE --num NUM_OF_ACTIONS --iter NUM_OF_ITERATIONS --tl
```

PATH_TO_FMM_CONFIG_FILE and PATH_TO_SYSTEM_CONFIG_FILE need to be in the FMM_Analysis_TL/config directory, and the corresponding output will be saved in the corresponding experiment folder (with time stamp) in the corresponding output folder.

NUM_OF_ACTIONS is the number of actions you want the simulator to randomly generate for a single file.

NUM_OF_ITERATIONS is the number of files you want the simulator to run for a single experiment.

Use --postp flag to save both the original results and the post-processed results (disregard all following errors identified after a blocking state).

An output from run.py includes:
- A computed directory, which includes one file for the FMM simulation result (end with FMMFSM_Result.json) two files for he system simulation result (Sys_Binary.json: binary result; Sys_Readable.json: For readability), and a result file that includes the analysis result from outputChecker.py.
- A config directory, which includes all config files with the randomly generated action schedules.

After you run the run.py, you can run the analyze.py to summarize findings from the analysis results:

```bat
python analyze.py PATH_TO_EXPERIMENT_FOLDER
```

Use flag --postp to save the summarization for post-processed results.

Use flag --all to save the summarization for pre-processed results.

Use flag --save to save the summarization to a file in the output folder: we recommand you do this every time since the summarization could be too long to read in the terminal.
