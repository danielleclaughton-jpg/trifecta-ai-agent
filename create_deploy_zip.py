import os
import zipfile

def zip_project(output_filename, source_dir):
    exclude_dirs = {'.git', '.venv', '__pycache__', '.vscode', 'tests', 'logs', 'node_modules'}
    exclude_files = {output_filename, 'zip_project.py', 'create_deploy_zip.py'}

    with zipfile.ZipFile(output_filename, 'w', zipfile.ZIP_DEFLATED) as zipf:
        for root, dirs, files in os.walk(source_dir):
            # Modify dirs in-place to skip excluded directories
            dirs[:] = [d for d in dirs if d not in exclude_dirs]
            
            for file in files:
                if file in exclude_files:
                    continue
                if file.endswith('.pyc') or file.endswith('.pyo'):
                    continue
                    
                file_path = os.path.join(root, file)
                archive_name = os.path.relpath(file_path, source_dir)
                print(f"Adding {archive_name}")
                zipf.write(file_path, archive_name)

if __name__ == "__main__":
    zip_project('deploy.zip', '.')
    print("Created deploy.zip")
