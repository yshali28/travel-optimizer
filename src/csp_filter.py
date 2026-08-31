# csp_filter.py
from utils import load_attractions

def apply_constraints(attractions, user_budget, user_interests, visit_hours=(10,18)):
    feasible = []
    start_hour, end_hour = visit_hours

    for attr in attractions:
        # Budget
        if attr['cost'] > user_budget:
            continue

        # Interest match
        if not any(interest.lower() in attr['category'].lower() for interest in user_interests):
            continue

        # Duration check: attraction must fit within available visit hours
        available_start = max(start_hour, attr['open_hour'])
        available_end = min(end_hour, attr['close_hour'])
        if available_end - available_start < attr['duration']:
            continue

        feasible.append(attr)

    return feasible




# Quick test when running this file
if __name__ == "__main__":
    attractions = load_attractions()
    user_budget = 100
    user_interests = ['museum']
    feasible = apply_constraints(attractions, user_budget, user_interests)
    print(f"Total attractions after CSP filtering: {len(feasible)}")
    for a in feasible:
        print(f"{a['name']} | {a['category']} | Cost: {a['cost']}")
