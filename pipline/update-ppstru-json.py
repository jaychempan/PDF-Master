import os
import json
import argparse

def extract_chat_output(content):
    """
    Extract the chat_output content before the first [UNUSED_TOKEN_145]
    """
    if '[UNUSED_TOKEN_145]' in content:
        return content.split('[UNUSED_TOKEN_145]')[0]
    return content

def process_json(directory, file_name):
    """
    Process specified JSON files in all first-level subdirectories of the specified directory
    """
    result = {}
    for subdir in os.listdir(directory):
        subdir_path = os.path.join(directory, subdir)
        if os.path.isdir(subdir_path):
            json_path = os.path.join(subdir_path, file_name)
            if os.path.exists(json_path):
                with open(json_path, 'r', encoding='utf-8') as file:
                    data = json.load(file)
                    for item in data:
                        image_name = item['image_name']
                        chat_output = extract_chat_output(item['chat_output'])
                        result[image_name] = chat_output
    return result

def update_ocr_json(directory, figures_data, content_key):
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
                        items = page.get(content_key, [])
                        if len(items) == 0:
                            continue
                        else:
                            for item in items:
                                for block in item.get('blocks', []):
                                    for line in block.get('lines', []):
                                        for span in line.get('spans', []):
                                            if span['type'] == 'image': 
                                                image_path = span.get('image_path')
                                                if image_path:
                                                    image_key = image_path.split('./')[-1]
                                                    if image_key in figures_data:
                                                        span['content'] = figures_data[image_key]
                                                        updated = True
                    
                    if updated:
                        with open(ocr_json_path, 'w', encoding='utf-8') as file:
                            json.dump(ocr_data, file, ensure_ascii=False, indent=4)
                            print(f'完成 {ocr_json_path} 的内容更新')

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description='Process JSON files and update OCR files.')
    parser.add_argument('directory', type=str, help='Directory containing the subdirectories with JSON files')
    parser.add_argument('--process', type=str, choices=['figures', 'tables', 'both'], default='both', help='Specify whether to process figures, tables, or both')
    args = parser.parse_args()
    
    directory_path = args.directory
    
    if args.process in ['figures', 'both']:
        figures_data = process_json(directory_path, 'figures.json')
        update_ocr_json(directory_path, figures_data, 'images')

    if args.process in ['tables', 'both']:
        tables_data = process_json(directory_path, 'tables.json')
        update_ocr_json(directory_path, tables_data, 'tables')