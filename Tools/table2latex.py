import json
import os
from pylatex import Document, Section, Subsection, NoEscape, Package
from pylatex.errors import CompilerError

def create_latex_document(pred_tex_code, output_path):
    # 确保输出目录存在
    os.makedirs(os.path.dirname(output_path), exist_ok=True)

    doc = Document(documentclass='article')
    doc.packages.append(Package('graphicx'))
    doc.packages.append(Package('array'))
    doc.packages.append(Package('booktabs'))
    doc.packages.append(Package('ragged2e'))
    doc.packages.append(Package('ctex', options='UTF8'))
    doc.packages.append(Package('CJKutf8'))

    doc.append(NoEscape(pred_tex_code))
    
    try:
        # 保存并编译文档
        doc.generate_pdf(output_path, clean_tex=False, compiler='xelatex')
        return True
    except CompilerError:
        return False

def create_latex_documents_from_json(json_path, result_pdf_path):
    # 读取JSON文件
    with open(json_path, 'r', encoding='utf-8') as file:
        data = json.load(file)
    
    total = len(data)
    error_count = 0

    # 确保 'tables' 目录存在
    os.makedirs('tables', exist_ok=True)
    
    # 创建结果记录的 LaTeX 文档
    result_doc = Document(documentclass='article')
    result_doc.packages.append(Package('graphicx'))
    result_doc.packages.append(Package('array'))
    result_doc.packages.append(Package('booktabs'))
    result_doc.packages.append(Package('ragged2e'))
    result_doc.packages.append(Package('ctex', options='UTF8'))
    result_doc.packages.append(Package('CJKutf8'))

    result_doc.append(NoEscape(r'\section{Compilation Results}'))
    
    for idx, item in enumerate(data):
        image_name = item.get('image_name', 'N/A').split(".jpg")[0]
        pred_tex_code = item.get('pred_tex_code', '')
        
        output_path = os.path.join('tables', f'{image_name}')
        
        # 生成LaTeX文档并编译
        try:
            success = create_latex_document(pred_tex_code, output_path)
        except Exception as e:
            success = False
            print(f"Unexpected error compiling LaTeX for {image_name}: {e}")
        
        if not success:
            error_count += 1
            print(f"Error compiling LaTeX for {image_name}")
        
        # 记录结果到结果文档中
        with result_doc.create(Subsection(f'Image Index: {image_name}')):
            result_doc.append(f'Compilation {"Success" if success else "Failed"}')
    
    success_count = total - error_count
    success_rate = (success_count / total) * 100
    
    # 记录总结信息
    result_doc.append(NoEscape(r'\section{Summary}'))
    result_doc.append(f'Total: {total}, Success: {success_count}, Errors: {error_count}, Success Rate: {success_rate:.2f}%')
    
    # 保存并编译结果文档
    result_doc.generate_pdf(result_pdf_path, clean_tex=False, compiler='xelatex')

if __name__ == '__main__':
    json_path = 'sample_table.json'  # 替换为你的JSON文件路径
    result_pdf_path = os.path.join('tables', 'tables_compilation_results')  # 结果PDF输出路径
    create_latex_documents_from_json(json_path, result_pdf_path)