import os
import json
import argparse
from collections import defaultdict

def parse_arguments():
    parser = argparse.ArgumentParser(description="Analyze the output of an experiment")
    parser.add_argument("experiment_folder", help="Path to the experiment folder")
    parser.add_argument("--postp", action="store_true", help="Analyze only post-processed files (default)")
    parser.add_argument("--all", action="store_true", help="Analyze only non-post-processed files")
    parser.add_argument("--save", action="store_true", help="Save the analysis results to a file")
    parser.add_argument("--tl", action="store_true", help="Use the code in FMMFSM_analyzer_Tl")
    args = parser.parse_args()

    # Set default flag if none provided
    if not args.postp and not args.all:
        args.postp = True

    return args

def analyze_experiment_folder(experiment_folder, analyze_postp, save_results, use_tl):
    computed_folder = os.path.join(experiment_folder, 'computed')
    
    if not os.path.exists(computed_folder):
        print(f"Computed folder does not exist: {computed_folder}")
        return
    
    result_files = []

    # Traverse the computed folder to find result files in each subfolder
    print(f"Analyzing experiment folder: {computed_folder}")
    for subdir in os.listdir(computed_folder):
        result_folder = os.path.join(computed_folder, subdir, 'result')
        if os.path.exists(result_folder):
            for file in os.listdir(result_folder):
                if analyze_postp and file.endswith('PostProcessed_Result.json'):
                    result_file_path = os.path.join(result_folder, file)
                    result_files.append(result_file_path)
                elif not analyze_postp and file.endswith('Result.json') and not file.endswith('PostProcessed_Result.json'):
                    result_file_path = os.path.join(result_folder, file)
                    result_files.append(result_file_path)

    total_files = len(result_files)
    result_lines = [f"Total result files found: {total_files}\n"]

    error_types = {
        "Dominant Error State Check": 0,
        "Nondeterministic Confusion Check": 0,
        "Vacuous Confusion Check": 0,
        "Dominant Blocking State Check": 0,
        "Dominant Task Labels Blocking State Check": 0,
        "Task Label Mismatch Check": 0,
        "Task Label Nondeterministic Confusion Check": 0  # New error type
    }

    state_errors = defaultdict(lambda: defaultdict(int))
    action_errors = defaultdict(lambda: defaultdict(int))
    previous_state_action_errors = defaultdict(lambda: defaultdict(int))
    previous_state_action_confusions = defaultdict(lambda: defaultdict(int))
    blocking_errors = defaultdict(int)
    task_label_mismatch_errors = defaultdict(int)
    dominant_task_labels_blocking_errors = defaultdict(int)
    task_label_nondeterministic_confusion_errors = defaultdict(int)  # New error tracking
    compound_errors_count = 0
    compound_errors_by_previous = defaultdict(lambda: defaultdict(int))
    error_files = defaultdict(list)
    compound_error_files = defaultdict(list)
    files_with_errors = {error_type: set() for error_type in error_types.keys()}

    for result_file in result_files:
        relative_path = os.path.relpath(result_file, experiment_folder)
        with open(result_file, 'r') as file:
            results = json.load(file)
            for error_type in error_types.keys():
                if error_type in results:
                    has_error = False
                    compound_error = False
                    previous_state = "N/A"
                    previous_action = "N/A"
                    for idx, entry in enumerate(results[error_type]):
                        if error_type == "Dominant Error State Check":
                            if entry.get("Result") == "False":
                                if not compound_error:
                                    error_types[error_type] += 1
                                    has_error = True
                                    compound_error = True
                                    error_info = {
                                        "file": relative_path,
                                        "state": entry.get("FMMFSM State"),
                                        "action": entry.get("Action"),
                                        "is_compound_error": False,
                                        "Previous State": previous_state,
                                        "Previous Action": previous_action,
                                        "Fuzzy Max State": entry.get("Fuzzy Max State"),
                                        "Binary True State": entry.get("Binary True State")
                                    }
                                    previous_state = entry.get("FMMFSM State")
                                    previous_action = entry.get("Action")
                                    error_files[error_type].append(error_info)
                                    
                                    # Track the previous state and action errors for the initial error
                                    if idx > 0:
                                        prev_entry = results[error_type][idx - 1]
                                        prev_state = prev_entry.get("FMMFSM State")
                                        prev_action = prev_entry.get("Action")
                                        previous_state_action_errors[(prev_state, prev_action)][entry.get("FMMFSM State")] += 1
                                else:
                                    compound_errors_count += 1
                                    compound_errors_by_previous[(previous_state, previous_action)][entry.get("FMMFSM State")] += 1
                                    error_info = {
                                        "file": relative_path,
                                        "state": entry.get("FMMFSM State"),
                                        "action": entry.get("Action"),
                                        "is_compound_error": True,
                                        "Previous State": previous_state,
                                        "Previous Action": previous_action,
                                        "Fuzzy Max State": entry.get("Fuzzy Max State"),
                                        "Binary True State": entry.get("Binary True State")
                                    }
                                    compound_error_files[error_type].append(error_info)
                                if entry.get("FMMFSM State"):
                                    state_errors[entry.get("FMMFSM State")][error_type] += 1
                                if entry.get("Action"):
                                    action_errors[entry.get("Action")][error_type] += 1
                            else:
                                compound_error = False
                        elif error_type == "Task Label Mismatch Check":
                            has_error = True
                            error_types[error_type] += 1
                            fmmfsm_task_label = entry.get("FMMFSM Task Label")
                            system_task_label = entry.get("System Task Label")
                            error_info = {"file": relative_path, "FMMFSM Task Label": fmmfsm_task_label, "System Task Label": system_task_label}
                            task_label_mismatch_errors[(fmmfsm_task_label, system_task_label)] += 1
                            error_files[error_type].append(error_info)
                        elif error_type == "Task Label Nondeterministic Confusion Check":
                            has_error = True
                            error_types[error_type] += 1
                            task_labels = entry.get("FMMFSM Task Labels")
                            error_info = {"file": relative_path, "FMMFSM Task Labels": task_labels}
                            task_label_nondeterministic_confusion_errors[tuple(task_labels.keys())] += 1
                            error_files[error_type].append(error_info)
                        else:
                            if entry.get("Result") != "True":
                                has_error = True
                                error_types[error_type] += 1
                                state = entry.get("FMMFSM State")
                                action = entry.get("Action")
                                error_info = {"file": relative_path, "state": state, "action": action}
                                if error_type == "Nondeterministic Confusion Check":
                                    error_info["States"] = entry.get("States")

                                    # Get previous state and action if possible
                                    if idx > 0:
                                        previous_entry = results[error_type][idx - 1]
                                        previous_state = previous_entry.get("FMMFSM State")
                                        previous_action = previous_entry.get("Action")
                                        previous_state_action_confusions[(previous_state, previous_action)][state] += 1
                                        error_info["Previous State"] = previous_state
                                        error_info["Previous Action"] = previous_action
                                
                                elif error_type == "Dominant Blocking State Check":
                                    blocking_errors[(state, action)] += 1
                                elif error_type == "Dominant Task Labels Blocking State Check":
                                    dominant_task_labels_blocking_errors[(state, action)] += 1

                                error_files[error_type].append(error_info)
                                if state:
                                    state_errors[state][error_type] += 1
                                if action:
                                    action_errors[action][error_type] += 1
                    if has_error:
                        files_with_errors[error_type].add(relative_path)

    result_lines.append(f"Total files analyzed: {total_files}\n")
    for error_type, files in files_with_errors.items():
        count = len(files)
        percentage = (count / total_files) * 100 if total_files > 0 else 0
        result_lines.append(f"{error_type}: {percentage:.2f}% of files contain this error\n")

    result_lines.append("\nTotal Number of Each Error Type:\n")
    result_lines.append(f"Dominant Error State Check (Compound Errors): {compound_errors_count}\n")
    for error_type, count in error_types.items():
        result_lines.append(f"{error_type}: {count} occurrences\n")

    if previous_state_action_errors:
        result_lines.append("\nDominant Error Check by Previous State and Previous Action:\n")
        for (prev_state, prev_action), errors in previous_state_action_errors.items():
            for state, count in errors.items():
                result_lines.append(f"Previous State {prev_state}, Previous Action {prev_action} -> State {state}: {count} errors\n")

    if compound_errors_by_previous:
        result_lines.append("\nCompound Errors by Previous State and Previous Action:\n")
        for (prev_state, prev_action), errors in compound_errors_by_previous.items():
            for state, count in errors.items():
                result_lines.append(f"Previous State {prev_state}, Previous Action {prev_action} -> State {state}: {count} compound errors\n")

    if blocking_errors:
        result_lines.append("\nDominant Blocking State Check by State and Action:\n")
        for (state, action), count in blocking_errors.items():
            result_lines.append(f"State {state}, Action {action}: {count} errors\n")

    if dominant_task_labels_blocking_errors:
        result_lines.append("\nDominant Task Labels Blocking State Check by State and Action:\n")
        for (state, action), count in dominant_task_labels_blocking_errors.items():
            result_lines.append(f"State {state}, Action {action}: {count} errors\n")

    if task_label_mismatch_errors:
        result_lines.append("\nTask Label Mismatch Check by FMMFSM Task Label and System Task Label:\n")
        for (fmmfsm_task_label, system_task_label), count in task_label_mismatch_errors.items():
            result_lines.append(f"FMMFSM Task Label {fmmfsm_task_label}, System Task Label {system_task_label}: {count} errors\n")

    if task_label_nondeterministic_confusion_errors:
        result_lines.append("\nTask Label Nondeterministic Confusion Check by FMMFSM Task Labels:\n")
        for task_labels, count in task_label_nondeterministic_confusion_errors.items():
            result_lines.append(f"Task Labels {task_labels}: {count} errors\n")

    result_lines.append("\n\nErrors by Files:\n")
    for error_type, files in error_files.items():
        result_lines.append(f"\n{error_type}:\n")
        for error_info in files:
            file = error_info["file"]
            if error_type == "Dominant Error State Check":
                state = error_info["state"]
                action = error_info["action"]
                fuzzy_max_state = error_info.get("Fuzzy Max State")
                binary_true_state = error_info.get("Binary True State")
                previous_state = error_info.get("Previous State", "N/A")
                previous_action = error_info.get("Previous Action", "N/A")
                compound_status = "Compound Error" if error_info["is_compound_error"] else "Initial Error"
                result_lines.append(f"  {file} - {compound_status}, Previous State: {previous_state}, Previous Action: {previous_action}, FMMFSM State: {state}, Fuzzy Max State: {fuzzy_max_state}, Binary True State: {binary_true_state}\n")
            elif error_type == "Nondeterministic Confusion Check":
                state = error_info["state"]
                action = error_info["action"]
                states = error_info.get("States")
                previous_state = error_info.get("Previous State", "N/A")
                previous_action = error_info.get("Previous Action", "N/A")
                result_lines.append(f"  {file} - FMMFSM State: {state}, Action: {action}, States: {states}, Previous State: {previous_state}, Previous Action: {previous_action}\n")
            elif error_type == "Task Label Mismatch Check":
                fmmfsm_task_label = error_info["FMMFSM Task Label"]
                system_task_label = error_info["System Task Label"]
                result_lines.append(f"  {file} - FMMFSM Task Label: {fmmfsm_task_label}, System Task Label: {system_task_label}\n")
            elif error_type == "Task Label Nondeterministic Confusion Check":
                task_labels = error_info["FMMFSM Task Labels"]
                result_lines.append(f"  {file} - Task Labels: {task_labels}\n")
            else:
                state = error_info["state"]
                action = error_info["action"]
                result_lines.append(f"  {file} - FMMFSM State: {state}, Action: {action}\n")

    result_lines.append("\nDominant Error State Check (Compound Errors) by Files:\n")
    for error_type, files in compound_error_files.items():
        for error_info in files:
            file = error_info["file"]
            state = error_info["state"]
            action = error_info["action"]
            if error_type == "Dominant Error State Check":
                fuzzy_max_state = error_info.get("Fuzzy Max State")
                binary_true_state = error_info.get("Binary True State")
                previous_state = error_info.get("Previous State", "N/A")
                previous_action = error_info.get("Previous Action", "N/A")
                result_lines.append(f"  {file} - Compound Error, Previous State: {previous_state}, Previous Action: {previous_action}, FMMFSM State: {state}, Fuzzy Max State: {fuzzy_max_state}, Binary True State: {binary_true_state}\n")

    result_text = ''.join(result_lines)
    print(result_text)

    if save_results:
        analysis_filename = "analyzePostp.txt" if analyze_postp else "analyzeAll.txt"
        analysis_filepath = os.path.join(experiment_folder, analysis_filename)
        with open(analysis_filepath, 'w') as analysis_file:
            analysis_file.write(result_text)
        print(f"Analysis results saved to {analysis_filepath}")

def main():
    args = parse_arguments()
    analyze_experiment_folder(args.experiment_folder, args.postp, args.save, args.tl)

if __name__ == "__main__":
    main()
