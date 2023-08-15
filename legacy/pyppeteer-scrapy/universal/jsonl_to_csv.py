import json
import pandas as pd

data = []

with open('new_used_car_info.jsonl', 'r') as file:
    for line in file:
        data.append(json.loads(line))

df = pd.DataFrame(data)

df.to_csv('new_used_car_info.csv', index=False)
