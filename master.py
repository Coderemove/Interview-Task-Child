import sys
import os

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

import ctypes
import platform
import subprocess
import datetime
import tkinter as tk
from tkinter import messagebox
from contextlib import redirect_stdout, redirect_stderr
from tqdm import tqdm
import runpy
import threading
import psutil
import time
import io
import json

class TeeOutput:
    """Captures output to both console and log file"""
    def __init__(self, log_file, original_stream):
        self.log_file = log_file
        self.original_stream = original_stream
        
    def write(self, text):
        self.original_stream.write(text)
        self.original_stream.flush()
        self.log_file.write(text)
        self.log_file.flush()
        
    def flush(self):
        self.original_stream.flush()
        self.log_file.flush()

class ResourceMonitor:
    """Monitors CPU, RAM, and GPU usage during script execution"""
    def __init__(self):
        self.monitoring = False
        self.cpu_samples = []
        self.ram_samples = []
        self.gpu_samples = []
        self.monitor_thread = None
        
    def start_monitoring(self):
        self.monitoring = True
        self.cpu_samples = []
        self.ram_samples = []
        self.gpu_samples = []
        self.monitor_thread = threading.Thread(target=self._monitor_loop, daemon=True)
        self.monitor_thread.start()
        
    def stop_monitoring(self):
        self.monitoring = False
        if self.monitor_thread:
            self.monitor_thread.join(timeout=2)
            
    def _monitor_loop(self):
        while self.monitoring:
            try:
                # CPU usage
                cpu_percent = psutil.cpu_percent(interval=None)
                self.cpu_samples.append(cpu_percent)
                
                # RAM usage
                memory = psutil.virtual_memory()
                ram_percent = memory.percent
                ram_used_gb = memory.used / (1024**3)
                self.ram_samples.append((ram_percent, ram_used_gb))
                
                # GPU usage (requires nvidia-ml-py or similar)
                gpu_usage = self._get_gpu_usage()
                if gpu_usage is not None:
                    self.gpu_samples.append(gpu_usage)
                    
                time.sleep(1)  # Sample every second
            except Exception as e:
                print(f"Error in resource monitoring: {e}")
                
    def _get_gpu_usage(self):
        """Get GPU usage for all supported GPU vendors"""
        gpu_data = []
        
        # Try NVIDIA first
        nvidia_data = self._get_nvidia_gpu_usage()
        if nvidia_data:
            gpu_data.extend(nvidia_data)
            
        # Try AMD
        amd_data = self._get_amd_gpu_usage()
        if amd_data:
            gpu_data.extend(amd_data)
            
        # Try Intel
        intel_data = self._get_intel_gpu_usage()
        if intel_data:
            gpu_data.extend(intel_data)
            
        return gpu_data if gpu_data else None
        
    def _get_nvidia_gpu_usage(self):
        """Get NVIDIA GPU usage using nvidia-smi"""
        try:
            result = subprocess.run([
                'nvidia-smi', '--query-gpu=utilization.gpu,memory.used,memory.total',
                '--format=csv,noheader,nounits'
            ], capture_output=True, text=True, timeout=5)
            
            if result.returncode == 0:
                lines = result.stdout.strip().split('\n')
                gpu_data = []
                for i, line in enumerate(lines):
                    parts = line.split(', ')
                    if len(parts) >= 3:
                        util = float(parts[0])
                        mem_used = float(parts[1])
                        mem_total = float(parts[2])
                        mem_percent = (mem_used / mem_total) * 100
                        gpu_data.append((f"NVIDIA-{i}", util, mem_percent, mem_used))
                return gpu_data
        except (FileNotFoundError, subprocess.TimeoutExpired, ValueError, IndexError):
            pass
        return None
        
    def _get_amd_gpu_usage(self):
        """Get AMD GPU usage using rocm-smi or radeontop"""
        gpu_data = []
        
        # Try rocm-smi first (for newer AMD cards)
        try:
            result = subprocess.run([
                'rocm-smi', '--showuse', '--showmemuse'
            ], capture_output=True, text=True, timeout=5)
            
            if result.returncode == 0:
                lines = result.stdout.strip().split('\n')
                for i, line in enumerate(lines[1:]):  # Skip header
                    if 'GPU' in line:
                        parts = line.split()
                        if len(parts) >= 4:
                            util = float(parts[2].rstrip('%'))
                            mem_percent = float(parts[3].rstrip('%'))
                            gpu_data.append((f"AMD-{i}", util, mem_percent, 0))
                return gpu_data
        except (FileNotFoundError, subprocess.TimeoutExpired, ValueError, IndexError):
            pass
            
        # Fallback to WMI for basic AMD info
        try:
            result = subprocess.run([
                'wmic', 'path', 'Win32_VideoController', 'where', 
                'Name like "%AMD%" or Name like "%Radeon%"',
                'get', 'Name,AdapterRAM'
            ], capture_output=True, text=True, timeout=5)
            
            if result.returncode == 0 and 'AMD' in result.stdout or 'Radeon' in result.stdout:
                # Basic detection only - no usage stats available via WMI
                gpu_data.append(("AMD-0", 0, 0, 0))  # Placeholder values
                return gpu_data
        except (FileNotFoundError, subprocess.TimeoutExpired, ValueError):
            pass
            
        return None
        
    def _get_intel_gpu_usage(self):
        """Get Intel GPU usage using intel_gpu_top"""
        try:
            result = subprocess.run([
                'intel_gpu_top', '-J'  # JSON output
            ], capture_output=True, text=True, timeout=5)
            
            if result.returncode == 0:
                # Use the globally imported json module
                data = json.loads(result.stdout)
                if 'engines' in data:
                    util = data.get('engines', {}).get('Render/3D', {}).get('busy', 0)
                    return [("Intel-0", util, 0, 0)]  # Intel tools don't easily expose memory
        except (FileNotFoundError, subprocess.TimeoutExpired, ValueError, json.JSONDecodeError):
            pass
            
        # Fallback to WMI for basic Intel detection
        try:
            result = subprocess.run([
                'wmic', 'path', 'Win32_VideoController', 'where',
                'Name like "%Intel%"', 'get', 'Name,AdapterRAM'
            ], capture_output=True, text=True, timeout=5)
            
            if result.returncode == 0 and 'Intel' in result.stdout:
                return [("Intel-0", 0, 0, 0)]  # Placeholder values
        except (FileNotFoundError, subprocess.TimeoutExpired, ValueError):
            pass
            
        return None
    def get_averages(self):
        """Calculate average resource usage"""
        cpu_avg = sum(self.cpu_samples) / len(self.cpu_samples) if self.cpu_samples else 0
        
        if self.ram_samples:
            ram_percent_avg = sum(sample[0] for sample in self.ram_samples) / len(self.ram_samples)
            ram_used_avg = sum(sample[1] for sample in self.ram_samples) / len(self.ram_samples)
        else:
            ram_percent_avg = ram_used_avg = 0
            
        gpu_info = None
        if self.gpu_samples and any(self.gpu_samples):
            # Average across all GPUs and samples
            all_gpu_util = []
            all_gpu_mem_percent = []
            all_gpu_mem_used = []
            
            for sample in self.gpu_samples:
                if sample:
                    for gpu_data in sample:
                        if len(gpu_data) >= 4:
                            vendor, util, mem_percent, mem_used = gpu_data
                            all_gpu_util.append(util)
                            all_gpu_mem_percent.append(mem_percent)
                            all_gpu_mem_used.append(mem_used)
                        
            if all_gpu_util:
                gpu_info = {
                    'utilization_avg': sum(all_gpu_util) / len(all_gpu_util),
                    'memory_percent_avg': sum(all_gpu_mem_percent) / len(all_gpu_mem_percent),
                    'memory_used_avg': sum(all_gpu_mem_used) / len(all_gpu_mem_used)
                }
                
        return {
            'cpu_percent': cpu_avg,
            'ram_percent': ram_percent_avg,
            'ram_used_gb': ram_used_avg,
            'gpu': gpu_info
        }

