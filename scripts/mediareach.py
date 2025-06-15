import pandas as pd
import matplotlib.pyplot as plt
from scipy.stats import f_oneway
from path_utils import safe_read_csv, get_output_path, DATASET_KEYS, DIRECTORY_KEYS

# Load your dataset using safe path management
df = safe_read_csv(DATASET_KEYS['INSTAGRAM_POST_ENGAGEMENT'])

# Ensure 'Media reach' column has no missing values
df = df.dropna(subset=['Media reach'])

# Monthly Analysis
df['Month'] = pd.to_datetime(df['Date']).dt.to_period('M')
monthly_avg = df.groupby('Month')['Media reach'].mean().reset_index()
monthly_avg['Month'] = monthly_avg['Month'].dt.to_timestamp()

# Weekly Analysis
df['Week'] = pd.to_datetime(df['Date']).dt.to_period('W')
weekly_avg = df.groupby('Week')['Media reach'].mean().reset_index()
weekly_avg['Week'] = weekly_avg['Week'].dt.start_time

# Save Monthly Graph
plt.figure(figsize=(10, 6))
plt.plot(monthly_avg['Month'], monthly_avg['Media reach'], marker='o', linestyle='-')
plt.title('Average Media Reach by Month')
plt.xlabel('Month')
plt.ylabel('Average Media Reach')
plt.grid(False)

# Save using safe path management
monthly_output_path = get_output_path(DIRECTORY_KEYS['GRAPHS'], 'graph2_monthly.png')
plt.savefig(monthly_output_path)
print(f"✓ Saved monthly chart: {monthly_output_path}")
plt.close()

# Save Weekly Graph
plt.figure(figsize=(10, 6))
plt.plot(weekly_avg['Week'], weekly_avg['Media reach'], marker='o', linestyle='-')
plt.title('Average Media Reach by Week')
plt.xlabel('Week')
plt.ylabel('Average Media Reach')
plt.grid(False)

# Save using safe path management
weekly_output_path = get_output_path(DIRECTORY_KEYS['GRAPHS'], 'graph2_weekly.png')
plt.savefig(weekly_output_path)
print(f"✓ Saved weekly chart: {weekly_output_path}")
plt.close()

# Compare Monthly and Weekly Results
# Align data for comparison
monthly_avg['Period'] = monthly_avg['Month'].dt.to_period('M')
weekly_avg['Period'] = weekly_avg['Week'].dt.to_period('M')

# Merge monthly and weekly averages on the same period
comparison_df = pd.merge(monthly_avg, weekly_avg, on='Period', suffixes=('_monthly', '_weekly'))

# Perform ANOVA test to check for significant differences
f_stat, p_value = f_oneway(comparison_df['Media reach_monthly'], comparison_df['Media reach_weekly'])

# Display results
if p_value < 0.05:
    print(f"Significant difference detected between monthly and weekly averages (F-statistic: {f_stat:.2f}, p-value: {p_value:.4f})")
else:
    print(f"No significant difference detected between monthly and weekly averages (F-statistic: {f_stat:.2f}, p-value: {p_value:.4f})")

print("✓ Media reach analysis completed successfully")






