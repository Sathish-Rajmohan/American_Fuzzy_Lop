import os
import time

class Seed:
    def __init__(self, path, seed_id, coverage, exec_time):
        self.path = path
        self.seed_id = seed_id
        self.coverage = coverage
        self.exec_time = exec_time
        self.favored = 0
        self.file_size = self._get_file_size()
        self.used_in_cycle = False
        self.timeout_count = 0
        self.new_edges_found = 0
        self.successful_mutations = []
        self.discovery_time = time.time()
        self.energy = 1.0 
        self.crash_count = 0

    def _get_file_size(self):
        try:
            return os.path.getsize(self.path)
        except OSError:
            return 0

    def mark_favored(self):
        self.favored = 1

    def unmark_favored(self):
        self.favored = 0
    
    def is_favored(self):
        return self.favored == 1
    
    def mark_used_in_cycle(self):
        self.used_in_cycle = True
    
    def reset_cycle_usage(self):
        self.used_in_cycle = False
        
    def increment_timeout(self):
        self.timeout_count += 1
        
    def increment_crash_count(self):
        self.crash_count += 1
        
    def adjust_energy(self, factor):
        self.energy *= factor
        self.energy = max(0.1, min(1.0, self.energy))