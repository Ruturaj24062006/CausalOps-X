import csv
from collections import Counter

csv_path = r'd:\Projects\CausalOps X\datasets\processed\model1_causalops_v1_features.csv'
with open(csv_path, 'r', encoding='utf-8') as f:
    reader = csv.DictReader(f)
    data = list(reader)

c = Counter([f"{r['namespace']}/{r['pod']}" for r in data])
for k, v in c.items():
    print(f'- {k}: {v}')
print(f'Total usable feature rows: {len(data)}')

print('--- DATA SUFFICIENCY --')
n = len(data)
train_end = int(n * 0.7)
val_end = int(n * 0.85)

train_rows = data[:train_end]
val_rows = data[train_end:val_end]
test_rows = data[val_end:]

print(f"Train rows: {len(train_rows)}")
print(f"Validation rows: {len(val_rows)}")
print(f"Test rows: {len(test_rows)}")

print(f"Train expected seq: 0")
print(f"Validation expected seq: 0")
print(f"Test expected seq: 0")
