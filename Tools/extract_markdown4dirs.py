import os
import shutil

def extract_markdown_files(src_dir):
    # 定义目标目录路径
    parent_dir = os.path.dirname(src_dir)
    target_dir = os.path.join(parent_dir, "markdown")
    
    # 如果目标目录不存在，则创建
    if not os.path.exists(target_dir):
        os.makedirs(target_dir)
    
    # 遍历源目录下的所有一级子目录
    for subdir in os.listdir(src_dir):
        subdir_path = os.path.join(src_dir, subdir)
        if os.path.isdir(subdir_path):
            # 遍历子目录中的所有文件
            for file in os.listdir(subdir_path):
                if file.endswith(".md"):
                    file_path = os.path.join(subdir_path, file)
                    # 将Markdown文件复制到目标目录
                    shutil.copy(file_path, target_dir)
                    print(f"复制文件 {file} 到 {target_dir}")

# 示例用法
src_directory = "/mnt/petrelfs/panjiancheng/llm-pdf-parsing/data/output/bench_process/structure"
extract_markdown_files(src_directory)