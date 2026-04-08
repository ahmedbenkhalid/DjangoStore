import re
import os

def check_file(file_path):
    with open(file_path, 'r', encoding='utf-8') as f:
        lines = f.readlines()

    for i, line in enumerate(lines):
        # Check if a line contains an unclosed {% or {{
        open_tag = re.search(r'{%[^{%]*$', line)
        if open_tag and '%}' not in line[open_tag.start():]:
            print(f"Split tag found in {file_path} on line {i+1}: {line.strip()}")
        
        open_var = re.search(r'{{[^{{]*$', line)
        if open_var and '}}' not in line[open_var.start():]:
            print(f"Split variable found in {file_path} on line {i+1}: {line.strip()}")

templates_dir = r'd:\Software\TestForKMAStore\templates'
for root, dirs, files in os.walk(templates_dir):
    for file in files:
        if file.endswith('.html'):
            check_file(os.path.join(root, file))

apps_dir = r'd:\Software\TestForKMAStore\apps'
for root, dirs, files in os.walk(apps_dir):
    for file in files:
        if file.endswith('.html'):
            check_file(os.path.join(root, file))