#––– helper to run a single external command elevated via UAC –––
def run_as_admin(cmd, args):
    """Safely run command with UAC elevation"""
    # Validate command is in allowed list
    allowed_commands = ["taskkill"]
    if cmd not in allowed_commands:
        raise ValueError(f"Command {cmd} not allowed")
    
    # Use subprocess with list arguments (safer)
    try:
        subprocess.run([cmd] + args, check=True, shell=False)
    except subprocess.CalledProcessError as e:
        raise RuntimeError(f"Failed to execute: {cmd} {args}")

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

    # Check for plotly for dashboards
    try:
        import plotly
    except ImportError:
        root = tk.Tk(); root.withdraw()
        install = messagebox.askyesno(
            "Plotly Missing",
            "Dashboards require Plotly for visualization.\nWould you like to install it now?"
        )
        root.destroy()
        if install:
            subprocess.check_call([sys.executable, "-m", "pip", "install", "plotly"])
        else:
            print("Warning: Dashboard functionality will be limited without Plotly.")

    # Check for psutil for resource monitoring
    try:
        import psutil
    except ImportError:
        root = tk.Tk(); root.withdraw()
        install = messagebox.askyesno(
            "psutil Missing",
            "Resource monitoring requires psutil.\nWould you like to install it now?"
        )
        root.destroy()
        if install:
            subprocess.check_call([sys.executable, "-m", "pip", "install", "psutil"])
            import psutil
        else:
            print("Warning: Resource monitoring will be disabled without psutil.")

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

