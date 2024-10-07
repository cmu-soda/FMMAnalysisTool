import json
import os

def load_json_file(file_path):
    """Load JSON data from a file."""
    with open(file_path, 'r') as file:
        data = json.load(file)
    return data

# 1. Dominant State Error Check
def dominant_state_error_check(fuzzy_data, system_data):
    """
    Check for dominant state error:
    The human thinks the state category the automation is most possibly in 
    does not match the state's actual category.
    """
    results = []
    for fuzzy, binary in zip(fuzzy_data, system_data):
        max_state = max(fuzzy, key=fuzzy.get)
        max_value = fuzzy[max_state]
        if binary[max_state] == 1:
            results.append(True)
        else:
            true_state = next((state for state in binary if binary[state] == 1), None)
            results.append((False, {max_state: max_value}, {true_state: fuzzy[true_state]}))
    return results

# 2. Threshold State Error Check
def threshold_state_error_check(fuzzy_data, system_data, threshold=0.7):
    """
    Check for threshold state error:
    The human thinks the state category the automation is most possibly in 
    does not match the state's actual category based on a threshold.
    """
    results = []
    for fuzzy, binary in zip(fuzzy_data, system_data):
        above_threshold = {state: value for state, value in fuzzy.items() if value > threshold}
        if not above_threshold:
            results.append((False, "No state above threshold"))
            continue
        states_with_binary = {state: binary[state] for state in above_threshold if binary[state] == 1}
        if len(states_with_binary) == 1:
            max_state = max(above_threshold, key=above_threshold.get)
            results.append((True, {max_state: above_threshold[max_state]}, states_with_binary))
    return results

# 3. Dominant Task Error Check
def dominant_task_error_check(task_membership_history, system_data):
    """
    Check for dominant task error:
    The human thinks the task label category the automation is most possibly in 
    does not match the system task label.
    """
    mismatch_steps = []
    for i, task_membership in enumerate(task_membership_history):
        fmmfsm_task_label = max(task_membership, key=task_membership.get)
        system_task_label = system_data[i]['task_label']
        if fmmfsm_task_label != system_task_label:
            mismatch_steps.append((i, fmmfsm_task_label, system_task_label))
    return mismatch_steps

# 4. Threshold Task Error Check
def threshold_task_error_check(task_membership_history, system_data, threshold=0.7):
    """
    Check for threshold task error:
    The human thinks the task label category the automation is most possibly in 
    does not match the system task label, considering a threshold.
    """
    mismatch_steps = []
    for i, task_membership in enumerate(task_membership_history):
        task_membership_above_threshold = {label: value for label, value in task_membership.items() if value >= threshold}
        system_task_label = system_data[i]['task_label']
        if system_task_label not in task_membership_above_threshold:
            fmmfsm_task_label = max(task_membership, key=task_membership.get)
            mismatch_steps.append((i, fmmfsm_task_label, system_task_label))
    return mismatch_steps

# 5. Dominant Blocking State Check
def dominant_blocking_state_check(mental_model_history, system_data):
    """
    Check for dominant blocking state:
    The human thinks the most possible automation state(s) does not allow for a specific action
    that would cause a system change. A change in system state is detected but the dominant state 
    in the mental model is not changed.
    """
    blocking_steps = []
    
    # Iterate through all consecutive pairs of states including the last two
    for i in range(len(system_data) - 1):
        current_system_state = system_data[i]
        next_system_state = system_data[i + 1]
        current_mental_model = mental_model_history[i]
        next_mental_model = mental_model_history[i + 1]

        # Filter out non-numeric values from the system states
        numeric_current_system_state = {k: v for k, v in current_system_state.items() if isinstance(v, (int, float))}
        numeric_next_system_state = {k: v for k, v in next_system_state.items() if isinstance(v, (int, float))}

        # Ensure there are valid numeric values to work with
        if not numeric_current_system_state or not numeric_next_system_state:
            continue

        # Get the dominant system state (highest value) from numeric system states only
        dominant_system_current = max(numeric_current_system_state, key=numeric_current_system_state.get)
        dominant_system_next = max(numeric_next_system_state, key=numeric_next_system_state.get)

        # Get the dominant mental model state (highest membership value)
        dominant_mental_model_current = max(current_mental_model, key=current_mental_model.get)
        dominant_mental_model_next = max(next_mental_model, key=next_mental_model.get)

        # If system state changes but the mental model dominant state remains the same, it's a blocking step
        if dominant_system_current != dominant_system_next and dominant_mental_model_current == dominant_mental_model_next:
            blocking_steps.append(i)
    
    return blocking_steps

