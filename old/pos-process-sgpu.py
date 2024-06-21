import os
import argparse
import multiprocessing as mp
import subprocess
import numpy as np

def is_equations_empty(directory):
    equations_path = os.path.join(directory, 'equations')
    return os.path.isfile(equations_path) and os.path.getsize(equations_path) == 0

def split_dirs(input_directory, num_splits):
    dir_list = []
    for root, dirs, files in os.walk(input_directory):
        for dir_ in dirs:
            dir_list.append(os.path.join(os.path.abspath(root), dir_))
        break  # 只处理顶级目录
    return np.array_split(dir_list, num_splits)

def worker(directories, config_path):
    for dir_path in directories:
        cmd = [
            'python', 'pos-process-single.py', 
            '--input_directory', dir_path,
            '--config_path', config_path
        ]
        subprocess.run(cmd)

def main(input_directory, config_path, num_processes):
    dir_chunks = split_dirs(input_directory, num_processes)
    
    # # 检查每个目录块，删除包含空的 equations 文件的目录块
    # dir_chunks = [chunk for chunk in dir_chunks if not is_equations_empty(chunk)]

    with mp.Pool(processes=num_processes) as pool:
        pool.starmap(worker, [(chunk, config_path) for chunk in dir_chunks])

if __name__ == "__main__":
    import warnings
    warnings.filterwarnings('ignore')
    import time
    start_time = time.time()
    parser = argparse.ArgumentParser(description="多进程处理目录下的子目录中的JSON文件")
    parser.add_argument("--input_directory", type=str, required=True, help="指定目录下的所有子目录包含了json文件")
    parser.add_argument("--config_path", type=str, required=True, help="配置文件路径")
    parser.add_argument("--num_processes", type=int, required=True, help="指定并行处理的进程数")
    args = parser.parse_args()
    main(args.input_directory, args.config_path, args.num_processes)
    # 输出运行时间，时-分-秒
    print(time.strftime("%H:%M:%S", time.gmtime(time.time() - start_time)))
