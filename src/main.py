from pathlib import Path

from utils import load_attractions, haversine
from csp_filter import apply_constraints
from ga_optimizer import optimize_route_order
import pandas as pd
import folium

OUTPUT_DIR = Path(__file__).resolve().parent.parent / "output"

# -----------------------------
# Map plotting
# -----------------------------
def plot_route(route, filename="map.html"):
    if not route:
        return
    m = folium.Map(location=[route[0]['lat'], route[0]['lon']], zoom_start=13)
    coords = [(a['lat'], a['lon']) for a in route]
    folium.PolyLine(coords, color="blue").add_to(m)
    for a in route:
        folium.Marker([a['lat'], a['lon']],
                      popup=f"{a['name']} ({a['category']})\nDuration: {a['duration']}h\nCost: {a['cost']}").add_to(m)
    m.save(filename)

# -----------------------------
# Knapsack-based top itineraries
# -----------------------------
def get_top_itineraries_knapsack(feasible, max_total_hours=8, top_k=3, avg_speed_kmph=25, user_budget=100):
    import copy
    remaining_attractions = copy.deepcopy(feasible)
    top_itineraries = []
    used_names = {}

    for k in range(top_k):
        if not remaining_attractions:
            break

        # Apply soft penalty for reusing same attractions
        for a in remaining_attractions:
            penalty = 0.9 ** used_names.get(a['name'], 0)
            a['adjusted_rating'] = a['rating'] * penalty

        n = len(remaining_attractions)
        dp = [[0 for _ in range(max_total_hours + 1)] for _ in range(n + 1)]

        for i in range(1, n + 1):
            duration = remaining_attractions[i - 1]['duration']
            rating = remaining_attractions[i - 1]['adjusted_rating']
            for w in range(1, max_total_hours + 1):
                if duration <= w:
                    dp[i][w] = max(dp[i - 1][w], dp[i - 1][w - duration] + rating)
                else:
                    dp[i][w] = dp[i - 1][w]

        # Retrieve selected items
        res = []
        w = max_total_hours
        for i in range(n, 0, -1):
            if dp[i][w] != dp[i - 1][w]:
                res.append(remaining_attractions[i - 1])
                w -= remaining_attractions[i - 1]['duration']
        itinerary = res[::-1]

        if not itinerary:
            continue

        # Metrics
        total_distance = sum(haversine(itinerary[i], itinerary[i + 1]) for i in range(len(itinerary) - 1)) if len(itinerary) > 1 else 0
        travel_time_hours = total_distance / avg_speed_kmph
        total_duration = sum(a['duration'] for a in itinerary)
        total_cost = sum(a['cost'] for a in itinerary)
        total_rating = sum(a['rating'] for a in itinerary)
        total_time = total_duration + travel_time_hours

        if total_cost > user_budget:
            continue
        if total_time <= max_total_hours * 1.2:
            time_efficiency = max_total_hours / total_time
            score = (total_rating * time_efficiency) / (1 + total_distance)
            top_itineraries.append((score, itinerary, total_distance, total_rating, total_duration, travel_time_hours, total_cost))

        for a in itinerary:
            used_names[a['name']] = used_names.get(a['name'], 0) + 1

    top_itineraries.sort(reverse=True, key=lambda x: x[0])
    return top_itineraries[:top_k]

