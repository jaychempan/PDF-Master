# 大模型PDF文档解析-llm-pdf-parsing
## 项目介绍

主要针对LLM领域数据中的pdf解析，完成对批量PDF转换成LLM训练数据

PDF解析：进行版面识别得到结构化的json输出，然后对一些难处理的图片表格等进行后处理（生成markdown格式）

## 环境安装

环境安装可以参考：https://github.com/PaddlePaddle/PaddleOCR/blob/release/2.6/ppstructure/recovery/README_ch.md#2

```
conda create --name llmpro python=3.9
conda activate llmpro
python3 -m pip install "paddlepaddle-gpu" -i https://mirror.baidu.com/pypi/simple
cd llm-pdf-parsing/PaddleOCR
python3 -m pip install -r ppstructure/recovery/requirements.txt
# 安装 paddleocr，推荐使用2.6版本
pip3 install "paddleocr>=2.6"

# markdown转换需要
pip install markdownify

# 公式支持
pip install --upgrade unimernet
pip install transformers==4.40.0 # 需要确保transformers版本号
sudo apt-get install libmagickwand-dev
```
## 目录结构
以下是`llm-pdf-parsing`项目的目录结构说明
```
.
├── inference # 存放的是whl包文件中的基本权重，一般使用whl默认权重，如果有更好的权重可以放到可以替换成
│   ├── cls # 分类
│   ├── det # 检测
│   ├── layout # 布局
│   ├── rec # 重建
│   └── table # 表格
├── LICENSE
├── PaddleOCR  # PaddleOCR的主目录，里面包括各种函数，包括训练模型等
│   ├── applications
│   ├── benchmark
│   ├── configs
│   ├── deploy
│   ├── doc
│   ├── __init__.py
│   ├── LICENSE
│   ├── MANIFEST.in
│   ├── paddleocr.py
│   ├── ppocr
│   ├── PPOCRLabel
│   ├── ppstructure # 主要用来解析pdf版面的结构的代码
│   ├── README_ch.md
│   ├── README_en.md
│   ├── README.md
│   ├── requirements.txt
│   ├── setup.py
│   ├── StyleText
│   ├── test_tipc
│   ├── tools
│   └── train.sh
├── pdf-structure.py # 执行PaddleOCR里面的ppstructure主函数，获得结构化的数据json
├── pos-process.py # 执行PaddleOCR后的后处理，针对难处理的数据进行处理，获得后处理后的结构化数据json
├── json2markdown.py # 将结构化的json转换成markdown
├── markdown2jsonl.py # 将markdown转换成可训练的jsonl格式
├── README.md
└── data  # 数据
    ├── input
    └── output
```

## 使用

1.执行`pdf-structure.py`解析出pdf的结构，生成结构化的json文件

