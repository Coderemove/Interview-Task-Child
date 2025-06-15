import pandas as pd
import matplotlib.pyplot as plt

df = pd.read_csv('dataset/Instagram Post Engagement.csv')
df['Date'] = pd.to_datetime(df['Date'])
df['MonthYear'] = df['Date'].dt.to_period('M')
grouped = df.groupby(['MonthYear', 'Media product type']).size().unstack(fill_value=0)
grouped.plot(kind='bar', stacked=True, figsize=(12, 6))
plt.title('Type of Media Product by Month')
plt.xlabel('Date')
plt.ylabel('Count')
plt.tight_layout()
plt.savefig('graphs/graph3.png')

