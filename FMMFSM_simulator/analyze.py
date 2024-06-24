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
    args = parser.parse_args()

    # Set default flag if none provided
    if not args.postp and not args.all:
        args.postp = True

    return args

def analyze_experiment_folder(experiment_folder, analyze_postp, save_results):
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
        "Dominant Blocking State Check": 0
    }

    state_errors = defaultdict(lambda: defaultdict(int))
    action_errors = defaultdict(lambda: defaultdict(int))
    error_files = defaultdict(list)
    files_with_errors = {error_type: set() for error_type in error_types.keys()}

    for result_file in result_files:
        relative_path = os.path.relpath(result_file, experiment_folder)
        with open(result_file, 'r') as file:
            results = json.load(file)
            for error_type in error_types.keys():
                if error_type in results:
                    has_error = False
                    for entry in results[error_type]:
                        if entry.get("Result") != "True":
                            has_error = True
                            state = entry.get("FMMFSM State")
                            action = entry.get("Action")
                            error_info = {"file": relative_path, "state": state, "action": action}
                            if error_type == "Dominant Error State Check":
                                error_info["Fuzzy Max State"] = entry.get("Fuzzy Max State")
                                error_info["Binary True State"] = entry.get("Binary True State")
                            elif error_type == "Nondeterministic Confusion Check":
                                error_info["States"] = entry.get("States")
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

    result_lines.append("\nErrors by FMMFSM State:\n")
    for state, errors in state_errors.items():
        for error_type, count in errors.items():
            result_lines.append(f"State {state} - {error_type}: {count} errors\n")

    result_lines.append("\nErrors by Action:\n")
    for action, errors in action_errors.items():
        for error_type, count in errors.items():
            result_lines.append(f"Action {action} - {error_type}: {count} errors\n")

    result_lines.append("\n\nErrors by Files:\n")
    for error_type, files in error_files.items():
        result_lines.append(f"\n{error_type}:\n")
        for error_info in files:
            file = error_info["file"]
            state = error_info["state"]
            action = error_info["action"]
            if error_type == "Dominant Error State Check":
                fuzzy_max_state = error_info.get("Fuzzy Max State")
                binary_true_state = error_info.get("Binary True State")
                result_lines.append(f"  {file} - FMMFSM State: {state}, Action: {action}, Fuzzy Max State: {fuzzy_max_state}, Binary True State: {binary_true_state}\n")
            elif error_type == "Nondeterministic Confusion Check":
                states = error_info.get("States")
                result_lines.append(f"  {file} - FMMFSM State: {state}, Action: {action}, States: {states}\n")
            else:
                result_lines.append(f"  {file} - FMMFSM State: {state}, Action: {action}\n")

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
    analyze_experiment_folder(args.experiment_folder, args.postp, args.save)

if __name__ == "__main__":
    main()
