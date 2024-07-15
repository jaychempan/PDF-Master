import os
import jsonlines
from tqdm import tqdm
import uuid

def read_markdown_files(directory):
    data = []
    for root, dirs, files in os.walk(directory):
        print(f"总共得到的文件目录数：{len(dirs)}")
        for dir in dirs:
            subdir = os.path.join(root, dir)
            for root_, dirs_, files_ in os.walk(subdir):
                for file_ in files_:
                    if file_.endswith('.md'):
                        with open(os.path.join(subdir, file_), 'r', encoding='utf-8') as file:
                            content = file.read()
                            data.append({
                                "id": uuid.uuid4().hex,  # 使用相对路径作为id
                                "file_name": file_,
                                "content": content
                            })
                break
        break
    return data

def write_jsonl(data, output_file):
    with jsonlines.open(output_file, mode='w') as writer:
        for entry in tqdm(data, desc="Writing JSON Lines"):
            writer.write(entry)

def main(input_directory):
    print("Reading markdown files...")
    data = read_markdown_files(input_directory)
    file_name = os.path.basename(os.path.normpath(input_directory.split('/structure')[0]))  + '.jsonl'
    print(file_name)
    output_file = os.path.join(input_directory.split('/structure')[0], file_name)
    print("Writing to JSON Lines file...")
    write_jsonl(data, output_file)
    print(f"JSON Lines file has been created at: {output_file}")

if __name__ == "__main__":
    import argparse
    import time
    parser = argparse.ArgumentParser(
        description=(
            "将格式化markdown文件转换成jsonl格式的训练数据"
        )
    )
    parser.add_argument(
        "--input_directory",
        type=str,
        required=True,
        help="指定目录下的所有子目录包含了markdown文件",
    )

    args = parser.parse_args()

    start_time = time.time()
    main(args.input_directory)
    print(time.strftime("%H:%M:%S", time.gmtime(time.time() - start_time)))
