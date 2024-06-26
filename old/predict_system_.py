# Copyright (c) 2020 PaddlePaddle Authors. All Rights Reserved.
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.
from tqdm import tqdm
import os
import sys
import subprocess

__dir__ = os.path.dirname(os.path.abspath(__file__))
sys.path.append(__dir__)
sys.path.insert(0, os.path.abspath(os.path.join(__dir__, "../")))

os.environ["FLAGS_allocator_strategy"] = "auto_growth"
import cv2
import json
import numpy as np
import time
import logging
from copy import deepcopy

from paddle.utils import try_import
from ppocr.utils.utility import get_image_file_list, check_and_read
from ppocr.utils.logging import get_logger
from ppocr.utils.visual import draw_ser_results, draw_re_results
from tools.infer.predict_system import TextSystem
from ppstructure.layout.predict_layout import LayoutPredictor
from ppstructure.table.predict_table import TableSystem, to_excel
from ppstructure.utility import parse_args, draw_structure_result, cal_ocr_word_box

logger = get_logger()

class StructureSystem(object):
    def __init__(self, args):
        self.mode = args.mode
        self.recovery = args.recovery

        self.image_orientation_predictor = None
        if args.image_orientation:
            import paddleclas

            self.image_orientation_predictor = paddleclas.PaddleClas(
                model_name="text_image_orientation"
            )
        # 输出pdf的结构
        if self.mode == "structure":
            if not args.show_log:
                logger.setLevel(logging.INFO)
            if args.layout == False and args.ocr == True:
                args.ocr = False
                logger.warning(
                    "When args.layout is false, args.ocr is automatically set to false"
                )
            # init model
            self.layout_predictor = None # 重点
            self.text_system = None # 重点
            self.table_system = None
            if args.layout:
                self.layout_predictor = LayoutPredictor(args)
                if args.ocr:
                    self.text_system = TextSystem(args)
            if args.table: #不用表格解析，加快速度，因为表格是直接保存图片的方式
                if self.text_system is not None:
                    
                    self.table_system = TableSystem(
                        args,
                        self.text_system.text_detector,
                        self.text_system.text_recognizer,
                    )
                else:
                    self.table_system = TableSystem(args)
        # 知识信息抽取
        elif self.mode == "kie":
            from ppstructure.kie.predict_kie_token_ser_re import SerRePredictor

            self.kie_predictor = SerRePredictor(args)

        self.return_word_box = args.return_word_box

    def __call__(self, img, return_ocr_result_in_table=False, img_idx=0):
        time_dict = {
            "image_orientation": 0,
            "layout": 0,
            "table": 0,
            "table_match": 0,
            "det": 0,
            "rec": 0,
            "kie": 0,
            "all": 0,
        }
        start = time.time()
        # 用于确定图像的方向并相应地旋转图像，以便图像正向朝上
        if self.image_orientation_predictor is not None:
            tic = time.time()
            cls_result = self.image_orientation_predictor.predict(input_data=img)
            cls_res = next(cls_result)
            angle = cls_res[0]["label_names"][0]
            cv_rotate_code = {
                "90": cv2.ROTATE_90_COUNTERCLOCKWISE,
                "180": cv2.ROTATE_180,
                "270": cv2.ROTATE_90_CLOCKWISE,
            }
            if angle in cv_rotate_code:
                img = cv2.rotate(img, cv_rotate_code[angle])
            toc = time.time()
            time_dict["image_orientation"] = toc - tic

        if self.mode == "structure":
            ori_im = img.copy()
            if self.layout_predictor is not None: # 布局识别
                layout_res, elapse = self.layout_predictor(img)
                # print(layout_res)

                time_dict["layout"] += elapse

            else: # 如果不启用布局识别，就是直接使用表格识别
                h, w = ori_im.shape[:2]
                layout_res = [dict(bbox=None, label="table")]

            # As reported in issues such as #10270 and #11665, the old
            # implementation, which recognizes texts from the layout regions,
            # has problems with OCR recognition accuracy.
            #
            # To enhance the OCR recognition accuracy, we implement a patch fix
            # that first use text_system to detect and recognize all text information
            # and then filter out relevant texts according to the layout regions.
            text_res = None
            if self.text_system is not None:
                text_res, ocr_time_dict = self._predict_text(img)
                time_dict["det"] += ocr_time_dict["det"]
                time_dict["rec"] += ocr_time_dict["rec"]

            res_list = []
            for region in layout_res:
                res = ""
                if region["bbox"] is not None:
                    x1, y1, x2, y2 = region["bbox"]
                    x1, y1, x2, y2 = int(x1), int(y1), int(x2), int(y2)
                    roi_img = ori_im[y1:y2, x1:x2, :]
                else:
                    x1, y1, x2, y2 = 0, 0, w, h
                    roi_img = ori_im
                bbox = [x1, y1, x2, y2]

                # 识别表格
                if region["label"] == "table":
                    if self.table_system is not None:
                        res, table_time_dict = self.table_system(
                            roi_img, return_ocr_result_in_table
                        )
                        time_dict["table"] += table_time_dict["table"]
                        time_dict["table_match"] += table_time_dict["match"]
                        time_dict["det"] += table_time_dict["det"]
                        time_dict["rec"] += table_time_dict["rec"]
                else: #除了表格，都要进行过滤，因为主要为文本
                    if text_res is not None:
                        # Filter the text results whose regions intersect with the current layout bbox.
                        res = self._filter_text_res(text_res, bbox)
                
                # 这里初步对header和footer进行过滤
                if region["label"] != "header" and region["label"] != "footer" and region["label"] != "reference":
                    res_list.append(
                        {
                            "type": region["label"].lower(), # 识别区域的类别
                            "bbox": bbox, # bbox框住的图片
                            "img": roi_img, # 对应的文字识别的小块图片
                            "res": res, # 这个是识别的文字
                            "img_idx": img_idx, # 这个是跟页码相关的例如3表示第四页
                        }
                )
                    
            end = time.time()
            time_dict["all"] = end - start
            return res_list, time_dict

        elif self.mode == "kie":
            re_res, elapse = self.kie_predictor(img)
            time_dict["kie"] = elapse
            time_dict["all"] = elapse
            return re_res[0], time_dict

        return None, None

    def _predict_text(self, img):
        filter_boxes, filter_rec_res, ocr_time_dict = self.text_system(img)

        # remove style char,
        # when using the recognition model trained on the PubtabNet dataset,
        # it will recognize the text format in the table, such as <b>
        style_token = [
            "<strike>",
            "<strike>",
            "<sup>",
            "</sub>",
            "<b>",
            "</b>",
            "<sub>",
            "</sup>",
            "<overline>",
            "</overline>",
            "<underline>",
            "</underline>",
            "<i>",
            "</i>",
        ]
        res = []
        for box, rec_res in zip(filter_boxes, filter_rec_res):
            rec_str, rec_conf = rec_res[0], rec_res[1]
            for token in style_token:
                if token in rec_str:
                    rec_str = rec_str.replace(token, "")
            if self.return_word_box:
                word_box_content_list, word_box_list = cal_ocr_word_box(
                    rec_str, box, rec_res[2]
                )
                res.append(
                    {
                        "text": rec_str,
                        "confidence": float(rec_conf),
                        "text_region": box.tolist(),
                        "text_word": word_box_content_list,
                        "text_word_region": word_box_list,
                    }
                )
            else: # 一般走这个，不需要具体到单词的word
                res.append(
                    {
                        "text": rec_str,
                        "confidence": float(rec_conf),
                        "text_region": box.tolist(),
                    }
                )
        return res, ocr_time_dict

    def _filter_text_res(self, text_res, bbox):
        res = []
        for r in text_res:
            box = r["text_region"]
            rect = box[0][0], box[0][1], box[2][0], box[2][1]
            if self._has_intersection(bbox, rect):
                res.append(r)
        return res

    def _has_intersection(self, rect1, rect2):
        x_min1, y_min1, x_max1, y_max1 = rect1
        x_min2, y_min2, x_max2, y_max2 = rect2
        if x_min1 > x_max2 or x_max1 < x_min2:
            return False
        if y_min1 > y_max2 or y_max1 < y_min2:
            return False
        return True


