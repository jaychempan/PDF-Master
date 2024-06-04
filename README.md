# 大模型PDF文档解析-llm-pdf-parsing
## 项目介绍

主要针对LLM领域数据中的pdf解析，完成对批量PDF转换成LLM训练数据

PDF解析：进行版面识别得到结构化的json输出，然后对一些难处理的图片表格等进行后处理（生成markdown格式）


> 项目版本提交命令

```
git add .
git commit -m 'init llm-pdf-parsing'
git push origin main
可以简化成：
git commit -am 'init llm-pdf-parsing'
git push origin main

# 提交到其他分支
git push origin XXX
```
或者参考更多git相关的命令：https://gist.github.com/jaychempan/222113eba9c109238766a3906dc6b8f7

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
├── README.md
└── shangfei  # 商飞数据例子
    ├── output
    └── pdf
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

python ./PaddleOCR/ppstructure/predict_system.py --image_dir ./shangfei/pdf/ --det_model_dir ./inference/det/ch/ch_PP-OCRv4_det_infer --rec_model_dir ./inference/rec/ch/ch_PP-OCRv4_rec_infer --rec_char_dict_path ./PaddleOCR/ppocr/utils/ppocr_keys_v1.txt --table_model_dir ./inference/table/ch_ppstructure_mobile_v2.0_SLANet_infer --table_char_dict_path ./PaddleOCR/ppocr/utils/dict/table_structure_dict_ch.txt --layout_model_dir ./inference/layout/picodet_lcnet_x1_0_fgd_layout_cdla_infer --layout_dict_path ./PaddleOCR/ppocr/utils/dict/layout_dict/layout_cdla_dict.txt --recovery True --output ./shangfei/out/ --use_pdf2docx_api False --mode structure --return_word_box False --use_gpu True

# 可以使用参数进行多线程处理，但是模型并不并行，并不能本质加快模型处理速度，如果需要并行处理可以使用pdf-structure-mu.py代码进行多进程处理分片的pdf实现加速。

python ./PaddleOCR/ppstructure/predict_system.py --image_dir ./shangfei/pdf/ --det_model_dir ./inference/det/ch/ch_PP-OCRv4_det_infer --rec_model_dir ./inference/rec/ch/ch_PP-OCRv4_rec_infer --rec_char_dict_path ./PaddleOCR/ppocr/utils/ppocr_keys_v1.txt --table_model_dir ./inference/table/ch_ppstructure_mobile_v2.0_SLANet_infer --table_char_dict_path ./PaddleOCR/ppocr/utils/dict/table_structure_dict_ch.txt --layout_model_dir ./inference/layout/picodet_lcnet_x1_0_fgd_layout_cdla_infer --layout_dict_path ./PaddleOCR/ppocr/utils/dict/layout_dict/layout_cdla_dict.txt --recovery True --output ./shangfei/out/ --use_pdf2docx_api False --mode structure --return_word_box False --use_gpu True --use_mp True --total_process_num 8

# 单卡多进程版本

pdf-structure-sgpu.py 对指定目录下的所有pdf文件进行分片处理（可以按照大小进行均等划分）,会多次调用predict_system函数

# 多卡多进程版本（充分利用显卡资源的方式）

python pdf-structure-mgpu.py --input_directory ./shangfei/more_pdfs_x8_n6 --num_processes 6
or,
python pdf-structure-mgpu.py --input_directory ./shangfei/more_pdfs_x8_n7 --num_processes 7
```
2.执行`pos-process.py`对公式，图像，表格进行后处理，更新前一步骤生成的json文件（处理指定目录下的所有子目录中的json文件）
```
python pos-process.py --input_directory ./shangfei/out/structure

# 单卡多进程版本，会多次调用pos-process-single函数(处理指定目录下的json文件)

python pos-process-sgpu.py --input_directory ./shangfei/more_outputs_x16_n6/structure --config_path ./models/unimernet/demo.yaml --num_processes 2

# 多卡多进程版本，会多次调用pos-process-single函数(处理指定目录下的json文件)