# -----------------------------
# HTML Summary
# -----------------------------
def generate_html_summary(user_budget, user_interests, visit_hours, knapsack_itineraries, ga_routes):
    html = f"""
    <html><head><title>Itinerary Summary</title>
    <link href="https://fonts.googleapis.com/css2?family=Roboto:wght@400;500&family=Open+Sans:wght@400;600&display=swap" rel="stylesheet">
    <style>
        body {{font-family:'Open Sans',sans-serif;background:#f9f9f9;color:#333;margin:0;padding:20px;}}
        h1{{font-family:'Roboto',sans-serif;color:#2c3e50;}}
        h2{{font-family:'Roboto',sans-serif;color:#34495e;border-bottom:2px solid #ddd;padding-bottom:5px;}}
        h3{{font-family:'Roboto',sans-serif;color:#555;margin-top:15px;}}
        p{{font-size:0.95em;line-height:1.4em;}}
        table{{border-collapse:collapse;width:100%;margin-bottom:20px;font-size:0.9em;background:#fff;box-shadow:0 2px 5px rgba(0,0,0,0.05);}}
        th,td{{border:1px solid #e0e0e0;padding:8px 12px;text-align:left;}}
        th{{background:#f0f0f0;font-weight:600;}}
        tr:nth-child(even){{background:#f9f9f9;}}
        a.button{{text-decoration:none;background:#3498db;color:white;padding:5px 10px;border-radius:5px;font-size:0.9em;}}
        .summary-box{{background:#ecf0f1;padding:10px 15px;border-radius:5px;margin-bottom:20px;}}
    </style></head><body>
    <h1>Personalized Itinerary Summary</h1>
    <div class="summary-box">
        <p><strong>Budget:</strong> {user_budget} &nbsp;&nbsp;|&nbsp;&nbsp;
        <strong>Interests:</strong> {', '.join(user_interests)} &nbsp;&nbsp;|&nbsp;&nbsp;
        <strong>Visit Hours:</strong> {visit_hours[0]} to {visit_hours[1]} ({visit_hours[1]-visit_hours[0]} hrs)</p>
    </div>
    """

    # Knapsack itineraries
    html += "<h2>Top Knapsack-based Itineraries</h2>"
    for idx, (score, combo, dist, rating, duration, travel_time, cost) in enumerate(knapsack_itineraries, start=1):
        map_file = f"map_option{idx}.html"
        html += f"<h3>Option {idx} (Score: {score:.2f}) <a class='button' href='{map_file}'>View Map</a></h3>"
        html += f"<p>Total Cost: {cost}, Total Rating: {rating:.2f}, Duration: {duration}h, Travel: {travel_time:.2f}h, Distance: {dist:.2f} km</p>"
        html += "<table><tr><th>#</th><th>Attraction</th><th>Category</th><th>Cost</th><th>Rating</th><th>Duration</th></tr>"
        for i, a in enumerate(combo,1):
            html += f"<tr><td>{i}</td><td>{a['name']}</td><td>{a['category']}</td><td>{a['cost']}</td><td>{a['rating']}</td><td>{a['duration']}</td></tr>"
        html += "</table>"

    # GA-optimized routes
    html += "<h2>GA Optimized Visiting Order</h2>"
    for idx, (route, fit) in enumerate(ga_routes,1):
        map_file = f"map_ga_option{idx}.html"
        total_distance = sum(haversine(route[i], route[i+1]) for i in range(len(route)-1)) if len(route)>1 else 0
        travel_time = total_distance / 25
        total_duration = sum(a['duration'] for a in route)
        total_cost = sum(a['cost'] for a in route)
        total_time = total_duration + travel_time
        html += f"<h3>Option {idx} (Fitness: {fit:.2f}) <a class='button' href='{map_file}'>View Map</a></h3>"
        html += f"<p>Total Cost: {total_cost}, Duration: {total_duration}h, Travel: {travel_time:.2f}h, Total Time: {total_time:.2f}h, Distance: {total_distance:.2f} km</p>"
        html += "<table><tr><th>#</th><th>Attraction</th><th>Category</th><th>Duration</th></tr>"
        for i, a in enumerate(route,1):
            html += f"<tr><td>{i}</td><td>{a['name']}</td><td>{a['category']}</td><td>{a['duration']}</td></tr>"
        html += "</table>"

    html += "</body></html>"

    OUTPUT_DIR.mkdir(exist_ok=True)
    summary_path = OUTPUT_DIR / "itinerary_summary.html"
    with open(summary_path, "w", encoding="utf-8") as f:
        f.write(html)
    print(f"HTML summary saved as {summary_path}")

# -----------------------------
# Main
# -----------------------------
def main():
    OUTPUT_DIR.mkdir(exist_ok=True)
    attractions = load_attractions()
    print(f"Total attractions in dataset: {len(attractions)}")

    # User input
    user_budget = float(input("Enter your budget (e.g., 40): "))
    user_interests = [x.strip() for x in input("Enter your interests separated by comma: ").split(",")]
    start_hour = int(input("Enter visit start hour (0-23): "))
    end_hour = int(input("Enter visit end hour (0-23): "))
    visit_hours = (start_hour, end_hour)
    available_hours = end_hour - start_hour

    # CSP filtering
    feasible_attractions = apply_constraints(attractions, user_budget, user_interests, visit_hours)
    print(f"\nFeasible attractions after CSP filtering: {len(feasible_attractions)}")
    for a in feasible_attractions:
        print(f"{a['name']} | {a['category']} | Cost: {a['cost']} | Rating: {a['rating']} | Duration: {a['duration']}h")

    if not feasible_attractions:
        print("No attractions fit your constraints.")
        return

    # Knapsack itineraries
    top_itineraries = get_top_itineraries_knapsack(feasible_attractions, max_total_hours=available_hours, top_k=3, user_budget=user_budget)
    for idx, (score, combo, dist, rating, duration, travel_time, cost) in enumerate(top_itineraries,1):
        plot_route(combo, filename=str(OUTPUT_DIR / f"map_option{idx}.html"))

    # GA optimization of visiting order for each knapsack itinerary
    ga_routes = []
    for idx, (_, combo, _, _, _, _, _) in enumerate(top_itineraries,1):
        optimized_route, fit = optimize_route_order(combo, generations=60)
        ga_routes.append((optimized_route, fit))
        plot_route(optimized_route, filename=str(OUTPUT_DIR / f"map_ga_option{idx}.html"))

    # Generate HTML summary
    generate_html_summary(user_budget, user_interests, visit_hours, top_itineraries, ga_routes)

if __name__ == "__main__":
    main()
