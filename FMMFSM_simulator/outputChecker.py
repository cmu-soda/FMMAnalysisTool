import json
import os

def load_json_file(file_path):
    with open(file_path, 'r') as file:
        data = json.load(file)
    return data

'''
Check for dominant error state:
The human thinks the state category the automation is most possibly in 
does not match the states actual category.
'''
def dominant_error_state_check(fuzzy_data, system_data):
    results = []
    for fuzzy, binary in zip(fuzzy_data, system_data):
        # Find the state with the highest membership in the fuzzy data
        max_state = max(fuzzy, key=fuzzy.get)
        max_value = fuzzy[max_state]

        # Check if the corresponding binary state is set to 1
        if binary[max_state] == 1:
            results.append(True)
        else:
            # Find the actual binary state set to 1 for comparison
            true_state = next((state for state in binary if binary[state] == 1), None)
            results.append((False, {max_state: max_value}, {true_state: fuzzy[true_state]}))
    
    return results

'''
Check for nondeterministic confusion:
The human thinks two or more task categories are (effectively) equally the most possible.
'''
def nondeterministic_confusion_check(data, threshold=0.05):
    confusion_steps = []
    for index, step in enumerate(data):
        # Find the maximum membership value
        max_value = max(step.values())

        # Find all states that are within the threshold of the maximum value
        near_max_states = {state: value for state, value in step.items() 
                           if max_value - value <= threshold * max_value}

        # Check if multiple states are within this range
        if len(near_max_states) > 1:
            confusion_steps.append((index + 1, near_max_states))

    return confusion_steps

'''
Check for vacuous confusion:
The human does not have strong membership for any state category (task label).
'''
def vacuous_confusion_check(data, threshold=0.05):
    confusion_steps = []
    for index, step in enumerate(data):
        max_value = max(step.values())
        
        # Check if the highest value is below the threshold
        if max_value < threshold:
            confusion_steps.append((index + 1, step))
    
    return confusion_steps

'''
Check for dominant blocking state:
The human thinks the most possible automation state(s) 
does not allow for a specific action that would cause a system change.
'''
def dominant_blocking_state_check(blocking_history, system_data):
    blocking_steps = []
    for i, (blocking, current_system_state) in enumerate(zip(blocking_history, system_data)):
        B = blocking['B']
        C = blocking['C']
        if B > C:
            current_state = max(current_system_state, key=current_system_state.get)
            if i + 1 < len(system_data):
                next_system_state = system_data[i + 1]
                next_state = max(next_system_state, key=next_system_state.get)
                if current_state != next_state:
                    blocking_steps.append(i)
    return blocking_steps

'''
TODO: Implement the following checks
Check for threshold error state:
The human thinks that an automation state category (task label) that mismatches 
the actual automation category 
is possible enough (above an analyst specified threshold) to cause trouble.
'''

'''
TODO: Implement the following checks
Check for threshold blocking state:
The human thinks that an automation state 
where there is blocking is possible enough (above a specified threshold) to cause trouble.
'''

def check_and_save_results(fuzzy_data_path, system_data_path):
    fuzzy_data = load_json_file(fuzzy_data_path)
    system_data = load_json_file(system_data_path)

    state_membership_history = fuzzy_data['state_membership_history']
    blocking_history = fuzzy_data['blocking_history']

    base_directory = os.path.dirname(fuzzy_data_path)
    result_directory = os.path.join(base_directory, 'result')
    os.makedirs(result_directory, exist_ok=True)
    filename = os.path.basename(fuzzy_data_path).replace('FMMFSM_Result.json', 'Result.json')

    dominant_error_state = dominant_error_state_check(state_membership_history, system_data)
    nondeterministic_confusions = nondeterministic_confusion_check(state_membership_history)
    vacuous_confusions = vacuous_confusion_check(state_membership_history)
    dominant_blocking_states = dominant_blocking_state_check(blocking_history, system_data)

    results = {}

    dominant_error_state_results = [
        {"Step": idx, "Result": "True"} if result is True else {"Step": idx, "Result": "False", "Fuzzy Max State": result[1], "Binary True State": result[2]}
        for idx, result in enumerate(dominant_error_state)
    ]

    if dominant_error_state_results:
        results["Dominant Error State Check"] = dominant_error_state_results

    if nondeterministic_confusions:
        results["Nondeterministic Confusion Check"] = [
            {"Step": step - 1, "States": states}
            for step, states in nondeterministic_confusions
        ]

    if vacuous_confusions:
        results["Vacuous Confusion Check"] = [
            {"Step": step - 1, "State Memberships": states}
            for step, states in vacuous_confusions
        ]

    if dominant_blocking_states:
        results["Dominant Blocking State Check"] = [
            {"Step": step}
            for step in dominant_blocking_states
        ]

    result_path = os.path.join(result_directory, filename)
    with open(result_path, 'w') as result_file:
        json.dump(results, result_file, indent=4)