def save_structure_res(res, save_folder, img_name, img_idx=0):
    excel_save_folder = os.path.join(save_folder, img_name)
    os.makedirs(excel_save_folder, exist_ok=True)
    # 增加子目录存放不同类别
    os.makedirs(excel_save_folder + '/tables/', exist_ok=True)
    os.makedirs(excel_save_folder + '/figures/', exist_ok=True)
    os.makedirs(excel_save_folder + '/equations/', exist_ok=True)
    os.makedirs(excel_save_folder + '/res/', exist_ok=True)
    res_cp = deepcopy(res)
    # save res
    with open(
        os.path.join(excel_save_folder, "res/res_{}.txt".format(img_idx)),
        "w",
        encoding="utf8",
    ) as f:
        for region in res_cp:
            roi_img = region.pop("img") # 将图片信息删除后的dict信息
            f.write("{}\n".format(json.dumps(region)))


            if region["type"].lower() == "table":
                # img_path = os.path.join(
                #     excel_save_folder, "tables/{}_{}.jpg".format(img_idx, region["bbox"])
                # )
                cv2.imwrite(os.path.join(
                    excel_save_folder, "tables/{}_{}.jpg".format(img_idx, region["bbox"])
                ), roi_img)

            elif region["type"].lower() == "figure":
                # img_path = os.path.join(
                #     # excel_save_folder, "figures/{}_{}.jpg".format(region["bbox"], img_idx)
                #     excel_save_folder, "figures/{}_{}.jpg".format(img_idx, region["bbox"])
                # )
                cv2.imwrite(os.path.join(
                    # excel_save_folder, "figures/{}_{}.jpg".format(region["bbox"], img_idx)
                    excel_save_folder, "figures/{}_{}.jpg".format(img_idx, region["bbox"])
                ), roi_img)
            elif region["type"].lower() == "equation":
                # img_path = os.path.join(
                #     # excel_save_folder, "figures/{}_{}.jpg".format(region["bbox"], img_idx)
                #     excel_save_folder, "equations/{}_{}.jpg".format(img_idx, region["bbox"])
                # )
                cv2.imwrite(os.path.join(
                    # excel_save_folder, "figures/{}_{}.jpg".format(region["bbox"], img_idx)
                    excel_save_folder, "equations/{}_{}.jpg".format(img_idx, region["bbox"])
                ), roi_img)