```
python pdf-structure.py
```
修改`args`参数列表即可
```
args = {
    '--image_dir': './shangfei/pdf',
    '--det_model_dir': './whl/det/ch/ch_PP-OCRv4_det_infer', 
    '--rec_model_dir': './whl/rec/ch/ch_PP-OCRv4_rec_infer',
    '--rec_char_dict_path': './PaddleOCR/ppocr/utils/ppocr_keys_v1.txt',
    '--table_model_dir': './whl/table/ch_ppstructure_mobile_v2.0_SLANet_infer',
    '--table_char_dict_path': './PaddleOCR/ppocr/utils/dict/table_structure_dict_ch.txt',
    '--layout_model_dir': './whl/layout/picodet_lcnet_x1_0_fgd_layout_cdla_infer',
    '--layout_dict_path': './PaddleOCR/ppocr/utils/dict/layout_dict/layout_cdla_dict.txt',
    '--vis_font_path': './ppocr_img/fonts/simfang.ttf',
    '--recovery': 'False',
    '--output': './shangfei/out',
    '--use_gpu': 'False'
}

or 

python ./PaddleOCR/ppstructure/predict_system_debug.py --image_dir ./shangfei/pdf/ --det_model_dir ./inference/det/ch/ch_PP-OCRv4_det_infer --rec_model_dir ./inference/rec/ch/ch_PP-OCRv4_rec_infer --rec_char_dict_path ./PaddleOCR/ppocr/utils/ppocr_keys_v1.txt --table_model_dir ./inference/table/ch_ppstructure_mobile_v2.0_SLANet_infer --table_char_dict_path ./PaddleOCR/ppocr/utils/dict/table_structure_dict_ch.txt --layout_model_dir ./inference/layout/picodet_lcnet_x1_0_fgd_layout_cdla_infer --layout_dict_path ./PaddleOCR/ppocr/utils/dict/layout_dict/layout_cdla_dict.txt --recovery True --output ./shangfei/out/ --use_pdf2docx_api False --mode structure --return_word_box False --use_gpu True

python ./PaddleOCR/ppstructure/predict_system.py --image_dir ./shangfei/pdf/ --det_model_dir ./inference/det/ch/ch_PP-OCRv4_det_infer --rec_model_dir ./inference/rec/ch/ch_PP-OCRv4_rec_infer --rec_char_dict_path ./PaddleOCR/ppocr/utils/ppocr_keys_v1.txt --table_model_dir ./inference/table/ch_ppstructure_mobile_v2.0_SLANet_infer --table_char_dict_path ./PaddleOCR/ppocr/utils/dict/table_structure_dict_ch.txt --layout_model_dir ./inference/layout/picodet_lcnet_x1_0_fgd_layout_cdla_infer --layout_dict_path ./PaddleOCR/ppocr/utils/dict/layout_dict/layout_cdla_dict.txt --recovery True --output ./shangfei/out/ --use_pdf2docx_api False --mode structure --return_word_box False --use_gpu True

# 可以使用参数进行多线程处理，但是模型并不并行，并不能本质加快模型处理速度，如果需要并行处理可以使用pdf-structure-mu.py代码进行多进程处理分片的pdf实现加速。

python ./PaddleOCR/ppstructure/predict_system.py --image_dir ./shangfei/pdf/ --det_model_dir ./inference/det/ch/ch_PP-OCRv4_det_infer --rec_model_dir ./inference/rec/ch/ch_PP-OCRv4_rec_infer --rec_char_dict_path ./PaddleOCR/ppocr/utils/ppocr_keys_v1.txt --table_model_dir ./inference/table/ch_ppstructure_mobile_v2.0_SLANet_infer --table_char_dict_path ./PaddleOCR/ppocr/utils/dict/table_structure_dict_ch.txt --layout_model_dir ./inference/layout/picodet_lcnet_x1_0_fgd_layout_cdla_infer --layout_dict_path ./PaddleOCR/ppocr/utils/dict/layout_dict/layout_cdla_dict.txt --recovery True --output ./shangfei/out/ --use_pdf2docx_api False --mode structure --return_word_box False --use_gpu True --use_mp True --total_process_num 8

# 单卡多进程版本

pdf-structure-sgpu.py 对指定目录下的所有pdf文件进行分片处理（可以按照大小进行均等划分）,会多次调用predict_system函数

# 多卡多进程版本（充分利用显卡资源的方式）

python pdf-structure-mgpu.py --input_directory /mnt/petrelfs/panjiancheng/llm-pdf-parsing/shangfei/20240617_comac_pdfs_inter --output_directory /mnt/petrelfs/panjiancheng/llm-pdf-parsing/shangfei/20240617_comac_pdfs_inter_process --num_processes 2
```
2.执行`pos-process.py`对公式，图像，表格进行后处理，更新前一步骤生成的json文件（处理指定目录下的所有子目录中的json文件）
```
python pos-process.py --input_directory ./shangfei/out/structure

# 单卡多进程版本，会多次调用pos-process-single函数(处理指定目录下的json文件)

python pos-process-sgpu.py --input_directory shangfei/out/structure  --config_path UniMERNet/configs/demo.yaml --num_processes 2

# 多卡多进程版本，会多次调用pos-process-single函数(处理指定目录下的json文件)

python pos-process-mgpu.py --input_directory /mnt/petrelfs/panjiancheng/llm-pdf-parsing/shangfei/20240617_comac_pdfs_inter_process/structure --config_path ./models/unimernet/demo.yaml --num_processes 2

```

3.执行`json2markdown.py`将json文件转换成markdown格式

```
python json2markdown.py --input_directory /mnt/petrelfs/panjiancheng/llm-pdf-parsing/shangfei/20240617_comac_pdfs_inter_process/structure
```

4.执行`markdown2jsonl.py`将markdown转换成jsonl格式
```
python markdown2jsonl.py --input_directory /mnt/petrelfs/panjiancheng/llm-pdf-parsing/shangfei/20240617_comac_pdfs_inter_process/structure
```