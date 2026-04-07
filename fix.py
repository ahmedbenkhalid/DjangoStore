import os
import glob

files_to_check = glob.glob('apps/**/*.py', recursive=True) + ['shop/settings.py', 'core/urls.py', 'apps/core/urls.py']
for filepath in files_to_check:
    if not os.path.exists(filepath): continue
    with open(filepath, 'r', encoding='utf-8') as f:
        content = f.read()
    new_content = content.replace('from apps.', 'from ').replace('import apps.', 'import ')
    if new_content != content:
        with open(filepath, 'w', encoding='utf-8') as f:
            f.write(new_content)
        print(f'Fixed {filepath}')
