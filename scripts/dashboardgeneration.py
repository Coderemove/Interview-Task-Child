import subprocess
import time
import os
import sys
import webbrowser
import pandas as pd
import datetime  # needed for timestamping if required

def create_dashboard_qmd():
    dashboard_content = """---
title: "Interactive Dashboard"
format:
  html:
    echo: false
    theme: lumen
    dashboard: true
jupyter:
  python: "quarto-env"
---

::: {.sidebar}
```{python}
#| widget: true
import pandas as pd
import seaborn as sns
import plotly.express as px
import ipywidgets as widgets
from IPython.display import display

# Load and parse date column
df = pd.read_csv("dataset/Instagram Profile Overview.csv", parse_dates=["Date"])
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
            labels={"x": "", "y": col}
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
  #mode-toggle-container {
    position: fixed;
    top: 10px;
    right: 10px;
    z-index: 1000;
  }
  .switch {
    position: relative;
    display: inline-block;
    width: 60px;
    height: 34px;
  }
  .switch input { 
    opacity: 0;
    width: 0;
    height: 0;
  }
  .slider {
    position: absolute;
    cursor: pointer;
    top: 0; left: 0; right: 0; bottom: 0;
    background-color: #ccc;
    transition: 0.4s;
  }
  .slider:before {
    position: absolute;
    content: "";
    height: 26px;
    width: 26px;
    left: 4px;
    bottom: 4px;
    background-color: white;
    transition: 0.4s;
  }
  input:checked + .slider {
    background-color: #2196F3;
  }
  input:checked + .slider:before {
    transform: translateX(26px);
  }
  .slider.round {
    border-radius: 34px;
  }
  .slider.round:before {
    border-radius: 50%;
  }
  /* Dark mode styling */
  .dark-mode {
    background-color: #121212;
    color: #ffffff;
  }
  .dark-mode img {
    filter: invert(1) hue-rotate(180deg);
  }
</style>

<div id="mode-toggle-container">
  <label class="switch">
    <input type="checkbox" id="mode-toggle">
    <span class="slider round"></span>
  </label>
</div>

<script>
document.getElementById("mode-toggle").addEventListener("change", function() {
  if (this.checked) {
      document.body.classList.add("dark-mode");
  } else {
      document.body.classList.remove("dark-mode");
  }
});
</script>

```{python}
#| echo: false
import seaborn as sns
# Set Seaborn to use the muted color palette and whitegrid style
sns.set_theme(style="whitegrid", palette="muted")
```

# Dashboard Overview

This interactive dashboard was generated automatically using Quarto.

## Analysis Results

Add your interactive analysis components or visualizations here.
"""
    with open("dashboard.qmd", "w", encoding="utf-8") as f:
        f.write(dashboard_content)
    print("Created dashboard.qmd with the required dashboard content.")

def run_dashboard():
    try:
        # Use quarto preview to serve the dashboard locally.
        # Quarto will automatically open the dashboard in your default browser.
        process = subprocess.Popen(["quarto", "preview", "dashboard.qmd"], shell=True)
        print("Launching the dashboard. It should open in your browser shortly.")
        # Allow time for the server to start.
        time.sleep(5)
    except Exception as e:
        print(f"Error launching dashboard: {e}")
        sys.exit(1)

if __name__ == "__main__":
    create_dashboard_qmd()
    run_dashboard()