def main(args):
    image_file_list = get_image_file_list(args.image_dir)
    image_file_list = image_file_list
    image_file_list = image_file_list[args.process_id :: args.total_process_num]

    if not args.use_pdf2docx_api:
        structure_sys = StructureSystem(args)
        save_folder = os.path.join(args.output, structure_sys.mode)
        os.makedirs(save_folder, exist_ok=True)
    img_num = len(image_file_list)

    # for i, image_file in enumerate(image_file_list):
    #     # logger.info("[{}/{}] {}".format(i, img_num, image_file))
    #     img, flag_gif, flag_pdf = check_and_read(image_file)
    #     img_name = os.path.basename(image_file).split(".")[0]

    # 使用 tqdm 进行进度可视化
    for i, image_file in enumerate(tqdm(image_file_list, desc="Processing Images", position=0, leave=True)):
        img, flag_gif, flag_pdf = check_and_read(image_file)
        img_name = os.path.basename(image_file).split(".")[0]

        # 在处理pdf前进行判断，如果最终需要的json文件存在则跳过（表明已经处理过了）
        json_path = os.path.join(os.path.join(save_folder, img_name), f"{img_name}_ocr.json")
        if os.path.exists(json_path):
            # print(f"json文件存在,跳过处理: {json_path}")
            continue

        if args.recovery and args.use_pdf2docx_api and flag_pdf:
            try_import("pdf2docx")
            from pdf2docx.converter import Converter

            os.makedirs(args.output, exist_ok=True)
            docx_file = os.path.join(args.output, "{}_api.docx".format(img_name))
            cv = Converter(image_file)
            cv.convert(docx_file)
            cv.close()
            # logger.info("docx save to {}".format(docx_file))
            continue

        if not flag_gif and not flag_pdf:
            img = cv2.imread(image_file)

        if not flag_pdf:
            if img is None:
                # logger.error("error in loading image:{}".format(image_file))
                continue
            imgs = [img]
        else:
            imgs = img

        all_res = []
        for index, img in enumerate(imgs):
            res, time_dict = structure_sys(img, img_idx=index)
            # print(res) # 这里的res表示的每个bbox对应的图片信息，例如bbox信息，文本内容，置信度等
            # os.makedirs(os.path.join(save_folder, img_name) + '/shows/', exist_ok=True)
            # img_save_path = os.path.join(
            #     save_folder, img_name, "shows/show_{}.jpg".format(index)
            # )
            # os.makedirs(os.path.join(save_folder, img_name), exist_ok=True)
            # if structure_sys.mode == "structure" and res != []:
                # 绘制show文件,可以修改这个，让其不需要重建的另一半
                # draw_img = draw_structure_result(img, res, args.vis_font_path)
                # 保存res文件，可以整个一起报错
                # save_structure_res(res, save_folder, img_name, index)
            # elif structure_sys.mode == "kie":
            #     if structure_sys.kie_predictor.predictor is not None:
            #         draw_img = draw_re_results(img, res, font_path=args.vis_font_path)
            #     else:
            #         draw_img = draw_ser_results(img, res, font_path=args.vis_font_path)

            #     with open(
            #         os.path.join(save_folder, img_name, "res_{}_kie.txt".format(index)),
            #         "w",
            #         encoding="utf8",
            #     ) as f:
            #         res_str = "{}\t{}\n".format(
            #             image_file, json.dumps({"ocr_info": res}, ensure_ascii=False)
            #         )
            #         f.write(res_str)
            # if res != []:
            #     cv2.imwrite(img_save_path, draw_img)
            #     logger.info("result save to {}".format(img_save_path))
            if args.recovery and res != []:
                from ppstructure.recovery.recovery_to_doc import (
                    sorted_layout_boxes,
                    # convert_info_docx,
                    # convert_info_markdown,
                    convert_info_to_json,
                    
                )

                h, w, _ = img.shape
                res = sorted_layout_boxes(res, w) # 这里完成对文章顺序的重新排列，尤其是对双栏的文档，为了保证排序的准确性这里还是不能进行合并
                all_res.append(res) # 这里all_res里面包含多个子列表

        page_idx = -1
        # 保存图像文件
        for res in all_res:
            page_idx = page_idx + 1
            save_structure_res(res, save_folder, img_name, page_idx)

        if args.recovery and all_res != []:
            try:
                # Example usage:
                convert_info_to_json(img, all_res, save_folder, img_name)
                # convert_info_markdown(img, all_res, save_folder, img_name)
                # convert_info_docx(img, all_res, save_folder, img_name)
            except Exception as ex:
                # logger.error(
                #     "error in layout recovery image:{}, err msg: {}".format(
                #         image_file, ex
                #     )
                # )
                continue
        # logger.info("Predict time : {:.3f}s".format(time_dict["all"]))


if __name__ == "__main__":
    args = parse_args()
    if args.use_mp:
        p_list = []
        total_process_num = args.total_process_num
        for process_id in range(total_process_num):
            cmd = (
                [sys.executable, "-u"]
                + sys.argv
                + ["--process_id={}".format(process_id), "--use_mp={}".format(False)]
            )
            p = subprocess.Popen(cmd, stdout=sys.stdout, stderr=sys.stdout)
            p_list.append(p)
        for p in p_list:
            p.wait()
    else:
        main(args)
