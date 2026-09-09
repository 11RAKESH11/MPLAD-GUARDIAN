import glob, os

for f in glob.glob('backend/app/routers/*.py'):
    with open(f, 'r', encoding='utf-8') as file:
        content = file.read()
    if 'prefix="/api/' in content:
        content = content.replace('prefix="/api/', 'prefix="/api/v1/')
        with open(f, 'w', encoding='utf-8') as file:
            file.write(content)
        print(f'Updated {f}')
