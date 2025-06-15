import subprocess
import time
import os
import sys
import webbrowser
import pandas as pd
import datetime
from path_utils import get_dataset_path, get_output_path, DATASET_KEYS, DIRECTORY_KEYS

def create_dashboard_qmd():
    # Get the safe path to the dataset for use in the dashboard content
    try:
        profile_overview_path = get_dataset_path(DATASET_KEYS['INSTAGRAM_PROFILE_OVERVIEW'])
        # Convert to relative path for the dashboard (assuming dashboard.qmd is in project root)
        relative_path = os.path.relpath(profile_overview_path)
    except Exception as e:
        print(f"Error getting dataset path: {e}")
        # Fallback to the centralized path system
        relative_path = "dataset/Instagram Profile Overview.csv"
    
    dashboard_content = f"""---
title: "Interactive Dashboard"
format:
  html:
    echo: false
    theme: lumen
    dashboard: true
jupyter:
  kernelspec:
    name: "quarto-env"
    language: "python"
    display_name: "Quarto-Python"
---

::: {{.sidebar}}
```{{python}}
#| widget: true
import pandas as pd
import seaborn as sns
import plotly.express as px
import ipywidgets as widgets
from IPython.display import display

# Load and parse date column using safe path
df = pd.read_csv("{relative_path}", parse_dates=["Date"])
dates = sorted(df["Date"].unique())

# Vertical range slider for date selection
date_slider = widgets.SelectionRangeSlider(
    options=[(d.strftime("%Y-%m-%d"), d) for d in dates],
    index=(0, len(dates)-1),
    description="Date Range:",
    orientation="vertical",
    layout=widgets.Layout(height="400px", width="200px")
)

# Convert seaborn muted palette to hex
colors = sns.color_palette("muted", 2).as_hex()

def update(date_range):
    start, end = date_range
    mask = (df["Date"] >= start) & (df["Date"] <= end)
    sel = df.loc[mask]

    figs = []
    for col in df.columns.drop("Date"):
        total = df[col].sum()
        selected = sel[col].sum()
        fig = px.bar(
            x=["Total", "Selected"],
            y=[total, selected],
            color=["Total", "Selected"],
            color_discrete_sequence=colors,
            title=col,
            labels={{"x": "", "y": col}}
        )
        figs.append(fig)
    # stack vertically
    return widgets.VBox(figs)

interactive = widgets.interactive(update, date_range=date_slider)
display(widgets.HBox([date_slider, interactive.children[1]]))
```
:::

<!-- Dark/Light Mode Toggle Slider -->
<style>
  /* Position the toggle slider at the top right corner */
  #mode-toggle-container {{
    position: fixed;
    top: 10px;
    right: 10px;
    z-index: 1000;
  }}
  .switch {{
    position: relative;
    display: inline-block;
    width: 60px;
    height: 34px;
  }}
  .switch input {{ 
    opacity: 0;
    width: 0;
    height: 0;
  }}
  .slider {{
    position: absolute;
    cursor: pointer;
    top: 0; left: 0; right: 0; bottom: 0;
    background-color: #ccc;
    transition: 0.4s;
  }}
  .slider:before {{
    position: absolute;
    content: "";
    height: 26px;
    width: 26px;
    left: 4px;
    bottom: 4px;
    background-color: white;
    transition: 0.4s;
  }}
  input:checked + .slider {{
    background-color: #2196F3;
  }}
  input:checked + .slider:before {{
    transform: translateX(26px);
  }}
  .slider.round {{
    border-radius: 34px;
  }}
  .slider.round:before {{
    border-radius: 50%;
  }}
  /* Dark mode styling */
  .dark-mode {{
    background-color: #121212;
    color: #ffffff;
  }}
  .dark-mode img {{
    filter: invert(1) hue-rotate(180deg);
  }}
</style>

<div id="mode-toggle-container">
  <label class="switch">
    <input type="checkbox" id="mode-toggle">
    <span class="slider round"></span>
  </label>
</div>

<script>
document.getElementById("mode-toggle").addEventListener("change", function() {{
  if (this.checked) {{
      document.body.classList.add("dark-mode");
  }} else {{
      document.body.classList.remove("dark-mode");
  }}
}});
</script>

"""
    
    # Save the dashboard file to project root using safe path management
    dashboard_path = get_output_path('..', "dashboard.qmd")  # Save to project root
    with open(dashboard_path, "w", encoding="utf-8") as f:
        f.write(dashboard_content)
    print(f"✓ Created dashboard.qmd at: {dashboard_path}")
    return dashboard_path

def validate_dashboard_file(dashboard_path):
    """Validate that the dashboard file was created properly"""
    if not os.path.exists(dashboard_path):
        raise FileNotFoundError(f"Dashboard file not found: {dashboard_path}")
    
    # Check file size (should not be empty)
    file_size = os.path.getsize(dashboard_path)
    if file_size < 100:  # Minimum reasonable size
        raise ValueError("Dashboard file appears to be corrupted or empty")
    
    print(f"✓ Dashboard file validated: {file_size} bytes")
    return True

def run_dashboard():
    try:
        # Create and validate the dashboard file first
        dashboard_path = create_dashboard_qmd()
        validate_dashboard_file(dashboard_path)
        
        # Change to the directory containing the dashboard file
        dashboard_dir = os.path.dirname(dashboard_path)
        original_dir = os.getcwd()
        
        try:
            os.chdir(dashboard_dir)
            
            # Use quarto preview to serve the dashboard locally
            cmd_parts = ["quarto", "preview", os.path.basename(dashboard_path)]
            
            # Validate command
            allowed_commands = ["quarto"]
            if cmd_parts[0] not in allowed_commands:
                raise ValueError("Command not allowed")
            
            print(f"Launching dashboard from: {dashboard_dir}")
            process = subprocess.Popen(cmd_parts, shell=False)
            print("✓ Dashboard server started. It should open in your browser shortly.")
            
            # Allow time for the server to start
            time.sleep(5)
            
        finally:
            # Always return to original directory
            os.chdir(original_dir)
            
    except Exception as e:
        print(f"Error launching dashboard: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)

if __name__ == "__main__":
    run_dashboard()