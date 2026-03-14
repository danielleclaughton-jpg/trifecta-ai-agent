import os
import zipfile
import shutil

source_dir = r"C:\Users\TrifectaAgent\trifecta-ai-agent"
output_zip = r"C:\Users\TrifectaAgent\trifecta-ai-agent\deploy_clean.zip"

# Directories and files to exclude
exclude_dirs = {'.git', '.venv', '__pycache__', '.pytest_cache', '.vscode', 'node_modules', 'logs', 'Microsoft', 'Tailored DBT Sessions', 'client_portal_mockup', 'dashboards'}
exclude_files = {'.env', '.env.local', '.env.example', 'deploy.zip', 'deploy_clean.zip', 'create_zip.ps1', 'trifecta-client-portal (5).zip', 'Interactive-1.ipynb', 'lead_pipeline.db', 'quick_test.py', 'test_chat.py', 'test_dashboard_load.html', 'test_local.ps1', 'test_skills.py', 'dashboard_dev.py', 'CLAUDE.md', 'START_HERE.md'}

def should_exclude(path):
    # Get the base name of the path
    basename = os.path.basename(path)
    # Check if any part of the path matches exclude patterns
    parts = path.replace('\\', '/').split('/')
    for part in parts:
        if part in exclude_dirs or part in exclude_files:
            return True
    return False

# Create the zip file
with zipfile.ZipFile(output_zip, 'w', zipfile.ZIP_DEFLATED) as zipf:
    for root, dirs, files in os.walk(source_dir):
        # Skip excluded directories at any level
        dirs[:] = [d for d in dirs if d not in exclude_dirs]
        
        for file in files:
            if file in exclude_files:
                continue
            
            file_path = os.path.join(root, file)
            rel_path = os.path.relpath(file_path, source_dir)
            
            # Use forward slashes for Linux compatibility
            arc_path = rel_path.replace('\\', '/')
            
            if not should_exclude(rel_path):
                zipf.write(file_path, arc_path)
                print(f"Added: {arc_path}")

print(f"\nCreated: {output_zip}")

# Show size
zip_size = os.path.getsize(output_zip)
print(f"Size: {zip_size:,} bytes ({zip_size/1024:.1f} KB)")
