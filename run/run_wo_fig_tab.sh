#!/bin/bash

# 设置目录变量
input_directory="../data/input/zysy/"
output_directory="../data/output/zysy_process/"
config_path="../weights/unimernet/demo.yaml"
num_processes="2"

# 进入pipline目录
cd pipline

# 运行pdf-structure-mgpu.py
python pdf-structure-mgpu.py --input_directory "$input_directory" --output_directory "$output_directory" --num_processes "$num_processes" --gpus "0,1,2,3,4,5,6,7,8"

# 运行pos-process-mgpu.py
python pos-process-mgpu.py --input_directory "${output_directory}structure" --config_path "$config_path" --num_processes "$num_processes" --gpus "0,1,2,3,4,5,6,7,8"

# 运行json2markdown.py
python json2markdown.py --input_directory "${output_directory}structure" --is_figure False --is_table True --is_ocr_table True

# 运行markdown2jsonl.py
python markdown2jsonl.py --input_directory "${output_directory}structure"

# 运行clean-jsonl.py
python clean-jsonl.py --input_file "${output_directory}*_process.jsonl" --delete_strs "key1" "key2"