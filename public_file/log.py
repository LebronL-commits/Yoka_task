import sys

def log_file_path(file_path, log_file='file_paths.log'):
    try:
        with open(log_file, 'a') as f:
            f.write(f"{file_path}\n")
    except Exception as e:
        print(f"Failed to write to log file: {e}", file=sys.stderr)
        sys.exit(1)

if __name__ == "__main__":
    # 获取所有传递的文件路径
    file_paths = sys.argv[1:]
    print(file_paths)
    if not file_paths:
        print("No files to process", file=sys.stderr)
        sys.exit(1)
    
    for file_path in file_paths:
        log_file_path(file_path)
    
    print(f"Successfully logged {len(file_paths)} files")