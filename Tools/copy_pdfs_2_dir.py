"""
将原始预料目录下（包括子目录）的所有pdf拷贝到指定目录下，并统计各类文件数量
"""

import os
import shutil
from pathlib import Path
from concurrent.futures import ThreadPoolExecutor, as_completed

def copy_file(file_path, dst_dir, file_stats):
    file_size = os.path.getsize(file_path)
    ext = file_path.suffix.lower()
    
    if ext == '.pdf':
        file_stats['pdf']['count'] += 1
        file_stats['pdf']['size'] += file_size
    elif ext == '.doc':
        file_stats['doc']['count'] += 1
        file_stats['doc']['size'] += file_size
    elif ext == '.docx':
        file_stats['docx']['count'] += 1
        file_stats['docx']['size'] += file_size

    shutil.copy2(file_path, dst_dir)

def process_files(src_dir, dst_dir):
    Path(dst_dir).mkdir(parents=True, exist_ok=True)

    file_stats = {
        'pdf': {'count': 0, 'size': 0},
        'doc': {'count': 0, 'size': 0},
        'docx': {'count': 0, 'size': 0}
    }

    files_to_copy = []
    for root, dirs, files in os.walk(src_dir):
        for file in files:
            if file.lower().endswith(('.pdf', '.doc', '.docx')):
                files_to_copy.append(Path(root) / file)

    with ThreadPoolExecutor() as executor:
        future_to_file = {executor.submit(copy_file, file_path, dst_dir, file_stats): file_path for file_path in files_to_copy}

        for future in as_completed(future_to_file):
            try:
                future.result()
            except Exception as exc:
                print(f'文件 {future_to_file[future]} 处理时出错: {exc}')

    for file_type in file_stats:
        file_stats[file_type]['size'] = file_stats[file_type]['size'] / (1024 ** 3)

    return file_stats

# 使用示例
src_directory = '/mnt/petrelfs/shengkejun/project_data/COMAC_pretrain_data/语料库_excel/'
dst_directory = '/mnt/petrelfs/shengkejun/project_data/COMAC_pretrain_data/comac_pdfs/'
stats = process_files(src_directory, dst_directory)

print(f"PDF文件数: {stats['pdf']['count']}, 大小: {stats['pdf']['size']:.2f} GB")
print(f"DOC文件数: {stats['doc']['count']}, 大小: {stats['doc']['size']:.2f} GB")
print(f"DOCX文件数: {stats['docx']['count']}, 大小: {stats['docx']['size']:.2f} GB")