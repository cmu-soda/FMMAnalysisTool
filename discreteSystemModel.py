import json
import os

def load_configurations(file_path):
    with open(file_path, 'r') as file:
        data = json.load(file)
    return data['initial_state'], data['transitions'], data['action_schedule']

def transition_state(transitions, current_state, action):
    return transitions[current_state][action]

def simulate_actions_from_file(config_file, file_path):
    initial_state, transitions, action_schedule = load_configurations(config_file)
    current_state = initial_state
    total_steps = 0
    history_readable = []
    history_binary = []

    print(f"Initial state: {current_state}")
    history_readable.append(f"Initial state: {current_state}")
    history_binary.append({state: 1 if state == current_state else 0 for state in transitions.keys()})

    for action, steps in action_schedule:
        for step in range(steps):
            current_state = transition_state(transitions, current_state, action)
            total_steps += 1
            output = f"After total step {total_steps} with action '{action}': {current_state}"
            print(output)
            history_readable.append(output)
            history_binary.append({state: 1 if state == current_state else 0 for state in transitions.keys()})

    save_results(file_path+'computed/System/', config_file, history_readable, history_binary)

def save_results(folder_path, input_file, readable_data, binary_data):
    base_name = os.path.splitext(os.path.basename(input_file))[0]
    readable_filename = os.path.join(folder_path, f"{base_name}Readable.json")
    binary_filename = os.path.join(folder_path, f"{base_name}Binary.json")
    os.makedirs(folder_path, exist_ok=True)

    with open(readable_filename, 'w') as file:
        json.dump(readable_data, file, indent=4)

    with open(binary_filename, 'w') as file:
        json.dump(binary_data, file, indent=4)

# Example usage
file_path = './use_cases/gear/'
file_name = 'gear2Sys.json'
config_file = file_path + file_name
simulate_actions_from_file(config_file, file_path)