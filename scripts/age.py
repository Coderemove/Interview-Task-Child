import sys
import os
import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns

# Add scripts directory to path
script_dir = os.path.dirname(os.path.abspath(__file__))
if script_dir not in sys.path:
    sys.path.insert(0, script_dir)

# Now import path_utils
from path_utils import safe_read_csv, get_output_path, DATASET_KEYS, DIRECTORY_KEYS

# Read the CSV file using safe path management
df = safe_read_csv(DATASET_KEYS['INSTAGRAM_AGE_GENDER'])

# Convert the Profile followers column to numeric values
df['Profile followers'] = pd.to_numeric(df['Profile followers'], errors='coerce')

# Calculate total followers
total_followers = df['Profile followers'].sum()
print(f"Total number of followers: {total_followers}")

# Calculate followers per gender and output their contribution
genders = ['female', 'male', 'undefined']
for gender in genders:
    gender_followers = df[df['Gender'] == gender]['Profile followers'].sum()
    percentage = (gender_followers / total_followers) * 100 if total_followers > 0 else 0
    print(f"{gender.capitalize()} contributes {gender_followers} followers ({percentage:.1f}%).")

def make_autopct(values):
    def my_autopct(pct):
        if pct < 5:
            return ""
        return '{:.1f}%'.format(pct)
    return my_autopct

for gender in genders:
    # Filter rows for the current gender and group by age, summing the followers
    df_gender = df[df['Gender'] == gender]
    age_distribution = df_gender.groupby('Age')['Profile followers'].sum()
    
    # Generate a muted color palette using Seaborn
    colors = sns.color_palette("muted", len(age_distribution))
    
    # Create the pie chart figure
    fig, ax = plt.subplots(figsize=(6, 6))
    wedges, texts, autotexts = ax.pie(
        age_distribution,
        autopct=make_autopct(age_distribution),
        startangle=90,
        colors=colors
    )
    
    # Set the title
    ax.set_title(f"Age Distribution for {gender.capitalize()}")
    
    # Add a legend on the side for better readability
    ax.legend(wedges, age_distribution.index, title="Age Groups", loc="center left", bbox_to_anchor=(1, 0, 0.5, 1))
    
    # Save the figure using safe path management
    filename = f"graph4_{gender}.png"
    output_path = get_output_path(DIRECTORY_KEYS['GRAPHS'], filename)
    plt.savefig(output_path, bbox_inches="tight")
    print(f"✓ Saved chart: {output_path}")
    plt.close(fig)

print("✓ Age analysis completed successfully")