# 6. Threshold Blocking State Check
def threshold_blocking_state_check(mental_model_history, system_data, threshold=0.7):
    """
    Check for threshold blocking state:
    The human thinks the most possible automation state(s) does not allow for a specific action 
    that would cause a system change. The system state changes but the mental model's states 
    above the threshold remain unchanged.
    """
    blocking_steps = []
    
    # Iterate through all consecutive pairs of states including the last two
    for i in range(len(system_data) - 1):
        current_system_state = system_data[i]
        next_system_state = system_data[i + 1]
        current_mental_model = mental_model_history[i]
        next_mental_model = mental_model_history[i + 1]

        # Filter out non-numeric values from system states
        numeric_current_system_state = {k: v for k, v in current_system_state.items() if isinstance(v, (int, float))}
        numeric_next_system_state = {k: v for k, v in next_system_state.items() if isinstance(v, (int, float))}

        # Ensure there are valid numeric values to work with
        if not numeric_current_system_state or not numeric_next_system_state:
            continue

        # Get the dominant system state (highest value) from numeric system states only
        dominant_system_current = max(numeric_current_system_state, key=numeric_current_system_state.get)
        dominant_system_next = max(numeric_next_system_state, key=numeric_next_system_state.get)

        # Get mental model states above the threshold
        current_mental_model_above_threshold = {state: value for state, value in current_mental_model.items() if value > threshold}
        next_mental_model_above_threshold = {state: value for state, value in next_mental_model.items() if value > threshold}

        # If system state changes but the mental model states above the threshold remain the same
        if dominant_system_current != dominant_system_next and current_mental_model_above_threshold == next_mental_model_above_threshold:
            blocking_steps.append(i)
    
    return blocking_steps


# 7. Dominant Blocking Task Check
def dominant_task_blocking_state_check(mental_model_task_history, system_data):
    """
    Check for dominant task labels blocking state:
    The human thinks the most possible task label(s) does not allow for a specific action
    that would cause a system change. The system task label changes but the dominant task 
    label in the mental model does not.
    """
    blocking_steps = []
    
    # Iterate through all consecutive pairs of task labels including the last two
    for i in range(len(system_data) - 1):
        current_task_label = system_data[i]
        next_task_label = system_data[i + 1]
        current_mental_model_task = mental_model_task_history[i]
        next_mental_model_task = mental_model_task_history[i + 1]

        # Filter out non-numeric values from system states
        numeric_current_task_label = {k: v for k, v in current_task_label.items() if isinstance(v, (int, float))}
        numeric_next_task_label = {k: v for k, v in next_task_label.items() if isinstance(v, (int, float))}

        # Ensure there are valid numeric values to work with
        if not numeric_current_task_label or not numeric_next_task_label:
            continue

        # Get the dominant system task label (highest value in numeric task labels)
        dominant_task_system_current = max(numeric_current_task_label, key=numeric_current_task_label.get)
        dominant_task_system_next = max(numeric_next_task_label, key=numeric_next_task_label.get)

        # Get the dominant task in the mental model
        dominant_mental_model_task_current = max(current_mental_model_task, key=current_mental_model_task.get)
        dominant_mental_model_task_next = max(next_mental_model_task, key=next_mental_model_task.get)

        # If system task changes but the mental model dominant task label remains the same
        if dominant_task_system_current != dominant_task_system_next and dominant_mental_model_task_current == dominant_mental_model_task_next:
            blocking_steps.append(i)
    
    return blocking_steps