def validate_script_path(script_path, allowed_dir):
    """Validate script is in allowed directory and exists"""
    script_path = os.path.abspath(script_path)
    allowed_dir = os.path.abspath(allowed_dir)
    
    if not script_path.startswith(allowed_dir):
        raise ValueError("Script outside allowed directory")
    if not os.path.exists(script_path):
        raise FileNotFoundError(f"Script not found: {script_path}")
    return script_path

def safe_log_cleanup(log_dir):
    """Safely clean up log files"""
    log_dir = os.path.abspath(log_dir)
    log_files = []
    
    for f in os.listdir(log_dir):
        if f.startswith("log_") and f.endswith(".txt"):
            full_path = os.path.join(log_dir, f)
            # Ensure file is actually in log directory
            if os.path.abspath(full_path).startswith(log_dir):
                log_files.append(f)
    
    return sorted(log_files, key=lambda f: os.path.getmtime(os.path.join(log_dir, f)))

def safe_install_module(module_name):
    """Safely install Python module"""
    # Validate module name (alphanumeric, hyphens, underscores only)
    import re
    if not re.match(r'^[a-zA-Z0-9_-]+$', module_name):
        raise ValueError(f"Invalid module name: {module_name}")
    
    subprocess.check_call([
        sys.executable, "-m", "pip", "install", 
        "--user",  # Install to user directory only
        module_name
    ])

class PathManager:
    """Centralized and validated path management for the project"""
    
    def __init__(self, project_root):
        self.project_root = os.path.abspath(project_root)
        self._validate_project_structure()
        
        # Define allowed dataset files
        self.allowed_datasets = {
            'instagram_analytics_excel': 'Copy of Instagram_Analytics - DO NOT DELETE (for interview purposes).xlsx',
            'instagram_age_gender': 'Instagram Age Gender Demographi.csv',
            'instagram_post_engagement': 'Instagram Post Engagement.csv', 
            'instagram_profile_overview': 'Instagram Profile Overview.csv',
            'instagram_top_cities': 'Instagram Top Cities Regions.csv'
        }
        
        # Define project directories
        self.directories = {
            'dataset': os.path.join(self.project_root, 'dataset'),
            'scripts': os.path.join(self.project_root, 'scripts'),
            'graphs': os.path.join(self.project_root, 'graphs'),
            'log': os.path.join(self.project_root, 'log')
        }
        
    def _validate_project_structure(self):
        """Validate that we're in the correct project directory"""
        required_items = ['dataset', 'scripts']
        for item in required_items:
            item_path = os.path.join(self.project_root, item)
            if not os.path.exists(item_path):
                raise ValueError(f"Invalid project structure: missing {item} directory")
                
    def get_dataset_path(self, dataset_key):
        """Get validated path to a dataset file"""
        if dataset_key not in self.allowed_datasets:
            raise ValueError(f"Dataset key '{dataset_key}' not allowed. Valid keys: {list(self.allowed_datasets.keys())}")
            
        filename = self.allowed_datasets[dataset_key]
        filepath = os.path.join(self.directories['dataset'], filename)
        
        # Validate the file exists and is within dataset directory
        if not os.path.exists(filepath):
            raise FileNotFoundError(f"Dataset file not found: {filepath}")
            
        # Security check: ensure file is actually in dataset directory
        abs_filepath = os.path.abspath(filepath)
        abs_dataset_dir = os.path.abspath(self.directories['dataset'])
        if not abs_filepath.startswith(abs_dataset_dir):
            raise ValueError(f"Security violation: file outside dataset directory")
            
        return abs_filepath
        
    def get_output_path(self, directory_key, filename):
        """Get validated output path for graphs, logs, etc."""
        if directory_key not in self.directories:
            raise ValueError(f"Directory key '{directory_key}' not allowed")
            
        # Sanitize filename
        safe_filename = self._sanitize_filename(filename)
        output_dir = self.directories[directory_key]
        
        # Create directory if it doesn't exist
        os.makedirs(output_dir, exist_ok=True)
        
        output_path = os.path.join(output_dir, safe_filename)
        
        # Security check: ensure output is within intended directory
        abs_output_path = os.path.abspath(output_path)
        abs_output_dir = os.path.abspath(output_dir)
        if not abs_output_path.startswith(abs_output_dir):
            raise ValueError(f"Security violation: output path outside intended directory")
            
        return abs_output_path
        
    def _sanitize_filename(self, filename):
        """Sanitize filename to prevent path traversal and invalid characters"""
        import re
        # Remove/replace dangerous characters
        sanitized = re.sub(r'[<>:"/\\|?*]', '_', filename)
        # Remove path traversal attempts
        sanitized = sanitized.replace('..', '_').replace('~', '_')
        # Limit length
        sanitized = sanitized[:255]
        # Ensure it's not empty
        if not sanitized or sanitized in ['.', '..']:
            sanitized = 'unnamed_file'
        return sanitized
        
    def list_available_datasets(self):
        """List all available dataset keys and their descriptions"""
        return {
            key: {
                'filename': filename,
                'exists': os.path.exists(os.path.join(self.directories['dataset'], filename))
            }
            for key, filename in self.allowed_datasets.items()
        }
        
    def export_paths_config(self):
        """Export path configuration for use by other scripts"""
        config = {
            'project_root': self.project_root,
            'datasets': {key: self.get_dataset_path(key) for key in self.allowed_datasets if os.path.exists(os.path.join(self.directories['dataset'], self.allowed_datasets[key]))},
            'directories': self.directories
        }
        
        config_path = os.path.join(self.project_root, 'path_config.json')
        with open(config_path, 'w', encoding='utf-8') as f:
            json.dump(config, f, indent=2)
        return config_path

