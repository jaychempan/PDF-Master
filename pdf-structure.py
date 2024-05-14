import subprocess
import time

# 定义参数字典
args = {
    '--image_dir': '/home/panjiancheng/llm-pdf-parsing/shangfei/shangfei_pdf_single',
    '--det_model_dir': './inference/det/ch/ch_PP-OCRv4_det_infer', 
    '--rec_model_dir': './inference/rec/ch/ch_PP-OCRv4_rec_infer',
    '--rec_char_dict_path': './PaddleOCR/ppocr/utils/ppocr_keys_v1.txt',
    '--table_model_dir': './inference/table/ch_ppstructure_mobile_v2.0_SLANet_infer',
    '--table_char_dict_path': './PaddleOCR/ppocr/utils/dict/table_structure_dict_ch.txt',
    '--layout_model_dir': './inference/layout/picodet_lcnet_x1_0_fgd_layout_cdla_infer',
    '--layout_dict_path': './PaddleOCR/ppocr/utils/dict/layout_dict/layout_cdla_dict.txt',
    '--vis_font_path': './ppocr_img/fonts/simfang.ttf',
    '--recovery': 'True',
    '--output': '/home/panjiancheng/llm-pdf-parsing/shangfei/shangfei_pdf_output_test',
    '--use_pdf2docx_api': 'False',
    '--mode': 'structure',
    '--return_word_box': 'False',
    '--use_gpu': 'False'
}

def run_predict_system(args_dict):
    # 将参数字典中的键值对转换为命令行参数列表
    command = ['python3', './PaddleOCR/ppstructure/predict_system.py']
    for key, value in args_dict.items():
        if not key.startswith('--'):
            raise ValueError(f"Invalid parameter '{key}' without '--' prefix")
        command.extend([key, str(value)])

    # 执行命令
    subprocess.run(command, check=True)

start_time = time.time()

# 调用函数并传入参数字典
run_predict_system(args)

# 输出运行时间，时-分-秒
print(time.strftime("%H:%M:%S", time.gmtime(time.time() - start_time)))
