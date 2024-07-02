import json
import re

def process_jsonl(input_file, delete_strs):
    output_file = input_file.replace('.jsonl', '_clean.jsonl')
    
    with open(input_file, 'r', encoding='utf-8') as infile, open(output_file, 'w', encoding='utf-8') as outfile:
        for line in infile:
            data = json.loads(line.strip())
            content = data.get('content', '')

            # 替换 delete_strs 中的字符串为相同长度的 'X'
            for delete_str in delete_strs:
                content = content.replace(delete_str, 'X' * len(delete_str))

            # 删除用$...$包裹的包含连续两个\cdot的内容
            content = re.sub(r'\$[^$]*\\cdot \\cdot[^$]*\$', '', content)
            data['content'] = content

            content = re.sub(r'\$[^$]*\\! \\![^$]*\$', '', content)
            data['content'] = content

            content = re.sub(r'\$[^$]*\\, \\,[^$]*\$', '', content)
            data['content'] = content

            content = re.sub(r'\$[^$]* . .[^$]*\$', '', content)
            data['content'] = content

            # 将处理后的数据写入输出文件
            outfile.write(json.dumps(data, ensure_ascii=False) + '\n')

# 使用示例
if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(description='Process JSONL files.')
    parser.add_argument('--input_file', type=str, help='Path to the input JSONL file')
    parser.add_argument('--delete_strs', nargs='+', type=str, help='Strings to be replaced with "X"')

    args = parser.parse_args()

    process_jsonl(args.input_file, args.delete_strs)