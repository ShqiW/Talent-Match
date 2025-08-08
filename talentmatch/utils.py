import os
import re
from werkzeug.datastructures import FileStorage
from io import BytesIO
from pypdf import PdfReader
import base64
from typing import List, Dict
import uuid


def escape_latex_chars(text: str) -> str:
    """转义LaTeX特殊字符"""
    if not text:
        return text

    # 首先处理可能的Unicode问题字符序列
    text = text.replace('\\u', r'\textbackslash{}u')
    text = text.replace('\\n', '\n')  # 保持真实换行
    text = text.replace('\\t', ' ')  # 制表符转空格
    text = text.replace('\\r', '')  # 移除回车符

    # 然后处理反斜杠，避免与其他转义冲突
    text = text.replace('\\', r'\textbackslash{}')

    # 处理其他LaTeX特殊字符
    latex_special_chars = {
        '&': r'\&',
        '%': r'\%',
        '$': r'\$',
        '#': r'\#',
        '^': r'\textasciicircum{}',
        '_': r'\_',
        '{': r'\{',
        '}': r'\}',
        '~': r'\textasciitilde{}'
    }

    for char, escape in latex_special_chars.items():
        text = text.replace(char, escape)

    # 处理Unicode字符 - 替换为ASCII等价物或移除
    text = text.encode('ascii', errors='ignore').decode('ascii')

    return text


def clean_latex_response(latex_response: str) -> str:
    """清理OpenAI返回的LaTeX代码"""
    # 移除开头的说明文字
    lines = latex_response.split('\n')
    latex_start_idx = -1

    # 查找LaTeX代码开始的位置
    for i, line in enumerate(lines):
        line_stripped = line.strip()
        if line_stripped.startswith('\\documentclass'):
            latex_start_idx = i
            break
        elif '```latex' in line_stripped.lower():
            # 如果找到markdown代码块，跳过这一行
            latex_start_idx = i + 1
            break

    if latex_start_idx == -1:
        # 如果没找到正确的开始，尝试查找任何以\开头的LaTeX命令
        for i, line in enumerate(lines):
            if line.strip().startswith('\\'):
                latex_start_idx = i
                break

    if latex_start_idx != -1:
        # 从找到的位置开始提取LaTeX代码
        latex_lines = lines[latex_start_idx:]

        # 移除结尾的markdown标记
        while latex_lines and latex_lines[-1].strip() in [
                '```', '```latex', ''
        ]:
            latex_lines.pop()

        latex_content = '\n'.join(latex_lines)
    else:
        # 如果找不到合适的开始位置，使用原始内容
        latex_content = latex_response

    # 移除可能的markdown代码块标记
    latex_content = re.sub(r'^```(?:latex)?\s*\n',
                           '',
                           latex_content,
                           flags=re.MULTILINE)
    latex_content = re.sub(r'\n```\s*$', '', latex_content, flags=re.MULTILINE)

    # 确保有文档结构
    if '\\documentclass' not in latex_content:
        # 如果没有文档类声明，添加一个基本结构
        latex_content = f"""\\documentclass{{article}}
\\usepackage[utf8]{{inputenc}}
\\usepackage{{xcolor}}
\\usepackage{{geometry}}
\\geometry{{margin=1in}}

\\begin{{document}}

{latex_content}

\\end{{document}}"""

    return latex_content.strip()


def allowed_file(filename: str, allowed_extensions: set) -> bool:
    """检查文件扩展名是否允许"""
    return '.' in filename and \
           filename.rsplit('.', 1)[1].lower() in allowed_extensions


def extract_text_from_file(file_path: str) -> str:
    """从文件中提取文本（简化版本，主要处理txt文件）"""
    try:
        with open(file_path, 'r', encoding='utf-8') as file:
            return file.read()
    except Exception as e:
        print(f"Error reading file {file_path}: {e}")
        return ""


def create_upload_folder(folder_path: str):
    """创建上传文件夹"""
    if not os.path.exists(folder_path):
        os.makedirs(folder_path)


def extract_text_from_pdf_file(pdf_file: FileStorage) -> str:
    """
    从React Post上传的PDF（二进制）文件中提取文本
    :param pdf_file: werkzeug.datastructures.FileStorage对象
    :return: 提取的文本内容
    """
    if not isinstance(pdf_file, FileStorage):
        raise ValueError(
            f"Expected a FileStorage object for PDF file, got {type(pdf_file)}"
        )

    try:
        pdf_reader = PdfReader(BytesIO(pdf_file.read()))
        text_parts = []

        for page in pdf_reader.pages:
            page_text = page.extract_text()
            if page_text:
                # 清理文本格式
                cleaned_text = re.sub(r'\s+', ' ', page_text.strip())
                text_parts.append(cleaned_text)

        # 用双换行连接页面，保持结构
        full_text = '\n\n'.join(text_parts)
        return full_text.strip()

    except Exception as e:
        print(f"Error extracting text from PDF: {e}")
        return ""


