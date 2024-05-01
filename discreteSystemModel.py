import json

def load_configurations(file_path):
    with open(file_path, 'r') as file:
        data = json.load(file)
    return data['initial_state'], data['transitions'], data['action_schedule']

def transition_state(transitions, current_state, action):
    return transitions[current_state][action]

def simulate_actions_from_file(config_file):
    initial_state, transitions, action_schedule = load_configurations(config_file)
    current_state = initial_state
    total_steps = 0
    print(f"Initial state: {current_state}")

    for action, steps in action_schedule:
        for step in range(steps):
            current_state = transition_state(transitions, current_state, action)
            total_steps += 1
            print(f"After total step {total_steps} with action '{action}': {current_state}")

# Example usage
config_file = './use_cases/gear/gearSys.json'
simulate_actions_from_file(config_file)