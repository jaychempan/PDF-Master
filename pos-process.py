import os
import json
import argparse
import numpy as np
import cv2
import torch
from PIL import Image
from unimernet.common.config import Config
import unimernet.tasks as tasks
from unimernet.processors import load_processor

class ImageProcessor:
    def __init__(self, cfg_path):
        self.cfg_path = cfg_path
        self.device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
        self.model, self.vis_processor = self.load_model_and_processor()

    def load_model_and_processor(self):
        args = argparse.Namespace(cfg_path=self.cfg_path, options=None)
        cfg = Config(args)
        task = tasks.setup_task(cfg)
        model = task.build_model(cfg).to(self.device)
        vis_processor = load_processor('formula_image_eval', cfg.config.datasets.formula_rec_eval.vis_processor.eval)
        return model, vis_processor

    def process_single_image(self, image_path):
        try:
            raw_image = Image.open(image_path)
        except IOError:
            print(f"Error: Unable to open image at {image_path}")
            return ""
        
        image = self.vis_processor(raw_image).unsqueeze(0).to(self.device)
        output = self.model.generate({"image": image})
        pred = output["pred_str"][0]
        # print("*************")
        # print(pred)
        return pred

def process_span(span, processor, base_path):
    image_path = span.get("image_path", "")
    image_path_ = os.path.normpath(os.path.join(base_path, image_path))
    content = span.get("content", "")
    if image_path_:
        content = processor.process_single_image(image_path_)
    spa = {
        "bbox": span.get("bbox", []),
        "content": content,
        "image_path": image_path,
        "type": span.get("type", "")
    }
    print(spa)
    return spa

def process_interline_equation(equation, processor, base_path):
    # 处理 interline_equation
    processed_equation = {
        "type": equation.get("type", "interline_equation"),
        "bbox": equation.get("bbox", []),
        "lines": [
            {
                "bbox": line.get("bbox", []),
                "spans": [process_span(span, processor, base_path) for span in line.get("spans", [])]
            }
            for line in equation.get("lines", [])
        ]
    }
    return processed_equation

def process_page_info(page, processor, base_path):
    # 处理每个页面信息
    processed_page = {
        "preproc_blocks": page.get("preproc_blocks", []),
        "page_idx": page.get("page_idx", -1),
        "images": page.get("images", []),
        "tables": page.get("tables", []),
        "interline_equations": [process_interline_equation(equation, processor, base_path) for equation in page.get("interline_equations", [])],
        "discarded_blocks": page.get("discarded_blocks", []),
        "para_blocks": page.get("para_blocks", [])
    }
    return processed_page

def process_pdf_info(dir_path, file_path, processor):
    with open(file_path, 'r', encoding='utf-8') as f:
        data = json.load(f)
    processed_pdf_info = {
        "pdf_info": [process_page_info(page, processor, dir_path) for page in data.get("pdf_info", [])],
        "_parse_type": data.get("_parse_type", "ocr")
    }
     # 保存处理后的结果到原文件
    with open(file_path, 'w', encoding='utf-8') as f:
        json.dump(processed_pdf_info, f, ensure_ascii=False, indent=4)

def process_directory(root_dir, processor):
    results = []
    for root, dirs, files in os.walk(root_dir):
        for dir_ in dirs:
            dir_path = os.path.join(root, dir_)
            print(f"dir_path:{dir_path}")
            for _, _, files in os.walk(dir_path):
                print(files)
                for file in files:
                    if file.endswith('.json'):
                        file_path = os.path.join(dir_path, file)
                        processed_pdf_info = process_pdf_info(dir_path, file_path, processor)
                break
        break

# 主函数
def main(input_directory, config_path):
    import time
    processor = ImageProcessor(config_path)
    start_time = time.time()
    process_directory(input_directory, processor)
    # 输出运行时间，时-分-秒
    print(time.strftime("%H:%M:%S", time.gmtime(time.time() - start_time)))

if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser(
    description=(
        "将格式化的json文件转换成markdown文件"
    )
    )
    parser.add_argument(
    "--input_directory",
    type=str,
    required=True,
    help="指定目录下的所有子目录包含了json文件",
    )
    args = parser.parse_args()
    config_path = "./models/unimernet/demo.yaml"  # 替换为实际的配置文件
    main(args.input_directory, config_path)
