# llm-pdf-parsing
## 项目介绍

主要针对LLM领域数据中的pdf解析，完成对批量PDF转换成LLM训练数据

1. PDF版面解析（正在进行）

    进行版面识别，然后格式化输出（生成结构化的数据，例如markdown）

2. 数据清洗流程（暂未更新）

    对结构化的的输出进行清洗流程

> 项目版本提交命令
```
git add .
git commit -m 'init llm-pdf-parsing'
git push origin main
可以简化成：
git commit -am 'init llm-pdf-parsing'
git push origin main
# 分支管理可以提交到其他分支
git push origin XXX
```
或者参考更多git相关的命令：https://gist.github.com/jaychempan/222113eba9c109238766a3906dc6b8f7
## 环境安装

环境安装可以参考：https://github.com/PaddlePaddle/PaddleOCR/blob/release/2.6/ppstructure/recovery/README_ch.md#2

```
TODO:再次安装,可以写一个具体教程
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
│   ├── ppstructure # 主要用来解析pdf结构的代码
│   ├── README_ch.md
│   ├── README_en.md
│   ├── README.md
│   ├── requirements.txt
│   ├── setup.py
│   ├── StyleText
│   ├── test_tipc
│   ├── tools
│   └── train.sh
├── pdf-structure.py # 执行PaddleOCR里面的ppstructure主函数
├── ppocr_img # 官方给的一些PaddleOCR的测试例子，也包括字体等
│   ├── ch
│   ├── fonts
│   ├── imgs
│   ├── imgs_en
│   ├── imgs_words
│   └── table
├── README.md
└── shangfei  # 商飞数据例子
    ├── shangfei_pdf
    ├── shangfei_pdf_output
    ├── shangfei_pdf_output_single
    └── shangfei_pdf_single
```

## 使用

执行`pdf-structure.py`

```
python pdf-structure.py
```
修改`args`参数列表即可
```
args = {
    '--image_dir': '/home/panjiancheng/llm-pdf-parsing/shangfei/shangfei_pdf_single',
    '--det_model_dir': './whl/det/ch/ch_PP-OCRv4_det_infer', 
    '--rec_model_dir': './whl/rec/ch/ch_PP-OCRv4_rec_infer',
    '--rec_char_dict_path': './PaddleOCR/ppocr/utils/ppocr_keys_v1.txt',
    '--table_model_dir': './whl/table/ch_ppstructure_mobile_v2.0_SLANet_infer',
    '--table_char_dict_path': './PaddleOCR/ppocr/utils/dict/table_structure_dict_ch.txt',
    '--layout_model_dir': './whl/layout/picodet_lcnet_x1_0_fgd_layout_cdla_infer',
    '--layout_dict_path': './PaddleOCR/ppocr/utils/dict/layout_dict/layout_cdla_dict.txt',
    '--vis_font_path': './ppocr_img/fonts/simfang.ttf',
    '--recovery': 'False',
    '--output': '/home/panjiancheng/llm-pdf-parsing/shangfei/shangfei_pdf_output_single',
    '--use_gpu': 'False'
}
```

## 任务

1.输出格式问题（从txt生成对应的markdown，修改`llm-pdf-parsing/PaddleOCR/ppstructure/predict_system.py`文件）

> 实现思路：将输出的dict格式直接转换，但需要思考具体的类别（例如公式，表格，图片如果进行转换）

2.页面元素顺序问题（具体到每一个页面的顺序和双栏的顺序）

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

4.pdf解析精度问题

> 调用pdf2docx的api进行识别 --use_pdf2docx_api

但是会有双栏格式问题
5.效率问题

> 版面分析+重建

CPU上进行处理：5页PDF，时间: 00:00:50
GPUs上进行待测：