import os
import shutil

def move_pdfs_and_cleanup(root_dir):
    # 遍历指定目录下的所有文件和子目录
    for item in os.listdir(root_dir):
        item_path = os.path.join(root_dir, item)
        
        # 检查是否是目录
        if os.path.isdir(item_path):
            # 遍历子目录中的所有文件
            for sub_item in os.listdir(item_path):
                sub_item_path = os.path.join(item_path, sub_item)
                
                # 检查是否是PDF文件
                if os.path.isfile(sub_item_path) and sub_item_path.lower().endswith('.pdf'):
                    # 移动PDF文件到指定目录下
                    shutil.move(sub_item_path, root_dir)
            
            # 删除空子目录
            os.rmdir(item_path)

# 使用示例
root_directory = '/mnt/petrelfs/shengkejun/project_data/COMAC_pretrain_data/comac_pdfs/comac-pdfs-by-category'
move_pdfs_and_cleanup(root_directory)