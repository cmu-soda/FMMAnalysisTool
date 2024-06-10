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
                    blocking_steps.append(i + 1)
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

def save_results(results, output_directory, filename):
    os.makedirs(output_directory, exist_ok=True)
    file_path = os.path.join(output_directory, filename)
    with open(file_path, 'w') as file:
        file.write(results)

def main():
    # Paths and data loading
    fuzzy_data_path = './FMMFSM_tester/use_cases/cruise/computed/FMMFSM/cruise2.jsonResult.json'
    system_data_path = './FMMFSM_tester/use_cases/cruise/computed/System/cruise2SysBinary.json'
    fuzzy_data = load_json_file(fuzzy_data_path)
    system_data = load_json_file(system_data_path)

    state_membership_history = fuzzy_data['state_membership_history']
    blocking_history = fuzzy_data['blocking_history']

    base_directory = os.path.dirname(fuzzy_data_path)
    result_directory = os.path.join(base_directory, 'result')
    filename = os.path.basename(fuzzy_data_path).replace('.jsonResult.json', 'RESULT.txt')

    # Perform checks
    dominant_error_state = dominant_error_state_check(state_membership_history, system_data)
    nondeterministic_confusions = nondeterministic_confusion_check(state_membership_history)
    vacuous_confusions = vacuous_confusion_check(state_membership_history)
    dominant_blocking_states = dominant_blocking_state_check(blocking_history, system_data)

    # Prepare and print results
    results = "Dominant Error State Check:\n"
    for idx, result in enumerate(dominant_error_state):
        if result is True:
            results += f"Step {idx}: True\n"
        else:
            results += f"Step {idx}: False, Fuzzy Max State: {result[1]}, Binary True State: {result[2]}\n"
    print(results)  # Print to terminal

    nondet_results = "\nNondeterministic Confusion Check:\n"
    if nondeterministic_confusions:
        for step, states in nondeterministic_confusions:
            nondet_results += f"Step {step-1} shows nondeterministic confusion with states: {states}\n"
    else:
        nondet_results += "No nondeterministic confusion found.\n"
    print(nondet_results)  # Print to terminal

    vacuous_results = "\nVacuous Confusion Check:\n"
    if vacuous_confusions:
        for step, states in vacuous_confusions:
            vacuous_results += f"Step {step-1} shows vacuous confusion with state memberships: {states}\n"
    else:
        vacuous_results += "No vacuous confusion found.\n"
    print(vacuous_results)  # Print to terminal

    blocking_results = "\nDominant Blocking State Check:\n"
    if dominant_blocking_states:
        for step in dominant_blocking_states:
            blocking_results += f"Step {step} shows dominant blocking state.\n"
    else:
        blocking_results += "No dominant blocking states found.\n"
    print(blocking_results)  # Print to terminal

    # Save all results
    full_results = results + nondet_results + vacuous_results + blocking_results
    save_results(full_results, result_directory, filename)

if __name__ == "__main__":
    main()