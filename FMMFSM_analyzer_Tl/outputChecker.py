import json
import os

def load_json_file(file_path):
    with open(file_path, 'r') as file:
        data = json.load(file)
    return data

'''
Check for dominant error state:
The human thinks the state category the automation is most possibly in 
does not match the state's actual category.
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
            # Filter out non-numeric values and find the max state
            numeric_states = {k: v for k, v in current_system_state.items() if isinstance(v, (int, float))}
            if numeric_states:
                current_state = max(numeric_states, key=numeric_states.get)
                if i + 1 < len(system_data):
                    next_system_state = system_data[i + 1]
                    numeric_next_states = {k: v for k, v in next_system_state.items() if isinstance(v, (int, float))}
                    if numeric_next_states:
                        next_state = max(numeric_next_states, key=numeric_next_states.get)
                        if current_state != next_state:
                            blocking_steps.append(i)
    return blocking_steps

'''
Check for dominant task labels blocking state:
The human thinks the most possible task label(s) 
does not allow for a specific action that would cause a system change.
'''
def dominant_task_labels_blocking_state_check(blocking_history, system_data):
    blocking_steps = []
    for i, (blocking, current_system_state) in enumerate(zip(blocking_history, system_data)):
        B_task = blocking['B_task']
        C_task = blocking['C_task']
        if B_task > C_task:
            # Check if 'task_label' exists in current_system_state
            current_task_label = current_system_state.get('task_label')
            if current_task_label is not None and i + 1 < len(system_data):
                next_task_label = system_data[i + 1].get('task_label')
                if next_task_label is not None and current_task_label != next_task_label:
                    blocking_steps.append(i)
    return blocking_steps

'''
Check for task label mismatch:
The human thinks the task label category the automation is most possibly in 
does not match the system task label.
'''
def task_label_mismatch_check(task_membership_history, system_data):
    mismatch_steps = []
    for i, task_membership in enumerate(task_membership_history):
        fmmfsm_task_label = max(task_membership, key=task_membership.get)
        system_task_label = system_data[i]['task_label']
        if fmmfsm_task_label != system_task_label:
            mismatch_steps.append((i, fmmfsm_task_label, system_task_label))
    return mismatch_steps

'''
Check for task label nondeterministic confusion:
The human thinks two or more task labels are (effectively) equally the most possible.
'''
def task_label_nondeterministic_confusion_check(task_membership_history, threshold=0.05):
    confusion_steps = []
    for index, step in enumerate(task_membership_history):
        # Find the maximum membership value
        max_value = max(step.values())

        # Find all task labels that are within the threshold of the maximum value
        near_max_labels = {label: value for label, value in step.items()
                           if max_value - value <= threshold * max_value}

        # Check if multiple task labels are within this range
        if len(near_max_labels) > 1:
            confusion_steps.append((index + 1, near_max_labels))

    return confusion_steps

def get_fmmfsm_state(membership):
    return max(membership, key=membership.get) if membership else None

def check_and_save_results(fuzzy_data_path, system_data_path, expanded_schedule):
    fuzzy_data = load_json_file(fuzzy_data_path)
    system_data = load_json_file(system_data_path)

    state_membership_history = fuzzy_data['state_membership_history']
    blocking_history = fuzzy_data['blocking_history']
    task_membership_history = fuzzy_data['task_membership_history']

    base_directory = os.path.dirname(fuzzy_data_path)
    result_directory = os.path.join(base_directory, 'result')
    os.makedirs(result_directory, exist_ok=True)
    filename = os.path.basename(fuzzy_data_path).replace('FMMFSM_Result.json', 'Result.json')

    dominant_error_state = dominant_error_state_check(state_membership_history, system_data)
    nondeterministic_confusions = nondeterministic_confusion_check(state_membership_history)
    vacuous_confusions = vacuous_confusion_check(state_membership_history)
    dominant_blocking_states = dominant_blocking_state_check(blocking_history, system_data)
    dominant_task_labels_blocking_states = dominant_task_labels_blocking_state_check(blocking_history, system_data)
    task_label_mismatches = task_label_mismatch_check(task_membership_history, system_data)
    task_label_nondeterministic_confusions = task_label_nondeterministic_confusion_check(task_membership_history)

    results = {}

    dominant_error_state_results = [
        {
            "Step": idx,
            "Action": expanded_schedule[idx] if idx < len(expanded_schedule) else None,
            "FMMFSM State": get_fmmfsm_state(state_membership_history[idx]) if idx < len(state_membership_history) else None,
            "Result": "True"
        } if result is True else {
            "Step": idx,
            "Action": expanded_schedule[idx] if idx < len(expanded_schedule) else None,
            "FMMFSM State": get_fmmfsm_state(state_membership_history[idx]) if idx < len(state_membership_history) else None,
            "Result": "False",
            "Fuzzy Max State": result[1],
            "Binary True State": result[2]
        }
        for idx, result in enumerate(dominant_error_state)
    ]

    if dominant_error_state_results:
        results["Dominant Error State Check"] = dominant_error_state_results

    if nondeterministic_confusions:
        results["Nondeterministic Confusion Check"] = [
            {"Step": step - 1, "Action": expanded_schedule[step - 1] if step - 1 < len(expanded_schedule) else None, "FMMFSM State": get_fmmfsm_state(state_membership_history[step - 1]) if step - 1 < len(state_membership_history) else None, "States": states}
            for step, states in nondeterministic_confusions
        ]

    if vacuous_confusions:
        results["Vacuous Confusion Check"] = [
            {"Step": step - 1, "Action": expanded_schedule[step - 1] if step - 1 < len(expanded_schedule) else None, "FMMFSM State": get_fmmfsm_state(state_membership_history[step - 1]) if step - 1 < len(state_membership_history) else None, "State Memberships": states}
            for step, states in vacuous_confusions
        ]

    if dominant_blocking_states:
        results["Dominant Blocking State Check"] = [
            {"Step": step, "Action": expanded_schedule[step] if step < len(expanded_schedule) else None, "FMMFSM State": get_fmmfsm_state(state_membership_history[step]) if step < len(state_membership_history) else None}
            for step in dominant_blocking_states
        ]

    if dominant_task_labels_blocking_states:
        results["Dominant Task Labels Blocking State Check"] = [
            {"Step": step, "Action": expanded_schedule[step] if step < len(expanded_schedule) else None, "FMMFSM State": get_fmmfsm_state(state_membership_history[step]) if step < len(state_membership_history) else None}
            for step in dominant_task_labels_blocking_states
        ]

    if task_label_mismatches:
        results["Task Label Mismatch Check"] = [
            {"Step": step, "Action": expanded_schedule[step] if step < len(expanded_schedule) else None, "FMMFSM Task Label": fmmfsm_task_label, "System Task Label": system_task_label}
            for step, fmmfsm_task_label, system_task_label in task_label_mismatches
        ]

    if task_label_nondeterministic_confusions:
        results["Task Label Nondeterministic Confusion Check"] = [
            {"Step": step - 1, "Action": expanded_schedule[step - 1] if step - 1 < len(expanded_schedule) else None, "FMMFSM Task Labels": labels}
            for step, labels in task_label_nondeterministic_confusions
        ]

    result_path = os.path.join(result_directory, filename)
    with open(result_path, 'w') as result_file:
        json.dump(results, result_file, indent=4)