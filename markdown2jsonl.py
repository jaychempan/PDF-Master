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
                # print(files_)
                for file_ in files_:
                    if file_.endswith('.md'):
                        with open(os.path.join(subdir, file_), 'r', encoding='utf-8') as file:
                            content = file.read()
                            data.append({
                                "id": uuid.uuid4().hex,  # 使用相对路径作为id
                                "content": content
                            })
                break
        break
    return data

def write_jsonl(data, output_file):
    with jsonlines.open(output_file, mode='w') as writer:
        for entry in tqdm(data, desc="Writing JSON Lines"):
            writer.write(entry)

def main(input_directory, output_file):
    print("Reading markdown files...")
    data = read_markdown_files(input_directory)
    print("Writing to JSON Lines file...")
    write_jsonl(data, output_file)
    print(f"JSON Lines file has been created at: {output_file}")

# 使用示例
input_directory = '/mnt/petrelfs/panjiancheng/llm-pdf-parsing/shangfei/commac_pdfs_0604/structure/'  # 替换为你的Markdown文件目录
output_file = 'commac_pdfs_0604.jsonl'  # 输出的JSON Lines文件路径

main(input_directory, output_file)
