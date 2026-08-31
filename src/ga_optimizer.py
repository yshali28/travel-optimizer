import random
from utils import haversine

def fitness(route, avg_speed_kmph):
    """Fitness just considers travel distance/time for ordering (rating is already optimized by knapsack)."""
    total_distance = sum(haversine(route[i], route[i+1]) for i in range(len(route)-1)) if len(route) > 1 else 0
    travel_time = total_distance / avg_speed_kmph
    # Smaller travel time = higher fitness
    return -travel_time

def initialize_population(route, pop_size=30):
    return [random.sample(route, len(route)) for _ in range(pop_size)]

def selection(population, fitnesses, top_k=10):
    scored = list(zip(fitnesses, population))
    scored.sort(reverse=True, key=lambda x:x[0])
    return [ind for _,ind in scored[:top_k]]

def crossover(parent1, parent2):
    size = len(parent1)
    start, end = sorted(random.sample(range(size), 2))
    child_p1 = parent1[start:end]
    child_p2 = [a for a in parent2 if a not in child_p1]
    return child_p2[:start] + child_p1 + child_p2[start:]

def mutate(individual, mutation_rate=0.1):
    for _ in range(int(len(individual) * mutation_rate)):
        i,j = random.sample(range(len(individual)),2)
        individual[i],individual[j] = individual[j],individual[i]
    return individual

def optimize_route_order(route, generations=50, pop_size=30, avg_speed_kmph=25):
    """GA for optimizing visiting order only."""
    if len(route) <= 1:
        return route, 0.0

    population = initialize_population(route, pop_size)
    best_route = route
    best_fit = fitness(route, avg_speed_kmph)

    for _ in range(generations):
        fitnesses = [fitness(ind, avg_speed_kmph) for ind in population]
        selected = selection(population, fitnesses, top_k=max(2, pop_size//2))

        # Track best
        for f, ind in zip(fitnesses, population):
            if f > best_fit:
                best_fit = f
                best_route = ind

        new_population = []
        while len(new_population) < pop_size:
            p1, p2 = random.sample(selected, 2)
            child = crossover(p1, p2)
            child = mutate(child)
            new_population.append(child)
        population = new_population

    return best_route, best_fit
