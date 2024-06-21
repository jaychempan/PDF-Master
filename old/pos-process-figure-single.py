from lmdeploy import pipeline
from lmdeploy.vl import load_image
import os
import json

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
    questions = ['假如你是航空领域的专家，用专业的描述下面的图像？'] * len(images)
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

if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(
        description=(
            "Process images in specified directories and generate a JSON file with results."
        )
    )

    parser.add_argument(
        "--model_path",
        type=str,
        default='/mnt/petrelfs/panjiancheng/HFs/InternVL-Chat-V1-5',
        help="Path to the pretrained model.",
    )

    parser.add_argument(
        "--root_directory",
        type=str,
        required=True,
        default='/mnt/petrelfs/panjiancheng/llm-pdf-parsing/data/output/te/structure/国际标准——E8M-16a(文字版)',
        help="Root directory containing subdirectories with images.",
    )

    parser.add_argument(
        "--dir_name",
        type=str,
        default='figures',
        help="Subdirectory containing images.",
    )

    args = parser.parse_args()
    pipe = pipeline(args.model_path)
    output_file = os.path.join(args.root_directory, f"{args.dir_name}.json")
    if not os.path.isfile(output_file):
        images, image_names = load_images(args.root_directory, args.dir_name)
        all_data = process_images(images, image_names, pipe)

        with open(output_file, 'w', encoding='utf-8') as f:
            json.dump(all_data, f, ensure_ascii=False, indent=4)

        print(f"Results saved to {output_file}")
    else:
        print(f"已经处理过: {output_file}")