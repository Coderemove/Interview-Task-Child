import sys
import os
import pandas as pd
import matplotlib.pyplot as plt
import rpy2.robjects as ro
from rpy2.robjects import pandas2ri
from rpy2.robjects.conversion import localconverter
from rpy2.robjects.vectors import FloatVector
from rpy2.robjects.packages import importr
import re

# Add scripts directory to path
script_dir = os.path.dirname(os.path.abspath(__file__))
if script_dir not in sys.path:
    sys.path.insert(0, script_dir)

# Now import path_utils
from path_utils import safe_read_csv, get_output_path, DATASET_KEYS, DIRECTORY_KEYS

os.environ["RPY2_CFFI_MODE"] = "ABI"
required_packages = ["ggplot2", "dplyr", "stats"]

def validate_r_package_name(pkg):
    """Validate R package names"""
    import re
    if not re.match(r'^[a-zA-Z][a-zA-Z0-9.]*$', pkg):
        raise ValueError(f"Invalid R package name: {pkg}")
    return pkg

# Validate packages before use
validated_packages = [validate_r_package_name(pkg) for pkg in required_packages]

ro.r(f'''
packages <- c({", ".join([f'"{pkg}"' for pkg in validated_packages])})
installed <- rownames(installed.packages())
for (pkg in packages) {{
  if (!pkg %in% installed) {{
    install.packages(pkg, repos="https://cloud.r-project.org")
  }}
}}
''')

r_libs = {pkg: importr(pkg) for pkg in validated_packages}

# Read the CSV file using safe path management
df = safe_read_csv(DATASET_KEYS['INSTAGRAM_POST_ENGAGEMENT'])

df = df[df['Media product type'].isin(['FEED', 'REELS'])]

df['Date'] = pd.to_datetime(df['Date'], errors='coerce')
df.dropna(subset=['Date'], inplace=True)

if 'post_engagement' not in df.columns:
    df['post_engagement'] = df['Like count'] + df['Comments count'] + df['Shares'] + df['Unique saves']

df['Week'] = df['Date'].dt.to_period('W').apply(lambda r: r.start_time)

weekly = df.groupby('Week')['post_engagement'].mean().reset_index()

weekly['Month'] = weekly['Week'].dt.to_period('M')

unique_months = sorted(weekly['Month'].unique())

results = []
for i in range(1, len(unique_months)):
    prev_month = unique_months[i - 1]
    curr_month = unique_months[i]
    
    prev_weekly_samples = weekly[weekly['Month'] == prev_month]['post_engagement']
    curr_weekly_samples = weekly[weekly['Month'] == curr_month]['post_engagement']
    
    change = curr_weekly_samples.mean() - prev_weekly_samples.mean()
    
    if len(prev_weekly_samples) < 2 or len(curr_weekly_samples) < 2:
        t_stat = None
        p_value = None
        significant = False
        print(f"Skipping t.test for month {curr_month} due to insufficient weekly observations.")
    else:
        with localconverter(ro.default_converter + pandas2ri.converter):
            r_prev = FloatVector(list(prev_weekly_samples))
            r_curr = FloatVector(list(curr_weekly_samples))
        t_test_result = ro.r['t.test'](r_curr, r_prev)
        p_value = t_test_result.rx2('p.value')[0]
        t_stat = t_test_result.rx2('statistic')[0]
        significant = p_value < 0.05
        
    results.append({
        'Month': str(curr_month),
        'Change': change,
        't_stat': t_stat,
        'p_value': p_value,
        'Significant': significant
    })

results_df = pd.DataFrame(results)
print(results_df)

plt.figure(figsize=(10,6))
plt.plot(weekly['Week'], weekly['post_engagement'], marker='o', label='Weekly Average Engagement', color='blue')

highlight_month = pd.Period('2024-11', freq='M')
highlight = weekly[weekly['Month'] == highlight_month]
if not highlight.empty:
    plt.plot(highlight['Week'], highlight['post_engagement'], marker='o', color='red',
             linewidth=3, label='Significant Drop (2024-11)')

plt.title('Changes in the Average Engagement on Instagram')
plt.ylabel('Average Post Engagement')
plt.xticks(rotation=45)
plt.legend()
plt.tight_layout()

# Save the figure using safe path management
output_path = get_output_path(DIRECTORY_KEYS['GRAPHS'], "graph1.png")
plt.savefig(output_path)
print(f"✓ Saved chart: {output_path}")
plt.close()

print("✓ Average engagement analysis completed successfully")










