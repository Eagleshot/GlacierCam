import yaml
import pandas as pd
import matplotlib.pyplot as plt

# Load data from the YAML file
yaml_file_path = 'data.yaml'

with open(yaml_file_path, 'r') as file:
    data = yaml.safe_load(file)

# Convert the data into a Pandas DataFrame
df = pd.DataFrame(data)

# Convert timestamp strings to datetime objects
df['TIMESTAMP_CSV'] = pd.to_datetime(df['TIMESTAMP_CSV'])

# Plotting examples
# Plotting temperature over time
plt.figure(figsize=(10, 6))
plt.plot(df['TIMESTAMP_CSV'], df['temperature'], marker='o', linestyle='-', color='b')
plt.title('Temperature over Time')
plt.xlabel('Timestamp')
plt.ylabel('Temperature (°C)')
plt.xticks(rotation=45)
plt.tight_layout()

# Display the plot
plt.show()

# Convert 'next_startup_time' to a readable format (optional)
df['next_startup_time'] = pd.to_datetime(df['next_startup_time'], unit='s')

print(df)