python pos-process-mgpu.py --input_directory ./shangfei/more_outputs_x16_n6/structure --config_path ./models/unimernet/demo.yaml --num_processes 12

```

3.执行`json2markdown.py`将json文件转换成markdown格式

```
python json2markdown.py --directory_path ./shangfei/out/structure
```

## 任务

1.（完成）输出格式问题（从txt生成对应的markdown，修改`llm-pdf-parsing/PaddleOCR/ppstructure/predict_system.py`文件）

> 实现思路：将输出的dict格式直接转换，但需要思考具体的类别（例如公式，表格，图片如果进行转换）

2.（完成）页面元素顺序问题（具体到每一个页面的顺序和双栏的顺序）

> 实现思路：单栏的可以直接按照bbox的y坐标大小进行排序，针对双栏需要先对x进行再对y进行排序

`llm-pdf-parsing/PaddleOCR/ppstructure/recovery/recovery_to_doc.py`中有关于单双栏的识别
```
flag = 1
    for i, region in enumerate(res):
        if len(region["res"]) == 0:
            continue
        img_idx = region["img_idx"]
        if flag == 2 and region["layout"] == "single":
            section = doc.add_section(WD_SECTION.CONTINUOUS)
            section._sectPr.xpath("./w:cols")[0].set(qn("w:num"), "1")
            flag = 1
        elif flag == 1 and region["layout"] == "double":
            section = doc.add_section(WD_SECTION.CONTINUOUS)
            section._sectPr.xpath("./w:cols")[0].set(qn("w:num"), "2")
            flag = 2
```

3.公式识别问题，转换成latex格式

> 实现思路: 提升准确性，行间公式和行内公式的提取，对于符号角标（例如右下角和右上角等的符号，可以考虑用一些开源符号）


基于书生自研开源公式提取

4.pdf解析精度问题

> 调用pdf2docx的api进行识别 --use_pdf2docx_api

但是会有双栏格式问题

5.效率问题

> 版面分析+重建

CPU上进行处理：5页PDF，时间: 00:00:50
GPUs上进行待测：暂时不处理

为了提升效率，可以取消一些中间结果的报错（show等）

6.内容分段（主要指的是对一个识别框内的文本进行分段落）

> 实现思路：对得到的文本`res`结果进行再次处理，使得同意段落的句子放在以及，划分中段落级别为一条`res`

将内容排序后通过持续更新的方法来逐条进行分段

一种思路是通过相邻region bbox变化是都操作前面的阈值来实现，但是这种方法测试了并不是很好，因为ocr位置识别就存在误差，而且需要设置阈值

另一种思路是通过段落缩进来进行判断,实现效果不行

再另一种还是通过对基于固定规则的分段方式，（效果可以，但是需要对特殊情况再设置规则）


7.（完成）过滤页面中无用成分（去除页眉，页脚，图片标题和表格标题与注解，保证正文流畅）

目前的方法是保存了res后进行的生成`res`后markdown生成前的的过滤，进一步提升效率可以考虑在保存`res`前就把不需要的进行过滤，可以提升速度，但是如果后面需要这部分信息就会丢失。

8.添加公式转latex功能（基座公式转换模型：https://github.com/opendatalab/UniMERNet）

环境配置：
```
git clone https://github.com/opendatalab/UniMERNet.git

# Download git-lfs by following the steps based on your operating system.
curl -s https://packagecloud.io/install/repositories/github/git-lfs/script.deb.sh | sudo bash
sudo apt-get install git-lfs

git lfs install
git clone https://huggingface.co/wanderkid/unimernet

