from pypandoc.pandoc_download import download_pandoc
# see the documentation how to customize the installation path
# but be aware that you then need to include it in the `PATH`
download_pandoc()

# import os
# import pypandoc

# def convert_docx_to_pdf(directory):
#     # 获取目录中的所有文件
#     files = os.listdir(directory)
    
#     # 过滤出 .docx 文件
#     docx_files = [f for f in files if f.endswith('.doc') or f.endswith('.docx')]
#     print(docx_files)
#     # 遍历每个 .docx 文件并将其转换为 .pdf
#     for docx_file in docx_files:
#         docx_path = os.path.join(directory, docx_file)
#         if docx_file.endswith('.doc'):
#             pdf_path = os.path.join(directory, docx_file.replace('.doc', '.pdf'))
#         elif docx_file.endswith('.docx'):
#             pdf_path = os.path.join(directory, docx_file.replace('.docx', '.pdf'))
#         # 使用 pypandoc 进行转换
#         pypandoc.convert_file(docx_path, 'pdf', outputfile=pdf_path)
#         print(f"Converted {docx_file} to {pdf_path}")

# # 调用函数并指定目录路径
# directory_path = "/mnt/petrelfs/shengkejun/project_data/COMAC_pretrain_data/comac_pdfs/"  # 请替换为实际目录路径
# convert_docx_to_pdf(directory_path)
