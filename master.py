import sys
import os
import ctypes
import platform
import subprocess
import datetime
import tkinter as tk
from tkinter import messagebox
from contextlib import redirect_stdout, redirect_stderr
from tqdm import tqdm
import runpy
import socket
import webbrowser
import signal
import threading  

#––– helper to run a single external command elevated via UAC –––
def run_as_admin(cmd, args):
    """
    Runs [cmd] with arguments [args] elevated. 
    Blocks until the command completes.
    """
    # build quoted parameter string
    params = " ".join(f'"{a}"' for a in args)
    # invoke UAC‐elevated ShellExecuteW
    ret = ctypes.windll.shell32.ShellExecuteW(
        None, 
        "runas", 
        cmd, 
        params, 
        None, 
        1
    )
    if ret <= 32:
        raise RuntimeError(f"Failed to elevate: {cmd} {params}")

#––– privileged operations –––
def check_quarto_processes():
    try:
        out = subprocess.check_output(
            ["tasklist","/FI","IMAGENAME eq quarto.exe"], 
            universal_newlines=True
        ).lower()
        if "quarto.exe" in out:
            if messagebox.askyesno(
                "Quarto Detected", 
                "Found running Quarto. Close all instances?"
            ):
                run_as_admin("taskkill", ["/F","/IM","quarto.exe"])
                print("→ Quarto processes terminated.")
            else:
                print("→ Leaving Quarto running.")
    except Exception as e:
        print("Error checking/killing Quarto:", e)

def find_free_port():
    s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    s.bind(("127.0.0.1", 0))
    port = s.getsockname()[1]
    s.close()
    return port

def add_firewall_rule(port):
    rule = f"QuartoPreview_{port}"
    args = [
        "advfirewall","firewall","add","rule",
        f"name={rule}",
        "dir=in","action=allow","protocol=TCP",
        f"localport={port}",
        "remoteip=127.0.0.1",
        "profile=Private"
    ]
    run_as_admin("netsh", args)
    return rule

def remove_firewall_rule(rule, port):
    args = [
        "advfirewall","firewall","delete","rule",
        f"name={rule}",
        "protocol=TCP",
        f"localport={port}"
    ]
    run_as_admin("netsh", args)

def run_dashboard():
    port = find_free_port()
    rule = add_firewall_rule(port)

    cmd = [
      "quarto", "preview", "dashboard.qmd",
      "--port", str(port),
      "--no-browser"
    ]
    proc = subprocess.Popen(cmd, shell=False)
    webbrowser.open(f"http://127.0.0.1:{port}")

    # Cleanup function to terminate Quarto and remove firewall rule
    def cleanup():
        if proc.poll() is None:
            proc.terminate()
        remove_firewall_rule(rule, port)

    # Handler for signals (Ctrl+C or termination)
    def on_exit(signum=None, frame=None):
        cleanup()
        sys.exit(0)

    signal.signal(signal.SIGINT, on_exit)
    signal.signal(signal.SIGTERM, on_exit)

    # Schedule automatic cleanup after 1 hour (3600 seconds)
    timer = threading.Timer(3600, on_exit)
    timer.daemon = True
    timer.start()

    # Wait for Quarto to exit; then cancel the timer and clean up
    proc.wait()
    timer.cancel()
    cleanup()

#––– your existing non‐privileged functions below –––

def show_error(msg):
    tk.Tk().withdraw()
    messagebox.showerror("Dependency Error", msg)

def check_dependencies():
    try:
        subprocess.run(["quarto","--version"], check=True, stdout=subprocess.DEVNULL)
    except FileNotFoundError:
        show_error("Please install Quarto and add to PATH.")
        sys.exit(1)

    try:
        subprocess.run(["R","--version"], check=True, stdout=subprocess.DEVNULL)
    except FileNotFoundError:
        show_error("Please install R and add to PATH.")
        sys.exit(1)

    # --- NEW: Ensure Jupyter & Python kernel support for dynamic dashboards ---
    try:
        # this will fail if jupyter-cli or jupyter-client isn't installed
        subprocess.run(["jupyter","--version"], check=True, stdout=subprocess.DEVNULL)
    except (FileNotFoundError, subprocess.CalledProcessError):
        root = tk.Tk(); root.withdraw()
        install = messagebox.askyesno(
            "Jupyter Missing",
            "Dynamic dashboards require Jupyter (notebook, ipykernel, jupyter-client).\n"
            "Would you like to install them now?"
        )
        root.destroy()
        if install:
            # install packages into the current Python environment
            subprocess.check_call([
                sys.executable, "-m", "pip", "install",
                "notebook", "ipykernel", "jupyter-client"
            ])
            # register a user‐level kernel named 'quarto-env'
            subprocess.check_call([
                sys.executable, "-m", "ipykernel", "install",
                "--user", "--name", "quarto-env", "--display-name", "Quarto-Python"
            ])
        else:
            show_error("Jupyter support is required for dynamic dashboards. Exiting.")
            sys.exit(1)

def get_cpu_name():
    try:
        output = subprocess.check_output(
            ["wmic", "cpu", "get", "Name"],
            stderr=subprocess.DEVNULL,
            universal_newlines=True
        )
        lines = output.strip().splitlines()
        if len(lines) >= 2:
            return lines[1].strip()
    except Exception:
        return platform.processor()
    return platform.processor()

def get_gpu_name():
    try:
        output = subprocess.check_output(
            "wmic path win32_VideoController get Name",
            shell=True,
            stderr=subprocess.DEVNULL,
            universal_newlines=True
        )
        lines = output.strip().splitlines()
        gpus = [line.strip() for line in lines[1:] if line.strip()]
        return ", ".join(gpus) if gpus else "N/A"
    except Exception:
        return "N/A"

