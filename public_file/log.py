import sys

def process_file(file_path):
    # 在这里处理文件路径
    print(f"Processing file: {file_path}")
    # 添加你的文件处理逻辑

if __name__ == "__main__":
    # 获取所有传递的文件路径
    file_paths = sys.argv[1:]
    
    for file_path in file_paths:
        process_file(file_path)