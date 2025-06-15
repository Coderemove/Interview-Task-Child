import pandas as pd
import matplotlib.pyplot as plt
from path_utils import safe_read_csv, get_output_path, DATASET_KEYS, DIRECTORY_KEYS

# Read the CSV file using safe path management
df = safe_read_csv(DATASET_KEYS['INSTAGRAM_POST_ENGAGEMENT'])

df['Date'] = pd.to_datetime(df['Date'])
df['MonthYear'] = df['Date'].dt.to_period('M')
grouped = df.groupby(['MonthYear', 'Media product type']).size().unstack(fill_value=0)
grouped.plot(kind='bar', stacked=True, figsize=(12, 6))
plt.title('Type of Media Product by Month')
plt.xlabel('Date')
plt.ylabel('Count')
plt.tight_layout()

# Save the figure using safe path management
output_path = get_output_path(DIRECTORY_KEYS['GRAPHS'], 'graph3.png')
plt.savefig(output_path)
print(f"✓ Saved chart: {output_path}")
plt.close()

print("✓ Feed vs Reel analysis completed successfully")

