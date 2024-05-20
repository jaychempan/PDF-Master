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
├── pdf-structure.py # 执行PaddleOCR里面的ppstructure主函数，获得结构化的数据json
├── pos-process.py # 执行PaddleOCR后的后处理，针对难处理的数据，转换成markdown
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

8.添加公式转latex功能（Shanghai AI Lab：https://github.com/opendatalab/UniMERNet）

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

json格式写入（需要有顺序）
```
{
    "pdf_info": [
        {
            "preproc_blocks": [
                {
                    "type": "title",
                    "bbox": [
                        274,
                        152,
                        341,
                        171
                    ],
                    "lines": [
                        {
                            "bbox": [
                                272,
                                150,
                                342,
                                174
                            ],
                            "spans": [
                                {
                                    "bbox": [
                                        272,
                                        150,
                                        342,
                                        174
                                    ],
                                    "content": "后记",
                                    "type": "text"
                                }
                            ]
                        }
                    ]
                },
                {
                    "type": "text",
                    "bbox": [
                        84,
                        236,
                        508,
                        314
                    ],
                    "lines": [
                        {
                            "bbox": [
                                113,
                                236,
                                508,
                                251
                            ],
                            "spans": [
                                {
                                    "bbox": [
                                        113,
                                        236,
                                        505,
                                        251
                                    ],
                                    "content": "在飞机设计手册的编写过程中，航空界很多单位和人士，提供了",
                                    "type": "text"
                                }
                            ]
                        },
                        {
                            "bbox": [
                                84,
                                266,
                                508,
                                281
                            ],
                            "spans": [
                                {
                                    "bbox": [
                                        86,
                                        266,
                                        507,
                                        281
                                    ],
                                    "content": "不少宝贵的经验和资料，给予了热情的帮助和支持，对此表示由衷的",
                                    "type": "text"
                                }
                            ]
                        },
                        {
                            "bbox": [
                                84,
                                295,
                                119,
                                314
                            ],
                            "spans": [
                                {
                                    "bbox": [
                                        84,
                                        295,
                                        119,
                                        314
                                    ],
                                    "content": "感谢。",
                                    "type": "text"
                                }
                            ]
                        }
                    ]
                },
                {
                    "type": "text",
                    "bbox": [
                        84,
                        327,
                        508,
                        402
                    ],
                    "lines": [
                        {
                            "bbox": [
                                113,
                                327,
                                508,
                                343
                            ],
                            "spans": [
                                {
                                    "bbox": [
                                        115,
                                        327,
                                        507,
                                        343
                                    ],
                                    "content": "飞机设计手册的问世，是参与编写工作的几百名专家和领导团结",
                                    "type": "text"
                                }
                            ]
                        },
                        {
                            "bbox": [
                                84,
                                358,
                                508,
                                371
                            ],
                            "spans": [
                                {
                                    "bbox": [
                                        87,
                                        358,
                                        508,
                                        371
                                    ],
                                    "content": "协作、艰苦奋斗、辛勤劳动和无私奉献的结晶，对他们的敬业和奉献",
                                    "type": "text"
                                }
                            ]
                        },
                        {
                            "bbox": [
                                84,
                                387,
                                176,
                                402
                            ],
                            "spans": [
                                {
                                    "bbox": [
                                        86,
                                        387,
                                        176,
                                        402
                                    ],
                                    "content": "精神深表敬意。",
                                    "type": "text"
                                }
                            ]
                        }
                    ]
                },
                {
                    "type": "text",
                    "bbox": [
                        84,
                        417,
                        508,
                        522
                    ],
                    "lines": [
                        {
                            "bbox": [
                                113,
                                417,
                                508,
                                432
                            ],
                            "spans": [
                                {
                                    "bbox": [
                                        113,
                                        417,
                                        508,
                                        432
                                    ],
                                    "content": "这套系列手册的时候，十分遗憾的是，有的同志已经不能分享凝",
                                    "type": "text"
                                }
                            ]
                        },
                        {
                            "bbox": [
                                84,
                                447,
                                508,
                                462
                            ],
                            "spans": [
                                {
                                    "bbox": [
                                        86,
                                        447,
                                        508,
                                        462
                                    ],
                                    "content": "聚着自己心血的劳动成果；对为本系列手册的编写起了积级倡导作用",
                                    "type": "text"
                                }
                            ]
                        },
                        {
                            "bbox": [
                                84,
                                478,
                                508,
                                491
                            ],
                            "spans": [
                                {
                                    "bbox": [
                                        87,
                                        478,
                                        507,
                                        491
                                    ],
                                    "content": "的原总编委会主任、名誉主任委员何文治同志、原总编委会委员赵沛",
                                    "type": "text"
                                }
                            ]
                        },
                        {
                            "bbox": [
                                84,
                                507,
                                287,
                                522
                            ],
                            "spans": [
                                {
                                    "bbox": [
                                        86,
                                        507,
                                        287,
                                        522
                                    ],
                                    "content": "霖同志的离去，表示深切的怀念。",
                                    "type": "text"
                                }
                            ]
                        }
                    ]
                },
                {
                    "type": "title",
                    "bbox": [
                        327,
                        571,
                        489,
                        589
                    ],
                    "lines": [
                        {
                            "bbox": [
                                327,
                                574,
                                487,
                                589
                            ],
                            "spans": [
                                {
                                    "bbox": [
                                        327,
                                        574,
                                        487,
                                        589
                                    ],
                                    "content": "《飞机设计手册》总编委会",
                                    "type": "text"
                                }
                            ]
                        }
                    ]
                },
                {
                    "type": "text",
                    "bbox": [
                        379,
                        621,
                        489,
                        639
                    ],
                    "lines": [
                        {
                            "bbox": [
                                379,
                                621,
                                489,
                                639
                            ],
                            "spans": [
                                {
                                    "bbox": [
                                        379,
                                        621,
                                        489,
                                        639
                                    ],
                                    "content": "1995年7月20日",
                                    "type": "text"
                                }
                            ]
                        }
                    ]
                }
            ],
            "layout_bboxes": [
                {
                    "layout_bbox": [
                        0,
                        152,
                        595.0,
                        637
                    ],
                    "layout_label": "H",
                    "sub_layout": []
                }
            ],
            "page_idx": 801,
            "page_size": [
                595.0,
                842.0
            ],
            "_layout_tree": [
                {
                    "layout_bbox": [
                        0,
                        152,
                        595.0,
                        637
                    ],
                    "layout_label": "H",
                    "sub_layout": []
                }
            ],
            "images": [],
            "tables": [],
            "interline_equations": [],
            "discarded_blocks": [
                {
                    "bbox": [
                        278,
                        72,
                        334,
                        84
                    ]
                },
                {
                    "bbox": [
                        85,
                        72,
                        99,
                        81
                    ]
                }
            ],
            "para_blocks": [
                {
                    "type": "title",
                    "bbox": [
                        274,
                        152,
                        341,
                        171
                    ],
                    "lines": [
                        {
                            "bbox": [
                                272,
                                150,
                                342,
                                174
                            ],
                            "spans": [
                                {
                                    "bbox": [
                                        272,
                                        150,
                                        342,
                                        174
                                    ],
                                    "content": "后记",
                                    "type": "text"
                                }
                            ]
                        }
                    ]
                },
                {
                    "type": "text",
                    "bbox": [
                        84,
                        236,
                        508,
                        314
                    ],
                    "lines": [
                        {
                            "bbox": [
                                113,
                                236,
                                508,
                                251
                            ],
                            "spans": [
                                {
                                    "bbox": [
                                        113,
                                        236,
                                        505,
                                        251
                                    ],
                                    "content": "在飞机设计手册的编写过程中，航空界很多单位和人士，提供了",
                                    "type": "text"
                                }
                            ]
                        },
                        {
                            "bbox": [
                                84,
                                266,
                                508,
                                281
                            ],
                            "spans": [
                                {
                                    "bbox": [
                                        86,
                                        266,
                                        507,
                                        281
                                    ],
                                    "content": "不少宝贵的经验和资料，给予了热情的帮助和支持，对此表示由衷的",
                                    "type": "text"
                                }
                            ]
                        },
                        {
                            "bbox": [
                                84,
                                295,
                                119,
                                314
                            ],
                            "spans": [
                                {
                                    "bbox": [
                                        84,
                                        295,
                                        119,
                                        314
                                    ],
                                    "content": "感谢。",
                                    "type": "text"
                                }
                            ]
                        }
                    ]
                },
                {
                    "type": "text",
                    "bbox": [
                        84,
                        327,
                        508,
                        402
                    ],
                    "lines": [
                        {
                            "bbox": [
                                113,
                                327,
                                508,
                                343
                            ],
                            "spans": [
                                {
                                    "bbox": [
                                        115,
                                        327,
                                        507,
                                        343
                                    ],
                                    "content": "飞机设计手册的问世，是参与编写工作的几百名专家和领导团结",
                                    "type": "text"
                                }
                            ]
                        },
                        {
                            "bbox": [
                                84,
                                358,
                                508,
                                371
                            ],
                            "spans": [
                                {
                                    "bbox": [
                                        87,
                                        358,
                                        508,
                                        371
                                    ],
                                    "content": "协作、艰苦奋斗、辛勤劳动和无私奉献的结晶，对他们的敬业和奉献",
                                    "type": "text"
                                }
                            ]
                        },
                        {
                            "bbox": [
                                84,
                                387,
                                176,
                                402
                            ],
                            "spans": [
                                {
                                    "bbox": [
                                        86,
                                        387,
                                        176,
                                        402
                                    ],
                                    "content": "精神深表敬意。",
                                    "type": "text"
                                }
                            ]
                        }
                    ]
                },
                {
                    "type": "text",
                    "bbox": [
                        84,
                        417,
                        508,
                        522
                    ],
                    "lines": [
                        {
                            "bbox": [
                                113,
                                417,
                                508,
                                432
                            ],
                            "spans": [
                                {
                                    "bbox": [
                                        113,
                                        417,
                                        508,
                                        432
                                    ],
                                    "content": "这套系列手册的时候，十分遗憾的是，有的同志已经不能分享凝",
                                    "type": "text"
                                }
                            ]
                        },
                        {
                            "bbox": [
                                84,
                                447,
                                508,
                                462
                            ],
                            "spans": [
                                {
                                    "bbox": [
                                        86,
                                        447,
                                        508,
                                        462
                                    ],
                                    "content": "聚着自己心血的劳动成果；对为本系列手册的编写起了积级倡导作用",
                                    "type": "text"
                                }
                            ]
                        },
                        {
                            "bbox": [
                                84,
                                478,
                                508,
                                491
                            ],
                            "spans": [
                                {
                                    "bbox": [
                                        87,
                                        478,
                                        507,
                                        491
                                    ],
                                    "content": "的原总编委会主任、名誉主任委员何文治同志、原总编委会委员赵沛",
                                    "type": "text"
                                }
                            ]
                        },
                        {
                            "bbox": [
                                84,
                                507,
                                287,
                                522
                            ],
                            "spans": [
                                {
                                    "bbox": [
                                        86,
                                        507,
                                        287,
                                        522
                                    ],
                                    "content": "霖同志的离去，表示深切的怀念。",
                                    "type": "text"
                                }
                            ]
                        }
                    ]
                },
                {
                    "type": "title",
                    "bbox": [
                        327,
                        571,
                        489,
                        589
                    ],
                    "lines": [
                        {
                            "bbox": [
                                327,
                                574,
                                487,
                                589
                            ],
                            "spans": [
                                {
                                    "bbox": [
                                        327,
                                        574,
                                        487,
                                        589
                                    ],
                                    "content": "《飞机设计手册》总编委会",
                                    "type": "text"
                                }
                            ]
                        }
                    ]
                },
                {
                    "type": "text",
                    "bbox": [
                        379,
                        621,
                        489,
                        639
                    ],
                    "lines": [
                        {
                            "bbox": [
                                379,
                                621,
                                489,
                                639
                            ],
                            "spans": [
                                {
                                    "bbox": [
                                        379,
                                        621,
                                        489,
                                        639
                                    ],
                                    "content": "1995年7月20日",
                                    "type": "text"
                                }
                            ]
                        }
                    ]
                }
            ]
        }
    ],
    "_parse_type": "ocr"
}

```