def get_total_ram():
    try:
        output = subprocess.check_output(
            "wmic ComputerSystem get TotalPhysicalMemory",
            shell=True,
            stderr=subprocess.DEVNULL,
            universal_newlines=True
        )
        lines = output.strip().splitlines()
        if len(lines) >= 2:
            total_ram_bytes = int(lines[1].strip())
            total_ram_gb = total_ram_bytes / (1024**3)
            return f"{total_ram_gb:.2f} GB"
    except Exception:
        return "N/A"
    return "N/A"

def main():
    master_start = datetime.datetime.now()
    current_dir = os.path.dirname(os.path.abspath(__file__))
    scripts_dir = os.path.join(current_dir, 'scripts')
    check_dependencies()
    # GUI root for any further prompts:
    root = tk.Tk(); root.withdraw()

    check_quarto_processes()
    
    ipy_files = [
        os.path.join(scripts_dir, 'clean.py'),
        os.path.join(scripts_dir, 'averageengagement.py'),
        os.path.join(scripts_dir, 'mediareach.py'),
        os.path.join(scripts_dir, 'feedvsreel.py'),
        os.path.join(scripts_dir, 'age.py'),
        os.path.join(scripts_dir, 'reportgeneration.py'),
        os.path.join(scripts_dir, 'dashboardgeneration.py'),
        # Add more scripts in the desired order if needed.
    ]
    
    total_steps = 3 + len(ipy_files) + 1
    progress = tqdm(total=total_steps, desc="Master Script Progress", unit="step")
    
    log_dir = os.path.join(current_dir, 'log')
    os.makedirs(log_dir, exist_ok=True)
  
    log_files = sorted(
        [f for f in os.listdir(log_dir) if f.startswith("log_") and f.endswith(".txt")],
        key=lambda f: os.path.getmtime(os.path.join(log_dir, f))
    )
    if len(log_files) >= 10:
        root = tk.Tk()
        root.withdraw()
        consent_cleanup = messagebox.askyesno(
            "Log Cleanup",
            f"There are {len(log_files)} log files in {log_dir}.\nWould you like to delete the oldest log file ({log_files[0]})?"
        )
        root.destroy()
        if consent_cleanup:
            oldest_log = os.path.join(log_dir, log_files[0])
            try:
                os.remove(oldest_log)
                print(f"Deleted oldest log file: {log_files[0]}")
            except Exception as e:
                print(f"Error deleting log file: {e}")
        else:
            print("No log files were deleted.")
    progress.update(1)
    
    recommended_python = "Python 3.13.4"
    current_python = f"Python {sys.version_info.major}.{sys.version_info.minor}.{sys.version_info.micro}"
    if current_python != recommended_python:
        print(f"WARNING: The version running this script ({current_python}) does not match the recommended version ({recommended_python}).")
    progress.update(1)
    
    timestamp = datetime.datetime.now().strftime("%d%m%Y_%H%M%S")
    log_file_path = os.path.join(log_dir, f"log_{timestamp}.txt")
    root = tk.Tk()
    root.withdraw()
    consent_input = messagebox.askyesno(
        "Debug Consent",
        "This script collects non-identifiable debugging information (OS, CPU, GPU, RAM, Python Version) for logging purposes.\nDo you consent?"
    )
    root.destroy()
    debug_consent = consent_input
    progress.update(1)
    
    with open(log_file_path, 'w') as log_file:
        with redirect_stdout(log_file), redirect_stderr(log_file):
            if debug_consent:
                print("Debugging Information:")
                print(f"Operating System: {platform.system()} {platform.release()}")
                print(f"OS Version: {platform.version()}")
                print(f"Machine: {platform.machine()}")
                print(f"CPU: {get_cpu_name()}")
                print(f"GPU: {get_gpu_name()}")
                print(f"Total RAM: {get_total_ram()}")
                print(f"Python Version: {sys.version}")
                print("\n")
            else:
                print("User did not consent to collect debugging information.\n")
            
            for ipy_file in ipy_files:
                print(f"Running {ipy_file}...")
                start_time = datetime.datetime.now()
                while True:
                    try:
                        runpy.run_path(ipy_file, run_name="__main__")
                        break  
                    except ModuleNotFoundError as e:
                        missing_module = e.name if hasattr(e, "name") else str(e).split("'")[1]
                        root = tk.Tk()
                        root.withdraw()
                        answer = messagebox.askyesno(
                            "Missing Module",
                            f"Module '{missing_module}' is missing when running {ipy_file}.\nWould you like to install it?"
                        )
                        root.destroy()
                        if answer:
                            try:
                                subprocess.check_call([sys.executable, "-m", "pip", "install", missing_module])
                                print(f"Module '{missing_module}' installed. Retrying {ipy_file}...")
                            except Exception as e2:
                                print(f"Error installing '{missing_module}': {e2}")
                                break  
                        else:
                            print("Skipping installation and continuing.")
                            break  
                    except Exception as e:
                        print(f"Error running {ipy_file}: {e}")
                        break
                end_time = datetime.datetime.now()
                duration = (end_time - start_time).total_seconds()
                print(f"Finished {ipy_file} in {duration:.2f} seconds\n")
                progress.update(1)
            
            master_end = datetime.datetime.now()
            master_duration = (master_end - master_start).total_seconds()
            print(f"Master script executed in {master_duration:.2f} seconds")
    progress.update(1)
    progress.close()
    
    print(f"All scripts executed. Check log file: {log_file_path}")

if __name__ == "__main__":
    main()