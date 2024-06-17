from transformers import AutoTokenizer, AutoModel
import torch
import torchvision.transforms as T
from PIL import Image
import os
import numpy as np
import re
import json
import time
from torchvision.transforms.functional import InterpolationMode

IMAGENET_MEAN = (0.485, 0.456, 0.406)
IMAGENET_STD = (0.229, 0.224, 0.225)

def build_transform(input_size):
    MEAN, STD = IMAGENET_MEAN, IMAGENET_STD
    transform = T.Compose([
        T.Lambda(lambda img: img.convert('RGB') if img.mode != 'RGB' else img),
        T.Resize((input_size, input_size), interpolation=InterpolationMode.BICUBIC),
        T.ToTensor(),
        T.Normalize(mean=MEAN, std=STD)
    ])
    return transform

def find_closest_aspect_ratio(aspect_ratio, target_ratios, width, height, image_size):
    best_ratio_diff = float('inf')
    best_ratio = (1, 1)
    area = width * height
    for ratio in target_ratios:
        target_aspect_ratio = ratio[0] / ratio[1]
        ratio_diff = abs(aspect_ratio - target_aspect_ratio)
        if ratio_diff < best_ratio_diff:
            best_ratio_diff = ratio_diff
            best_ratio = ratio
        elif ratio_diff == best_ratio_diff:
            if area > 0.5 * image_size * image_size * ratio[0] * ratio[1]:
                best_ratio = ratio
    return best_ratio

def dynamic_preprocess(image, min_num=1, max_num=6, image_size=448, use_thumbnail=False):
    orig_width, orig_height = image.size
    aspect_ratio = orig_width / orig_height

    target_ratios = set(
        (i, j) for n in range(min_num, max_num + 1) for i in range(1, n + 1) for j in range(1, n + 1) if
        i * j <= max_num and i * j >= min_num)
    target_ratios = sorted(target_ratios, key=lambda x: x[0] * x[1])

    target_aspect_ratio = find_closest_aspect_ratio(
        aspect_ratio, target_ratios, orig_width, orig_height, image_size)

    target_width = image_size * target_aspect_ratio[0]
    target_height = image_size * target_aspect_ratio[1]
    blocks = target_aspect_ratio[0] * target_aspect_ratio[1]

    resized_img = image.resize((target_width, target_height))
    processed_images = []
    for i in range(blocks):
        box = (
            (i % (target_width // image_size)) * image_size,
            (i // (target_width // image_size)) * image_size,
            ((i % (target_width // image_size)) + 1) * image_size,
            ((i // (target_width // image_size)) + 1) * image_size
        )
        split_img = resized_img.crop(box)
        processed_images.append(split_img)
    assert len(processed_images) == blocks
    if use_thumbnail and len(processed_images) != 1:
        thumbnail_img = image.resize((image_size, image_size))
        processed_images.append(thumbnail_img)
    return processed_images

def load_image(image_file, input_size=448, max_num=6):
    image = Image.open(image_file).convert('RGB')
    transform = build_transform(input_size=input_size)
    images = dynamic_preprocess(image, image_size=input_size, use_thumbnail=True, max_num=max_num)
    pixel_values = [transform(image) for image in images]
    pixel_values = torch.stack(pixel_values)
    return pixel_values

def load_images(folder_path, batch_size):
    image_counts = []
    image_list = []
    image_names = []
    for root, dirs, files in os.walk(folder_path):
        for dir_name in dirs:
            dir_path = os.path.join(root, dir_name)
            images_folder_path = os.path.join(dir_path, "figures")
            if os.path.isdir(images_folder_path):
                for filename in os.listdir(images_folder_path):
                    if filename.endswith(('.png', '.jpg', '.jpeg')):
                        img_path = os.path.join(images_folder_path, filename)
                        img_tensor = load_image(img_path, max_num=6).to(torch.bfloat16).cuda()
                        image_count = img_tensor.size(0)
                        image_counts.append(image_count)
                        image_list.append(img_tensor)
                        image_names.append(os.path.join(dir_name, filename))
                        if len(image_list) >= batch_size:
                            yield torch.cat(image_list, dim=0), image_counts, image_names
                            image_counts = []
                            image_list = []
                            image_names = []

    if image_list:
        yield torch.cat(image_list, dim=0), image_counts, image_names

def process_batch(pixel_values, image_counts, image_names, model, tokenizer):
    generation_config = dict(
        num_beams=1,
        max_new_tokens=512,
        do_sample=False,
    )
    questions = ['假如你是航空领域的专家，解读图像表示了什么？'] * len(image_counts)
    responses = model.batch_chat(tokenizer, pixel_values,
                                 image_counts=image_counts,
                                 questions=questions,
                                 generation_config=generation_config)
    batch_data = []
    for image_name, question, response in zip(image_names, questions, responses):
        one_data = {
            "image_name": image_name,
            "chat_output": response
        }
        batch_data.append(one_data)
    return batch_data

if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(
        description=(
            "Process images in specified directories in batches and generate a JSON file with results."
        )
    )

    parser.add_argument(
        "--model_path",
        type=str,
        default='/mnt/petrelfs/panjiancheng/HFs/.empty/Mini-InternVL-Chat-4B-V1-5 ',
        # required=True,
        help="Path to the pretrained model.",
    )

    parser.add_argument(
        "--root_directory",
        type=str,
        default='/mnt/petrelfs/panjiancheng/llm-pdf-parsing/shangfei/20240605_comac_pdfs_process/structure',
        # required=True,
        help="Root directory containing subdirectories with images.",
    )

    parser.add_argument(
        "--output_path",
        type=str,
        default='out.json',
        # required=True,
        help="Path to save the output JSON file.",
    )
    
    parser.add_argument(
        "--batch_size",
        type=int,
        default=8,
        help="Number of images to process in each batch.",
    )
    
    args = parser.parse_args()

    model = AutoModel.from_pretrained(
        args.model_path,
        torch_dtype=torch.bfloat16,
        low_cpu_mem_usage=True,
        trust_remote_code=True,
        device_map='auto').eval()

    tokenizer = AutoTokenizer.from_pretrained(args.model_path, trust_remote_code=True)

    all_data = []

    for pixel_values, image_counts, image_names in load_images(args.root_directory, args.batch_size):
        batch_data = process_batch(pixel_values, image_counts, image_names, model, tokenizer)
        all_data.extend(batch_data)
    
    with open(args.output_path, 'w', encoding='utf-8') as f:
        json.dump(all_data, f, ensure_ascii=False, indent=4)

    print(f"Results saved to {args.output_path}")