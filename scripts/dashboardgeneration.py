import sys
import os
import subprocess
import time
import webbrowser
import pandas as pd
import datetime
import json
import requests
import hashlib # Add this for checksum calculation

# Add scripts directory to path
script_dir = os.path.dirname(os.path.abspath(__file__))
if script_dir not in sys.path:
    sys.path.insert(0, script_dir)

from path_utils import get_dataset_path, get_output_path, DATASET_KEYS, DIRECTORY_KEYS

# --- Security Configuration for Plotly Download ---
# Option: Pin to a specific version for better security and stability
PLOTLY_VERSION = "3.0.1" # Example: Check Plotly's website for the latest stable version
PLOTLY_JS_FILENAME = f"plotly-{PLOTLY_VERSION}.min.js"
PLOTLY_CDN_URL = f"https://cdn.plot.ly/{PLOTLY_JS_FILENAME}"
EXPECTED_PLOTLY_CHECKSUM = "A32E817BB121E9E89016CE4CEE85EE3F1C66F6A6C95C4B53A5F488F77756D7A4" 

def calculate_sha256(filepath):
    """Calculates the SHA256 checksum of a file."""
    sha256_hash = hashlib.sha256()
    with open(filepath, "rb") as f:
        # Read and update hash string value in blocks of 4K
        for byte_block in iter(lambda: f.read(4096), b""):
            sha256_hash.update(byte_block)
    return sha256_hash.hexdigest()

def download_plotly_js_secure(output_dir):
    """
    Downloads a specific version of plotly.min.js to the specified directory
    and verifies its checksum.
    """
    plotly_js_path = os.path.join(output_dir, PLOTLY_JS_FILENAME)

    if os.path.exists(plotly_js_path):
        print(f"Verifying checksum of existing local file: {plotly_js_path}...")
        local_checksum = calculate_sha256(plotly_js_path)
        if local_checksum.lower() == EXPECTED_PLOTLY_CHECKSUM.lower():
            print(f"✓ Checksum MATCHES. {PLOTLY_JS_FILENAME} is valid.")
            return PLOTLY_JS_FILENAME
        else:
            print(f"✗ Checksum MISMATCH for existing {PLOTLY_JS_FILENAME}.")
            print(f"  Expected: {EXPECTED_PLOTLY_CHECKSUM}")
            print(f"  Found:    {local_checksum}")
            print(f"  Attempting to re-download...")
            try:
                os.remove(plotly_js_path) # Remove corrupted/wrong version
            except OSError as e:
                print(f"✗ Error removing existing file {plotly_js_path}: {e}. Please remove it manually and retry.")
                raise # Re-raise to stop execution if we can't remove the bad file

    print(f"Downloading {PLOTLY_JS_FILENAME} (Version: {PLOTLY_VERSION}) to {output_dir}...")
    try:
        response = requests.get(PLOTLY_CDN_URL, timeout=30)
        response.raise_for_status()  # Raise an exception for HTTP errors

        # Temporarily save to verify checksum before final move (optional, but safer)
        temp_plotly_js_path = plotly_js_path + ".tmp"
        with open(temp_plotly_js_path, 'wb') as f:
            f.write(response.content)
        
        print("Verifying checksum of downloaded file...")
        downloaded_checksum = calculate_sha256(temp_plotly_js_path)

        if downloaded_checksum.lower() == EXPECTED_PLOTLY_CHECKSUM.lower():
            print(f"✓ Checksum MATCHES. {PLOTLY_JS_FILENAME} downloaded and verified successfully.")
            os.rename(temp_plotly_js_path, plotly_js_path) # Move verified file
            # Optional: Set read-only permissions (platform dependent)
            # try:
            #     os.chmod(plotly_js_path, 0o444) # Read-only for all
            # except OSError:
            #     print("Could not set read-only permissions (platform may not support or permission issue).")
            return PLOTLY_JS_FILENAME
        else:
            os.remove(temp_plotly_js_path) # Clean up temp file
            print(f"✗ CRITICAL: Checksum MISMATCH after download for {PLOTLY_JS_FILENAME}.")
            print(f"  Expected: {EXPECTED_PLOTLY_CHECKSUM}")
            print(f"  Found:    {downloaded_checksum}")
            print("  The downloaded file might be corrupted or tampered with. ABORTING.")
            print(f"  Please verify the version {PLOTLY_VERSION} and its checksum, or check your network security.")
            raise ValueError(f"Plotly.js checksum verification failed for version {PLOTLY_VERSION}.")

    except requests.exceptions.RequestException as e:
        print(f"✗ Failed to download {PLOTLY_JS_FILENAME}: {e}")
        raise # Re-raise to stop execution
    except Exception as e: # Catch other potential errors like file system issues
        print(f"✗ An unexpected error occurred during Plotly download/verification: {e}")
        if os.path.exists(temp_plotly_js_path):
            os.remove(temp_plotly_js_path) # Ensure temp file is cleaned up
        raise