# 8. Threshold Blocking Task Check
def threshold_task_blocking_state_check(mental_model_task_history, system_data, threshold=0.7):
    """
    Check for threshold task labels blocking state:
    The human thinks the most possible task label(s) 
    does not allow for a specific action that would cause a system change.
    The system task label is the one where the value is 1, while the mental model's task labels
    above the threshold remain unchanged.
    """
    blocking_steps = []
    
    # Iterate through all consecutive pairs of task labels including the last two
    for i in range(len(system_data) - 1):
        current_task_label = system_data[i]
        next_task_label = system_data[i + 1]
        current_mental_model_task = mental_model_task_history[i]
        next_mental_model_task = mental_model_task_history[i + 1]

        # Filter out non-numeric values from system states
        numeric_current_task_label = {k: v for k, v in current_task_label.items() if isinstance(v, (int, float))}
        numeric_next_task_label = {k: v for k, v in next_task_label.items() if isinstance(v, (int, float))}

        # Ensure there are valid numeric values to work with
        if not numeric_current_task_label or not numeric_next_task_label:
            continue

        # Get the system task label where the value is 1
        system_task_current = numeric_current_task_label.get('task_label')
        system_task_next = numeric_next_task_label.get('task_label')

        # Get task labels above the threshold in the current and next mental model tasks
        current_task_above_threshold = {task: value for task, value in current_mental_model_task.items() if value > threshold}
        next_task_above_threshold = {task: value for task, value in next_mental_model_task.items() if value > threshold}

        # If the system task label changed (where value is 1), but the mental model's task labels above the threshold remained the same
        if system_task_current != system_task_next and current_task_above_threshold == next_task_above_threshold:
            blocking_steps.append(i)
    
    return blocking_steps

# 9. Dominant Nondeterministic State Confusion
def dominant_nondeterministic_state_confusion_check(data):
    """
    Check for dominant nondeterministic state confusion:
    The human thinks two or more task categories are equally the most possible.
    """
    confusion_steps = []
    for index, step in enumerate(data):
        max_value = max(step.values())
        near_max_states = {state: value for state, value in step.items() if value == max_value}
        if len(near_max_states) > 1:
            confusion_steps.append((index + 1, near_max_states))
    return confusion_steps

# 10. Threshold Nondeterministic State Confusion
def threshold_nondeterministic_state_confusion_check(data, threshold=0.7):
    """
    Check for threshold nondeterministic state confusion:
    The human thinks two or more task categories are equally the most possible.
    """
    confusion_steps = []
    for index, step in enumerate(data):
        above_threshold_states = {state: value for state, value in step.items() if value > threshold}
        if len(above_threshold_states) > 1:
            confusion_steps.append((index + 1, above_threshold_states))
    return confusion_steps

# 11. Dominant Nondeterministic Task Confusion
def dominant_task_nondeterministic_confusion_check(task_membership_history):
    """
    Check for dominant nondeterministic task confusion:
    The human thinks two or more task labels are equally the most possible.
    """
    confusion_steps = []
    for index, step in enumerate(task_membership_history):
        max_value = max(step.values())
        near_max_labels = {label: value for label, value in step.items() if value == max_value}
        if len(near_max_labels) > 1:
            confusion_steps.append((index + 1, near_max_labels))
    return confusion_steps

# 12. Threshold Nondeterministic Task Confusion
def threshold_task_nondeterministic_confusion_check(task_membership_history, threshold=0.7):
    """
    Check for threshold nondeterministic task confusion:
    The human thinks two or more task labels are equally the most possible.
    """
    confusion_steps = []
    for index, step in enumerate(task_membership_history):
        above_threshold_labels = {label: value for label, value in step.items() if value > threshold}
        if len(above_threshold_labels) > 1:
            confusion_steps.append((index + 1, above_threshold_labels))
    return confusion_steps

