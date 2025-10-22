# 🧠 Simple_Checker — Smart Lightweight Process Analyzer

**Simple_Checker** is a **language-agnostic**, **Valgrind-like CLI tool** written in Python.  
It's designed to monitor and analyze **CPU, memory, and execution time** of any command-line program.  
Unlike traditional profilers, it's lightweight, fast, and "smart" — it automatically adapts its monitoring mode based on the process runtime.

---

## ✨ Features

- ⚡ **Smart Execution**  
  Starts in *light mode* for fast runs, automatically switches to *monitor mode* for longer processes (>1s).

- 📊 **Resource Tracking**  
  Tracks **duration**, **peak memory (MB)**, **average/peak CPU usage (%)**, and **exit code**.

- 🤖 **Automatic Analysis**  
  Detects and reports:
  - High memory usage  
  - Long runtimes  
  - Low CPU utilization (I/O-bound or possible deadlocks)  
  - Non-zero exit codes  

- 🧩 **Configurable Thresholds**  
  Customize thresholds for memory, runtime, and CPU sensitivity.

- 🧱 **Automation-Ready**  
  Supports JSON output for **CI pipelines**, build systems, and automated regression tests.

---

## ⚙️ Installation

### 1️⃣ Prerequisites

You'll need **Python 3.8+** and the `psutil` library:
```bash
pip install psutil
```

### 2️⃣ Clone and Run Locally
```bash
git clone https://github.com/Mr615-TN/Simple_Checker.git
cd Simple_Checker
python simple_checker.py --help
```

### 3️⃣ (Optional) Install as a Global CLI Tool

To make it accessible anywhere:
```bash
pip install .
```

Then run it globally:
```bash
simple_checker <your-command>
```

To enable this, make sure your setup.py or pyproject.toml defines:
```python
entry_points={
    "console_scripts": [
        "simple_checker = simple_checker:main",
    ],
}
```

---

## 🚀 Usage

Run any command through Simple_Checker:
```bash
python simple_checker.py <command> [args...]
```

### Example 1: Analyze a Python script
```bash
python simple_checker.py python my_fibo_script.py 100
```

### Example 2: Enforce a timeout (5 seconds)
```bash
python simple_checker.py ./my_program --timeout 5
```

### Example 3: Use strict thresholds
```bash
python simple_checker.py ./fast_tool --max-memory 64 --max-duration 3
```

---

## 🔧 Configuration

| Argument | Type | Default | Description |
|----------|------|---------|-------------|
| --max-memory | int | 500 | Memory threshold (MB) for high memory warning. |
| --max-duration | int | 10 | Duration threshold (seconds) for long runtime warning. |
| --min-cpu-for-long-run | int | 5 | Minimum average CPU % before triggering low-CPU warning. |
| --timeout | int | None | Kill process after given seconds. |
| --json | flag | False | Output results in JSON format (for CI automation). |

---

## 🧪 Example Output

### Human-readable console summary:
```
========================================
--- 🚀 Resource Summary ---
========================================
Mode: Light
Duration: 0.62s
Peak Memory: 4.56 MB
Exit Code: 0

----------------------------------------
--- 🔬 Analysis ---
----------------------------------------
✅ No obvious issues detected.
```

### JSON output:
```bash
python simple_checker.py ./test_suite --json > results.json
```
```json
{
    "exit_code": 0,
    "duration": 0.057,
    "peak_memory": 4.56,
    "avg_cpu": 0.0,
    "peak_cpu": 0.0,
    "stdout": "...",
    "stderr": "",
    "mode": "light",
    "analysis_issues": [
        "✅ No obvious issues detected."
    ]
}
```

---

## 🧩 Analysis Warnings

| Symbol | Description |
|--------|-------------|
| ❗ | Non-zero exit code (program crashed or errored). |
| ⚠️ | High memory usage (exceeds --max-memory). |
| ⚠️ | Long runtime (exceeds --max-duration). |
| ⚠️ | Low average CPU in long run (possible I/O wait or deadlock). |
| ✅ | No obvious issues detected. |

---

## 🛠️ Example Use Cases

- Detecting memory leaks or runaway resource usage in scripts.
- Verifying efficiency of Python, C/C++, Go, or Rust programs.
- Lightweight CI/CD performance checks.
- Identifying hung or I/O-bound processes during testing.

---

## 📦 Dependencies

- **psutil** — Cross-platform process and system monitoring library.

Install it with:
```bash
pip install psutil
```

---

## 🤝 Contributing

Pull requests are welcome!  
To contribute:

1. Fork the repo
2. Create a new branch (feature/my-improvement)
3. Commit your changes
4. Submit a PR with a short summary of your fix or enhancement

---

