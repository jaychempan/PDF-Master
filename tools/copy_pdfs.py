"""
测试代码，少量pdf拷贝N次生成批量PDF

"""


import os
import shutil
from tqdm import tqdm

def copy_pdfs(src_directory, dest_directory, n):
    if not os.path.exists(dest_directory):
        os.makedirs(dest_directory)
    
    pdf_files = [os.path.join(src_directory, f) for f in os.listdir(src_directory) if f.lower().endswith('.pdf')]
    
    for pdf_file in tqdm(pdf_files, desc="Copying PDFs"):
        base_name = os.path.basename(pdf_file)
        name, ext = os.path.splitext(base_name)
        
        for i in range(n):
            new_name = f"{name}_copy_{i+1}{ext}"
            dest_path = os.path.join(dest_directory, new_name)
            shutil.copy(pdf_file, dest_path)

# 指定源目录
src_directory = "/mnt/petrelfs/panjiancheng/llm-pdf-parsing/shangfei"
# 指定目标目录
dest_directory = "/mnt/petrelfs/panjiancheng/llm-pdf-parsing/shangfei/pdfs_x8_n6"
# 指定复制次数
n = 8

# 复制指定目录下的所有 PDF 文件 N 次到目标目录
copy_pdfs(src_directory, dest_directory, n)