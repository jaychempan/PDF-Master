from lmdeploy import pipeline
from lmdeploy.vl import load_image

# 创建pipeline对象，设置最大token数量
pipe = pipeline('/mnt/petrelfs/panjiancheng/HFs/InternVL-Chat-V1-5')

# 加载图像
image = load_image('/mnt/petrelfs/panjiancheng/llm-pdf-parsing/data/output/20240617_comac_pdfs_inter_process/structure/CDS5133_B_襟翼曲柄滑块直线导轨运动机构设计规范/figures/10_[300, 582, 1504, 1116].jpg')


# 生成响应
response = pipe(('假如你是航空领域的专家，用专业的描述下面的图像？', image))

# 打印响应
print(response)