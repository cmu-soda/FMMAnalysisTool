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

# Configure logging
logging.basicConfig(filename='run_log.log', level=logging.INFO, format='%(asctime)s - %(message)s')

def log_execution():
    command = ' '.join(sys.argv)
    logging.info(f"Command executed: {command}")

def log_file_creation(file_path):
    logging.info(f"File created: {file_path}")

# Log the execution command
log_execution()

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

def run_simulation(index, args):
    FMMFSM_data = load_configurations(args.FMMFSM_config_file)
    system_data = load_configurations(args.system_config_file)
    
    input_options = list(FMMFSM_data['input_fuzzified'].keys())

    random_schedule = generate_random_schedule(input_options, args.num)
    FMMFSM_data['input_schedule'] = random_schedule
    system_data['action_schedule'] = random_schedule
    
    directory = './output/config/'
    os.makedirs(os.path.dirname(directory), exist_ok=True)
    FMMFSM_base_filename = os.path.splitext(os.path.basename(args.FMMFSM_config_file))[0]
    system_base_filename = os.path.splitext(os.path.basename(args.system_config_file))[0]
    next_index = find_next_index(directory, FMMFSM_base_filename)
    
    output_FMMFSM_path = os.path.join(directory, f"{FMMFSM_base_filename}_{next_index}.json")
    output_system_path = os.path.join(directory, f"{system_base_filename}_{next_index}.json")
    
    save_configurations(FMMFSM_data, output_FMMFSM_path)
    save_configurations(system_data, output_system_path)

    simulate_actions_from_file(output_system_path, "./output/computed/"+f"{FMMFSM_base_filename}_{next_index}")

    history = evolve_state_over_time_from_file(output_FMMFSM_path)
    save_results_to_file("./output/computed/"+f"{FMMFSM_base_filename}_{next_index}", history, output_FMMFSM_path)

    fuzzy_data_file = "./output/computed/"+f"{FMMFSM_base_filename}_{next_index}/"+f"{FMMFSM_base_filename}_{next_index}FMMFSM_Result.json"
    system_data_file = "./output/computed/"+f"{FMMFSM_base_filename}_{next_index}/"+f"{system_base_filename}_{next_index}Binary.json"

    check_and_save_results(fuzzy_data_file, system_data_file)

def main():
    args = parse_arguments()
    first_file_logged = False
    for i in range(args.iter):
        run_simulation(i, args)
        if not first_file_logged:
            logging.info(f"First file created: {find_next_index('./output/config/', os.path.splitext(os.path.basename(args.FMMFSM_config_file))[0]) - 1}")
            first_file_logged = True
    last_file_index = find_next_index('./output/config/', os.path.splitext(os.path.basename(args.FMMFSM_config_file))[0]) - 1
    logging.info(f"Last file created: {last_file_index}")

if __name__ == "__main__":
    main()
