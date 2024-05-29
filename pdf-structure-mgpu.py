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
    '--output': './shangfei/more_out_6_new/',
    '--use_pdf2docx_api': 'False',
    '--mode': 'structure',
    '--return_word_box': 'False',
    '--use_gpu': 'True',
    '--show_log': 'False'
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
def run_predict_system(args_dict, gpu_id):
    command = ['python3', './PaddleOCR/ppstructure/predict_system.py']
    for key, value in args_dict.items():
        if not key.startswith('--'):
            raise ValueError(f"Invalid parameter '{key}' without '--' prefix")
        command.extend([key, str(value)])
    
    # 为子进程设置独立的环境变量
    env = os.environ.copy()
    env['CUDA_VISIBLE_DEVICES'] = str(gpu_id)
    env['PROCESS_NAME'] = current_process().name
    
    while True:
        try:
            subprocess.run(command, check=True, env=env)
            break  # 成功运行则退出循环
        except subprocess.CalledProcessError as e:
            print(f"Error occurred while running the command: {e.cmd}")
            print(f"Exit code: {e.returncode}")
            print(f"Output: {e.output}")
            print(f"Error: {e.stderr}")
            print("Retrying...")

def process_split_dir(params):
    split_dir, gpu_id = params
    updated_args = update_args_with_split(args, split_dir)
    run_predict_system(updated_args, gpu_id)

if __name__ == '__main__':
    start_time = time.time()
    base_dir = './shangfei/more_pdfs_6'
    num_splits = 6  # 每个GPU卡分配的进程数
    gpus = [0, 1, 2, 3, 4, 5, 6, 7]  # 可用的GPU ID列表

    # 获取PDF文件及其大小
    pdf_files_with_sizes = get_pdf_files_with_sizes(base_dir)
    
    # 按大小排序并分片
    splits = split_pdf_files_by_size(pdf_files_with_sizes, len(gpus) * num_splits)
    
    # 创建并移动文件到子目录
    split_dirs = create_and_move_files(base_dir, splits)
    
    # 为每个分片指定GPU ID，确保每个GPU运行N个进程
    split_gpu_pairs = [(split_dirs[i], gpus[i % len(gpus)]) for i in range(len(split_dirs))]

    with Pool(len(split_gpu_pairs)) as pool:
        pool.map(process_split_dir, split_gpu_pairs)

    # 输出运行时间，时-分-秒
    print(time.strftime("最终运行时间为：%H:%M:%S", time.gmtime(time.time() - start_time)))
