import json
import shutil
import os

# 读取JSON文件
def read_json_file(file_path):
    with open(file_path, 'r', encoding='utf-8') as file:
        data = json.load(file)
    return data

# 检查chat_output是否包含表格内容
def contains_table(chat_output):
    return "" in chat_output

# 处理数据并复制文件
def process_data_and_copy_files(data, source_directory, destination_directory):
    for item in data:
        print(item)
        if item["is_rule"]:
            # 复制文件到指定目录
            src = os.path.join(source_directory, item["image_name"])
            dest = os.path.join(destination_directory, os.path.basename(item["image_name"]))
            if os.path.exists(src):
                shutil.copy(src, dest)

# 主函数
def main(json_file_path, source_directory, destination_directory):
    # 确保目标目录存在
    if not os.path.exists(destination_directory):
        os.makedirs(destination_directory)
    
    # 读取和处理JSON数据
    data = read_json_file(json_file_path)
    process_data_and_copy_files(data, source_directory, destination_directory)
    
    # 将修改后的数据写回JSON文件
    with open(json_file_path, 'w', encoding='utf-8') as file:
        json.dump(data, file, ensure_ascii=False, indent=4)

# 示例调用
json_file_path = '/mnt/petrelfs/panjiancheng/llm-pdf-parsing/data/tables_clean_by_internvl.json'  # JSON文件路径
source_directory = '/mnt/petrelfs/panjiancheng/llm-pdf-parsing/data/tables_clean_by_ocr_wo_catg'  # 源目录路径
destination_directory = '/mnt/petrelfs/panjiancheng/llm-pdf-parsing/data/tables_clean_by_internvl_is_table'  # 目标目录路径
main(json_file_path, source_directory, destination_directory)

