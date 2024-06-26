import os
import cv2
import shutil
from paddleocr import PaddleOCR

# 初始化PaddleOCR，指定使用中文模型
ocr = PaddleOCR(use_angle_cls=True, lang='ch')

# 目标目录路径
source_dir = '/mnt/petrelfs/panjiancheng/llm-pdf-parsing/data/tables'
target_dir = '/mnt/petrelfs/panjiancheng/llm-pdf-parsing/data/tables_clean_by_ocr'

# 创建目标目录
if not os.path.exists(target_dir):
    os.makedirs(target_dir)

def contains_chinese(text):
    """判断文本中是否包含中文字符"""
    for char in text:
        if '\u4e00' <= char <= '\u9fff':
            return True
    return False

def process_images(source_dir, target_dir):
    for filename in os.listdir(source_dir):
        if filename.lower().endswith(('.png', '.jpg', '.jpeg', '.bmp', '.gif')):
            image_path = os.path.join(source_dir, filename)
            img = cv2.imread(image_path)
            if img is None:
                print(f"Error reading image {image_path}")
                continue

            # 识别图片中的文字
            result = ocr.ocr(img, cls=True)
            print(result[0])
            if result[0] is None or len(result[0]) == 0:
                print(f"No text found in image {image_path}")
                continue

            text = ''.join([line[1][0] for line in result[0]])

            if contains_chinese(text):
                shutil.copy(image_path, os.path.join(target_dir, filename))

# 处理图片
process_images(source_dir, target_dir)

print("处理完成。")