# 13. Vacuous State Confusion
def vacuous_state_confusion_check(data):
    """
    Check for vacuous state confusion:
    The human has no strong membership for any state category.
    """
    confusion_steps = []
    for index, step in enumerate(data):
        threshold = 0
        if max(step.values()) == threshold:
            confusion_steps.append((index + 1, step))
    return confusion_steps

# 14. Threshold Vacuous State Confusion
def threshold_vacuous_state_confusion_check(data, threshold=0.3):
    """
    Check for threshold vacuous state confusion:
    The human has no strong membership for any state category, based on a threshold.
    """
    confusion_steps = []
    for index, step in enumerate(data):
        if max(step.values()) <= threshold:
            confusion_steps.append((index + 1, step))
    return confusion_steps

# 15. Vacuous Task Confusion
def vacuous_task_confusion_check(task_membership_history):
    """
    Check for vacuous task confusion:
    The human has no idea what the system is doing as none of the task labels 
    have a membership above 0.
    """
    confusion_steps = []
    for index, step in enumerate(task_membership_history):
        if max(step.values()) == 0:
            confusion_steps.append((index + 1, step))
    return confusion_steps

# 16. Threshold Vacuous Task Confusion
def threshold_vacuous_task_confusion_check(task_membership_history, threshold=0.3):
    """
    Check for threshold vacuous task confusion:
    The human has little to no idea what the system is doing as none of the task labels 
    have a membership above a low threshold.
    """
    confusion_steps = []
    for index, step in enumerate(task_membership_history):
        if max(step.values()) <= threshold:
            confusion_steps.append((index + 1, step))
    return confusion_steps

# 17. Aggregate Blocking State Check
def aggregate_blocking_state_check(blocking_history, system_data):
    """
    Check for aggregate blocking state:
    The human thinks the most possible automation state(s) 
    does not allow for a specific action that would cause a system change.
    """
    pass
    

# 18. Aggregate Threshold Blocking State Check
def aggregate_threshold_blocking_state_check(blocking_history, system_data):
    """
    Check for taggregate hreshold blocking state:
    The human thinks the most possible automation state(s) 
    does not allow for a specific action that would cause a system change.
    """
    blocking_steps = []
    for i, (blocking, current_system_state) in enumerate(zip(blocking_history, system_data)):
        B = blocking['B']
        C = blocking['C']
        if B > C:
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

# 19. Aggregate Dominant Blocking Task Check
def aggregate_dominant_task_blocking_state_check(blocking_history, system_data):
    """
    Check for aggregate dominant task labels blocking state:
    The human thinks the most possible task label(s) 
    does not allow for a specific action that would cause a system change.
    """
    pass
    

