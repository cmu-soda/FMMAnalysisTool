import json
import random
import argparse
import os
import re
import logging
from datetime import datetime
import sys
from discreteSystemModel import simulate_actions_from_file
from FMMFSM import evolve_state_over_time_from_file, save_results_to_file
from outputChecker import check_and_save_results

def setup_logging(log_filename):
    logging.basicConfig(filename=log_filename, level=logging.INFO, format='%(asctime)s - %(message)s')

def log_execution():
    command = ' '.join(sys.argv)
    logging.info(f"Command executed: {command}")

def log_file_creation(file_path):
    logging.info(f"File created: {file_path}")

def load_configurations(file_path):
    with open(file_path, 'r') as file:
        data = json.load(file)
    return data

def generate_random_schedule(input_options, total_steps):
    schedule = []
    remaining_steps = total_steps

    while remaining_steps > 0:
        action = random.choice(input_options)
        steps = random.randint(1, min(5, remaining_steps))
        schedule.append([action, steps])
        remaining_steps -= steps

    return schedule

def save_configurations(data, file_path):
    with open(file_path, 'w') as file:
        json.dump(data, file, indent=4)
    log_file_creation(file_path)

def parse_arguments():
    parser = argparse.ArgumentParser(description="Monte Carlo simulation for FMMFSM")
    parser.add_argument("FMMFSM_config_file", help="Path to the input FMMFSM JSON configuration file")
    parser.add_argument("system_config_file", help="Path to the input system JSON configuration file")
    parser.add_argument("--num", type=int, help="Total number of steps in the generated path", required=True)
    parser.add_argument("--iter", type=int, help="Number of iterations to run", required=True)
    parser.add_argument("--postp", action="store_true", help="Enable post-processing to remove steps after blocking states are found")
    args = parser.parse_args()
    return args

def find_next_index(directory, base_filename):
    pattern = re.compile(rf'^{re.escape(base_filename)}_(\d+)\.json$')
    max_index = -1
    for filename in os.listdir(directory):
        match = pattern.match(filename)
        if match:
            index = int(match.group(1))
            if index > max_index:
                max_index = index
    return max_index + 1

def run_simulation(experiment_directory, args, iteration):
    os.makedirs(experiment_directory, exist_ok=True)
    
    FMMFSM_data = load_configurations(args.FMMFSM_config_file)
    system_data = load_configurations(args.system_config_file)
    
    input_options = list(FMMFSM_data['input_fuzzified'].keys())

    # Generate a random schedule and add it to both configurations
    random_schedule = generate_random_schedule(input_options, args.num)
    FMMFSM_data['input_schedule'] = random_schedule
    system_data['action_schedule'] = random_schedule
    
    config_directory = os.path.join(experiment_directory, 'config/')
    os.makedirs(config_directory, exist_ok=True)
    
    FMMFSM_base_filename = os.path.splitext(os.path.basename(args.FMMFSM_config_file))[0]
    system_base_filename = os.path.splitext(os.path.basename(args.system_config_file))[0]
    
    output_FMMFSM_path = os.path.join(config_directory, f"{FMMFSM_base_filename}_{iteration}.json")
    output_system_path = os.path.join(config_directory, f"{system_base_filename}_{iteration}.json")
    
    save_configurations(FMMFSM_data, output_FMMFSM_path)
    save_configurations(system_data, output_system_path)

    computed_directory = os.path.join(experiment_directory, 'computed/')
    os.makedirs(computed_directory, exist_ok=True)
    simulate_actions_from_file(output_system_path, os.path.join(computed_directory, f"{FMMFSM_base_filename}_{iteration}"))

    history = evolve_state_over_time_from_file(output_FMMFSM_path)
    save_results_to_file(os.path.join(computed_directory, f"{FMMFSM_base_filename}_{iteration}"), history, output_FMMFSM_path)

    fuzzy_data_file = os.path.join(computed_directory, f"{FMMFSM_base_filename}_{iteration}/{FMMFSM_base_filename}_{iteration}FMMFSM_Result.json")
    system_data_file = os.path.join(computed_directory, f"{FMMFSM_base_filename}_{iteration}/{system_base_filename}_{iteration}Binary.json")
    result_log_file = os.path.join(computed_directory, f"{FMMFSM_base_filename}_{iteration}/result/{FMMFSM_base_filename}_{iteration}Result.json")
    os.makedirs(os.path.dirname(result_log_file), exist_ok=True)

    expanded_schedule = expand_random_schedule(random_schedule)
    check_and_save_results(fuzzy_data_file, system_data_file, expanded_schedule)
    
    if args.postp:
        logging.info(f"Starting post-processing for simulation {iteration}")
        post_process_results(result_log_file)