def extract_text_from_pdf_base64(pdf_base64: str) -> str:
    """
    从React Post上传的PDF（二进制）文件中提取文本
    :param pdf_base64: base64编码的PDF字符串
    :return: 提取的文本内容
    """
    if not isinstance(pdf_base64, str):
        raise ValueError(
            f"Expected a base64 encoded string for PDF file, got {type(pdf_base64)}"
        )

    try:
        pdf_bytes = base64.b64decode(pdf_base64)
        pdf_reader = PdfReader(BytesIO(pdf_bytes))
        text_parts = []

        for page in pdf_reader.pages:
            page_text = page.extract_text()
            if page_text:
                # 清理文本格式
                cleaned_text = re.sub(r'\s+', ' ', page_text.strip())
                text_parts.append(cleaned_text)

        # 用双换行连接页面，保持结构
        full_text = '\n\n'.join(text_parts)
        return full_text.strip()

    except Exception as e:
        print(f"Error extracting text from PDF: {e}")
        return ""


def clean_latex_response(latex_response: str) -> str:
    """清理OpenAI返回的LaTeX代码"""
    # 移除开头的说明文字
    lines = latex_response.split('\n')
    latex_start_idx = -1

    # 查找LaTeX代码开始的位置
    for i, line in enumerate(lines):
        line_stripped = line.strip()
        if line_stripped.startswith('\\documentclass'):
            latex_start_idx = i
            break
        elif '```latex' in line_stripped.lower():
            # 如果找到markdown代码块，跳过这一行
            latex_start_idx = i + 1
            break

    if latex_start_idx == -1:
        # 如果没找到正确的开始，尝试查找任何以\开头的LaTeX命令
        for i, line in enumerate(lines):
            if line.strip().startswith('\\'):
                latex_start_idx = i
                break

    if latex_start_idx != -1:
        # 从找到的位置开始提取LaTeX代码
        latex_lines = lines[latex_start_idx:]

        # 移除结尾的markdown标记
        while latex_lines and latex_lines[-1].strip() in [
                '```', '```latex', ''
        ]:
            latex_lines.pop()

        latex_content = '\n'.join(latex_lines)
    else:
        # 如果找不到合适的开始位置，使用原始内容
        latex_content = latex_response

    # 移除可能的markdown代码块标记
    latex_content = re.sub(r'^```(?:latex)?\s*\n',
                           '',
                           latex_content,
                           flags=re.MULTILINE)
    latex_content = re.sub(r'\n```\s*$', '', latex_content, flags=re.MULTILINE)

    # 确保有文档结构
    if '\\documentclass' not in latex_content:
        # 如果没有文档类声明，添加一个基本结构
        latex_content = f"""\\documentclass{{article}}
\\usepackage[utf8]{{inputenc}}
\\usepackage{{xcolor}}
\\usepackage{{geometry}}
\\geometry{{margin=1in}}

\\begin{{document}}

{latex_content}

\\end{{document}}"""

    return latex_content.strip()


def _generate_summary(name: str, resume_text: str) -> str:
    """生成候选人摘要（简化版本）"""
    # 提取关键信息
    lines = resume_text.split('\n')
    key_info = []

    # 查找常见的关键词
    keywords = ['experience', 'skills', 'education', 'project', 'work', 'job']

    for line in lines:
        line_lower = line.lower()
        if any(keyword in line_lower for keyword in keywords):
            if len(line.strip()) > 10:  # 过滤太短的行
                key_info.append(line.strip())

    # 生成摘要
    if key_info:
        summary = f"{name} has relevant experience in: " + "; ".join(
            key_info[:3])
    else:
        summary = f"{name} is a qualified candidate with relevant background."

    return summary


def process_candidates(
    embedding_processor,
    candidates: List[Dict],
) -> List[Dict]:
    """处理候选人列表，为每个候选人生成嵌入"""
    processed_candidates = []

    for candidate in candidates:
        # 提取候选人信息
        candidate_id = candidate.get('id', str(uuid.uuid4()))
        name = candidate.get('name', f'Candidate_{candidate_id[:8]}')
        info = candidate.get('info', '')
        resume: str = candidate.get('resume', '')
        if (len(resume) > 0):
            resume_text = extract_text_from_pdf_base64(resume).strip()
        else:
            resume_text = ""

        merge_text = info + "\n" + resume_text

        # 生成嵌入
        embedding = embedding_processor.generate_embedding(merge_text)

        processed_candidate = {
            'id': candidate_id,
            'name': name,
            'resume_text': merge_text,
            'embedding': embedding.tolist(),  # 转换为列表以便JSON序列化
            'summary': _generate_summary(name, resume_text),
            'resume': resume,
        }

        processed_candidates.append(processed_candidate)

    return processed_candidates
