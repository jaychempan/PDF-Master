import os
import argparse
import multiprocessing as mp
import subprocess
import time
import logging
from queue import Queue, Empty
from multiprocessing import Manager

# 配置日志记录
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

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

def worker(task_queue, config_path, gpu_id, retry_counter, time_counter):
    process_name = mp.current_process().name
    start_time = time.time()
    retry_count = 0

    while True:
        try:
            dir_path = task_queue.get_nowait()
        except Empty:
            break

        cmd = [
            'python', 'pos-process-single.py', 
            '--input_directory', dir_path,
            '--config_path', config_path
        ]
        env = os.environ.copy()
        env['CUDA_VISIBLE_DEVICES'] = gpu_id

        while True:
            try:
                subprocess.run(cmd, check=True, env=env)
                logging.info(f"Successfully processed directory: {dir_path}")
                break
            except subprocess.CalledProcessError as e:
                retry_count += 1
                logging.error(f"Error occurred while running the command: {e.cmd}")
                logging.error(f"Exit code: {e.returncode}")
                logging.error(f"Output: {e.output}")
                logging.error(f"Error: {e.stderr}")
                logging.info(f"Retrying directory: {dir_path}")
                time.sleep(5)  # 等待5秒后重试

    end_time = time.time()
    duration = end_time - start_time
    retry_counter[process_name] = retry_count
    time_counter[process_name] = (start_time, end_time, duration)
    logging.info(f"Process {process_name} started at {time.strftime('%Y-%m-%d %H:%M:%S', time.localtime(start_time))}, ended at {time.strftime('%Y-%m-%d %H:%M:%S', time.localtime(end_time))}, duration {time.strftime('%H:%M:%S', time.gmtime(duration))}, retries {retry_count}")

def main(input_directory, config_path, num_processes):
    gpu_ids = "0,1,2,3,4,5,6,7"
    gpu_list = gpu_ids.split(",")
    num_gpus = len(gpu_list)
    
    total_processes = num_processes * num_gpus
    dir_chunks = split_dirs(input_directory, total_processes)

    task_queue = Queue()
    for chunk in dir_chunks:
        for dir_path in chunk:
            task_queue.put(dir_path)

    manager = Manager()
    retry_counter = manager.dict()
    time_counter = manager.dict()

    processes = []
    for i in range(total_processes):
        gpu_id = gpu_list[i % num_gpus]
        p = mp.Process(target=worker, args=(task_queue, config_path, gpu_id, retry_counter, time_counter))
        p.start()
        processes.append(p)

    for p in processes:
        p.join()

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