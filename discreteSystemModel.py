def transition_state(current_state, action):
    transitions = {
        'P': {
            'up1': 'P',
            'up2': 'P',
            'up3': 'P',
            'down1': 'R',
            'down2': 'N',
            'down3': 'D'
        },
        'R': {
            'up1': 'P',
            'up2': 'P',
            'up3': 'P',
            'down1': 'N',
            'down2': 'D',
            'down3': 'D'
        },
        'N': {
            'up1': 'R',
            'up2': 'P',
            'up3': 'P',
            'down1': 'D',
            'down2': 'D',
            'down3': 'D'
        },
        'D': {
            'up1': 'N',
            'up2': 'R',
            'up3': 'P',
            'down1': 'D',
            'down2': 'D',
            'down3': 'D'
        }
    }
    # Determine the next state based on the current state and action taken
    return transitions[current_state][action]

def simulate_actions(initial_state, actions):
    current_state = initial_state
    print(f"Initial state: {current_state}")

    for action, steps in actions:
        for step in range(steps):
            current_state = transition_state(current_state, action)
            print(f"After step {step + 1} with action '{action}': {current_state}")

# Example usage
initial_state = 'P'
actions = [('down1', 2), ('down2', 1), ('up1', 3), ('up2', 2), ('down3', 1), ('up3', 1), ('up1', 2)]

simulate_actions(initial_state, actions)