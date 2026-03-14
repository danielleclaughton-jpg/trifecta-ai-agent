import zipfile
import os

# Create minimal deployment zip with just essential files
source_dir = r"C:\Users\TrifectaAgent\trifecta-ai-agent"
output_zip = r"C:\Users\TrifectaAgent\trifecta-ai-agent\deploy_minimal.zip"

# Essential files only
essential_files = [
    'app.py',
    'requirements.txt',
    'startup.txt',
    'web.config',
    'host.json',
    'runtime.txt',
]

# Essential directories (flattened)
essential_dirs = [
    'Assets/skills',
    'templates',
]

def add_file(zipf, file_path, arc_path):
    if os.path.exists(file_path):
        zipf.write(file_path, arc_path)
        print(f"Added: {arc_path}")

with zipfile.ZipFile(output_zip, 'w', zipfile.ZIP_DEFLATED) as zipf:
    # Add essential files
    for f in essential_files:
        fpath = os.path.join(source_dir, f)
        add_file(zipf, fpath, f)
    
    # Add essential directories
    for d in essential_dirs:
        dpath = os.path.join(source_dir, d)
        if os.path.exists(dpath):
            for root, dirs, files in os.walk(dpath):
                for file in files:
                    file_path = os.path.join(root, file)
                    rel_path = os.path.relpath(file_path, source_dir)
                    # Use forward slashes for Linux
                    arc_path = rel_path.replace('\\', '/')
                    add_file(zipf, file_path, arc_path)

print(f"\nCreated: {output_zip}")
print(f"Size: {os.path.getsize(output_zip):,} bytes")