def create_dashboard_qmd():
    # Get the safe path to the dataset for use in the dashboard content
    try:
        profile_overview_path = get_dataset_path(DATASET_KEYS['INSTAGRAM_PROFILE_OVERVIEW'])
        # Convert to relative path for the dashboard (assuming dashboard.qmd is in project root)
        relative_path = os.path.relpath(profile_overview_path).replace('\\', '/')
    except Exception as e:
        print(f"Error getting dataset path: {e}")
        # Fallback to the centralized path system
        relative_path = "dataset/Instagram Profile Overview.csv"
    
    # Load data and clean it
    df = pd.read_csv(relative_path, parse_dates=["Date"])
    
    # Fill NaN values with 0 for numeric columns
    numeric_columns = df.select_dtypes(include=['number']).columns
    df[numeric_columns] = df[numeric_columns].fillna(0)
    
    df['MonthYear'] = df['Date'].dt.to_period('M').astype(str)
    available_periods = sorted(df['MonthYear'].unique())
    
    # Prepare data for JavaScript
    df_for_js = df.copy()
    # Ensure 'Date' column is in ISO format string for robust new Date() parsing in JS
    if 'Date' in df_for_js.columns and pd.api.types.is_datetime64_any_dtype(df_for_js['Date']):
        df_for_js['Date'] = df_for_js['Date'].dt.strftime('%Y-%m-%d')
    
    js_data_for_script = df_for_js.to_dict('records')
    
    # Get available numeric columns for metric selection (exclude Date and MonthYear)
    available_metrics = [col for col in df.columns if pd.api.types.is_numeric_dtype(df[col]) and col not in ['Date']]
    
    # Debug output
    print(f"Data shape: {df.shape}")
    print(f"Available periods: {available_periods}")
    print(f"Available metrics: {available_metrics}")
    print(f"Sample data: {df.head(2).to_dict('records')}")
    
    # Determine where dashboard.qmd will be saved (project root)
    # This is also where plotly-latest.min.js should be.
    
    # CORRECT WAY to get the project root directory:
    # Assuming 'scripts' is a subdirectory of the project root.
    current_script_dir = os.path.dirname(os.path.abspath(__file__))
    project_root_dir = os.path.abspath(os.path.join(current_script_dir, '..'))
    
    # Ensure the project root directory exists (it should, but good practice)
    os.makedirs(project_root_dir, exist_ok=True)
    print(f"Project root for Plotly download: {project_root_dir}") # Debug print

    try:
        # Download Plotly.js securely to the project_root_dir
        local_plotly_js_file = download_plotly_js_secure(project_root_dir)
    except Exception as e:
        print(f"✗✗✗ FATAL ERROR: Could not obtain a secure copy of Plotly.js. Dashboard generation aborted. ✗✗✗")
        print(f"Error details: {e}")
        raise

    # Create dashboard content with proper structure
    js_data_str = json.dumps(js_data_for_script, default=str)
    js_periods_str = json.dumps(available_periods)
    js_metrics_str = json.dumps(available_metrics)

    script_data_injection = f"""
      <script>
        console.log("Starting data injection...");
        try {{
          window.rawData = {js_data_str};
          window.availablePeriods = {js_periods_str};
          window.availableMetrics = {js_metrics_str};
          
          console.log("Data injection successful");
          console.log("Raw data length:", window.rawData?.length);
          console.log("Available periods:", window.availablePeriods);
          console.log("Available metrics:", window.availableMetrics);
        }} catch(e) {{
          console.error("Data injection failed:", e);
        }}
      </script>
    """

    dashboard_content = f"""---
title: "Interactive Instagram Analytics Dashboard"
format:
  html:
    echo: false
    theme: lumen
    page-layout: full
    code-fold: true
    toc: false
---

```{{python}}
#| echo: false
#| output: false
import pandas as pd
import json
from IPython.display import HTML, display

# Load data for context
df_qmd_context = pd.read_csv(r"{relative_path}", parse_dates=["Date"])
df_qmd_context['MonthYear'] = df_qmd_context['Date'].dt.to_period('M').astype(str)

print("--- QMD Python Context ---")
print(f"Data loaded: {{len(df_qmd_context)}} records")
print(f"Date range: {{df_qmd_context['Date'].min()}} to {{df_qmd_context['Date'].max()}}")
print(f"Available columns: {{list(df_qmd_context.columns)}}")
numeric_cols_qmd = [col for col in df_qmd_context.columns if pd.api.types.is_numeric_dtype(df_qmd_context[col])]
print(f"Numeric columns: {{numeric_cols_qmd}}")
print("--------------------------")
```

```{{python}}
#| echo: false
#| output: asis
from IPython.display import HTML

# Dashboard HTML content
dashboard_html = '''
<div style="display: flex; min-height: 80vh;">
    <!-- Sidebar -->
    <div id="controls-container" style="width: 320px; min-width: 220px; background: var(--bg-secondary); padding: 24px 16px 24px 16px; border-radius: 12px; margin: 24px 24px 24px 0; box-shadow: 0 2px 8px rgba(0,0,0,0.06); border: 1px solid var(--border-color); display: flex; flex-direction: column; gap: 32px;">
        <div style="display: flex; align-items: center; gap: 12px;">
            <h3 style="margin: 0; color: var(--text-primary); font-size: 1.2em;">Dashboard Controls</h3>
            <button id="theme-toggle" onclick="toggleTheme()" style="background: var(--primary-color); color: white; border: none; padding: 8px 16px; border-radius: 4px; cursor: pointer; margin-left: auto;">
                🌙 Dark Mode
            </button>
        </div>
        <div>
            <h4 style="margin-top: 0; color: var(--text-secondary);">Time Period</h4>
            <div id="period-slicer">
                <div style="margin: 10px 0;">
                    <button onclick="selectAllPeriods()" style="background: var(--primary-color); color: white; border: none; padding: 8px 16px; border-radius: 4px; margin-right: 10px; cursor: pointer;">Select All</button>
                    <button onclick="clearAllPeriods()" style="background: var(--secondary-color); color: white; border: none; padding: 8px 16px; border-radius: 4px; cursor: pointer;">Clear All</button>
                </div>
                <div id="period-checkboxes" style="max-height: 200px; overflow-y: auto; border: 1px solid var(--border-color); padding: 10px; border-radius: 4px; background: var(--bg-primary);">
                    <!-- Checkboxes populated by JavaScript -->
                </div>
            </div>
        </div>
        <div>
            <h4 style="margin-top: 0; color: var(--text-secondary);">Select Metrics</h4>
            <div style="margin: 10px 0;">
                <button onclick="selectAllMetrics()" style="background: var(--success-color); color: white; border: none; padding: 6px 12px; border-radius: 4px; margin-right: 10px; cursor: pointer;">Select All</button>
                <button onclick="clearAllMetrics()" style="background: var(--secondary-color); color: white; border: none; padding: 6px 12px; border-radius: 4px; cursor: pointer;">Clear All</button>
            </div>
            <div id="metric-buttons" style="max-height: 200px; overflow-y: auto; padding: 10px;">
                <!-- Metric toggle buttons populated by JavaScript -->
            </div>
        </div>
        <div id="debug-info-container" style="background: var(--bg-primary); padding: 10px; margin: 10px 0; border-radius: 5px; border: 1px solid var(--border-color);">
            <div style="display: flex; justify-content: space-between; align-items: center; cursor: pointer;" onclick="toggleDebugInfo()">
                <strong style="color: var(--text-primary);">Debug Info</strong>
                <button id="debug-toggle-btn" style="background: none; border: none; font-size: 1.2em; color: var(--text-primary); cursor: pointer; padding: 0 5px;">▼</button>
            </div>
            <div id="debug-content" style="font-family: monospace; font-size: 12px; margin-top: 8px; display: none;">Loading...</div>
        </div>
    </div>
    <!-- Main content -->
    <div style="flex: 1; min-width: 0;">
        <div id="charts-container" style="padding: 24px 0 24px 0;">
            <div id="overview-charts-area" style="margin: 20px 0;"></div> <!-- Container for multiple overview charts -->
            <div id="comparison-chart" style="margin: 20px 0;"></div> <!-- REMOVED -->
            <div id="trends-chart" style="margin: 20px 0;"></div>
            <div id="summary-stats" style="margin: 20px 0; padding: 20px; background: var(--bg-secondary); border-radius: 8px; border: 1px solid var(--border-color);"></div>
        </div>
    </div>
</div>

<script src="{local_plotly_js_file}"></script> 
{script_data_injection}
<script src="dashboard_script.js"></script>

<style>
:root {{
  /* Light theme (default) */
  --bg-primary: #ffffff;
  --bg-secondary: #f8f9fa;
  --text-primary: #333333;
  --text-secondary: #555555;
  --border-color: #dddddd;
  --primary-color: #007bff;
  --secondary-color: #6c757d;
  --success-color: #28a745;
  --info-color: #17a2b8;
  --warning-color: #ffc107;
  --danger-color: #dc3545;
}}

[data-theme="dark"] {{
  /* Dark theme */
  --bg-primary: #2d3748;
  --bg-secondary: #1a202c;
  --text-primary: #f7fafc;
  --text-secondary: #e2e8f0;
  --border-color: #4a5568;
  --primary-color: #4299e1;
  --secondary-color: #718096;
  --success-color: #48bb78;
  --info-color: #38b2ac;
  --warning-color: #ed8936;
  --danger-color: #f56565;
}}

body {{ 
    font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif; 
    line-height: 1.6; 
    color: var(--text-primary);
    background-color: var(--bg-primary);
    transition: background-color 0.3s ease, color 0.3s ease;
}}

.dashboard-container {{ 
    max-width: 1400px; 
    margin: 0 auto; 
    padding: 20px; 
}}

button:hover {{ 
    opacity: 0.8; 
    transform: translateY(-1px); 
    transition: all 0.2s ease;
}}

input[type="checkbox"] {{ 
    margin-right: 8px; 
}}

label {{ 
    font-weight: normal; 
    cursor: pointer; 
    color: var(--text-primary);
}}

label:hover {{ 
    color: var(--primary-color); 
}}

#charts-container > div {{ 
    margin: 30px 0; 
    padding: 20px; 
    background: var(--bg-primary); 
    border-radius: 10px; 
    box-shadow: 0 2px 8px rgba(0,0,0,0.1); 
    border: 1px solid var(--border-color);
}}

#theme-toggle {{
    transition: all 0.3s ease;
}}

#theme-toggle:hover {{
    transform: scale(1.05);
}}

.metric-button {{
    display: inline-block;
    margin: 4px;
    padding: 8px 12px;
    border: 2px solid var(--border-color);
    border-radius: 20px;
    background: var(--bg-primary);
    color: var(--text-primary);
    cursor: pointer;
    transition: all 0.2s ease;
    font-size: 14px;
}}

.metric-button:hover {{
    border-color: var(--primary-color);
    transform: translateY(-1px);
}}

.metric-button.active {{
    background: var(--primary-color);
    color: white;
    border-color: var(--primary-color);
}}

.metric-button.active:hover {{
    background: var(--info-color);
    border-color: var(--info-color);
}}
</style>
'''

display(HTML(dashboard_html))
```
"""
    
    # Save the dashboard file to project root
    dashboard_path = os.path.join(project_root_dir, "dashboard.qmd") # Ensure dashboard.qmd is also saved here
    with open(dashboard_path, "w", encoding="utf-8") as f:
        f.write(dashboard_content)
    print(f"✓ Created dashboard.qmd at: {dashboard_path}")
    return dashboard_path

