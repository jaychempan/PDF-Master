import os
import shutil

def update_json_files(source_dir, target_dir):
    # 遍历源目录的所有一级子目录
    for subdir in os.listdir(source_dir):
        source_subdir_path = os.path.join(source_dir, subdir)
        target_subdir_path = os.path.join(target_dir, subdir)

        # 检查是否为目录
        if os.path.isdir(source_subdir_path):
            # 遍历子目录中的所有文件
            for filename in os.listdir(source_subdir_path):
                if filename.endswith("_ocr.json"):
                    source_file_path = os.path.join(source_subdir_path, filename)
                    target_file_path = os.path.join(target_subdir_path, filename)

                    # 检查目标子目录是否存在，不存在则创建
                    if not os.path.exists(target_subdir_path):
                        os.makedirs(target_subdir_path)

                    # 如果目标文件存在，先删除它
                    if os.path.exists(target_file_path):
                        os.remove(target_file_path)
                        print(f"删除文件: {target_file_path}")

                    # 将文件复制到目标目录
                    shutil.copy2(source_file_path, target_file_path)
                    print(f"更新文件: {source_file_path} 到 {target_file_path}")


# 示例调用
source_directory = '/mnt/petrelfs/shengkejun/project_data/COMAC_pretrain_data/comac_pdfs/process-pdfs/20240605_comac_pdfs_process/structure/'
target_directory = '/mnt/petrelfs/panjiancheng/llm-pdf-parsing/data/output/20240605_comac_pdfs_process/structure/'

update_json_files(source_directory, target_directory)