# 20. Aggregate Threshold Blocking Task Check
def aggregate_threshold_task_blocking_state_check(blocking_history, system_data):
    """
    Check for aggregate threshold blocking task labels blocking state:
    The human thinks the most possible task label(s) 
    does not allow for a specific action that would cause a system change.
    """
    blocking_steps = []
    for i, (blocking, current_system_state) in enumerate(zip(blocking_history, system_data)):
        B_task = blocking['B_task']
        C_task = blocking['C_task']
        if B_task > C_task:
            current_task_label = current_system_state.get('task_label')
            if current_task_label is not None and i + 1 < len(system_data):
                next_task_label = system_data[i + 1].get('task_label')
                if next_task_label is not None and current_task_label != next_task_label:
                    blocking_steps.append(i)
    return blocking_steps

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

    dominant_error_state = dominant_state_error_check(state_membership_history, system_data)
    threshold_error_state = threshold_state_error_check(state_membership_history, system_data)
    nondeterministic_confusions = dominant_nondeterministic_state_confusion_check(state_membership_history)
    threshold_nondeterministic_confusions = threshold_nondeterministic_state_confusion_check(state_membership_history)
    vacuous_confusions = vacuous_state_confusion_check(state_membership_history)
    threshold_vacuous_confusions = threshold_vacuous_state_confusion_check(state_membership_history)
    dominant_blocking_states = dominant_blocking_state_check(state_membership_history, system_data)
    threshold_blocking_states = threshold_blocking_state_check(state_membership_history, system_data)
    dominant_task_labels_blocking_states = dominant_task_blocking_state_check(state_membership_history, system_data)
    threshold_task_labels_blocking_states = threshold_task_blocking_state_check(state_membership_history, system_data)
    task_label_mismatches = dominant_task_error_check(task_membership_history, system_data)
    threshold_task_label_mismatches = threshold_task_error_check(task_membership_history, system_data)
    task_label_nondeterministic_confusions = dominant_task_nondeterministic_confusion_check(task_membership_history)
    threshold_task_label_nondeterministic_confusions = threshold_task_nondeterministic_confusion_check(task_membership_history)
    vacuous_task_confusions = vacuous_task_confusion_check(task_membership_history)
    threshold_vacuous_task_confusions = threshold_vacuous_task_confusion_check(task_membership_history)

    results = {}

    # Dominant Error State results
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
        results["Dominant State Error"] = dominant_error_state_results

    # Threshold Error State results
    threshold_error_state_results = [
        {
            "Step": idx,
            "Action": expanded_schedule[idx] if idx < len(expanded_schedule) else None,
            "FMMFSM State": get_fmmfsm_state(state_membership_history[idx]) if idx < len(state_membership_history) else None,
            "Result": "True"
        } if result[0] else {
            "Step": idx,
            "Action": expanded_schedule[idx] if idx < len(expanded_schedule) else None,
            "FMMFSM State": get_fmmfsm_state(state_membership_history[idx]) if idx < len(state_membership_history) else None,
            "Result": "False",
            "Fuzzy Above Threshold": result[1],
        }
        for idx, result in enumerate(threshold_error_state)
    ]

    if threshold_error_state_results:
        results["Threshold State Error"] = threshold_error_state_results

    # Dominant Task Error results
    if task_label_mismatches:
        results["Dominant Task Error"] = [
            {"Step": step, "Action": expanded_schedule[step] if step < len(expanded_schedule) else None, "FMMFSM Task Label": fmmfsm_task_label, "System Task Label": system_task_label}
            for step, fmmfsm_task_label, system_task_label in task_label_mismatches
        ]
    
    # Threshold Task Error results
    if threshold_task_label_mismatches:
        results["Threshold Task Error"] = [
            {"Step": step, "Action": expanded_schedule[step] if step < len(expanded_schedule) else None, "FMMFSM Task Label": fmmfsm_task_label, "System Task Label": system_task_label}
            for step, fmmfsm_task_label, system_task_label in threshold_task_label_mismatches
        ]

    # Dominant Blocking State results
    if dominant_blocking_states:
        results["Dominant Blocking State"] = [
            {"Step": step, "Action": expanded_schedule[step] if step < len(expanded_schedule) else None, "FMMFSM State": get_fmmfsm_state(state_membership_history[step]) if step < len(state_membership_history) else None}
            for step in dominant_blocking_states
        ]

    # Threshold Blocking State results
    if threshold_blocking_states:
        results["Threshold Blocking State"] = [
            {"Step": step, "Action": expanded_schedule[step] if step < len(expanded_schedule) else None, "FMMFSM State": get_fmmfsm_state(state_membership_history[step]) if step < len(state_membership_history) else None}
            for step in threshold_blocking_states
        ]
    
    # Dominant Blocking Task results
    if dominant_task_labels_blocking_states:
        results["Dominant Blocking Task"] = [
            {"Step": step, "Action": expanded_schedule[step] if step < len(expanded_schedule) else None, "FMMFSM State": get_fmmfsm_state(state_membership_history[step]) if step < len(state_membership_history) else None}
            for step in dominant_task_labels_blocking_states
        ]

    # Threshold Blocking Task results
    if threshold_task_labels_blocking_states:
        results["Threshold Blocking Task"] = [
            {"Step": step, "Action": expanded_schedule[step] if step < len(expanded_schedule) else None, "FMMFSM State": get_fmmfsm_state(state_membership_history[step]) if step < len(state_membership_history) else None}
            for step in threshold_task_labels_blocking_states
        ]

    # Dominant Nondeterministic State Confusion results
    if nondeterministic_confusions:
        results["Dominant Nondeterministic State Confusion"] = [
            {"Step": step - 1, "Action": expanded_schedule[step - 1] if step - 1 < len(expanded_schedule) else None, "FMMFSM Task Labels": labels}
            for step, labels in nondeterministic_confusions
        ]

    # Threshold Nondeterministic State Confusion results
    if threshold_nondeterministic_confusions:
        results["Threshold Nondeterministic State Confusion"] = [
            {"Step": step - 1, "Action": expanded_schedule[step - 1] if step - 1 < len(expanded_schedule) else None, "FMMFSM Task Labels": labels}
            for step, labels in threshold_nondeterministic_confusions
        ]

    # Dominant Nondeterministic Task Confusion results
    if task_label_nondeterministic_confusions:
        results["Dominant Nondeterministic Task Confusion"] = [
            {"Step": step - 1, "Action": expanded_schedule[step - 1] if step - 1 < len(expanded_schedule) else None, "FMMFSM Task Labels": labels}
            for step, labels in task_label_nondeterministic_confusions
        ]

    # Threshold Nondeterministic Task Confusion results
    if threshold_task_label_nondeterministic_confusions:
        results["Threshold Nondeterministic Task Confusion"] = [
            {"Step": step - 1, "Action": expanded_schedule[step - 1] if step - 1 < len(expanded_schedule) else None, "FMMFSM Task Labels": labels}
            for step, labels in threshold_task_label_nondeterministic_confusions
        ]

    # Vacuous State Confusion
    if vacuous_confusions:
        results["Vacuous State Confusion"] = [
            {"Step": step - 1, "Action": expanded_schedule[step - 1] if step - 1 < len(expanded_schedule) else None, "FMMFSM State": get_fmmfsm_state(state_membership_history[step - 1]) if step - 1 < len(state_membership_history) else None, "State Memberships": states}
            for step, states in vacuous_confusions
        ]

    # Threshold Vacuous State Confusion
    if threshold_vacuous_confusions:
        results["Threshold Vacuous State Confusion"] = [
            {"Step": step - 1, "Action": expanded_schedule[step - 1] if step - 1 < len(expanded_schedule) else None, "FMMFSM State": get_fmmfsm_state(state_membership_history[step - 1]) if step - 1 < len(state_membership_history) else None, "State Memberships": states}
            for step, states in threshold_vacuous_confusions
        ]

    # Vacuous Task Confusion
    if vacuous_task_confusions:
        results["Vacuous Task Confusion"] = [
            {"Step": step - 1, "Action": expanded_schedule[step - 1] if step - 1 < len(expanded_schedule) else None, "FMMFSM Task Memberships": states}
            for step, states in vacuous_task_confusions
        ]

    # Threshold Vacuous Task Confusion
    if threshold_vacuous_task_confusions:
        results["Threshold Vacuous Task Confusion"] = [
            {"Step": step - 1, "Action": expanded_schedule[step - 1] if step - 1 < len(expanded_schedule) else None, "FMMFSM Task Memberships": states}
            for step, states in threshold_vacuous_task_confusions
        ]

    result_path = os.path.join(result_directory, filename)
    with open(result_path, 'w') as result_file:
        json.dump(results, result_file, indent=4)