def validate_dashboard_file(dashboard_path):
    """Validate that the dashboard file was created properly"""
    if not os.path.exists(dashboard_path):
        raise FileNotFoundError(f"Dashboard file not found: {dashboard_path}")
    file_size = os.path.getsize(dashboard_path)
    if file_size < 100:
        raise ValueError("Dashboard file appears to be corrupted or empty")
    print(f"✓ Dashboard file validated: {file_size} bytes")
    return True

def run_dashboard():
    try:
        required_packages = ['plotly']
        missing_packages = []
        for package in required_packages:
            try:
                __import__(package)
            except ImportError:
                missing_packages.append(package)
        
        if missing_packages:
            print(f"Installing missing packages: {missing_packages}")
            subprocess.check_call([sys.executable, "-m", "pip", "install"] + missing_packages)
            print("✓ Required packages installed")
        
        dashboard_path = create_dashboard_qmd()
        validate_dashboard_file(dashboard_path)
        
        dashboard_dir = os.path.dirname(os.path.abspath(dashboard_path))
        original_dir = os.getcwd()
        
        try:
            os.chdir(dashboard_dir)
            print(f"Changed directory to: {dashboard_dir}")
            
            print("Rendering dashboard to HTML...")
            render_cmd = ["quarto", "render", os.path.basename(dashboard_path)] 
            render_result = subprocess.run(render_cmd, shell=False, capture_output=True, text=True, check=False)
            
            if render_result.returncode != 0:
                print(f"✗ Quarto render failed with return code: {render_result.returncode}")
                print(f"STDOUT: {render_result.stdout}")
                print(f"STDERR: {render_result.stderr}")
            else:
                print("✓ Dashboard rendered successfully")
            
            html_file_name = os.path.splitext(os.path.basename(dashboard_path))[0] + ".html"
            html_file_path = os.path.join(dashboard_dir, html_file_name)

            if os.path.exists(html_file_path):
                print(f"✓ Dashboard HTML created: {html_file_path}")
                file_url = f"file:///{html_file_path.replace(os.sep, '/')}"
                print(f"Opening dashboard in browser: {file_url}")
                webbrowser.open(file_url)
                print("✓ Dashboard opened in browser")
            else:
                print(f"✗ Dashboard HTML file not found after rendering: {html_file_path}")
                
        finally:
            os.chdir(original_dir)
            print(f"Returned to original directory: {original_dir}")
            
    except Exception as e:
        print(f"✗ Error launching dashboard: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)

if __name__ == "__main__":
    run_dashboard()