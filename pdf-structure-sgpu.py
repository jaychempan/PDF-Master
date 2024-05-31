import subprocess
import time
import os
from multiprocessing import Pool, current_process
import shutil
import copy

# 定义参数字典
args = {
    '--det_model_dir': './inference/det/ch/ch_PP-OCRv4_det_infer', 
    '--rec_model_dir': './inference/rec/ch/ch_PP-OCRv4_rec_infer',
    '--rec_char_dict_path': './PaddleOCR/ppocr/utils/ppocr_keys_v1.txt',
    '--table_model_dir': './inference/table/ch_ppstructure_mobile_v2.0_SLANet_infer',
    '--table_char_dict_path': './PaddleOCR/ppocr/utils/dict/table_structure_dict_ch.txt',
    '--layout_model_dir': './inference/layout/picodet_lcnet_x1_0_fgd_layout_cdla_infer',
    '--layout_dict_path': './PaddleOCR/ppocr/utils/dict/layout_dict/layout_cdla_dict.txt',
    '--vis_font_path': './ppocr_img/fonts/simfang.ttf',
    '--recovery': 'True',
    '--output': './shangfei/all_out_newd/',
    '--use_pdf2docx_api': 'False',
    '--mode': 'structure',
    '--return_word_box': 'False',
    '--use_gpu': 'True'
}

# 获取所有PDF文件及其大小
def get_pdf_files_with_sizes(pdf_dir):
    pdf_files = []
    for f in os.listdir(pdf_dir):
        if f.lower().endswith('.pdf'):
            file_path = os.path.join(pdf_dir, f)
            size = os.path.getsize(file_path)
            pdf_files.append((f, size))
    return pdf_files

# 按大小排序并分片，使每个分片的总大小尽可能相近
def split_pdf_files_by_size(pdf_files, num_splits):
    pdf_files.sort(key=lambda x: x[1], reverse=True)  # 按大小降序排序
    splits = [[] for _ in range(num_splits)]
    split_sizes = [0] * num_splits

    for file, size in pdf_files:
        # 找到当前总大小最小的分片
        min_index = split_sizes.index(min(split_sizes))
        splits[min_index].append(file)
        split_sizes[min_index] += size

    return splits

# 创建并移动文件到子目录
def create_and_move_files(pdf_dir, splits):
    split_dirs = []
    for i, split_files in enumerate(splits):
        split_dir = os.path.join(pdf_dir, f'split_{i}')
        os.makedirs(split_dir, exist_ok=True)
        for file in split_files:
            shutil.move(os.path.join(pdf_dir, file), os.path.join(split_dir, file))
        split_dirs.append(split_dir)
    return split_dirs

# 更新参数字典中的image_dir参数
def update_args_with_split(args, split_dir):
    args_copy = copy.deepcopy(args)
    args_copy['--image_dir'] = split_dir
    return args_copy

# 执行预测系统
def run_predict_system(args_dict):
    command = ['python3', './PaddleOCR/ppstructure/predict_system.py']
    for key, value in args_dict.items():
        if not key.startswith('--'):
            raise ValueError(f"Invalid parameter '{key}' without '--' prefix")
        command.extend([key, str(value)])
    
    # 为子进程设置独立的环境变量
    env = os.environ.copy()
    env['PROCESS_NAME'] = current_process().name
    
    subprocess.run(command, check=True, env=env)

def process_split_dir(split_dir):
    updated_args = update_args_with_split(args, split_dir)
    run_predict_system(updated_args)

if __name__ == '__main__':
    import warnings
    warnings.filterwarnings('ignore')
    base_dir = './shangfei/pdfs_6'
    num_splits = 6  # N

    # 获取PDF文件及其大小
    pdf_files_with_sizes = get_pdf_files_with_sizes(base_dir)
    
    # 按大小排序并分片
    splits = split_pdf_files_by_size(pdf_files_with_sizes, num_splits)
    
    # 创建并移动文件到子目录
    split_dirs = create_and_move_files(base_dir, splits)
    
    start_time = time.time()

    with Pool(num_splits) as pool:
        pool.map(process_split_dir, split_dirs)

    # 输出运行时间，时-分-秒
    print(time.strftime("%H:%M:%S", time.gmtime(time.time() - start_time)))
