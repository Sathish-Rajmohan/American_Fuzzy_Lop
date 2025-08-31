import os
import argparse
import signal
import shutil
import random
import sys
from conf import *
from libc import *
from feedback import *
from execution import *
from seed import *
from schedule import *
from mutation import *

FORKSRV_FD = 198

def signal_handler(sig, frame):
    print('Ending fuzzing session...')
    sys.exit(0)

def run_forkserver(conf, ctl_read_fd, st_write_fd):
    """Set up and run the forkserver"""
    os.dup2(ctl_read_fd, FORKSRV_FD)
    os.dup2(st_write_fd, FORKSRV_FD + 1)
    cmd = [conf['target']] + conf['target_args']
    
    dev_null_fd = os.open(os.devnull, os.O_RDWR)
    os.dup2(dev_null_fd, 1)
    os.dup2(dev_null_fd, 2)
    os.execv(conf['target'], cmd)

def run_fuzzing(conf, st_read_fd, ctl_write_fd, trace_bits):
    """Main fuzzing loop"""
    read_bytes = os.read(st_read_fd, 4)
    if len(read_bytes) == 4:
        print("Forkserver ready - begin fuzzing (Ctrl+C to stop)")

    crash_queue = []
    seed_queue = []
    
    if not os.path.exists(conf['queue_folder']):
        os.makedirs(conf['queue_folder'])
    
    print("Starting dry run...")
    
    initial_seeds = sorted(os.listdir(conf['seeds_folder']))
    for i, seed_file in enumerate(initial_seeds):
        src_path = os.path.join(conf['seeds_folder'], seed_file)
        queue_filename = f"id_{i:06d}"
        dst_path = os.path.join(conf['queue_folder'], queue_filename)
        shutil.copyfile(src_path, dst_path)
        
        shutil.copyfile(dst_path, conf['current_input'])
        
        status_code, exec_time = run_target(ctl_write_fd, st_read_fd, trace_bits)
        
        if status_code == 9:
            print(f"Dry run timeout on {seed_file}")
            sys.exit(1)
        if check_crash(status_code):
            print(f"Dry run crash on {seed_file}")
            sys.exit(1)
            
        new_edge_covered, coverage = check_coverage(trace_bits)
        seed_obj = Seed(dst_path, i, coverage, exec_time)
        seed_queue.append(seed_obj)

    print(f"Dry run completed with {len(seed_queue)} seeds")
    print(f"Initial coverage: {get_total_coverage()} edges")
    
    calculate_favored_seeds(seed_queue)
    
    iteration = 0
    
    while True:
        selected_seed = select_next_seed(seed_queue)
        if selected_seed is None:
            break
            
        shutil.copyfile(selected_seed.path, conf['current_input'])

        power_schedule = get_power_schedule(selected_seed)
        
        if iteration % 100 == 0:
            favored_count = sum(1 for s in seed_queue if s.is_favored())
            print(f"Iteration {iteration}: Seeds={len(seed_queue)} ({favored_count} favored), "
                  f"Coverage={get_total_coverage()}, Crashes={len(crash_queue)}")
        
        for mutation_round in range(power_schedule):
            havoc_mutation(conf, selected_seed)
            
            status_code, exec_time = run_target(ctl_write_fd, st_read_fd, trace_bits)
            
            if status_code == 9:
                selected_seed.increment_timeout()
                continue
            
            if check_crash(status_code):
                crash_id = len(crash_queue)
                crash_filename = f"crash_{crash_id:06d}"
                crash_path = os.path.join(conf['crashes_folder'], crash_filename)
                shutil.copyfile(conf['current_input'], crash_path)
                crash_queue.append(crash_path)
                print(f"*** CRASH FOUND *** Saved to {crash_path}")
                continue
                
            new_edge_covered, coverage = check_coverage(trace_bits)
            
            if new_edge_covered:
                new_seed_path = save_new_seed(conf, seed_queue)
                new_seed = Seed(new_seed_path, len(seed_queue), coverage, exec_time)
                seed_queue.append(new_seed)
                
                if len(seed_queue) % 25 == 0:
                    calculate_favored_seeds(seed_queue)
        
        iteration += 1

def main():
    print("=== Mini-Lop Fuzzer ===")
    parser = argparse.ArgumentParser(description='Lightweight grey-box fuzzer')
    parser.add_argument('--config', '-c', required=True, help='Config file path')
    args = parser.parse_args()

    config_valid, conf = parse_config(os.path.abspath(args.config))
    if not config_valid:
        print("Invalid configuration, exiting")
        sys.exit(1)

    libc = get_libc()
    shmid, trace_bits = setup_shm(libc)
    os.environ[SHM_ENV_VAR] = str(shmid)
    clear_shm(trace_bits)

    signal.signal(signal.SIGINT, signal_handler)
    
    st_read_fd, st_write_fd = os.pipe()
    ctl_read_fd, ctl_write_fd = os.pipe()

    if os.fork() == 0:
        run_forkserver(conf, ctl_read_fd, st_write_fd)
    else:
        run_fuzzing(conf, st_read_fd, ctl_write_fd, trace_bits)

if __name__ == '__main__':
    main()