def expand_random_schedule(random_schedule):
    expanded_schedule = []
    for action, count in random_schedule:
        expanded_schedule.extend([action] * count)
    return expanded_schedule

def post_process_results(result_log_file):
    logging.info("Starting post-processing")
    
    with open(result_log_file, 'r') as file:
        fuzzy_data = json.load(file)
    
    # Identify the first blocking state step
    blocking_history = fuzzy_data.get('Dominant Blocking State Check', [])
    first_blocking_state_step = next((step['Step'] for step in blocking_history if 'Step' in step), None)

    logging.info(f"First blocking state step: {first_blocking_state_step}")

    # Truncate all relevant data up to and including the first blocking state step if it exists
    truncated_results = {}

    if first_blocking_state_step is not None:
        if 'Dominant Error State Check' in fuzzy_data:
            truncated_results['Dominant Error State Check'] = [
                result for result in fuzzy_data['Dominant Error State Check']
                if result['Step'] <= first_blocking_state_step
            ]

        if 'Dominant Blocking State Check' in fuzzy_data:
            truncated_results['Dominant Blocking State Check'] = [
                result for result in fuzzy_data['Dominant Blocking State Check']
                if result['Step'] <= first_blocking_state_step
            ]

        if 'Nondeterministic Confusion Check' in fuzzy_data:
            truncated_results['Nondeterministic Confusion Check'] = [
                result for result in fuzzy_data['Nondeterministic Confusion Check']
                if result['Step'] <= first_blocking_state_step
            ]

        if 'Vacuous Confusion Check' in fuzzy_data:
            truncated_results['Vacuous Confusion Check'] = [
                result for result in fuzzy_data['Vacuous Confusion Check']
                if result['Step'] <= first_blocking_state_step
            ]
    else:
        # If no blocking state is found, use the full results
        truncated_results = fuzzy_data

    result_directory = os.path.dirname(result_log_file)
    os.makedirs(result_directory, exist_ok=True)  # Ensure the directory exists
    result_filename = os.path.basename(result_log_file).replace('Result.json', 'PostProcessed_Result.json')
    result_path = os.path.join(result_directory, result_filename)

    with open(result_path, 'w') as result_file:
        json.dump(truncated_results, result_file, indent=4)
    
    logging.info(f"Post-processed file saved to: {result_path}")

def main():
    args = parse_arguments()
    experiment_timestamp = datetime.now().strftime('%Y%m%d%H%M%S')
    experiment_directory = f'./output/{experiment_timestamp}/'
    
    os.makedirs(experiment_directory, exist_ok=True)
    log_filename = os.path.join(experiment_directory, 'run_log.log')
    setup_logging(log_filename)  # Set up logging for this experiment
    log_execution()  # Log the execution command

    first_file_logged = False
    for i in range(args.iter):
        run_simulation(experiment_directory, args, i)
        if not first_file_logged:
            logging.info(f"First file created: {find_next_index(experiment_directory + 'config/', os.path.splitext(os.path.basename(args.FMMFSM_config_file))[0]) - 1}")
            first_file_logged = True
    last_file_index = find_next_index(experiment_directory + 'config/', os.path.splitext(os.path.basename(args.FMMFSM_config_file))[0]) - 1
    logging.info(f"Last file created: {last_file_index}")

if __name__ == "__main__":
    main()
