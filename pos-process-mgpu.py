import os
import argparse
import multiprocessing as mp
import subprocess
import numpy as np

def is_equations_empty(directory):
    equations_path = os.path.join(directory, 'equations')
    # 检查目录是否存在且是目录
    if not os.path.isdir(equations_path):
        return True  # 如果目录不存在，也视为空目录
    # 列出目录中的文件和子目录，如果为空，则返回True
    return not os.listdir(equations_path)


def split_dirs(input_directory, num_splits):
    dir_list = []
    for root, dirs, files in os.walk(input_directory):
        for dir_ in dirs:
            if is_equations_empty(dir_):
                dir_list.append(os.path.join(os.path.abspath(root), dir_))
        break  # 只处理顶级目录
    return np.array_split(dir_list, num_splits)

def worker(directories, config_path, gpu_ids):
    for dir_path in directories:
        cmd = [
            'python', 'pos-process-single.py', 
            '--input_directory', dir_path,
            '--config_path', config_path
        ]
        
        while True:
            try:
                env = os.environ.copy()
                env['CUDA_VISIBLE_DEVICES'] = gpu_ids
                subprocess.run(cmd, check=True, env=env)
                break  # 成功运行则退出循环
            except subprocess.CalledProcessError as e:
                print(f"Error occurred while running the command: {e.cmd}")
                print(f"Exit code: {e.returncode}")
                print(f"Output: {e.output}")
                print(f"Error: {e.stderr}")
                print("Retrying...")

def main(input_directory, config_path, num_processes):
    gpu_ids = "0,1,2,3,4,5,6,7"  # 设置可用的GPU列表
    gpu_list = gpu_ids.split(",")
    num_gpus = len(gpu_list)
    
    total_processes = num_processes * num_gpus  # 每张卡分配num_processes个进程
    dir_chunks = split_dirs(input_directory, total_processes)

    pool_args = [(chunk, config_path, gpu_list[i % num_gpus]) for i, chunk in enumerate(dir_chunks)]
    
    with mp.Pool(processes=total_processes) as pool:
        pool.starmap(worker, pool_args)

if __name__ == "__main__":
    import time
    start_time = time.time()
    parser = argparse.ArgumentParser(description="多进程处理目录下的子目录中的JSON文件")
    parser.add_argument("--input_directory", type=str, required=True, help="指定目录下的所有子目录包含了json文件")
    parser.add_argument("--config_path", type=str, required=True, help="配置文件路径")
    parser.add_argument("--num_processes", type=int, required=True, help="每张GPU卡分配的进程数")
    args = parser.parse_args()
    main(args.input_directory, args.config_path, args.num_processes)
    # 输出运行时间，时-分-秒
    print(time.strftime("最终运行时间为：%H:%M:%S", time.gmtime(time.time() - start_time)))
