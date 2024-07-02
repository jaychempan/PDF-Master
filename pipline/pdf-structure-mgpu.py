import subprocess
import time
import os
from multiprocessing import Pool, current_process, Manager
import shutil
import copy
import logging
from datetime import datetime

# 设置日志记录
timestamp = datetime.now().strftime('%Y-%m-%d_%H-%M-%S')
log_filename = f'logs/pdf-structure-mgpu-{timestamp}.log'
logging.basicConfig(filename=log_filename, level=logging.INFO, format='%(asctime)s %(levelname)s:%(message)s')

# 定义参数字典
args = {
    '--image_dir': '../demo/demo.pdf',
    '--det_model_dir': '../weights/ppocr_weights/det/ch/ch_PP-OCRv4_det_infer', 
    '--rec_model_dir': '../weights/ppocr_weights/rec/ch/ch_PP-OCRv4_rec_infer',
    '--rec_char_dict_path': '../paddleocr/ppocr/utils/ppocr_keys_v1.txt',
    '--table_model_dir': '../weights/ppocr_weights/table/ch_ppstructure_mobile_v2.0_SLANet_infer',
    '--table_char_dict_path': '../paddleocr/ppocr/utils/dict/table_structure_dict_ch.txt',
    '--layout_model_dir': '../weights/ppocr_weights/layout/picodet_lcnet_x1_0_fgd_layout_cdla_infer',
    '--layout_dict_path': '../paddleocr/ppocr/utils/dict/layout_dict/layout_cdla_dict.txt',
    '--recovery': 'True',
    '--output': './shangfei/default_output/',
    '--use_pdf2docx_api': 'False',
    '--mode': 'structure',
    '--return_word_box': 'False',
    '--use_gpu': 'True',
    '--show_log': 'False',
    '--use_mp': 'True',
    '--table': 'True'
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
def update_args_with_split(args, split_dir, output_directory):
    args_copy = copy.deepcopy(args)
    args_copy['--image_dir'] = split_dir
    args_copy['--output'] = output_directory
    return args_copy

# 执行预测系统
def run_predict_system(args_dict, gpu_id, retry_counter, time_counter):
    command = ['python3', './PaddleOCR/ppstructure/predict_system.py']
    for key, value in args_dict.items():
        if not key.startswith('--'):
            raise ValueError(f"Invalid parameter '{key}' without '--' prefix")
        command.extend([key, str(value)])
    
    # 为子进程设置独立的环境变量
    env = os.environ.copy()
    env['CUDA_VISIBLE_DEVICES'] = str(gpu_id)
    env['PROCESS_NAME'] = current_process().name

    retry_count = 0  # 重试计数器
    start_time = time.time()

    while True:
        try:
            with open(os.devnull, 'w') as devnull:  # 重定向输出到/dev/null
                # subprocess.run(command, check=True, env=env, stdout=devnull, stderr=devnull)
                subprocess.run(command, check=True, env=env)
                break  # 成功运行则退出循环
        except subprocess.CalledProcessError as e:
            retry_count += 1
            # logging.warning(f"Retrying... (Attempt {retry_count}) for process {current_process().name} on GPU {gpu_id}")
            # print(f"Retrying... (Attempt {retry_count}) for process {current_process().name} on GPU {gpu_id}")

    end_time = time.time()
    duration = end_time - start_time
    time_counter[current_process().name] = (start_time, end_time, duration)

    # # 输出重试次数
    # logging.info(f"Total retries for process {current_process().name} on GPU {gpu_id}: {retry_count}")
    # print(f"Total retries for process {current_process().name} on GPU {gpu_id}: {retry_count}")
    retry_counter[current_process().name] = retry_count

def process_split_dir(params):
    split_dir, gpu_id, retry_counter, time_counter, output_directory = params
    updated_args = update_args_with_split(args, split_dir, output_directory)
    run_predict_system(updated_args, gpu_id, retry_counter, time_counter)

if __name__ == '__main__':
    import warnings
    warnings.filterwarnings('ignore')
    import argparse
    parser = argparse.ArgumentParser(description="多进程处理目录下的子目录中的JSON文件")
    parser.add_argument("--input_directory", type=str, required=True, help="指定目录下的所有子目录包含了json文件")
    parser.add_argument("--output_directory", type=str, required=True, help="结构解析输出文件目录")
    parser.add_argument("--num_processes", type=int, required=True, help="每张GPU卡分配的进程数")
    args_sys = parser.parse_args()

    base_dir = args_sys.input_directory
    num_splits = args_sys.num_processes
    output_directory = args_sys.output_directory
    start_time = time.time()
    gpus = [0, 1, 2, 3, 4, 5, 6, 7]  # 可用的GPU ID列表
    # gpus = [2, 3, 4, 5]

    # Manager对象用于在进程之间共享数据
    manager = Manager()
    retry_counter = manager.dict()
    time_counter = manager.dict()

    # 获取PDF文件及其大小
    pdf_files_with_sizes = get_pdf_files_with_sizes(base_dir)
    
    # 按大小排序并分片
    splits = split_pdf_files_by_size(pdf_files_with_sizes, len(gpus) * num_splits)
    
    # 创建并移动文件到子目录
    split_dirs = create_and_move_files(base_dir, splits)
    
    # 为每个分片指定GPU ID，确保每个GPU运行N个进程
    split_gpu_pairs = [(split_dirs[i], gpus[i % len(gpus)], retry_counter, time_counter, output_directory) for i in range(len(split_dirs))]

    with Pool(len(split_gpu_pairs)) as pool:
        pool.map(process_split_dir, split_gpu_pairs)

    # 输出运行时间，时-分-秒
    end_time = time.time()
    duration = end_time - start_time
    logging.info(f"最终运行时间为：{time.strftime('%H:%M:%S', time.gmtime(duration))}")
    print(f"最终运行时间为：{time.strftime('%H:%M:%S', time.gmtime(duration))}")

    # 输出所有进程的重试次数
    total_retries = sum(retry_counter.values())
    logging.info(f"总重试次数：{total_retries}")
    print(f"总重试次数：{total_retries}")

    # 输出每个进程的开始时间、结束时间和运行时间
    for proc_name, times in time_counter.items():
        start, end, dur = times
        logging.info(f"Process {proc_name} started at {time.strftime('%Y-%m-%d %H:%M:%S', time.localtime(start))}, ended at {time.strftime('%Y-%m-%d %H:%M:%S', time.localtime(end))}, duration {time.strftime('%H:%M:%S', time.gmtime(dur))}")
        print(f"Process {proc_name} started at {time.strftime('%Y-%m-%d %H:%M:%S', time.localtime(start))}, ended at {time.strftime('%Y-%m-%d %H:%M:%S', time.localtime(end))}, duration {time.strftime('%H:%M:%S', time.gmtime(dur))}")