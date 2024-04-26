import numpy as np

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
    
    # Calculate the next state membership values for each state
    for current_state in states:
        for next_state in states:
            value = fuzzy_and([
                current_state_memberships[current_state],
                input_fuzzified[input_event][input_event],
                transition_probabilities[current_state][input_event][next_state]
            ])
            next_state_memberships[next_state].append(value)
    
    # Apply fuzzy OR across all calculated values for each next state
    for state in next_state_memberships:
        next_state_memberships[state] = fuzzy_or(next_state_memberships[state])
    
    return next_state_memberships

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

# Shift gear use case
# Driver begin with the car stopped, driver may think the car is in Neutral
'''
initial_state_memberships = {'P': 1, 'R': 0, 'N': 0.2, 'D': 0}
#initial_state_memberships = {'P': 1, 'R': 0, 'N': 0, 'D': 0}
input_fuzzified = {
    'up1': {'up1': 0.9, 'up2': 0.2, 'up3': 0, 'down1': 0.2, 'down2': 0, 'down3': 0}, 
    'up2': {'up1': 0.2, 'up2': 0.9, 'up3': 0.2, 'down1': 0, 'down2': 0.2, 'down3': 0},
    'up3': {'up1': 0, 'up2': 0.2, 'up3': 0.9, 'down1': 0, 'down2': 0, 'down3': 0.2},
    'down1': {'up1': 0.2, 'up2': 0, 'up3': 0, 'down1': 0.9, 'down2': 0.2, 'down3': 0},
    'down2': {'up1': 0, 'up2': 0.2, 'up3': 0, 'down1': 0.2, 'down2': 0.9, 'down3': 0.2},
    'down3': {'up1': 0, 'up2': 0, 'up3': 0.2, 'down1': 0, 'down2': 0.2, 'down3': 0.9}
}

input_fuzzified = {
    'up1': {'up1': 1, 'up2': 0, 'up3': 0, 'down1': 0, 'down2': 0, 'down3': 0}, 
    'up2': {'up1': 0, 'up2': 1, 'up3': 0, 'down1': 0, 'down2': 0, 'down3': 0},
    'up3': {'up1': 0, 'up2': 0, 'up3': 1, 'down1': 0, 'down2': 0, 'down3': 0},
    'down1': {'up1': 0, 'up2': 0, 'up3': 0, 'down1': 1, 'down2': 0, 'down3': 0},
    'down2': {'up1': 0, 'up2': 0, 'up3': 0, 'down1': 0, 'down2': 1, 'down3': 0},
    'down3': {'up1': 0, 'up2': 0, 'up3': 0, 'down1': 0, 'down2': 0, 'down3': 1}
}

transition_probabilities = {
    'P': {'up1': {'P': 1, 'R': 0, 'N': 0, 'D': 0}, 'up2': {'P': 1, 'R': 0, 'N': 0, 'D': 0}, 'up3': {'P': 1, 'R': 0, 'N': 0, 'D': 0}, 'down1': {'P': 0, 'R': 1, 'N': 0, 'D': 0}, 'down2': {'P': 0, 'R': 0, 'N': 1, 'D': 0}, 'down3': {'P': 0, 'R': 0, 'N': 0, 'D': 1}},
    'R': {'up1': {'P': 1, 'R': 0, 'N': 0, 'D': 0}, 'up2': {'P': 1, 'R': 0, 'N': 0, 'D': 0}, 'up3': {'P': 1, 'R': 0, 'N': 0, 'D': 0}, 'down1': {'P': 0, 'R': 0, 'N': 1, 'D': 0}, 'down2': {'P': 0, 'R': 0, 'N': 0, 'D': 1}, 'down3': {'P': 0, 'R': 0, 'N': 0, 'D': 1}},
    'N': {'up1': {'P': 0, 'R': 1, 'N': 0, 'D': 0}, 'up2': {'P': 1, 'R': 0, 'N': 0, 'D': 0}, 'up3': {'P': 1, 'R': 0, 'N': 0, 'D': 0}, 'down1': {'P': 0, 'R': 0, 'N': 0, 'D': 1}, 'down2': {'P': 0, 'R': 0, 'N': 0, 'D': 1}, 'down3': {'P': 0, 'R': 0, 'N': 0, 'D': 1}},
    'D': {'up1': {'P': 0, 'R': 0, 'N': 1, 'D': 0}, 'up2': {'P': 0, 'R': 1, 'N': 0, 'D': 0}, 'up3': {'P': 1, 'R': 0, 'N': 0, 'D': 0}, 'down1': {'P': 0, 'R': 0, 'N': 0, 'D': 1}, 'down2': {'P': 0, 'R': 0, 'N': 0, 'D': 1}, 'down3': {'P': 0, 'R': 0, 'N': 0, 'D': 1}}
}
input_schedule = [('down1', 2), ('down2', 1), ('up1', 3), ('up2', 2), ('down3', 1), ('up3', 1), ('up1', 2)]

'''

# cruise use case
initial_state_memberships = {'Active': 1, 'Inactive': 0.01}
input_fuzzified = {
    'Gas': {'Gas': 0.99, 'NoGas': 0.01}, 'NoGas': {'Gas': 0.00, 'NoGas': 1.00}}
transition_probabilities = {
    'Active': {'Gas': {'Active': 0.9, 'Inactive': 0.2}, 'NoGas': {'Active': 0.9, 'Inactive': 0.1}},
    'Inactive': {'Gas': {'Active': 0.2, 'Inactive': 0.9}, 'NoGas': {'Active': 0.0, 'Inactive': 1.0}}
}
input_schedule = [('Gas', 16), ('NoGas', 4)]


# Simulate the evolution of state memberships
history = evolve_state_over_time(initial_state_memberships, input_fuzzified, transition_probabilities, input_schedule)
for step, state_memberships in enumerate(history):
    print(f"Step {step}: {state_memberships}")
