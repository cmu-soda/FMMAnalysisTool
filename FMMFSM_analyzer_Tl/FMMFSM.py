import numpy as np
import json
import os

def fuzzy_and(values):
    return np.prod(values)

def fuzzy_or(values):
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

    # Apply fuzzy OR for each state based on accumulated values for that state
    for state in states:
        if transition_values[state]:
            next_state_memberships[state] = fuzzy_or(transition_values[state])
        else:
            next_state_memberships[state] = 0

    return next_state_memberships

def calculate_blocking_states(current_state_memberships, input_fuzzified, transition_probabilities, input_event):
    states = list(current_state_memberships.keys())
    
    B_values = []
    C_values = []

    for current_state in states:
        for input_condition in input_fuzzified[input_event].keys():
            input_membership = input_fuzzified[input_event][input_condition]
            
            for next_state in states:
                transition_probability = transition_probabilities[current_state][input_condition].get(next_state, 0)
                
                and_value = fuzzy_and([current_state_memberships[current_state], input_membership, transition_probability])
                
                if current_state == next_state:
                    B_values.append(and_value)
                else:
                    C_values.append(and_value)

    B = fuzzy_or(B_values)
    C = fuzzy_or(C_values)

    return B, C

def calculate_task_memberships(current_state_memberships, task_labels):
    tasks = list(task_labels.keys())
    task_memberships = {task: 0 for task in tasks}
    task_values = {task: [] for task in tasks}

    for state, state_membership in current_state_memberships.items():
        for task in tasks:
            task_membership = task_labels[task].get(state, 0)
            and_value = fuzzy_and([state_membership, task_membership])
            task_values[task].append(and_value)

    for task in tasks:
        if task_values[task]:
            task_memberships[task] = fuzzy_or(task_values[task])
        else:
            task_memberships[task] = 0

    return task_memberships

def calculate_task_based_blocking_states(current_state_memberships, input_fuzzified, transition_probabilities, input_event, task_labels, current_task_memberships):
    states = list(current_state_memberships.keys())
    
    B_values = []
    C_values = []

    for task_label_p, task_membership_p in current_task_memberships.items():
        #print(f"Task Label P: {task_label_p}, Membership: {task_membership_p}")
        for state_q, state_membership_q in current_state_memberships.items():
            #print(f"  State Q: {state_q}, Membership: {state_membership_q}")
            for input_sigma, input_membership_sigma in input_fuzzified[input_event].items():
                #print(f"    Input Sigma: {input_sigma}, Membership: {input_membership_sigma}")
                next_state_memberships = {state: transition_probabilities[state_q][input_sigma].get(state, 0) for state in states}
                next_task_memberships = calculate_task_memberships(next_state_memberships, task_labels)
                    
                for next_task_label, next_task_membership in next_task_memberships.items():
                    and_value = fuzzy_and([task_membership_p, state_membership_q, input_membership_sigma, next_task_membership])
                    if next_task_label == task_label_p:
                        #print(f"      Task Label: {next_task_label}, B AND Value: {and_value}")
                        B_values.append(and_value)
                    else:
                        #print(f"      Task Label: {next_task_label}, C AND Value: {and_value}")
                        C_values.append(and_value)

    B_task = fuzzy_or(B_values)
    C_task = fuzzy_or(C_values)

    #print(f"B_task: {B_task}, C_task: {C_task}")

    return B_task, C_task

def load_configurations(file_path):
    with open(file_path, 'r') as file:
        content = file.read()
        data = json.loads(content)
    return data['initial_state_memberships'], data['input_fuzzified'], data['transition_probabilities'], data['action_schedule'], data['task_labels']

def evolve_state_over_time_from_file(config_file):
    initial_state_memberships, input_fuzzified, transition_probabilities, action_schedule, task_labels = load_configurations(config_file)

    current_state_memberships = initial_state_memberships
    history = [current_state_memberships]
    blocking_history = []
    task_membership_history = [calculate_task_memberships(current_state_memberships, task_labels)]

    for input_event, steps in action_schedule:
        for _ in range(steps):
            B, C = calculate_blocking_states(current_state_memberships, input_fuzzified, transition_probabilities, input_event)
            current_task_memberships = calculate_task_memberships(current_state_memberships, task_labels)
            B_task, C_task = calculate_task_based_blocking_states(current_state_memberships, input_fuzzified, transition_probabilities, input_event, task_labels, current_task_memberships)
            blocking_history.append({'B': B, 'C': C, 'B_task': B_task, 'C_task': C_task})

            current_state_memberships = calculate_next_state_membership(current_state_memberships, input_fuzzified, transition_probabilities, input_event)
            history.append(current_state_memberships)

            task_memberships = calculate_task_memberships(current_state_memberships, task_labels)
            task_membership_history.append(task_memberships)

    results = {
        'state_membership_history': history,
        'blocking_history': blocking_history,
        'task_membership_history': task_membership_history
    }
    return results

def save_results_to_file(folder_path, data, input_filename):
    base_filename = os.path.basename(input_filename)
    base_filename = os.path.splitext(base_filename)[0]
    output_filename = f"{base_filename}FMMFSM_Result.json"
    os.makedirs(folder_path, exist_ok=True)
    output_file_path = os.path.join(folder_path, output_filename)

    with open(output_file_path, 'w') as f:
        json.dump(data, f, indent=4)