import os
import json
import argparse
from collections import defaultdict

def parse_arguments():
    parser = argparse.ArgumentParser(description="Analyze the output of an experiment")
    parser.add_argument("experiment_folder", help="Path to the experiment folder")
    parser.add_argument("--postp", action="store_true", help="Analyze only post-processed files (default)")
    parser.add_argument("--all", action="store_true", help="Analyze only non-post-processed files")
    args = parser.parse_args()

    # Set default flag if none provided
    if not args.postp and not args.all:
        args.postp = True

    return args

def analyze_experiment_folder(experiment_folder, analyze_postp):
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
    print(f"Total result files found: {total_files}")

    error_types = {
        "Dominant Error State Check": 0,
        "Nondeterministic Confusion Check": 0,
        "Vacuous Confusion Check": 0,
        "Dominant Blocking State Check": 0
    }

    state_errors = defaultdict(lambda: defaultdict(int))
    action_errors = defaultdict(lambda: defaultdict(int))
    error_files = defaultdict(list)

    for result_file in result_files:
        with open(result_file, 'r') as file:
            results = json.load(file)
            for error_type in error_types.keys():
                if error_type in results:
                    for entry in results[error_type]:
                        if entry.get("Result") != "True":
                            error_types[error_type] += 1
                            state = entry.get("FMMFSM State")
                            action = entry.get("Action")
                            error_info = {"file": result_file, "state": state, "action": action}
                            error_files[error_type].append(error_info)
                            if state:
                                state_errors[state][error_type] += 1
                            if action:
                                action_errors[action][error_type] += 1

    print(f"Total files analyzed: {total_files}")
    for error_type, count in error_types.items():
        percentage = (count / total_files) * 100 if total_files > 0 else 0
        print(f"{error_type}: {percentage:.2f}% of files contain this error")

    print("\nErrors by FMMFSM State:")
    for state, errors in state_errors.items():
        for error_type, count in errors.items():
            print(f"State {state} - {error_type}: {count} errors")

    print("\nErrors by Action:")
    for action, errors in action_errors.items():
        for error_type, count in errors.items():
            print(f"Action {action} - {error_type}: {count} errors")

    print("\n\nErrors by Files:")
    for error_type, files in error_files.items():
        print("\n"+f"{error_type}:")
        for error_info in files:
            file = error_info["file"]
            state = error_info["state"]
            action = error_info["action"]
            print(f"  {file} - FMMFSM State: {state}, Action: {action}")

def main():
    args = parse_arguments()
    analyze_experiment_folder(args.experiment_folder, args.postp)

if __name__ == "__main__":
    main()
