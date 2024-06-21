
import json
import os


def process_one_pdf(pdf_info):
    import markdownify
    markdown_content = []

    if "_parse_type" not in pdf_info or pdf_info["_parse_type"] != "ocr":
        print("Unsupported parse type or missing parse type.")
        return
    
    for page in pdf_info["pdf_info"]:
        process_one_page(page, markdown_content) # 这里面的是按照页面进行存放数据,pdf_info["pdf_info"]是包含每一页数据的列表

    return markdown_content

def process_one_page(page_info, markdown_content):
    # print(f"Processing page index: {page_info['page_idx']}")
    
    # 按照顺序处理每一个block
    for block_idx in range(len(page_info["preproc_blocks"])):
        
        process_one_block(page_info, markdown_content, page_info['page_idx'], block_idx)
    
    # 按照顺序处理preproc_blocks中的内容，拼装成markdown

# 针对不同block类型进行处理，输出成对应的markdown语句
def process_one_block(page_info, markdown_content, page_idx, block_idx):
    block = page_info['preproc_blocks'][block_idx]
    math_block = page_info['interline_equations']
    block_type = block["type"]
    # print(f"Processing {block_type}:")

    if block_type == "title":
        one_title = ""
        for line in block["lines"]:
            for span in line["spans"]:
                content = span['content']
                if span['type'] == "text":
                    one_title += content
                elif span['type'] == "inline_equation":
                    one_title += content # TODO：后续应该加上$$,现在不做处理
        markdown_content.append(f"# {one_title}")
    elif block_type == "text":
        one_text = ""
        for line in block["lines"]:
            for span in line["spans"]:
                if span["type"] == "text":
                    content = span['content']
                    if content.strip().endswith('.') or content.strip().endswith('\u3002'):
                        words = content.rsplit('.', 1)[0].lower().split()
                        if len(words) != 0 and words[-1] in ['fig', 'tab']:
                            one_text += content + ' '
                        else:
                            one_text += content + '\n\n'
                    elif content.strip().endswith('-'):
                        one_text += content.rstrip('-')
                    else:
                        one_text += content + ' '
        # print(one_text)
        markdown_content.append(f"{one_text}")
    # elif block_type == "image":
    #     one_image_body = ""
    #     one_image_caption = ""
    #     for block in block["blocks"]: # 里面可能有image_body和image_block
    #         if block['type'] == "image_body":
    #             for line in block["lines"]:
    #                 for span in line["spans"]:
    #                     if span["type"] == "image":
    #                         image_path = span['image_path']
    #                         one_image_body += f"![Figure {page_idx}]({image_path})\n\n"
    #         elif block['type'] == "image_caption":
    #             for line in block["lines"]:
    #                 for span in line["spans"]:
    #                     if span["type"] == "text": # 后面可以扩展行内公式（表格同理）
    #                         content = span['content']
    #                         one_image_body += content
    #     markdown_content.append(f"{one_image_body}")
    #     markdown_content.append(f"{one_image_caption}")
    # elif block_type == "table":
    #     one_image_body = ""
    #     one_image_caption = ""
    #     for block in block["blocks"]: # 里面可能有image_body和image_block
    #         if block['type'] == "table_body":
    #             for line in block["lines"]:
    #                 for span in line["spans"]:
    #                     if span["type"] == "image":
    #                         image_path = span['image_path']
    #                         one_image_body += f"![Table {page_idx}]({image_path})\n\n"
    #         elif block['type'] == "table_caption":
    #             for line in block["lines"]:
    #                 for span in line["spans"]:
    #                     content = span['content']
    #                     if span["type"] == "text": # 后面可以扩展行内公式（表格同理）
    #                         one_image_body += content
    #     markdown_content.append(f"{one_image_body}")
    #     markdown_content.append(f"{one_image_caption}")
    elif block_type == "interline_equation":
        one_image_body = ""
        for line in block["lines"]:
            for span in line["spans"]:
                if span["type"] == "interline_equation":
                    # print(span)
                    math_idx = span['math_idx']
                    # print(f"math_idx: {math_idx}")
                    content = math_block[math_idx]['lines'][-1]['spans'][-1]['content']
                    content = content.replace(' ', '') # 去除公式中的空格
                    one_image_body += f"\n\n$${content}$$\n\n"
                    # image_path = span['image_path']
                    # one_image_body += f"\n\n![interline_equation {page_idx}]({image_path})\n\n"
                elif span["type"] == "embedding":
                    # print(span)
                    math_idx = span['math_idx']
                    # print(f"math_idx: {math_idx}")
                    content = math_block[math_idx]['lines'][-1]['spans'][-1]['content']
                    if len(content)==0:
                        content = ''
                    content = content.replace(' ', '') # 去除公式中的空格
                    one_image_body += f" ${content}$ "
        markdown_content.append(f"{one_image_body}")



        

def load_json_file(file_path):
    with open(file_path, 'r', encoding='utf-8') as file:
        data = json.load(file)
    return data

def process_directory(directory_path):
    for root, dirs, files in os.walk(directory_path):
        for dir_ in dirs:
            dir_path = os.path.join(root, dir_)
            # print(f"dir_path:{dir_path}")
            for _, _, files in os.walk(dir_path):
                # print(files)
                for file in files:
                    if file.endswith(".json"):
                        # print(f"processing {file}...")
                        json_file_path = os.path.join(dir_path, file)
                        pdf_info = load_json_file(json_file_path)
                        markdown_content = process_one_pdf(pdf_info)
                        
                        if markdown_content:
                            markdown_file_name = file.replace(".json", ".md")
                            markdown_path = os.path.join(dir_path, markdown_file_name)
                            with open(markdown_path, 'w', encoding='utf-8') as md_file:
                                md_file.write("\n".join(markdown_content))
                            print(f"Markdown saved to {markdown_path}")
                break
        break


if __name__ == "__main__":
    import argparse
    import time
    parser = argparse.ArgumentParser(
    description=(
        "将格式化的json文件转换成markdown文件"
    )
    )
    parser.add_argument(
    "--input_directory",
    type=str,
    required=True,
    help="指定目录下的所有子目录包含了json文件",
    )

    args = parser.parse_args()

    start_time = time.time()
    # print(args.directory_path)
    process_directory(args.input_directory)

    print(time.strftime("%H:%M:%S", time.gmtime(time.time() - start_time)))