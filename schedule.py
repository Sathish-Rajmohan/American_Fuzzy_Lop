import random
import math
from datetime import datetime

current_cycle = 0
seeds_visited_in_cycle = set()

def calculate_favored_seeds(seed_queue):
    """Mark seeds as favored based on AFL algorithm"""
    if not seed_queue:
        return
    
    for seed in seed_queue:
        seed.unmark_favored()
    
    file_sizes = [s.file_size for s in seed_queue if s.file_size > 0]
    exec_times = [s.exec_time for s in seed_queue if s.exec_time > 0]
    coverages = [s.coverage for s in seed_queue if s.coverage > 0]
    
    if not file_sizes:
        return
        
    file_sizes_sorted = sorted(file_sizes)
    exec_times_sorted = sorted(exec_times) if exec_times else [0.001]
    coverages_sorted = sorted(coverages, reverse=True) if coverages else [1]
    
    size_threshold = file_sizes_sorted[len(file_sizes_sorted) // 4] if len(file_sizes_sorted) > 4 else file_sizes_sorted[0]
    time_threshold = exec_times_sorted[len(exec_times_sorted) // 4] if len(exec_times_sorted) > 4 else exec_times_sorted[0]
    coverage_threshold = coverages_sorted[len(coverages_sorted) // 4] if len(coverages_sorted) > 4 else coverages_sorted[0]
    
    favored_count = 0
    for seed in seed_queue:
        good_characteristics = 0
        
        if seed.file_size <= size_threshold:
            good_characteristics += 1
        if seed.exec_time <= time_threshold:
            good_characteristics += 1
        if seed.coverage >= coverage_threshold:
            good_characteristics += 1
        if good_characteristics >= 2:
            seed.mark_favored()
            favored_count += 1
    
    if favored_count == 0 and seed_queue:
        best_seed = max(seed_queue, key=lambda s: s.coverage/(s.exec_time + 0.001))
        best_seed.mark_favored()
        favored_count = 1
    
    print(f"Marked {favored_count}/{len(seed_queue)} seeds as favored")

def select_next_seed(seed_queue):
    """Select next seed with favored preference"""
    global current_cycle, seeds_visited_in_cycle
    
    if not seed_queue:
        return None
    
    if len(seeds_visited_in_cycle) >= len(seed_queue):
        seeds_visited_in_cycle.clear()
        current_cycle += 1
        for seed in seed_queue:
            seed.reset_cycle_usage()
    
    unvisited_seeds = [s for s in seed_queue 
                      if s.seed_id not in seeds_visited_in_cycle]
    
    if not unvisited_seeds:
        seeds_visited_in_cycle.clear()
        unvisited_seeds = seed_queue.copy()
    
    favored_unvisited = [s for s in unvisited_seeds if s.is_favored()]
    non_favored_unvisited = [s for s in unvisited_seeds if not s.is_favored()]
    
    selected = None
    
    if favored_unvisited and (random.random() < 0.75 or not non_favored_unvisited):
        selected = random.choice(favored_unvisited)
    else:
        if non_favored_unvisited:
            selected = random.choice(non_favored_unvisited)
        else:
            selected = random.choice(favored_unvisited) if favored_unvisited else random.choice(seed_queue)
    
    if selected:
        seeds_visited_in_cycle.add(selected.seed_id)
        selected.mark_used_in_cycle()
    
    return selected

def get_power_schedule(seed):
    """Power scheduling based on execution speed, edge coverage and energy"""
    base_power = 4
    
    coverage_multiplier = 1.0
    if seed.coverage > 0:
        coverage_multiplier = min(1.0 + math.log2(1 + seed.coverage / 10.0), 3.0)
    
    speed_multiplier = 1.0
    if seed.exec_time > 0:
        if seed.exec_time > 0.5: 
            speed_multiplier = 0.5
        elif seed.exec_time < 0.01: 
            speed_multiplier = 2.0
        elif seed.exec_time < 0.05: 
            speed_multiplier = 1.5
    
    favored_multiplier = 2.0 if seed.is_favored() else 1.0

    energy_multiplier = seed.energy
    
    power = base_power * coverage_multiplier * speed_multiplier * favored_multiplier * energy_multiplier

    power = max(1, min(int(power), 20))
    
    seed.adjust_energy(0.9)
    
    return power