import json
import random
import argparse
import os
import re

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

def parse_arguments():
    parser = argparse.ArgumentParser(description="Monte Carlo simulation for FMMFSM")
    parser.add_argument("FMMFSM_config_file", help="Path to the input FMMFSM JSON configuration file")
    parser.add_argument("system_config_file", help="Path to the input system JSON configuration file")
    parser.add_argument("--num", type=int, help="Total number of steps in the generated path", required=False)
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

def main():
    args = parse_arguments()

    FMMFSM_data = load_configurations(args.FMMFSM_config_file)
    system_data = load_configurations(args.system_config_file)
    
    input_options = list(FMMFSM_data['input_fuzzified'].keys())
    if args.num is None:
        print("Error: Please specify the total number of steps using the --num option.")
        return

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
    print(f"New configuration has been saved to {output_FMMFSM_path}")
    save_configurations(system_data, output_system_path)
    print(f"New system configuration has been saved to {output_system_path}")

if __name__ == "__main__":
    main()
