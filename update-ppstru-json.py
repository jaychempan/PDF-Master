import os
import json

def extract_chat_output(content):
    """
    Extract the chat_output content before the first [UNUSED_TOKEN_145]
    """
    if '[UNUSED_TOKEN_145]' in content:
        return content.split('[UNUSED_TOKEN_145]')[0]
    return content

def process_figures_json(directory):
    """
    Process figures.json files in all first-level subdirectories of the specified directory
    """
    result = {}
    for subdir in os.listdir(directory):
        subdir_path = os.path.join(directory, subdir)
        if os.path.isdir(subdir_path):
            figures_json_path = os.path.join(subdir_path, 'figures.json')
            if os.path.exists(figures_json_path):
                with open(figures_json_path, 'r', encoding='utf-8') as file:
                    figures = json.load(file)
                    for figure in figures:
                        image_name = figure['image_name']
                        chat_output = extract_chat_output(figure['chat_output'])
                        result[image_name] = chat_output
    return result

def process_tables_json(directory):
    """
    Process tables.json files in all first-level subdirectories of the specified directory
    """
    result = {}
    for subdir in os.listdir(directory):
        subdir_path = os.path.join(directory, subdir)
        if os.path.isdir(subdir_path):
            figures_json_path = os.path.join(subdir_path, 'tables.json')
            # print(figures_json_path)
            if os.path.exists(figures_json_path):
                with open(figures_json_path, 'r', encoding='utf-8') as file:
                    figures = json.load(file)
                    for figure in figures:
                        image_name = figure['image_name']
                        chat_output = extract_chat_output(figure['chat_output'])
                        # print(chat_output)
                        result[image_name] = chat_output
    return result

def update_fig_ocr_json(directory, figures_data):
    """
    Update _ocr.json files in all first-level subdirectories of the specified directory
    """
    for subdir in os.listdir(directory):
        subdir_path = os.path.join(directory, subdir)
        if os.path.isdir(subdir_path):
            for file_name in os.listdir(subdir_path):
                if file_name.endswith('_ocr.json'):
                    ocr_json_path = os.path.join(subdir_path, file_name)
                    with open(ocr_json_path, 'r', encoding='utf-8') as file:
                        ocr_data = json.load(file)
                    
                    updated = False
                    for page in ocr_data.get('pdf_info', []):
                        images = page['images']
                        if len(images) == 0:
                            # print(1)
                            continue
                        else:
                            for image in images:
                                for block in image.get('blocks', []):
                                    for line in block.get('lines', []):
                                        for span in line.get('spans', []):
                                            if span['type'] == 'image': 
                                                image_path = span.get('image_path')
                                                # print(image_path)
                                                # print(image_path.split('./')[-1])
                                                # if image_path and image_path in figures_data:
                                                span['content'] = figures_data[image_path.split('./')[-1]]
                                                # print(span['content'])
                                                updated = True

                    
                    if updated:
                        with open(ocr_json_path, 'w', encoding='utf-8') as file:
                            json.dump(ocr_data, file, ensure_ascii=False, indent=4)
                            print(f'完成 {ocr_json_path} 的图片语义写入')

def update_tab_ocr_json(directory, figures_data):
    """
    Update _ocr.json files in all first-level subdirectories of the specified directory
    """
    for subdir in os.listdir(directory):
        subdir_path = os.path.join(directory, subdir)
        if os.path.isdir(subdir_path):
            for file_name in os.listdir(subdir_path):
                if file_name.endswith('_ocr.json'):
                    ocr_json_path = os.path.join(subdir_path, file_name)
                    with open(ocr_json_path, 'r', encoding='utf-8') as file:
                        ocr_data = json.load(file)
                    
                    updated = False
                    for page in ocr_data.get('pdf_info', []):
                        images = page['tables']
                        if len(images) == 0:
                            # print(1)
                            continue
                        else:
                            for image in images:
                                for block in image.get('blocks', []):
                                    for line in block.get('lines', []):
                                        for span in line.get('spans', []):
                                            if span['type'] == 'image': 
                                                image_path = span.get('image_path')
                                                # print(image_path)
                                                # print(image_path.split('./')[-1])
                                                # if image_path and image_path in figures_data:
                                                span['content'] = figures_data[image_path.split('./')[-1]]
                                                # print(span['content'])
                                                # print(span['content'])
                                                updated = True

                    
                    if updated:
                        with open(ocr_json_path, 'w', encoding='utf-8') as file:
                            json.dump(ocr_data, file, ensure_ascii=False, indent=4)
                            print(f'完成 {ocr_json_path} 的表格写入')
# Example usage
directory_path = '/mnt/petrelfs/panjiancheng/llm-pdf-parsing/data/output/20240605_comac_pdfs_process/structure'
# directory_path = '/mnt/petrelfs/panjiancheng/llm-pdf-parsing/data/output/1pdfs_process/structure/'
figures_data = process_figures_json(directory_path)
update_fig_ocr_json(directory_path, figures_data)

tables_data = process_tables_json(directory_path)
update_tab_ocr_json(directory_path, tables_data)