sudo apt-get install libmagickwand-dev
```

9.在OCR框架后面再加入后处理阶段，针对一些不能直接转换的表格，图片和公式进行后处理

实现，如果直接转换成markdown读取需要花费大量的时间，所以还是先转换成结构化的json格式，后续可以直接调用针对具体类型进行处理，加快处理流程

<details>
  <summary>展开看具体json格式数据结构（参考基座）</summary>

```
# 主要针对pdf进行解析
pdf_info = {
    "pdf_info": [page_info1, page_info2, ...],
    "_parse_type": "ocr"
}
# 每个页面中获取的信息
page_info = {
        "preproc_blocks": [], # 也是按照顺序（包含所有需要的要素）
        # "layout_bboxes": [], # 感觉不需要
        "page_idx": page_idx, # 需要更新
        # "page_size": [595.0, 842.0], # 不重要暂时不处理
        # "_layout_tree": [], # 好像和layout_bboxes没区别
        "images": [], # 图像包括图像标题放这里
        "tables": [], # 表格包括表格标题放这里
        "interline_equations": [], # 行间公式放在这里
        "discarded_blocks": [], # 需要丢弃的放这里
        "para_blocks": [] # 按照段落顺序，可以放置preproc_blocks后处理格式
    }
################图像和图像标题处理###############################
# images 结构解析(三级结构)
{
    "type": "image",
    "bbox": [],
    "blocks": [] # 其中包含了image_body 和 image_caption
}

## image_body 和 image_caption具体结构都为
{
    "bbox": [],
    "type": "image_body", # or "image_caption"
    "lines": []
}

### lines内包含
#### image_body
{
    "bbox": [],
    "spans": [
        {
            "bbox": [],
            "type": "image",
            "image_path": "XXX.jpg"
        }
    ]
}
#### image_caption
{
    "bbox": [],
    "spans": [
        {
            "bbox": [],
            "content": "XXXX",
            "type": "inline_equation" # or "text"
        }
    ]
}

################表格和表格标题处理###############################
（同上格式）

################文本和文本标题处理###############################
# text/title
{
    "type": "text", # or "title"
    "bbox": [],
    "lines": [] # 其中包含了image_body 和 image_caption
}

lines 内部包含：
{
    "bbox": [],
    "spans": [
        {
            "bbox": [],
            "content": "XXX",
            "type": "inline_equation" # or "text"
        }
    ]
}
################公式处理###############################
# interline_equations
## 
{
    "type": "interline_equation", 
    "bbox": [],
    "lines": [] # 其中包含了image_body 和 image_caption
}

