# Travel Optimizer

A personalized itinerary planner that turns a traveler's budget, interests, and available
hours into ready-to-visit routes — filtered for feasibility, selected for maximum value, and
ordered for minimum travel time, with each option rendered as an interactive map.

## Problem

Planning a day of sightseeing means juggling several constraints at once: which attractions
fit the budget, which match your interests, which are even open during your visit window, and
in what order to visit them so you're not zig-zagging across the city. Doing this by hand
across dozens of attractions is tedious and easy to get wrong.

## Approach

The pipeline runs in three stages:

1. **CSP-based filtering** (`csp_filter.py`) — treats budget, interest category, and
   open/close hours as hard constraints and filters the full attraction list down to only
   those that are actually feasible for the trip.
2. **Knapsack-based attraction selection** (`main.py`) — given the feasible set, a 0/1
   knapsack (dynamic programming) picks the combination of attractions that maximizes total
   rating within the available visiting hours, subject to the budget. It generates the top-K
   distinct itinerary options (with a soft penalty discouraging repeated picks across options).
3. **Genetic Algorithm route optimization** (`ga_optimizer.py`) — for each selected itinerary,
   a GA (selection, crossover, mutation over generations) searches for the visiting *order*
   that minimizes total travel distance/time between stops, using haversine distance.

Each itinerary — before and after GA ordering — is rendered as an interactive **Folium** map
with markers and a route polyline, plus a consolidated HTML summary comparing all options.

## Tech stack

- Python 3
- [python-constraint](https://pypi.org/project/python-constraint/) — CSP filtering
- pandas, numpy — data handling
- [Folium](https://python-visualization.github.io/folium/) — interactive map visualization
- matplotlib — fitness/progress plotting

## Project structure

```
travel_optimizer/
├── src/
│   ├── main.py           # CLI entry point: orchestrates CSP -> Knapsack -> GA -> maps/report
│   ├── csp_filter.py      # Constraint-based feasibility filtering
│   ├── ga_optimizer.py    # Genetic algorithm for route ordering
│   └── utils.py           # Haversine distance, data loading
├── data/
│   └── attractions.json   # Attraction dataset (name, location, cost, rating, hours, etc.)
├── output/                 # Generated maps, itineraries, and reports (git-ignored)
├── requirements.txt
└── README.md
```

## Setup

```bash
python -m venv venv
venv\Scripts\activate        # Windows
# source venv/bin/activate   # macOS/Linux

pip install -r requirements.txt
```

## Run

```bash
python src/main.py
```

You'll be prompted for:

- **Budget** (e.g. `40`)
- **Interests**, comma-separated (e.g. `museum,park`)
- **Visit start hour** and **end hour** (24h format, e.g. `9` to `17`)

The script prints the feasible attractions after CSP filtering, then generates:

- `output/map_option{1,2,3}.html` — knapsack-selected itineraries (unordered)
- `output/map_ga_option{1,2,3}.html` — same itineraries with GA-optimized visiting order
- `output/itinerary_summary.html` — a combined summary report with cost, rating, duration,
  and travel-time metrics for every option, linking out to each map

Open `output/itinerary_summary.html` in a browser to explore the results.
