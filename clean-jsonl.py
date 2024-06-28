import json
import re

def process_jsonl(input_file, output_file, delete_strs):
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
input_file = '/mnt/petrelfs/panjiancheng/llm-pdf-parsing/data/output/20240605_comac_pdfs_process/20240605_comac_pdfs_process_wo_fig.jsonl'
output_file = '/mnt/petrelfs/panjiancheng/llm-pdf-parsing/data/output/20240605_comac_pdfs_process/20240605_comac_pdfs_process_wo_fig_clean.jsonl'
delete_strs = ['商飞', '中国商用飞机有限责任公司']  # 可以添加多个要替换的字符串

process_jsonl(input_file, output_file, delete_strs)
