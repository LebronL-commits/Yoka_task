import sys

def log_file_path(file_path, log_file='file_paths.log'):
    with open(log_file, 'a') as f:
        f.write(f"{file_path}\n")

if __name__ == "__main__":
    # 获取所有传递的文件路径
    file_paths = sys.argv[1:]
    
    for file_path in file_paths:
        log_file_path(file_path)