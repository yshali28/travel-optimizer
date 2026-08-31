import math
import json
from pathlib import Path

DATA_DIR = Path(__file__).resolve().parent.parent / "data"

def haversine(a, b):
    # a and b are dicts with 'lat' and 'lon'
    R = 6371  # Earth radius in km
    lat1, lon1 = math.radians(a['lat']), math.radians(a['lon'])
    lat2, lon2 = math.radians(b['lat']), math.radians(b['lon'])
    dlat = lat2 - lat1
    dlon = lon2 - lon1
    hav = math.sin(dlat/2)**2 + math.cos(lat1)*math.cos(lat2)*math.sin(dlon/2)**2
    return 2*R*math.asin(math.sqrt(hav))

def load_attractions(file_path=None):
    if file_path is None:
        file_path = DATA_DIR / "attractions.json"
    with open(file_path, "r") as f:
        data = json.load(f)
    return data

if __name__ == "__main__":
    attractions = load_attractions()
    print(f"Loaded {len(attractions)} attractions.")
    print("Distance between first two:", haversine(attractions[0], attractions[1]), "km")
