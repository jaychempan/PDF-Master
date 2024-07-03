import os
import argparse
import time
import multiprocessing as mp
import logging
import json
from datetime import datetime
from lmdeploy import pipeline
from lmdeploy.vl import load_image

# Ensure logs directory exists
os.makedirs('../logs', exist_ok=True)

# Setup logging
timestamp = datetime.now().strftime('%Y-%m-%d_%H-%M-%S')
log_filename = f'../logs/pos-process-table-{timestamp}.log'
logging.basicConfig(filename=log_filename, level=logging.INFO, format='%(asctime)s %(levelname)s:%(message)s')

def distribute_work(root_directory, gpus):
    subdirs = [d for d in os.listdir(root_directory) if os.path.isdir(os.path.join(root_directory, d))]
    work_distribution = {gpu_id: [] for gpu_id in gpus}

    for subdir in subdirs:
        figures_dir = os.path.join(root_directory, subdir, "tables")
        if os.path.isdir(figures_dir):
            file_count = len([f for f in os.listdir(figures_dir) if f.endswith(('.png', '.jpg', '.jpeg'))])
            gpu_id = min(work_distribution, key=lambda x: sum([fc for _, fc in work_distribution[x]]))
            work_distribution[gpu_id].append((subdir, file_count))

    return work_distribution

def load_images(folder_path, dir_name):
    image_list = []
    image_names = []
    for root, dirs, files in os.walk(folder_path):
        dir_path = os.path.join(root, dir_name)
        if os.path.isdir(dir_path):
            for filename in os.listdir(dir_path):
                if filename.endswith(('.png', '.jpg', '.jpeg')):
                    img_path = os.path.join(dir_path, filename)
                    image = load_image(img_path)
                    image_list.append(image)
                    image_names.append(os.path.join(dir_name, filename))
    return image_list, image_names

def process_images(images, image_names, pipe):
    questions = ['帮我将下面的表格图片转换成markdown格式输出：'] * len(images)
    all_data = []
    for image_name, question, image in zip(image_names, questions, images):
        response = pipe((question, image))
        response_text = response.text  # Extract the text content from the Response object
        one_data = {
            "image_name": image_name,
            "chat_output": response_text
        }
        all_data.append(one_data)
    return all_data

def process_subdir_on_gpu(root_directory, subdir, gpu_id, pipe, max_retries=3):
    os.environ["CUDA_VISIBLE_DEVICES"] = str(gpu_id)
    dir_path = os.path.join(root_directory, subdir)
    output_file = os.path.join(dir_path, "tables.json")
    
    if not os.path.isfile(output_file):
        retries = 0
        while retries < max_retries:
            try:
                images, image_names = load_images(dir_path, "tables")
                all_data = process_images(images, image_names, pipe)

                with open(output_file, 'w', encoding='utf-8') as f:
                    json.dump(all_data, f, ensure_ascii=False, indent=4)

                logging.info(f"Successfully processed directory: {subdir} on GPU {gpu_id}")
                break
            except Exception as e:
                retries += 1
                logging.warning(f"Retrying {subdir} on GPU {gpu_id} ({retries}/{max_retries}) due to error: {e}")
        if retries == max_retries:
            logging.error(f"Failed to process {subdir} on GPU {gpu_id} after {max_retries} attempts")
    else:
        logging.info(f"Already processed: {output_file}")

def process_all_gpus(gpu_id, subdirs, root_directory, model_path):
    os.environ["CUDA_VISIBLE_DEVICES"] = str(gpu_id)
    pipe = pipeline(model_path)
    for subdir, _ in subdirs:
        process_subdir_on_gpu(root_directory, subdir, gpu_id, pipe)

if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        description=(
            "Distribute image processing tasks across multiple GPUs based on the number of images in subdirectories."
        )
    )

    parser.add_argument(
        "--input_directory",
        type=str,
        required=True,
        help="Root directory containing subdirectories with images.",
    )

    parser.add_argument(
        "--gpus",
        type=str,
        default='0,1,2,3,4,5,6,7',
        help="Comma-separated list of GPU ids to use for processing.",
    )

    parser.add_argument(
        "--model_path",
        type=str,
        default='../../HFs/InternVL-Chat-V1-5',
        help="Path to the pretrained model.",
    )

    args = parser.parse_args()
    gpus = [int(gpu) for gpu in args.gpus.split(',')]

    start_time = time.time()
    work_distribution = distribute_work(args.input_directory, gpus)

    processes = []
    for gpu_id, subdirs in work_distribution.items():
        p = mp.Process(target=process_all_gpus, args=(gpu_id, subdirs, args.input_directory, args.model_path))
        processes.append(p)
        p.start()

    for p in processes:
        p.join()

    end_time = time.time()
    total_time = end_time - start_time
    logging.info(f"Total processing time: {total_time:.2f} seconds")
    print(f"Total processing time: {total_time:.2f} seconds")