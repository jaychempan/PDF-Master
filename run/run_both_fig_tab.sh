#!/bin/bash

# 设置目录变量
input_directory="../data/input/16pdfs/"
output_directory="../data/output/16pdfs_process/"
config_path="../weights/unimernet/demo.yaml"
num_processes = 2

# 进入pipline目录
cd pipline

# 运行pdf-structure-mgpu.py
python pdf-structure-mgpu.py --input_directory "$input_directory" --output_directory "$output_directory" --num_processes "$num_processes"

# 运行pos-process-mgpu.py
python pos-process-mgpu.py --input_directory "${output_directory}structure" --config_path "$config_path" --num_processes "$num_processes"

# 运行json2markdown.py
python json2markdown.py --input_directory "${output_directory}structure"

# 运行markdown2jsonl.py
python markdown2jsonl.py --input_directory "${output_directory}structure"

# 运行pos-process-figure-mgpu.py, pos-process-table-mgpu.py, update-ppstru-json.py
python pos-process-figure-mgpu.py --input_directory "${output_directory}structure" --gpus 0,1,2,3,5,6,7 --model_path ../../HFs/InternVL-Chat-V1-5
python pos-process-table-mgpu.py --input_directory "${output_directory}structure" --gpus 0,1,2,3,5,6,7 --model_path ../../HFs/InternVL-Chat-V1-5
python update-ppstru-json.py --input_directory "${output_directory}structure" --process both

# 运行clean-jsonl.py
python clean-jsonl.py --input_file "${output_directory}*_process.jsonl" --delete_strs "key1" "key2"