def load_path_config():
    """Load path configuration from JSON file (for use in other scripts)"""
    config_path = 'path_config.json'
    if not os.path.exists(config_path):
        raise FileNotFoundError("Path configuration not found. Please run master.py first.")
        
    with open(config_path, 'r', encoding='utf-8') as f:
        config = json.load(f)
    return config

def safe_read_csv(dataset_key, max_rows=100000):
    """Safely read CSV with size limits and validation"""
    config = load_path_config()
    
    if dataset_key not in config['datasets']:
        raise ValueError(f"Dataset key '{dataset_key}' not found in configuration")
        
    filepath = config['datasets'][dataset_key]
    
    if not os.path.exists(filepath):
        raise FileNotFoundError(f"Dataset file not found: {filepath}")
    
    # Check file size (limit to 50MB)
    file_size = os.path.getsize(filepath)
    if file_size > 50 * 1024 * 1024:
        raise ValueError("Dataset file too large (>50MB)")
    
    # Read with row limit
    import pandas as pd
    df = pd.read_csv(filepath, nrows=max_rows)
    
    # Sanitize data to prevent formula injection
    for col in df.select_dtypes(include=['object']).columns:
        df[col] = df[col].astype(str).apply(lambda x: x if not str(x).startswith(('=', '+', '-', '@')) else f"'{x}")
    
    return df

def safe_get_output_path(directory_key, filename):
    """Get safe output path for graphs, logs, etc."""
    config = load_path_config()
    
    if directory_key not in config['directories']:
        raise ValueError(f"Directory key '{directory_key}' not allowed")
        
    # Use the same sanitization logic
    path_manager = PathManager(config['project_root'])
    return path_manager.get_output_path(directory_key, filename)

