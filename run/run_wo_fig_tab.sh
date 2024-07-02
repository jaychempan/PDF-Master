#!/bin/bash

# 处理航空书籍

# 设置目录变量
input_directory="/mnt/petrelfs/shengkejun/project_data/COMAC_pretrain_data/comac_pdfs/input-pdfs/20240621_aircraft_design_manual/"
output_directory="/mnt/petrelfs/panjiancheng/llm-pdf-parsing/data/output/20240621_aircraft_design_manual/"
config_path="../weights/unimernet/demo.yaml"

# 进入pipline目录
cd pipline

# 运行pdf-structure-mgpu.py
python pdf-structure-mgpu.py --input_directory "$input_directory" --output_directory "$output_directory" --num_processes 2

# 运行pos-process-mgpu.py
python pos-process-mgpu.py --input_directory "${output_directory}structure" --config_path "$config_path" --num_processes 2

# 运行json2markdown.py
python json2markdown.py --input_directory "${output_directory}structure"