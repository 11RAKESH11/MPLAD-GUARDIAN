import os
import glob

for f in glob.glob('c:\\SIH_PROJECT\\tests\\*.py'):
    with open(f, 'r', encoding='utf-8') as file:
        content = file.read()
    
    if '/api/' in content:
        # replace /api/ with /api/v1/ except for already updated ones if any
        content = content.replace('/api/', '/api/v1/')
        content = content.replace('/api/v1/v1/', '/api/v1/')
        
    content = content.replace('pagination', 'meta')
    content = content.replace('total_records', 'total')
    
    with open(f, 'w', encoding='utf-8') as file:
        file.write(content)
    
    print(f'Updated tests in {f}')