def main():
    master_start = datetime.datetime.now()
    current_dir = os.path.dirname(os.path.abspath(__file__))
    scripts_dir = os.path.join(current_dir, 'scripts')
    
    # Add scripts directory to Python path so other scripts can import path_utils
    sys.path.insert(0, scripts_dir)
    
    # Ask for consent FIRST before any system information collection
    root = tk.Tk()
    root.withdraw()
    consent_input = messagebox.askyesno(
        "Debug Consent",
        "This script collects non-identifiable debugging information (OS, CPU, GPU, RAM, Python Version) for logging purposes.\nDo you consent?"
    )
    root.destroy()
    debug_consent = consent_input
    
    # Initialize path manager
    try:
        path_manager = PathManager(current_dir)
        print("✓ Project structure validated")
        
        # Export configuration for other scripts
        config_path = path_manager.export_paths_config()
        print(f"✓ Path configuration exported to: {config_path}")
        
        # Display available datasets
        datasets = path_manager.list_available_datasets()
        print("\n=== Available Datasets ===")
        for key, info in datasets.items():
            status = "✓" if info['exists'] else "✗"
            print(f"{status} {key}: {info['filename']}")
        print()
        
    except Exception as e:
        show_error(f"Project setup failed: {e}")
        sys.exit(1)
    
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
  
    log_files = safe_log_cleanup(log_dir)
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
    progress.update(1)
    
    # Initialize resource monitor
    resource_monitor = ResourceMonitor()
    
    with open(log_file_path, 'w', encoding='utf-8') as log_file:
        # Set up tee output to capture everything to both console and log
        original_stdout = sys.stdout
        original_stderr = sys.stderr
        
        tee_stdout = TeeOutput(log_file, original_stdout)
        tee_stderr = TeeOutput(log_file, original_stderr)
        
        sys.stdout = tee_stdout
        sys.stderr = tee_stderr
        
        try:
            if debug_consent:
                print("=== DEBUGGING INFORMATION ===")
                print(f"Operating System: {platform.system()} {platform.release()}")
                print(f"OS Version: {platform.version()}")
                print(f"Machine: {platform.machine()}")
                print(f"CPU: {get_cpu_name()}")
                print(f"GPU: {get_gpu_name()}")
                print(f"Total RAM: {get_total_ram()}")
                print(f"Python Version: {sys.version}")
                print(f"Log Started: {datetime.datetime.now()}")
                print("=" * 50)
                print()
            else:
                print("User did not consent to collect debugging information.")
                print(f"Log Started: {datetime.datetime.now()}")
                print("=" * 50)
                print()
            
            for ipy_file in ipy_files:
                script_name = os.path.basename(ipy_file)
                print(f"=== RUNNING {script_name} ===")
                start_time = datetime.datetime.now()
                
                # Start resource monitoring
                resource_monitor.start_monitoring()
                
                while True:
                    try:
                        validated_path = validate_script_path(ipy_file, scripts_dir)
                        runpy.run_path(validated_path, run_name="__main__")
                        break  
                    except ModuleNotFoundError as e:
                        missing_module = e.name if hasattr(e, "name") else str(e).split("'")[1]
                        
                        # Skip path_utils since it's a local module
                        if missing_module == 'path_utils':
                            print(f"ERROR: {script_name} cannot find path_utils.py")
                            print("Please ensure path_utils.py exists in the scripts directory")
                            break
                            
                        root = tk.Tk()
                        root.withdraw()
                        answer = messagebox.askyesno(
                            "Missing Module",
                            f"Module '{missing_module}' is missing when running {script_name}.\nWould you like to install it?"
                        )
                        root.destroy()
                        if answer:
                            try:
                                print(f"Installing module '{missing_module}'...")
                                safe_install_module(missing_module)
                                print(f"Module '{missing_module}' installed. Retrying {script_name}...")
                            except Exception as e2:
                                print(f"Error installing '{missing_module}': {e2}")
                                break  
                        else:
                            print("Skipping installation and continuing.")
                            break
                    except Exception as e:
                        print(f"ERROR in {script_name}: {e}")
                        import traceback
                        traceback.print_exc()
                        break
                
                # Stop resource monitoring and get averages
                resource_monitor.stop_monitoring()
                resource_usage = resource_monitor.get_averages()
                
                end_time = datetime.datetime.now()
                duration = (end_time - start_time).total_seconds()
                
                print(f"\n--- {script_name} COMPLETED ---")
                print(f"Duration: {duration:.2f} seconds")
                print(f"Average CPU Usage: {resource_usage['cpu_percent']:.1f}%")
                print(f"Average RAM Usage: {resource_usage['ram_percent']:.1f}% ({resource_usage['ram_used_gb']:.2f} GB)")
                
                if resource_usage['gpu']:
                    gpu_info = resource_usage['gpu']
                    print(f"Average GPU Usage: {gpu_info['utilization_avg']:.1f}%")
                    print(f"Average GPU Memory: {gpu_info['memory_percent_avg']:.1f}% ({gpu_info['memory_used_avg']:.0f} MB)")
                else:
                    print("GPU Usage: Not available")
                    
                print("=" * 50)
                print()
                progress.update(1)
            
            master_end = datetime.datetime.now()
            master_duration = (master_end - master_start).total_seconds()
            print(f"=== MASTER SCRIPT COMPLETED ===")
            print(f"Total execution time: {master_duration:.2f} seconds")
            print(f"Log ended: {master_end}")
            
        finally:
            # Restore original stdout/stderr
            sys.stdout = original_stdout
            sys.stderr = original_stderr
            
    progress.update(1)
    progress.close()
    
    print(f"All scripts executed. Full log saved to: {log_file_path}")

if __name__ == "__main__":
    main()