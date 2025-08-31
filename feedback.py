import ctypes
import sys
import sysv_ipc
import os
import shutil

SHM_ENV_VAR = "__AFL_SHM_ID"
MAP_SIZE_POW2 = 16
MAP_SIZE = (1 << MAP_SIZE_POW2)

global_coverage = set()

def setup_shm(libc):
    """Initialize shared memory segment"""
    shmget = libc.shmget
    shmat = libc.shmat

    shmat.restype = ctypes.c_void_p
    shmat.argtypes = (ctypes.c_int, ctypes.c_void_p, ctypes.c_int)

    shmid = shmget(sysv_ipc.IPC_PRIVATE, MAP_SIZE, sysv_ipc.IPC_CREAT | sysv_ipc.IPC_EXCL | 0o600)
    if shmid < 0:
        sys.exit("cannot get shared memory segment")

    shmptr = shmat(shmid, None, 0)
    if shmptr == 0 or shmptr == -1:
        sys.exit("cannot attach shared memory segment")

    return shmid, shmptr

def clear_shm(trace_bits):
    """Clear shared memory bitmap"""
    ctypes.memset(trace_bits, 0, MAP_SIZE)

def check_crash(status_code):
    """Check if program crashed"""
    crashed = False
    if status_code in [6, 8, 11, 134, 139]:
        crashed = True
        print(f"Found crash (status: {status_code})")
    return crashed

def get_total_coverage():
    """Get the total number of edges covered so far"""
    global global_coverage
    return len(global_coverage)

def check_coverage(trace_bits, selected_seed=None, strategy=None):
    """
    Feature 1: Check edge coverage and maintain global state
    """
    global global_coverage
    
    raw_bitmap = ctypes.string_at(trace_bits, MAP_SIZE)
    total_hits = 0
    new_edge_covered = False

    for i, byte_val in enumerate(raw_bitmap):
        if byte_val != 0:
            total_hits += 1
            if i not in global_coverage:
                global_coverage.add(i)
                new_edge_covered = True
    
    if new_edge_covered:
        print(f'Found new edges! Total coverage: {len(global_coverage)} edges')
    
    print(f'covered {total_hits} edges')
    return new_edge_covered, total_hits

def save_new_seed(conf, seed_queue):
    """Save interesting inputs to queue"""
    seed_index = len(seed_queue)
    new_seed_filename = f"id_{seed_index:06d}"
    new_seed_path = os.path.join(conf['queue_folder'], new_seed_filename)
    shutil.copyfile(conf['current_input'], new_seed_path)
    return new_seed_path