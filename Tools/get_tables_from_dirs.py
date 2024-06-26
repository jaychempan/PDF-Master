import os
import shutil
import pandas as pd
import re

def read_pdf_names_from_csv(csv_file):
    df = pd.read_csv(csv_file)
    # 筛选出 Old File Name 为中文名称的行
    chinese_name_pattern = re.compile(r'[\u4e00-\u9fff]+')
    filtered_df = df[df['Old File Name'].apply(lambda x: bool(chinese_name_pattern.search(str(x))))]
    pdf_names = filtered_df['New File Name'].tolist()
    return pdf_names

def copy_images_to_destination(pdf_names, source_dir, destination_dir):
    if not os.path.exists(destination_dir):
        os.makedirs(destination_dir)
    
    for pdf_name in pdf_names:
        pdf_dir = os.path.join(source_dir, pdf_name.split('.pdf')[0])
        tables_dir = os.path.join(pdf_dir, 'tables')
        # print(tables_dir)
        if os.path.exists(tables_dir) and os.path.isdir(tables_dir):
            for root, _, files in os.walk(tables_dir):
                for file in files:
                    if file.lower().endswith(('.png', '.jpg', '.jpeg', '.bmp', '.gif', '.tiff')):
                        source_file_path = os.path.join(root, file)
                        destination_file_path = os.path.join(destination_dir, file)
                        shutil.copy2(source_file_path, destination_file_path)
                        print(f"Copied {source_file_path} to {destination_file_path}")

# 示例使用方法
csv_file = '/mnt/petrelfs/panjiancheng/llm-pdf-parsing/data/output/20240605_comac_pdfs_process/20240605_rename_comac_pdfs.csv'  # 包含PDF名称的CSV文件路径
source_dir = '/mnt/petrelfs/panjiancheng/llm-pdf-parsing/data/output/20240605_comac_pdfs_process/structure'  # 源目录路径
destination_dir = '/mnt/petrelfs/panjiancheng/llm-pdf-parsing/data/tables'  # 目标目录路径

pdf_names = read_pdf_names_from_csv(csv_file)
copy_images_to_destination(pdf_names, source_dir, destination_dir)