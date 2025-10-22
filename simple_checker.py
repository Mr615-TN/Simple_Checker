import argparse
import subprocess
import psutil
import time
import sys
import json
from statistics import mean
from dataclasses import dataclass, field, asdict

# --- 1. Data Structure using dataclass ---

@dataclass
class RunResults:
    """Stores the monitoring results and analysis."""
    exit_code: int = 0
    duration: float = 0.0
    peak_memory: float = 0.0  # In MB
    avg_cpu: float = 0.0      # In percent
    peak_cpu: float = 0.0     # In percent
    stdout: str = ""
    stderr: str = ""
    mode: str = "unknown"
    analysis_issues: list[str] = field(default_factory=list)


# --- 2. Monitoring Functions ---

def monitor_process(proc, result: RunResults, sample_interval=0.2, timeout=None):
    """Monitor an already running process for CPU/memory usage."""
    cpu_samples = []
    mem_samples = []
    
    start_time = time.time()
    result.mode = "monitor"
    
    while proc.is_running():
        try:
            with proc.oneshot():
                # Get CPU and memory usage
                cpu = proc.cpu_percent(interval=None)
                mem = proc.memory_info().rss / (1024 * 1024)
                
                cpu_samples.append(cpu)
                mem_samples.append(mem)
                
                result.peak_memory = max(result.peak_memory, mem)
                result.peak_cpu = max(result.peak_cpu, cpu)
                
        except psutil.NoSuchProcess:
            break

        # Check for timeout
        if timeout and (time.time() - start_time > timeout):
            print("⛔ Timeout reached. Killing process.")
            proc.terminate() # Gracefully terminate first
            time.sleep(1)
            if proc.is_running():
                 proc.kill() # Force kill if still running
            break
        
        time.sleep(sample_interval)

    # Communicate to ensure stdout/stderr are captured after process termination
    try:
        stdout, stderr = proc.communicate(timeout=2) # Small timeout in case communicate hangs
    except subprocess.TimeoutExpired:
         stdout, stderr = b"", b"Error: communicate timed out after kill/terminate."

    end_time = time.time()
    
    # Update results object
    result.exit_code = proc.returncode
    result.duration = end_time - start_time
    result.avg_cpu = mean(cpu_samples) if cpu_samples else 0
    result.stdout = stdout.decode(errors="ignore")
    result.stderr = stderr.decode(errors="ignore")
    
    return result


def run_smart(cmd, timeout=None):
    """Run process and automatically choose between light and monitored modes."""
    result = RunResults()
    
    try:
        proc = psutil.Popen(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    except FileNotFoundError:
        result.exit_code = 127 # Common exit code for command not found
        result.stderr = f"Error: Command not found or not executable: {' '.join(cmd)}"
        return result
        
    start = time.time()
    
    try:
        # Try a quick communication to see if the process finishes fast (light mode)
        stdout, stderr = proc.communicate(timeout=1)
        end = time.time()
        
        result.mode = "light"
        result.exit_code = proc.returncode
        result.duration = end - start
        
        # Safely get memory info if process still exists
        try:
            mem_info = proc.memory_info().rss / (1024 * 1024)
        except psutil.NoSuchProcess:
            mem_info = 0.0  # process ended too quickly to sample

        result.peak_memory = mem_info
        result.stdout = stdout.decode(errors="ignore")
        result.stderr = stderr.decode(errors="ignore")
        
        return result

    except subprocess.TimeoutExpired:
        # Still running — switch to monitoring mode
        print("ℹ️ Detected long-running program — switching to monitor mode.")
        return monitor_process(proc, result, timeout=timeout)


# --- 3. Analysis Function ---

def analyze_results(results: RunResults, max_mem: int, max_duration: int, min_cpu_for_long_run: int):
    """Analyzes the run results against configurable thresholds."""
    
    if results.exit_code != 0:
        results.analysis_issues.append("❗ Non-zero exit code: program crashed or returned error.")
        
    if results.peak_memory > max_mem:
        results.analysis_issues.append(f"⚠️ High memory usage ({results.peak_memory:.2f} MB > {max_mem} MB). Possible leak or inefficiency.")
        
    if results.duration > max_duration:
        results.analysis_issues.append(f"⚠️ Long runtime ({results.duration:.2f}s > {max_duration}s). Check for inefficient loops or I/O.")
        
    if results.mode == "monitor":
        # Check for I/O bound or deadlock issue
        if results.avg_cpu < min_cpu_for_long_run and results.duration > max_duration / 2:
            results.analysis_issues.append(f"⚠️ Low average CPU ({results.avg_cpu:.2f}%) with long runtime — possible blocking I/O or deadlock.")
    
    if not results.analysis_issues:
        results.analysis_issues.append("✅ No obvious issues detected.")
        
    return results


# --- 4. Presentation/CLI Functions ---

def print_summary(results: RunResults):
    """Prints the results in a human-readable, formatted way."""
    
    # --- Resource Summary ---
    print("\n" + "="*40)
    print("--- 🚀 Resource Summary ---")
    print("="*40)
    print(f"Mode: {'Monitor' if results.mode == 'monitor' else 'Light'}")
    print(f"Duration: {results.duration:.2f}s")
    print(f"Peak Memory: {results.peak_memory:.2f} MB")
    
    if results.mode == "monitor":
        print(f"Average CPU: {results.avg_cpu:.2f}%")
        print(f"Peak CPU: {results.peak_cpu:.2f}%")
        
    print(f"Exit Code: {results.exit_code}\n")
    
    # --- Analysis ---
    print("-" * 40)
    print("--- 🔬 Analysis ---")
    print("-" * 40)
    for issue in results.analysis_issues:
        print(issue)
        
    # --- STDERR Output ---
    if results.stderr:
        print("\n" + "*" * 40)
        print("--- ❌ STDERR Output (truncated to 500 chars) ---")
        print("*" * 40)
        print(results.stderr[:500])


def main():
    parser = argparse.ArgumentParser(
        description="Smart lightweight Valgrind-like analyzer for process resource consumption.",
        epilog="Example: python proc-analyzer.py ./my_program arg1 --max-memory 256"
    )
    
    parser.add_argument("command", nargs="+", help="Command to run (e.g. ./a.out or python script.py)")
    parser.add_argument("--timeout", type=int, default=None, help="Optional timeout in seconds. Kills the process if reached.")
    
    # Configurable Thresholds
    parser.add_argument("--max-memory", type=int, default=500, help="Memory usage threshold in MB for 'High Memory' warning.")
    parser.add_argument("--max-duration", type=int, default=10, help="Duration threshold in seconds for 'Long Runtime' warning.")
    parser.add_argument("--min-cpu-for-long-run", type=int, default=5, help="Minimum average CPU % for long-running processes to avoid I/O-bound warning.")
    
    # Output Control
    parser.add_argument("--json", action="store_true", help="Output results as a single JSON object for automation/CI.")
    
    args = parser.parse_args()

    results = run_smart(args.command, timeout=args.timeout)

    # Perform analysis using the configurable thresholds
    results = analyze_results(
        results, 
        max_mem=args.max_memory, 
        max_duration=args.max_duration, 
        min_cpu_for_long_run=args.min_cpu_for_long_run
    )

    if args.json:
        # Output as JSON
        print(json.dumps(asdict(results), indent=4))
    else:
        # Output human-readable summary
        print_summary(results)


if __name__ == "__main__":
    # Ensure proper handling of signals and keyboard interrupts
    try:
        main()
    except KeyboardInterrupt:
        print("\n\n👋 Process analysis aborted by user.")
        sys.exit(1)
