import os
import argparse
import multiprocessing as mp
import subprocess
import time
import logging
from datetime import datetime
from tqdm import tqdm

# 设置日志记录
timestamp = datetime.now().strftime('%Y-%m-%d_%H-%M-%S')
log_filename = f'logs/pos-process-mgpu-{timestamp}.log'
logging.basicConfig(filename=log_filename, level=logging.INFO, format='%(asctime)s %(levelname)s:%(message)s')

def is_equations_empty(directory):
    equations_path = os.path.join(directory, 'equations')
    if not os.path.isdir(equations_path):
        return True
    return not os.listdir(equations_path)

def get_equation_files_count(directory):
    equations_path = os.path.join(directory, 'equations')
    if os.path.isdir(equations_path):
        return len(os.listdir(equations_path))
    return 0

def split_dirs(input_directory, num_splits):
    dir_list = []
    for root, dirs, files in os.walk(input_directory):
        for dir_ in dirs:
            dir_pth = os.path.join(os.path.abspath(root), dir_)
            if not is_equations_empty(dir_pth):
                dir_list.append(dir_pth)
        break  # 只处理顶级目录
    dir_list = [(dir_, get_equation_files_count(dir_)) for dir_ in dir_list]
    dir_list.sort(key=lambda x: x[1], reverse=True)
    splits = [[] for _ in range(num_splits)]
    file_counts = [0] * num_splits

    for dir_, count in dir_list:
        min_index = file_counts.index(min(file_counts))
        splits[min_index].append(dir_)
        file_counts[min_index] += count

    return splits

def worker(task_list, config_path, gpu_id, retry_counter, time_counter, progress_queue):
    process_name = mp.current_process().name
    start_time = time.time()
    retry_count = 0

    for dir_path in task_list:
        command = f"CUDA_VISIBLE_DEVICES={gpu_id} python pos-process-single.py --input_directory {dir_path} --config_path {config_path}"
        
        task_completed = False
        while not task_completed:  # 使用标志变量来控制重试
            try:
                with open(os.devnull, 'w') as devnull:  # 重定向输出到/dev/null
                    subprocess.run(command, check=True, shell=True, stdout=devnull, stderr=devnull)
                logging.info(f"Successfully processed directory: {dir_path}")
                task_completed = True  # 任务成功，设置标志变量
            except subprocess.CalledProcessError as e:
                retry_count += 1
                time.sleep(5)  # 等待5秒后重试

        progress_queue.put(1)  # 任务处理完成后，更新进度

    end_time = time.time()
    duration = end_time - start_time
    retry_counter[process_name] = retry_count
    time_counter[process_name] = (start_time, end_time, duration)
    logging.info(f"Process {process_name} started at {time.strftime('%Y-%m-%d %H:%M:%S', time.localtime(start_time))}, ended at {time.strftime('%Y-%m-%d %H:%M:%S', time.localtime(end_time))}, duration {time.strftime('%H:%M:%S', time.gmtime(duration))}, retries {retry_count}")

def log_progress(retry_counter, time_counter, interval=60):
    while True:
        time.sleep(interval)
        logging.info("Logging progress...")
        for proc_name, retries in retry_counter.items():
            start, end, duration = time_counter[proc_name]
            logging.info(f"Progress Report - Process {proc_name} - Start: {time.strftime('%Y-%m-%d %H:%M:%S', time.localtime(start))}, End: {time.strftime('%Y-%m-%d %H:%M:%S', time.localtime(end))}, Duration: {time.strftime('%H:%M:%S', time.gmtime(duration))}, Retries: {retries}")

def progress_monitor(total_tasks, progress_queue):
    with tqdm(total=total_tasks) as pbar:
        while total_tasks > 0:
            try:
                progress_queue.get(timeout=0.1)
                pbar.update(1)
                total_tasks -= 1
            except:
                pass

def main(input_directory, config_path, num_processes):
    gpu_ids = "0,1,2,3,4,5,6,7"
    gpu_list = gpu_ids.split(",")
    num_gpus = len(gpu_list)
    
    total_processes = num_processes * num_gpus
    dir_chunks = split_dirs(input_directory, total_processes)
    total_tasks = sum(len(chunk) for chunk in dir_chunks)

    manager = mp.Manager()
    retry_counter = manager.dict()
    time_counter = manager.dict()
    progress_queue = manager.Queue()

    processes = []
    for i in range(total_processes):
        gpu_id = gpu_list[i % num_gpus]
        task_list = dir_chunks[i]
        p = mp.Process(target=worker, args=(task_list, config_path, gpu_id, retry_counter, time_counter, progress_queue))
        p.start()
        processes.append(p)

    logging_thread = mp.Process(target=log_progress, args=(retry_counter, time_counter))
    logging_thread.start()

    monitor_thread = mp.Process(target=progress_monitor, args=(total_tasks, progress_queue))
    monitor_thread.start()

    for p in processes:
        p.join()

    logging_thread.terminate()
    monitor_thread.terminate()

    # 输出每个进程的重试次数和运行时间
    for proc_name, retries in retry_counter.items():
        start, end, duration = time_counter[proc_name]
        logging.info(f"Process {proc_name} - Start: {time.strftime('%Y-%m-%d %H:%M:%S', time.localtime(start))}, End: {time.strftime('%Y-%m-%d %H:%M:%S', time.localtime(end))}, Duration: {time.strftime('%H:%M:%S', time.gmtime(duration))}, Retries: {retries}")
        print(f"Process {proc_name} - Start: {time.strftime('%Y-%m-%d %H:%M:%S', time.localtime(start))}, End: {time.strftime('%Y-%m-%d %H:%M:%S', time.localtime(end))}, Duration: {time.strftime('%H:%M:%S', time.gmtime(duration))}, Retries: {retries}")

if __name__ == "__main__":
    start_time = time.time()
    parser = argparse.ArgumentParser(description="多进程处理目录下的子目录中的JSON文件")
    parser.add_argument("--input_directory", type=str, required=True, help="指定目录下的所有子目录包含了json文件")
    parser.add_argument("--config_path", type=str, required=True, help="配置文件路径")
    parser.add_argument("--num_processes", type=int, required=True, help="每张GPU卡分配的进程数")
    args = parser.parse_args()
    main(args.input_directory, args.config_path, args.num_processes)
    end_time = time.time()
    duration = end_time - start_time
    logging.info(f"最终运行时间为：{time.strftime('%H:%M:%S', time.gmtime(duration))}")
    print(f"最终运行时间为：{time.strftime('%H:%M:%S', time.gmtime(duration))}")