lines 内部包含：
{
    "bbox": [],
    "spans": [
        {
            "bbox": [],
            "content": "XXX",
            "type": "interline_equation" $ 是转换成latex格式的，所以需要进行后处理
        }
    ]
}
```
</details>

10.（基本完成）实现结构化json拼装markdown-json2markdown.py
    后续对于行内公式和更进一步的图像表格的latex转换后需要进一步修改

11.实现pos-process

```
## json全读取并进行重新写入，
# 功能1：实现公式到latex格式的转换，修改对应json中的位置
# 功能2：实现对表格到latex格式转换，修改对应json中的位置
# 功能3：实现对图片到语义的格式转换，修改对应json中的位置.
```
已经实现功能1

12.效率评估(不包括模型加载时间)

并行加速原理，根据文档大小进行排序或者直接N等份切分，尽可能分成大小相等的N份进行多进程处理。
处理总共153 MB大小的pdf文件集可以获得2.44 MB大小的markdown文件（单卡4090 24G）

|     程序                                     |     运行时间（N=1）    |     运行时间（N=2）                       |     运行时间（N=8）    |     运行时间（CPU）    |
|----------------------------------------------|------------------------|-------------------------------------------|------------------------|------------------------|
|     pdf-structure.py     （按照大小分配）    |            -           |     约16   min    |            -           |            -           |
|     pos-process.py（只包括行间公式插入）     |            -           |                      -                    |             约18 min           |            -           |
|     json2markdown.py                         |            -           |                      -                    |            -           |           约1s         |

处理总共153 MB X4 大小的pdf文件集可以获得 2.44X4 MB大小的markdown文件（单卡A100 80G）

|     程序                                     |     运行时间（N=1）    |     运行时间（N=8）                       |     运行时间（N=32）    |     运行时间（CPU）    |
|----------------------------------------------|------------------------|-------------------------------------------|------------------------|------------------------|
|     pdf-structure.py     （按照大小分配）    |            -           |     约28   min  |            -           |            -           |
|     pos-process.py（只包括行间公式插入）     |            -           |                      -                    |           约15   min             |            -           |
|     json2markdown.py                         |            -           |                      -                    |            -           |           约2s         |

处理总共153 MB X8 大小的pdf文件集可以获得 2.44X8 MB大小的markdown文件（8卡A100 80G）

|     程序                                     |     运行时间（N=1）    |     运行时间（N=48）                       |     运行时间（N=64）    |     运行时间（CPU）    |
|----------------------------------------------|------------------------|-------------------------------------------|------------------------|------------------------|
|     pdf-structure.py     （按照大小分配）    |            -           |     约14min  |            -           |            -           |
|     pos-process.py（只包括行间公式插入）     |            -           |                      -                    |           约27   min             |            -           |
|     json2markdown.py                         |            -           |                      -                    |            -           |           约5s         |

处理总共153 MB X16 大小的pdf文件集可以获得 2.44X16 MB大小的markdown文件（8卡A100 80G）

|     程序                                     |     运行时间（N=1）    |     运行时间（N=48）                       |     运行时间（N=64）    |     运行时间（CPU）    |
|----------------------------------------------|------------------------|-------------------------------------------|------------------------|------------------------|
|     pdf-structure.py     （按照大小分配）    |            -           |     约22min  |            -           |            -           |
|     pos-process.py（只包括行间公式插入）     |            -           |                      -                    |           约XX   min             |            -           |
|     json2markdown.py                         |            -           |                      -                    |            -           |           约5s         |

13.版面分析模型训练

一种方案重新训练一个高精度的可以识别出公式的layout模型（但是需要重新训练）

https://github.com/PaddlePaddle/PaddleOCR/blob/release/2.6/ppstructure/layout/README_ch.md

另一种方案是采用现在开源项目中涉及到行间公式是被的模块进行嵌入到流程里面

14.（已完成）优化pos-process不同进程的处理数据划分，尽可能让所有进程处理等量的数据

根据公式目录下的文件数量进行划分，尽可能每个进程的处理相等数量的公式，提高进程利用率，实现原理，可以在划分进程任务前对所有子目录（每个目录代表一个pdf文件）通过这种方式来实现对公式的读取。

15.（待做）多模态大模型处理图像数据的方式

搭建环境参考[[InterVL]](https://github.com/OpenGVLab/InternVL/tree/main)内的方式
```
# local 本地运行调用卡进行计算
python internvl-infer.py --model_path ./models/InternVL-Chat-V1-5 --root_directory /path/to/subdirs/ --csv_save_path 

# lmdeploy 构建仿openai进行处理

python internvl-infer-openai.py --api_key XXX --base_url XXX --model_name "internvl-internlm2" --input_dir XXX --output_dir XXX/csv
```

14.时间以及资源测试 (处理总共153X8 MB 大小的pdf文件集可以获得 2.44X8 MB大小的markdown文件（8卡A100 80G）)

`srun -p app-rag-agent --nodes=1  --gres=gpu:8 --ntasks-per-node=8 --pty bash -i`

```
python pdf-structure-mgpu.py --input_directory ./shangfei/pdfs_x8_n6 --num_processes 6
python pos-process-mgpu.py --input_directory ./shangfei/outputs_x8_n6/structure --config_path ./models/unimernet/demo.yaml --num_processes 12
```

|     程序                                     |     运行时间（N=1）    |     运行时间（N=48）                       |     运行时间（N=96）    |     运行时间（CPU）    |
|----------------------------------------------|------------------------|-------------------------------------------|------------------------|------------------------|
|     pdf-structure.py    |            -           |     00:11:28  |            -           |            -           |
|     pos-process.py     |            -           |                      -                    |           约XX   min             |            -           |
|     json2markdown.py                         |            -           |                      -                    |            -           |           约5s         |




## 感谢

https://github.com/opendatalab/UniMERNet

https://github.com/PaddlePaddle/PaddleOCR/tree/main

https://github.com/PaddlePaddle/PaddleOCR/blob/main/ppstructure/README_ch.md

https://github.com/OpenGVLab/InternVL/tree/main

## 版权

This project is released under the [MIT license](LICENSE). Parts of this project contain code and models from other sources, which are subject to their respective licenses.