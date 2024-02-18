import yaml
import random
from datetime import datetime

# Define the path to your YAML file
yaml_file_path = 'data.yaml'

# Generate random values
data = {
    'TIMESTAMP_CSV': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
    'next_startup_time': datetime.now().timestamp() + random.randint(60, 3600),  # Random future timestamp
    'battery_voltage': round(random.uniform(3.0, 4.2), 2),  # Example voltage range
    'internal_voltage': round(random.uniform(1.0, 1.5), 2),
    'internal_current': round(random.uniform(0.0, 5.0), 2),
    'temperature': round(random.uniform(-20, 40), 1),  # Example temperature range
    'signal_quality': random.randint(0, 100),
    'latitude': round(random.uniform(-90, 90), 6),
    'longitude': round(random.uniform(-180, 180), 6),
    'height': round(random.uniform(0, 10000), 2)  # Example height in meters
}

# Load the existing data from the YAML file
try:
    with open(yaml_file_path, 'r') as yaml_file:
        existing_data = yaml.safe_load(yaml_file) or []
except FileNotFoundError:
    existing_data = []

# Append the new data
existing_data.append(data)

# Write the updated data back to the YAML file
with open(yaml_file_path, 'w') as yaml_file:
    yaml.safe_dump(existing_data, yaml_file, default_flow_style=False)

print("Data added to YAML file successfully.")
