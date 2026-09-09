import os

files_to_update = [
    'frontend/src/components/layout/TopNav.tsx',
    'frontend/src/services/api.ts',
    'frontend/src/pages/ProjectsPage.tsx',
    'frontend/src/pages/MpsAnalyticsPage.tsx',
    'frontend/src/pages/AuditLogsPage.tsx',
    'frontend/src/pages/AlertsPage.tsx'
]

for file_path in files_to_update:
    full_path = os.path.join('c:\\SIH_PROJECT', file_path)
    with open(full_path, 'r', encoding='utf-8') as f:
        content = f.read()
    
    # In api.ts, change pagination: Pagination to meta: Pagination
    content = content.replace('pagination: Pagination', 'meta: Pagination')
    content = content.replace('res.pagination', 'res.meta')
    content = content.replace('.total_records', '.total')
    content = content.replace('total_records:', 'total:')
    
    # Note: limit might be tricky, it's used as limit: limit in some API calls,
    # but the frontend Pagination type now has page_size
    content = content.replace('pagination.limit', 'pagination.page_size')
    
    if file_path == 'frontend/src/services/api.ts':
        content = content.replace("const API_BASE = '/api'", "const API_BASE = '/api/v1'")

    with open(full_path, 'w', encoding='utf-8') as f:
        f.write(content)
    
    print(f"Updated {file_path}")
