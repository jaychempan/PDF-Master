"""
针对输出的中见结果进行markdown结果的统计，可以统计指定目录下的子目录里面是否有markdown和总markdown大小，并将没有markdown的目录名称进行保存no_markdown_subdirs.txt
"""

import os
import math

def convert_size(size_bytes):
    if size_bytes == 0:
        return "0B"
    size_name = ("B", "KB", "MB", "GB", "TB")
    i = int(math.floor(math.log(size_bytes, 1024)))
    p = math.pow(1024, i)
    s = round(size_bytes / p, 2)
    return f"{s} {size_name[i]}"


def check_markdown_files(directory):
    no_markdown_subdirs = []
    markdown_count = 0
    markdown_total_size = 0
    json_count = 0

    for root, dirs, files in os.walk(directory):
        print(f"总共得到的文件目录数：{len(dirs)}")
        for dir in dirs:
            subdir = os.path.join(root, dir)
            is_has_markdown = False
            for root_, dirs_, files_ in os.walk(subdir):
                # print(files_)
                for file in files_:
                    if file.endswith('.md'):
                        is_has_markdown = True
                        markdown_count += 1
                        markdown_total_size += os.path.getsize(os.path.join(subdir, file))
                    elif file.endswith('.json'):
                        json_count += 1

                if not is_has_markdown:
                    no_markdown_subdirs.append(subdir)
                break
        break

    return no_markdown_subdirs, json_count, markdown_count, markdown_total_size

def write_no_markdown_subdirs(no_markdown_subdirs, output_file):
    with open(output_file, 'w') as f:
        for subdir in no_markdown_subdirs:
            f.write(subdir + '\n')

def main():
    directory = '/mnt/petrelfs/panjiancheng/llm-pdf-parsing/shangfei/20240605_comac_pdfs_process/structure'  # 请替换为你的目录路径
    output_file = 'no_markdown_subdirs.txt'
    
    no_markdown_subdirs, json_count, markdown_count, markdown_total_size = check_markdown_files(directory)
    write_no_markdown_subdirs(no_markdown_subdirs, output_file)

    print(f"Json 文件总数: {json_count}")
    print(f"Markdown 文件总数: {markdown_count}")
    print(f"Markdown 文件总大小: {convert_size(markdown_total_size)}") 

if __name__ == '__main__':
    main()
