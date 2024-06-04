import os
import fitz  # PyMuPDF
from tqdm import tqdm

def process_pdf(file_path):
    doc = fitz.open(file_path)
    for page_num in range(len(doc)):
        page = doc.load_page(page_num)  # 加载页面
        # pix = page.get_pixmap()  # 将页面渲染为图像
        # output_file = os.path.join("output", f"{os.path.basename(file_path).split('.')[0]}_page_{page_num}.png")
        # pix.save(output_file)  # 保存图像文件

def process_directory(directory):
    if not os.path.exists("output"):
        os.makedirs("output")
    
    pdf_files = []
    for root, _, files in os.walk(directory):
        for file in files:
            if file.lower().endswith('.pdf'):
                pdf_files.append(os.path.join(root, file))
    
    for pdf_file in tqdm(pdf_files, desc="Processing PDFs"):
        process_pdf(pdf_file)

# 指定目录
directory_path = "/mnt/petrelfs/panjiancheng/llm-pdf-parsing/shangfei/more_pdfs_x16_n7"

# 处理指定目录及其子目录下的所有 PDF 文件
process_directory(directory_path)