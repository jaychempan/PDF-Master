"""
重命名pdf文件名
目前是加上comac_前缀，后续可以考虑不同类型的pdf加上不同的前缀
或者直接生成唯一的Uid来进行重命名

针对指定目录下的所有pdf文件进行重命名，包括子目录里面的pdf
"""
import os  
import glob  
from itertools import count  
  
def rename_pdfs_in_dir(directory):  
    # 计数器，用于生成唯一的序号  
    counter = count(1)  
  
    # 遍历指定目录及其所有子目录下的所有PDF文件  
    for root, dirs, files in os.walk(directory):  
        for file in files:  
            if file.lower().endswith('.pdf'):  # 确保是PDF文件（不区分大小写）  
                # 构建文件的完整路径  
                old_file_path = os.path.join(root, file)  
                  
                # 生成新的文件名（原始文件名（无扩展名）+ 序号 + .pdf）  
                base, ext = os.path.splitext(file)  
                new_file_name = f"comac_{next(counter):03d}{ext}"  # 序号格式化为3位数，前导零  
                  
                # 构建新的文件完整路径  
                new_file_path = os.path.join(root, new_file_name)  
                  
                # 重命名文件  
                os.rename(old_file_path, new_file_path)  
                print(f"Renamed '{old_file_path}' to '{new_file_path}'")  
  
# 使用示例：  
# 目标目录路径  
rename_pdfs_in_dir('/mnt/petrelfs/shengkejun/project_data/COMAC_pretrain_data/comac_pdfs/')