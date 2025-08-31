import os
import signal
import threading
import time
from feedback import clear_shm

TIMEOUT = 1000
TIMEOUT_SEC = float(TIMEOUT/1000)

def monitor_timeout(grandchild_pid):
    """Thread function to monitor if the status byte is read within timeout"""
    time.sleep(TIMEOUT_SEC)
    try:
        os.kill(grandchild_pid, signal.SIGKILL)
        print(f"Timeout of {TIMEOUT} ms reached. Killed grandchild process {grandchild_pid}.")
    except OSError:
        pass

def run_target(ctl_write_fd, st_read_fd, trace_bits):
    """Execute target program with timeout handling"""
    clear_shm(trace_bits)

    os.write(ctl_write_fd, (0).to_bytes(4, byteorder='little'))
    start_time = time.time()

    grandchild_pid_bytes = os.read(st_read_fd, 4)
    grandchild_pid = int.from_bytes(grandchild_pid_bytes, byteorder='little', signed=False)
    
    timeout_thread = threading.Thread(target=monitor_timeout, args=(grandchild_pid,))
    timeout_thread.start()

    try:
        status_bytes = os.read(st_read_fd, 4)
        status_code = int.from_bytes(status_bytes, byteorder='little', signed=False)
        end_time = time.time()
        exec_time = end_time - start_time
        
        if timeout_thread.is_alive():
            timeout_thread.join(0.001)
            
        return status_code, exec_time
        
    except OSError:
        end_time = time.time()
        exec_time = end_time - start_time
        return 9, exec_time 