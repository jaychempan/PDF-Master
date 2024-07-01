import os

def remove_ocr_suffix(directory):
    for root, dirs, files in os.walk(directory):
        for file in files:
            if file.endswith(".md") and "_ocr" in file:
                new_name = file.replace("_ocr", "")
                old_path = os.path.join(root, file)
                new_path = os.path.join(root, new_name)
                os.rename(old_path, new_path)
                print(f'Renamed: {old_path} -> {new_path}')

# 使用示例
directory = "/mnt/petrelfs/panjiancheng/llm-pdf-parsing/data/output/bench_process/markdown"
remove_ocr_suffix(directory)