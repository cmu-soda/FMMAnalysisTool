import json

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
TODO: Implement the following checks
Check for dominant blocking state:
The human thinks the most possible automation state(s) 
does not allow for a specific action that would cause a system change.
'''

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

fuzzy_data_path = './use_cases/cruise/computed/FMMFSM/cruise.jsonResult.json'
system_data_path = './use_cases/cruise/computed/System/cruiseSysBinary.json'
fuzzy_data = load_json_file(fuzzy_data_path)
system_data = load_json_file(system_data_path)

dominant_error_state = dominant_error_state_check(fuzzy_data, system_data)

print("Dominant Error State Check:")
for idx, result in enumerate(dominant_error_state):
    if result is True:
        print(f"Step {idx + 1}: True")
    else:
        print(f"Step {idx + 1}: False, Fuzzy Max State: {result[1]}, Binary True State: {result[2]}")

nondeterministic_confusions = nondeterministic_confusion_check(fuzzy_data)

print("\nNondeterministic Confusion Check:")
if nondeterministic_confusions:
    for step, states in nondeterministic_confusions:
        print(f"Step {step} shows nondeterministic confusion with states: {states}")
else:
    print("No nondeterministic confusion found.")

vacuous_confusions = vacuous_confusion_check(fuzzy_data)

print("\nVacuous Confusion Check:")
if vacuous_confusions:
    for step, states in vacuous_confusions:
        print(f"Step {step} shows vacuous confusion with state memberships: {states}")
else:
    print("No vacuous confusion found.")
