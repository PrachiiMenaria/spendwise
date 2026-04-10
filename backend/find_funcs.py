import re

with open('app.py', 'r', encoding='utf-8') as f:
    for i, line in enumerate(f):
        if 'api_update_budget' in line or 'api_mood_analytics' in line:
            print(f"{i+1}: {line.strip()}")
