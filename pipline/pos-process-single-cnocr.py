import os
import json
import argparse
import torch
from PIL import Image
from unimernet.common.config import Config
import unimernet.tasks as tasks
from unimernet.processors import load_processor
from transformers import TrOCRProcessor
from optimum.onnxruntime import ORTModelForVision2Seq


class ImageProcessor:
    def __init__(self, cfg_path):
        self.cfg_path = cfg_path
        self.device = torch.device("cuda")
        # self.device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
        # self.model, self.vis_processor = self.load_model_and_processor()

        self.cnocr_processor = TrOCRProcessor.from_pretrained('./weights/pix2text-mfr')
        self.cnocr_model = ORTModelForVision2Seq.from_pretrained('./weights/pix2text-mfr', use_cache=False)


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
        
        # image = self.vis_processor(raw_image).unsqueeze(0).to(self.device)
        # output = self.model.generate({"image": image})
        # pred = output["pred_str"][0]
        # # print("*************")
        # print(pred)

        pixel_values =  self.cnocr_processor(images=raw_image, return_tensors="pt").pixel_values
        generated_ids =   self.cnocr_model .generate(pixel_values)
        generated_text =  self.cnocr_processor.batch_decode(generated_ids, skip_special_tokens=True)
        # print(f'generated_ids: {generated_ids}, \ngenerated text: {generated_text}')
        pred_ocr = generated_text[0]

        # pred_str = output["pred_str"]

        return pred_ocr

def process_span(span, processor, base_path):
    image_path = span.get("image_path", "")
    image_path_ = os.path.normpath(os.path.join(base_path, image_path))
    content = span.get("content", "")
    # print(image_path_)
    if os.path.isfile(image_path_):
        print(f"正在将图像转换为latex公式:{image_path_}")
        content = processor.process_single_image(image_path_)
    else:
        content = ""
        print(f"文件不存在: {image_path_}")
    return {
        "bbox": span.get("bbox", []),
        "content": content,
        "image_path": image_path,
        "type": span.get("type", "")
    }

def process_interline_equation(equation, processor, base_path):
    return {
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

def process_page_info(page, processor, base_path):
    return {
        "preproc_blocks": page.get("preproc_blocks", []),
        "page_idx": page.get("page_idx", -1),
        "images": page.get("images", []),
        "tables": page.get("tables", []),
        "interline_equations": [process_interline_equation(equation, processor, base_path) for equation in page.get("interline_equations", [])],
        "discarded_blocks": page.get("discarded_blocks", []),
        "para_blocks": page.get("para_blocks", [])
    }

def process_pdf_info(dir_path, file_path, processor):
    with open(file_path, 'r', encoding='utf-8') as f:
        data = json.load(f)
    processed_pdf_info = {
        "pdf_info": [process_page_info(page, processor, dir_path) for page in data.get("pdf_info", [])],
        "_parse_type": data.get("_parse_type", "ocr")
    }
    with open(file_path, 'w', encoding='utf-8') as f:
        json.dump(processed_pdf_info, f, ensure_ascii=False, indent=4)

def process_directory(input_directory, processor):
    for root, _, files in os.walk(input_directory):
        for file in files:
            if file.endswith('_ocr.json'):
                file_path = os.path.join(root, file)
                print(f"正在处理：{file_path}")
                process_pdf_info(input_directory, file_path, processor)
        break  # Ensure it only processes the input_directory itself

def main(input_directory, config_path):
    # import time
    processor = ImageProcessor(config_path)
    # start_time = time.time()
    process_directory(input_directory, processor)
    # print(time.strftime("%H:%M:%S", time.gmtime(time.time() - start_time)))

if __name__ == "__main__":
    # import warnings
    # warnings.filterwarnings('ignore')
    parser = argparse.ArgumentParser(
        description="Process JSON files in the specified directory"
    )
    parser.add_argument(
        "--input_directory",
        type=str,
        required=True,
        help="Directory containing JSON files"
    )
    parser.add_argument(
        "--config_path",
        type=str,
        required=True,
        help="Path to the configuration file"
    )
    args = parser.parse_args()
    main(args.input_directory, args.config_path)

