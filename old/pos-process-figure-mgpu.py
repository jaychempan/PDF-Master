import os
import argparse
import time
import multiprocessing as mp
import subprocess
import logging
from datetime import datetime

# Ensure logs directory exists
os.makedirs('logs', exist_ok=True)

# Setup logging
timestamp = datetime.now().strftime('%Y-%m-%d_%H-%M-%S')
log_filename = f'logs/pos-process-figure-{timestamp}.log'
logging.basicConfig(filename=log_filename, level=logging.INFO, format='%(asctime)s %(levelname)s:%(message)s')

def distribute_work(root_directory, gpus):
    subdirs = [d for d in os.listdir(root_directory) if os.path.isdir(os.path.join(root_directory, d))]
    work_distribution = {gpu_id: [] for gpu_id in gpus}

    for subdir in subdirs:
        figures_dir = os.path.join(root_directory, subdir, "figures")
        if os.path.isdir(figures_dir):
            file_count = len([f for f in os.listdir(figures_dir) if f.endswith(('.png', '.jpg', '.jpeg'))])
            gpu_id = min(work_distribution, key=lambda x: sum([fc for _, fc in work_distribution[x]]))
            work_distribution[gpu_id].append((subdir, file_count))

    return work_distribution

def process_subdir_on_gpu(root_directory, subdir, gpu_id, max_retries=3):
    command = f"CUDA_VISIBLE_DEVICES={gpu_id} python pos-process-figure-single.py --root_directory '{os.path.join(root_directory, subdir)}'"
    retries = 0
    while retries < max_retries:
        result = subprocess.run(command, shell=True)
        if result.returncode == 0:
            logging.info(f"Successfully processed directory: {subdir} on GPU {gpu_id}")
            break
        retries += 1
        logging.warning(f"Retrying {subdir} on GPU {gpu_id} ({retries}/{max_retries})")
    if retries == max_retries:
        logging.error(f"Failed to process {subdir} on GPU {gpu_id} after {max_retries} attempts")

def process_all_gpus(gpu_id, subdirs, root_directory):
    for subdir, _ in subdirs:
        process_subdir_on_gpu(root_directory, subdir, gpu_id)

if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        description=(
            "Distribute image processing tasks across multiple GPUs based on the number of images in subdirectories."
        )
    )

    parser.add_argument(
        "--root_directory",
        type=str,
        default='/mnt/petrelfs/panjiancheng/llm-pdf-parsing/data/output/20240605_comac_pdfs_process/structure',
        help="Root directory containing subdirectories with images.",
    )

    parser.add_argument(
        "--gpus",
        type=str,
        default='0,1,2,3,4,5,6,7',
        help="Comma-separated list of GPU ids to use for processing.",
    )

    args = parser.parse_args()
    gpus = [int(gpu) for gpu in args.gpus.split(',')]

    start_time = time.time()
    work_distribution = distribute_work(args.root_directory, gpus)

    processes = []
    for gpu_id, subdirs in work_distribution.items():
        p = mp.Process(target=process_all_gpus, args=(gpu_id, subdirs, args.root_directory))
        processes.append(p)
        p.start()

    for p in processes:
        p.join()

    end_time = time.time()
    total_time = end_time - start_time
    logging.info(f"Total processing time: {total_time:.2f} seconds")
    print(f"Total processing time: {total_time:.2f} seconds")