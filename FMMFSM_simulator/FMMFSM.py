import numpy as np
import json
import os

def fuzzy_and(values):
    #return np.min(values)
    return np.prod(values)

def fuzzy_or(values):
    #return np.max(values)
    return 1 - np.prod(1 - np.array(values))

def calculate_next_state_membership(current_state_memberships, input_fuzzified, transition_probabilities, input_event):
    """ 
    fuzzy AND of 
    current state membership (my), 
    input event membership (sz), 
    and membership of x produced from y transitioning on z (φ (y, z)x ). 
    
    Because any possible combination of current states and inputs could transition to x, 
    we take a fuzzy OR of all possible memberships of current state and input event combinations transitioning to x
    """
    states = list(current_state_memberships.keys())
    next_state_memberships = {state: [] for state in states}

    # Hold values for each transition target state separately
    transition_values = {state: [] for state in states}

    # Loop through each state
    for current_state in states:
        # Loop through each possible transition target state
        for next_state in states:
            # Loop through each input condition
            for input_condition in input_fuzzified[input_event].keys():
                input_membership = input_fuzzified[input_event][input_condition]
                # Get the transition probability from the current state with the input condition to the next state
                transition_probability = transition_probabilities[current_state][input_condition].get(next_state, 0)
                
                # Calculate the fuzzy AND
                and_value = fuzzy_and([current_state_memberships[current_state], input_membership, transition_probability])
                
                # Append to the correct list based on the transition's target state (next_state)
                transition_values[next_state].append(and_value)

                '''
                print(f"Calculating membership for state {next_state} from state {current_state}")
                print(f"  Input condition: {input_condition}")
                print(f"    Current state membership: {current_state_memberships[current_state]}")
                print(f"    Input membership: {input_membership}")
                print(f"    Transition probability from {current_state} with input {input_condition} to {next_state}: {transition_probability}")
                '''

    # Apply fuzzy OR for each state based on accumulated values for that state
    for state in states:
        if transition_values[state]:
            next_state_memberships[state] = fuzzy_or(transition_values[state])
        else:
            next_state_memberships[state] = 0

    return next_state_memberships


def load_configurations(file_path):
    with open(file_path, 'r') as file:
        content = file.read()
        data = json.loads(content)
    return data['initial_state_memberships'], data['input_fuzzified'], data['transition_probabilities'], data['input_schedule']

def evolve_state_over_time_from_file(config_file):
    initial_state_memberships, input_fuzzified, transition_probabilities, input_schedule = load_configurations(config_file)

    current_state_memberships = initial_state_memberships
    history = [current_state_memberships]

    for input_event, steps in input_schedule:
        for _ in range(steps):
            current_state_memberships = calculate_next_state_membership(
                current_state_memberships, 
                input_fuzzified, 
                transition_probabilities, 
                input_event
            )
            history.append(current_state_memberships)

    return history

def evolve_state_over_time(initial_state_memberships, input_fuzzified, transition_probabilities, input_schedule):
    current_state_memberships = initial_state_memberships
    history = [current_state_memberships]

    for input_event, steps in input_schedule:
        for _ in range(steps):
            current_state_memberships = calculate_next_state_membership(
                current_state_memberships, 
                input_fuzzified, 
                transition_probabilities, 
                input_event
            )
            history.append(current_state_memberships)

    return history

def save_results_to_file(folder_path, data, input_filename):
    base_filename = os.path.basename(input_filename)  # Get the filename from the full path
    base_filename = os.path.splitext(base_filename)[0]  # Remove the file extension

    output_filename = f"{base_filename}FMMFSM_Result.json"

    os.makedirs(folder_path, exist_ok=True)

    output_file_path = os.path.join(folder_path, output_filename)

    with open(output_file_path, 'w') as f:
        json.dump(data, f, indent=4)