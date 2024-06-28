import json
import os
import re
import shutil

def process_json_and_copy_images(input_json, source_dir, target_dir_include, target_dir_exclude):
    # 创建目标目录，如果不存在则创建
    if not os.path.exists(target_dir_include):
        os.makedirs(target_dir_include)
    if not os.path.exists(target_dir_exclude):
        os.makedirs(target_dir_exclude)

    # 读取JSON文件
    with open(input_json, 'r', encoding='utf-8') as infile:
        data = json.load(infile)

    # 正则表达式匹配“第XX章”、“第XX节”、“XX章”和“XX节”
    chapter_pattern = re.compile(r'(第[\d一二三四五六七八九十百千]+章|[\d一二三四五六七八九十百千]+章)')
    section_pattern = re.compile(r'(第[\d一二三四五六七八九十百千]+节|[\d一二三四五六七八九十]+节)')

    # 遍历JSON数据
    for item in data:
        text = item.get('text', '')
        image_name = item.get('image_name', '')

        # 选择目标目录
        if chapter_pattern.search(text) or section_pattern.search(text):
            target_path = os.path.join(target_dir_include, image_name)
        else:
            target_path = os.path.join(target_dir_exclude, image_name)

        source_path = os.path.join(source_dir, image_name)

        # 如果源文件存在，则进行复制
        if os.path.exists(source_path):
            shutil.copy(source_path, target_path)
            print(f"Copied {image_name} to {target_path}")
        else:
            print(f"Source file {source_path} does not exist.")

# 使用示例
input_json = '/mnt/petrelfs/panjiancheng/llm-pdf-parsing/data/tables_clean_by_ocr_1.json'
source_dir = '/mnt/petrelfs/panjiancheng/llm-pdf-parsing/data/tables_clean_by_ocr_1'
target_dir_include = '/mnt/petrelfs/panjiancheng/llm-pdf-parsing/data/tables_clean_by_ocr_with_catg'
target_dir_exclude = '/mnt/petrelfs/panjiancheng/llm-pdf-parsing/data/tables_clean_by_ocr_wo_catg'

process_json_and_copy_images(input_json, source_dir, target_dir_include, target_dir_exclude)
