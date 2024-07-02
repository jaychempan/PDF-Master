from pdf2image import convert_from_path, convert_from_bytes
img_path = '/mnt/petrelfs/panjiancheng/llm-pdf-parsing/data/input/bench/split_26/ordinary_exam_paper_9077094d4750d65d9326ded96126c1f3.pdf'

# pages = convert_from_path(img_path, dpi=200)
with open(img_path, "rb") as f:
    binary_data = f.read()

pages = convert_from_bytes(binary_data, dpi=200)
