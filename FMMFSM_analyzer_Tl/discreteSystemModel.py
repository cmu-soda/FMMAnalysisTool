import json
import os

def load_configurations(file_path):
    with open(file_path, 'r') as file:
        data = json.load(file)
    return data['initial_state'], data['transitions'], data['action_schedule'], data['task_labels']

def transition_state(transitions, current_state, action):
    return transitions[current_state][action]

def simulate_actions_from_file(config_file, file_path):
    initial_state, transitions, action_schedule, task_labels = load_configurations(config_file)
    current_state = initial_state
    total_steps = 0
    history_readable = []
    history_binary = []
    task_label_history = []

    initial_task_label = task_labels[current_state]
    print(f"Initial state: {current_state}; initial task label: {initial_task_label}")
    history_readable.append(f"Initial state: {current_state}; initial task label: {initial_task_label}")
    history_binary.append({state: 1 if state == current_state else 0 for state in transitions.keys()})
    task_label_history.append(initial_task_label)

    for action, steps in action_schedule:
        for step in range(steps):
            current_state = transition_state(transitions, current_state, action)
            total_steps += 1
            current_task_label = task_labels[current_state]
            output = f"After total step {total_steps} with action '{action}': {current_state}, {current_task_label}"
            print(output)
            history_readable.append(output)
            history_binary.append({state: 1 if state == current_state else 0 for state in transitions.keys()})
            task_label_history.append(current_task_label)

    save_results(file_path, config_file, history_readable, history_binary, task_label_history)

def save_results(folder_path, input_file, readable_data, binary_data, task_label_data):
    base_name = os.path.splitext(os.path.basename(input_file))[0]
    readable_filename = os.path.join(folder_path, f"{base_name}Readable.json")
    binary_filename = os.path.join(folder_path, f"{base_name}Binary.json")
    os.makedirs(folder_path, exist_ok=True)

    with open(readable_filename, 'w') as file:
        json.dump(readable_data, file, indent=4)

    with open(binary_filename, 'w') as file:
        for i, entry in enumerate(binary_data):
            entry['task_label'] = task_label_data[i]
        json.dump(binary_data, file, indent=4)

# Example usage
config_file = './config/cruiseSys.json'
results_folder = './'

simulate_actions_from_file(config_file, results_folder)
