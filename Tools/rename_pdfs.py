import os
import csv
from itertools import count

def rename_pdfs_in_dir(directory, csv_filename):
    # 计数器，用于生成唯一的序号
    counter = count(1)
    
    # 打开CSV文件，用于写入旧文件名和新文件名的对应关系
    with open(csv_filename, mode='w', newline='') as csv_file:
        csv_writer = csv.writer(csv_file)
        # 写入CSV文件的头部
        csv_writer.writerow(['Old File Name', 'New File Name', 'Old File Path', 'New File Path'])
        
        # 遍历指定目录及其所有子目录下的所有PDF文件
        for root, dirs, files in os.walk(directory):
            for file in files:
                if file.lower().endswith('.pdf'):  # 确保是PDF文件（不区分大小写）
                    # 构建文件的完整路径
                    old_file_path = os.path.join(root, file)
                    
                    # 生成新的文件名（原始文件名（无扩展名）+ 序号 + .pdf）
                    base, ext = os.path.splitext(file)
                    new_file_name = f"20240605_comac_{next(counter):03d}{ext}"  # 序号格式化为3位数，前导零
                    
                    # 构建新的文件完整路径
                    new_file_path = os.path.join(root, new_file_name)
                    
                    # 重命名文件
                    os.rename(old_file_path, new_file_path)
                    print(f"Renamed '{file}' to '{new_file_name}'")
                    
                    # 写入CSV文件
                    csv_writer.writerow([file, new_file_name, old_file_path, new_file_path])

# 使用示例：
# 目标目录路径
rename_pdfs_in_dir('/mnt/petrelfs/shengkejun/project_data/COMAC_pretrain_data/comac_pdfs/20240605_rename_comac_pdfs', '20240605_rename_comac_pdfs.csv')