import os
import argparse
import time
import multiprocessing as mp
import json
from datetime import datetime
from lmdeploy import pipeline
from lmdeploy.vl import load_image

def distribute_work_equally(root_directory, gpus):
    files = [f for f in os.listdir(root_directory) if f.endswith(('.png', '.jpg', '.jpeg'))]
    num_files = len(files)
    num_gpus = len(gpus)
    chunk_size = (num_files + num_gpus - 1) // num_gpus  # Ensures even distribution

    work_distribution = {gpu_id: [] for gpu_id in gpus}
    
    for i, file in enumerate(files):
        gpu_id = gpus[i % num_gpus]
        work_distribution[gpu_id].append(file)
    
    return work_distribution

def load_images(folder_path, filenames):
    image_list = []
    image_names = []
    for filename in filenames:
        img_path = os.path.join(folder_path, filename)
        image = load_image(img_path)
        image_list.append(image)
        image_names.append(filename)
    return image_list, image_names

def process_images(images, image_names, pipe):
    questions = ['下面的图像是一张表格吗？是表格回答是，不是表格回答不是'] * len(images)
    all_data = []
    for image_name, question, image in zip(image_names, questions, images):
        response = pipe((question, image))
        response_text = response.text  # Extract the text content from the Response object
        is_rule = '不是' not in response_text  # Modify this rule as needed
        one_data = {
            "image_name": image_name,
            "chat_output": response_text,
            "is_rule": is_rule
        }
        all_data.append(one_data)
    return all_data

def process_images_on_gpu(root_directory, filenames, gpu_id, pipe, output_dir, max_retries=3):
    os.environ["CUDA_VISIBLE_DEVICES"] = str(gpu_id)
    output_file = os.path.join(output_dir, f"figures_gpu_{gpu_id}.json")

    retries = 0
    while retries < max_retries:
        try:
            images, image_names = load_images(root_directory, filenames)
            all_data = process_images(images, image_names, pipe)

            with open(output_file, 'w', encoding='utf-8') as f:
                json.dump(all_data, f, ensure_ascii=False, indent=4)

            print(f"Successfully processed images on GPU {gpu_id}")
            break
        except Exception as e:
            retries += 1
            print(f"Retrying images on GPU {gpu_id} ({retries}/{max_retries}) due to error: {e}")
    if retries == max_retries:
        print(f"Failed to process images on GPU {gpu_id} after {max_retries} attempts")

def process_all_gpus(gpu_id, filenames, root_directory, model_path, output_dir):
    os.environ["CUDA_VISIBLE_DEVICES"] = str(gpu_id)
    pipe = pipeline(model_path)
    process_images_on_gpu(root_directory, filenames, gpu_id, pipe, output_dir)

def merge_json_files(output_dir, final_output_path):
    merged_data = []
    for filename in os.listdir(output_dir):
        if filename.endswith('.json'):
            file_path = os.path.join(output_dir, filename)
            with open(file_path, 'r', encoding='utf-8') as f:
                data = json.load(f)
                merged_data.extend(data)
    
    with open(final_output_path, 'w', encoding='utf-8') as f:
        json.dump(merged_data, f, ensure_ascii=False, indent=4)

if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        description=(
            "Distribute image processing tasks across multiple GPUs based on the number of images."
        )
    )

    parser.add_argument(
        "--root_directory",
        type=str,
        default='/mnt/petrelfs/panjiancheng/llm-pdf-parsing/data/tables_clean_by_ocr_wo_catg',
        help="Root directory containing images.",
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
        default='/mnt/petrelfs/panjiancheng/HFs/InternVL-Chat-V1-5',
        help="Path to the pretrained model.",
    )

    parser.add_argument(
        "--output_dir",
        type=str,
        default='/mnt/petrelfs/panjiancheng/llm-pdf-parsing/data',
        help="Directory to store individual JSON outputs.",
    )

    parser.add_argument(
        "--final_output_path",
        type=str,
        default='/mnt/petrelfs/panjiancheng/llm-pdf-parsing/data/tables_clean_by_internvl.json',
        help="Path to store the merged JSON output.",
    )

    args = parser.parse_args()
    gpus = [int(gpu) for gpu in args.gpus.split(',')]

    os.makedirs(args.output_dir, exist_ok=True)

    start_time = time.time()
    work_distribution = distribute_work_equally(args.root_directory, gpus)

    processes = []
    for gpu_id, filenames in work_distribution.items():
        p = mp.Process(target=process_all_gpus, args=(gpu_id, filenames, args.root_directory, args.model_path, args.output_dir))
        processes.append(p)
        p.start()

    for p in processes:
        p.join()

    merge_json_files(args.output_dir, args.final_output_path)

    end_time = time.time()
    total_time = end_time - start_time
    print(f"Total processing time: {total_time:.2f} seconds")
    print(f"Merged JSON file created at: {args.final_output_path}")
