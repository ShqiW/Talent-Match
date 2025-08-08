import os
import re
import uuid
from typing import List, Dict, Tuple
import numpy as np
from sentence_transformers import SentenceTransformer
from sklearn.metrics.pairwise import cosine_similarity
from werkzeug.datastructures import FileStorage
from io import BytesIO
from pypdf import PdfReader
import base64
from pathlib import Path
import subprocess
import tempfile
import openai  # Uncomment when installed
# from pylatex import Document, Section, Subsection, Command  # Uncomment when installed
from talentmatch import OPENAI_API_KEY


def escape_latex_chars(text: str) -> str:
    """转义LaTeX特殊字符"""
    if not text:
        return text
    
    # 首先处理可能的Unicode问题字符序列 
    text = text.replace('\\u', r'\textbackslash{}u')
    text = text.replace('\\n', '\n')  # 保持真实换行
    text = text.replace('\\t', ' ')   # 制表符转空格
    text = text.replace('\\r', '')    # 移除回车符
    
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
        while latex_lines and latex_lines[-1].strip() in ['```', '```latex', '']:
            latex_lines.pop()
        
        latex_content = '\n'.join(latex_lines)
    else:
        # 如果找不到合适的开始位置，使用原始内容
        latex_content = latex_response
    
    # 移除可能的markdown代码块标记
    latex_content = re.sub(r'^```(?:latex)?\s*\n', '', latex_content, flags=re.MULTILINE)
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


class EmbeddingProcessor:

    def __init__(self, model_name: str = 'all-mpnet-base-v2'):
        """初始化嵌入处理器"""
        self.model = SentenceTransformer(model_name)

    def generate_embedding(self, text: str) -> np.ndarray:
        """生成文本嵌入"""
        # 清理文本
        cleaned_text = self._clean_text(text)
        # 生成嵌入
        embedding = self.model.encode(
            cleaned_text,
            show_progress_bar=True,
        )
        return embedding

    def _clean_text(self, text: str) -> str:
        """清理文本，移除特殊字符和多余空格"""
        # 移除HTML标签
        text = re.sub(r'<[^>]+>', '', text)
        # 移除特殊字符，保留字母、数字、空格和基本标点
        text = re.sub(r'[^\w\s\.\,\!\?\;\:\-\(\)]', '', text)
        # 移除多余空格
        text = re.sub(r'\s+', ' ', text).strip()
        return text

    def calculate_similarity(
        self,
        embedding1: np.ndarray,
        embedding2: np.ndarray,
    ) -> float:
        """计算两个嵌入之间的余弦相似度"""
        # 确保是2D数组
        if embedding1.ndim == 1:
            embedding1 = embedding1.reshape(1, -1)
        if embedding2.ndim == 1:
            embedding2 = embedding2.reshape(1, -1)

        similarity = cosine_similarity(embedding1, embedding2)[0][0]
        return float(similarity)


class CandidateProcessor:

    def __init__(self, embedding_processor: EmbeddingProcessor):
        self.embedding_processor = embedding_processor

    def process_candidates(self, candidates: List[Dict]) -> List[Dict]:
        """处理候选人列表，为每个候选人生成嵌入"""
        processed_candidates = []

        for candidate in candidates:
            # 提取候选人信息
            candidate_id = candidate.get('id', str(uuid.uuid4()))
            name = candidate.get('name', f'Candidate_{candidate_id[:8]}')
            info = candidate.get('info', '')
            resume: str = candidate.get('resume', '')
            resume_text = extract_text_from_pdf_base64(resume)
            if not resume_text.strip():
                continue

            # 生成嵌入
            embedding = self.embedding_processor.generate_embedding(
                resume_text)

            processed_candidate = {
                'id': candidate_id,
                'name': name,
                'resume': resume_text,
                'embedding': embedding.tolist(),  # 转换为列表以便JSON序列化
                'summary': self._generate_summary(name, resume_text)
            }

            processed_candidates.append(processed_candidate)

        return processed_candidates

    def _generate_summary(self, name: str, resume_text: str) -> str:
        """生成候选人摘要（简化版本）"""
        # 提取关键信息
        lines = resume_text.split('\n')
        key_info = []

        # 查找常见的关键词
        keywords = [
            'experience', 'skills', 'education', 'project', 'work', 'job'
        ]

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


class RecommendationEngine:

    def __init__(self, embedding_processor: EmbeddingProcessor):
        self.embedding_processor = embedding_processor

    def find_top_candidates(
        self,
        job_description: str,
        candidates: List[Dict],
        top_k: int = 10,
        min_similarity: float = 0.1,
    ) -> List[Dict]:
        """找到最匹配的候选人"""
        if not candidates:
            return []

        # 生成职位描述的嵌入
        job_embedding = self.embedding_processor.generate_embedding(
            job_description)

        # 计算每个候选人的相似度
        candidate_scores = []

        for candidate in candidates:
            if 'embedding' not in candidate:
                continue

            # 将嵌入转换回numpy数组
            candidate_embedding = np.array(candidate['embedding'])

            # 计算相似度
            similarity = self.embedding_processor.calculate_similarity(
                job_embedding,
                candidate_embedding,
            )

            if True or (similarity >= min_similarity):
                # Generate annotated resume using OpenAI and LaTeX
                annotated_resume_base64 = self._generate_annotated_resume(
                    job_description, candidate)

                candidate_scores.append(
                    {
                        'id': candidate['id'],
                        'name': candidate['name'],
                        'similarity_score': similarity,
                        'summary': candidate.get('summary', ''),
                        'annotated_resume': annotated_resume_base64,
                    }, )

        # 按相似度排序
        candidate_scores.sort(
            key=lambda x: x['similarity_score'],
            reverse=True,
        )

        # 返回前top_k个候选人
        return candidate_scores[:top_k]

    def _generate_annotated_resume(self, job_description: str,
                                   candidate: Dict) -> str:
        """
        Generate an annotated resume using OpenAI and LaTeX compilation
        
        Args:
            job_description: The job description to match against
            candidate: Candidate dictionary with resume text
            
        Returns:
            Base64 encoded PDF of the annotated resume
        """
        try:
            # Step 1: 在查询OpenAI前先处理简历文本
            processed_candidate = candidate.copy()
            if 'resume' in processed_candidate:
                processed_candidate['resume'] = escape_latex_chars(processed_candidate['resume'])
            
            # Step 1: Query OpenAI for LaTeX annotated resume
            latex_content = self._query_openai_for_latex(
                job_description, processed_candidate)

            # Step 2: Compile LaTeX to PDF
            pdf_path = self._compile_latex_to_pdf(latex_content,
                                                  candidate['id'])

            # Step 3: Convert PDF to base64
            if pdf_path and pdf_path.exists():
                with open(pdf_path, 'rb') as pdf_file:
                    pdf_base64 = base64.b64encode(
                        pdf_file.read()).decode('utf-8')

                # Clean up temporary files
                pdf_path.unlink()
                return pdf_base64
            else:
                print(
                    f"Failed to generate PDF for candidate {candidate['id']}")
                return ""

        except Exception as e:
            print(f"Error generating annotated resume: {e}")
            return ""

    def _query_openai_for_latex(
        self,
        job_description: str,
        candidate: Dict,
    ) -> str:
        """
        Query OpenAI to generate LaTeX annotated resume
        """
        try:
            client = openai.OpenAI(api_key=OPENAI_API_KEY)

            # 更严格的提示词，强调输出格式
            prompt = f"""
            Create a professional LaTeX resume document. IMPORTANT: Your response must contain ONLY the LaTeX code, no explanations or markdown formatting.

            Job Description:
            {job_description}

            Candidate Resume (already LaTeX-escaped):
            {candidate.get('resume', '')}

            Requirements:
            1. Start with \\documentclass{{article}}
            2. Include necessary packages: inputenc, xcolor, geometry, enumitem
            3. Use \\textbf{{}} to highlight relevant skills
            4. Use \\textcolor{{blue}}{{}} for skills matching job requirements
            5. Add \\textcolor{{red}}{{[ANNOTATION: explanation]}} for key matches
            6. Create sections: Summary, Experience, Skills, Education
            7. DO NOT use \\input or \\include commands
            8. DO NOT include any text outside the LaTeX code
            9. Ensure the document is complete and self-contained

            Output only valid LaTeX code starting with \\documentclass and ending with \\end{{document}}.
            """

            response = client.chat.completions.create(
                model="gpt-4",
                messages=[{
                    "role": "user",
                    "content": prompt
                }],
                max_tokens=4000,
                temperature=0.3,
            )

            latex_response = response.choices[0].message.content
            
            # 清理返回的LaTeX代码
            cleaned_latex = clean_latex_response(latex_response)
            
            return cleaned_latex

        except Exception as e:
            print(f"Error querying OpenAI: {e}")
            # 使用占位符实现作为后备
            return self._generate_placeholder_latex(candidate)

    def _generate_placeholder_latex(self, candidate: Dict) -> str:
        """Generate a simple LaTeX document as placeholder"""
        # 确保候选人简历文本被转义
        resume_text = escape_latex_chars(candidate.get('resume', 'No resume content available'))
        candidate_name = escape_latex_chars(candidate.get('name', 'Candidate'))
        
        # 改进的占位符模板，更像真实简历
        latex_content = f"""\\documentclass{{article}}
\\usepackage[utf8]{{inputenc}}
\\usepackage{{xcolor}}
\\usepackage{{geometry}}
\\usepackage{{enumitem}}
\\geometry{{margin=1in}}

\\title{{\\textbf{{{candidate_name}}}}}
\\author{{}}
\\date{{}}

\\begin{{document}}

\\maketitle

\\section{{Professional Summary}}
\\textcolor{{blue}}{{[ANNOTATION: This candidate demonstrates strong alignment with the position requirements]}}

\\section{{Experience and Qualifications}}
{resume_text}

\\section{{Key Strengths}}
\\textcolor{{red}}{{[ANNOTATION: Highlighted relevant skills and experiences that match the job description]}}

\\begin{{itemize}}
\\item Strong technical background relevant to the position
\\item Proven experience in related fields
\\item Excellent communication and collaboration skills
\\end{{itemize}}

\\section{{Match Analysis}}
\\textcolor{{blue}}{{[ANNOTATION: This candidate's profile shows good potential for the role based on their background and experience]}}

\\end{{document}}"""
        
        return latex_content

    def _compile_latex_to_pdf(
        self,
        latex_content: str,
        candidate_id: str,
    ) -> Path:
        """
        Compile LaTeX content to PDF using pdflatex
        """
        try:
            # 预处理LaTeX内容，移除可能的问题
            latex_content = self._preprocess_latex_content(latex_content)
            
            # Create temporary directory for LaTeX compilation
            temp_dir = Path(tempfile.mkdtemp())
            tex_file = temp_dir / f"resume_{candidate_id}.tex"
            pdf_file = temp_dir / f"resume_{candidate_id}.pdf"

            # 写入LaTeX文件时使用安全的编码处理
            try:
                with open(tex_file, 'w', encoding='utf-8', errors='replace') as f:
                    f.write(latex_content)
            except UnicodeEncodeError:
                # 如果UTF-8编码失败，使用ASCII编码
                latex_content_ascii = latex_content.encode('ascii', errors='ignore').decode('ascii')
                with open(tex_file, 'w', encoding='ascii') as f:
                    f.write(latex_content_ascii)

            # 多次编译以处理引用
            for attempt in range(2):  # 通常2次编译足够
                result = subprocess.run(
                    [
                        'pdflatex', '-output-directory',
                        str(temp_dir), '-interaction=nonstopmode',
                        str(tex_file)
                    ],
                    capture_output=True,
                    text=True,
                    cwd=temp_dir,
                    timeout=30
                )
                
                # 如果第一次编译成功，进行第二次编译处理引用
                if attempt == 0 and result.returncode == 0:
                    continue
                elif attempt == 1 or result.returncode == 0:
                    break

            if result.returncode == 0 and pdf_file.exists():
                # Move PDF to uploads directory
                final_pdf_path = Path("uploads") / f"annotated_resume_{candidate_id}.pdf"
                final_pdf_path.parent.mkdir(exist_ok=True)

                import shutil
                shutil.copy2(pdf_file, final_pdf_path)
                shutil.rmtree(temp_dir)

                return final_pdf_path
            else:
                # 详细的错误信息
                print(f"LaTeX compilation failed for candidate {candidate_id}")
                print(f"Return code: {result.returncode}")
                if result.stderr:
                    print(f"STDERR: {result.stderr}")
                if result.stdout:
                    print(f"STDOUT (last 1000 chars): {result.stdout[-1000:]}")
                
                # 保存调试文件
                debug_tex_path = Path("uploads") / f"debug_resume_{candidate_id}.tex"
                debug_tex_path.parent.mkdir(exist_ok=True)
                try:
                    with open(debug_tex_path, 'w', encoding='utf-8', errors='replace') as f:
                        f.write(latex_content)
                except UnicodeEncodeError:
                    with open(debug_tex_path, 'w', encoding='ascii', errors='ignore') as f:
                        f.write(latex_content)
                print(f"Debug .tex file saved to: {debug_tex_path}")
                
                # 如果OpenAI生成的LaTeX失败，尝试使用占位符
                if not hasattr(self, '_tried_placeholder'):
                    print(f"Trying placeholder LaTeX for candidate {candidate_id}")
                    self._tried_placeholder = True
                    placeholder_latex = self._generate_placeholder_latex(candidate)
                    delattr(self, '_tried_placeholder')  # 清除标记
                    return self._compile_latex_to_pdf(placeholder_latex, candidate_id)
                else:
                    delattr(self, '_tried_placeholder')  # 清除标记
                    return None
                
        except subprocess.TimeoutExpired:
            print(f"LaTeX compilation timed out for candidate {candidate_id}")
            import shutil
            shutil.rmtree(temp_dir, ignore_errors=True)
            return None
        except Exception as e:
            print(f"Error compiling LaTeX: {e}")
            # 如果是编码错误，尝试用占位符重新生成
            if "bad escape" in str(e) or "unicode" in str(e).lower():
                if not hasattr(self, '_tried_placeholder'):
                    print(f"Unicode error detected, trying placeholder for candidate {candidate_id}")
                    self._tried_placeholder = True
                    placeholder_latex = self._generate_placeholder_latex(candidate)
                    delattr(self, '_tried_placeholder')
                    return self._compile_latex_to_pdf(placeholder_latex, candidate_id)
            return None
        finally:
            # 清理临时目录
            if 'temp_dir' in locals():
                import shutil
                shutil.rmtree(temp_dir, ignore_errors=True)

    def _preprocess_latex_content(self, latex_content: str) -> str:
        """预处理LaTeX内容，移除可能导致编译失败的元素"""
        
        # 确保内容是字符串且不为空
        if not isinstance(latex_content, str):
            latex_content = str(latex_content)
        
        if not latex_content.strip():
            return self._generate_placeholder_latex({'name': 'Unknown', 'resume': 'No content available'})
        
        # 移除可能导致Python字符串解析错误的序列
        # 替换可能的问题序列
        latex_content = latex_content.replace('\\u', r'\textbackslash{}u')
        latex_content = latex_content.replace('\\n', '\\\\')  # LaTeX换行
        latex_content = latex_content.replace('\\t', ' ')     # 制表符转空格
        latex_content = latex_content.replace('\\r', '')     # 移除回车符
        
        # 移除可能的外部文件引用
        latex_content = re.sub(r'\\input\{[^}]+\}', '', latex_content)
        latex_content = re.sub(r'\\include\{[^}]+\}', '', latex_content)
        
        # 确保必要的包被包含
        required_packages = [
            r'\usepackage[utf8]{inputenc}',
            r'\usepackage{xcolor}', 
            r'\usepackage{geometry}',
            r'\usepackage{enumitem}'
        ]
        
        # 检查是否包含必要的包，如果没有则添加
        for package in required_packages:
            if package not in latex_content:
                # 在\documentclass之后添加包
                latex_content = re.sub(
                    r'(\\documentclass\{[^}]+\})',
                    f'\\1\n{package}',
                    latex_content
                )
        
        # 确保有geometry设置
        if r'\geometry{' not in latex_content and r'\usepackage{geometry}' in latex_content:
            latex_content = re.sub(
                r'(\\usepackage\{geometry\})',
                r'\1\n\\geometry{margin=1in}',
                latex_content
            )
        
        # 最终清理 - 移除非ASCII字符
        latex_content = latex_content.encode('ascii', errors='ignore').decode('ascii')
        
        return latex_content


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
        while latex_lines and latex_lines[-1].strip() in ['```', '```latex', '']:
            latex_lines.pop()
        
        latex_content = '\n'.join(latex_lines)
    else:
        # 如果找不到合适的开始位置，使用原始内容
        latex_content = latex_response
    
    # 移除可能的markdown代码块标记
    latex_content = re.sub(r'^```(?:latex)?\s*\n', '', latex_content, flags=re.MULTILINE)
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


class EmbeddingProcessor:

    def __init__(self, model_name: str = 'all-mpnet-base-v2'):
        """初始化嵌入处理器"""
        self.model = SentenceTransformer(model_name)

    def generate_embedding(self, text: str) -> np.ndarray:
        """生成文本嵌入"""
        # 清理文本
        cleaned_text = self._clean_text(text)
        # 生成嵌入
        embedding = self.model.encode(
            cleaned_text,
            show_progress_bar=True,
        )
        return embedding

    def _clean_text(self, text: str) -> str:
        """清理文本，移除特殊字符和多余空格"""
        # 移除HTML标签
        text = re.sub(r'<[^>]+>', '', text)
        # 移除特殊字符，保留字母、数字、空格和基本标点
        text = re.sub(r'[^\w\s\.\,\!\?\;\:\-\(\)]', '', text)
        # 移除多余空格
        text = re.sub(r'\s+', ' ', text).strip()
        return text

    def calculate_similarity(
        self,
        embedding1: np.ndarray,
        embedding2: np.ndarray,
    ) -> float:
        """计算两个嵌入之间的余弦相似度"""
        # 确保是2D数组
        if embedding1.ndim == 1:
            embedding1 = embedding1.reshape(1, -1)
        if embedding2.ndim == 1:
            embedding2 = embedding2.reshape(1, -1)

        similarity = cosine_similarity(embedding1, embedding2)[0][0]
        return float(similarity)


class CandidateProcessor:

    def __init__(self, embedding_processor: EmbeddingProcessor):
        self.embedding_processor = embedding_processor

    def process_candidates(self, candidates: List[Dict]) -> List[Dict]:
        """处理候选人列表，为每个候选人生成嵌入"""
        processed_candidates = []

        for candidate in candidates:
            # 提取候选人信息
            candidate_id = candidate.get('id', str(uuid.uuid4()))
            name = candidate.get('name', f'Candidate_{candidate_id[:8]}')
            info = candidate.get('info', '')
            resume: str = candidate.get('resume', '')
            resume_text = extract_text_from_pdf_base64(resume)
            if not resume_text.strip():
                continue

            # 生成嵌入
            embedding = self.embedding_processor.generate_embedding(
                resume_text)

            processed_candidate = {
                'id': candidate_id,
                'name': name,
                'resume': resume_text,
                'embedding': embedding.tolist(),  # 转换为列表以便JSON序列化
                'summary': self._generate_summary(name, resume_text)
            }

            processed_candidates.append(processed_candidate)

        return processed_candidates

    def _generate_summary(self, name: str, resume_text: str) -> str:
        """生成候选人摘要（简化版本）"""
        # 提取关键信息
        lines = resume_text.split('\n')
        key_info = []

        # 查找常见的关键词
        keywords = [
            'experience', 'skills', 'education', 'project', 'work', 'job'
        ]

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


class RecommendationEngine:

    def __init__(self, embedding_processor: EmbeddingProcessor):
        self.embedding_processor = embedding_processor

    def find_top_candidates(
        self,
        job_description: str,
        candidates: List[Dict],
        top_k: int = 10,
        min_similarity: float = 0.1,
    ) -> List[Dict]:
        """找到最匹配的候选人"""
        if not candidates:
            return []

        # 生成职位描述的嵌入
        job_embedding = self.embedding_processor.generate_embedding(
            job_description)

        # 计算每个候选人的相似度
        candidate_scores = []

        for candidate in candidates:
            if 'embedding' not in candidate:
                continue

            # 将嵌入转换回numpy数组
            candidate_embedding = np.array(candidate['embedding'])

            # 计算相似度
            similarity = self.embedding_processor.calculate_similarity(
                job_embedding,
                candidate_embedding,
            )

            if True or (similarity >= min_similarity):
                # Generate annotated resume using OpenAI and LaTeX
                annotated_resume_base64 = self._generate_annotated_resume(
                    job_description, candidate)

                candidate_scores.append(
                    {
                        'id': candidate['id'],
                        'name': candidate['name'],
                        'similarity_score': similarity,
                        'summary': candidate.get('summary', ''),
                        'annotated_resume': annotated_resume_base64,
                    }, )

        # 按相似度排序
        candidate_scores.sort(
            key=lambda x: x['similarity_score'],
            reverse=True,
        )

        # 返回前top_k个候选人
        return candidate_scores[:top_k]

    def _generate_annotated_resume(self, job_description: str,
                                   candidate: Dict) -> str:
        """
        Generate an annotated resume using OpenAI and LaTeX compilation
        
        Args:
            job_description: The job description to match against
            candidate: Candidate dictionary with resume text
            
        Returns:
            Base64 encoded PDF of the annotated resume
        """
        try:
            # Step 1: 在查询OpenAI前先处理简历文本
            processed_candidate = candidate.copy()
            if 'resume' in processed_candidate:
                processed_candidate['resume'] = escape_latex_chars(processed_candidate['resume'])
            
            # Step 1: Query OpenAI for LaTeX annotated resume
            latex_content = self._query_openai_for_latex(
                job_description, processed_candidate)

            # Step 2: Compile LaTeX to PDF
            pdf_path = self._compile_latex_to_pdf(latex_content,
                                                  candidate['id'])

            # Step 3: Convert PDF to base64
            if pdf_path and pdf_path.exists():
                with open(pdf_path, 'rb') as pdf_file:
                    pdf_base64 = base64.b64encode(
                        pdf_file.read()).decode('utf-8')

                # Clean up temporary files
                pdf_path.unlink()
                return pdf_base64
            else:
                print(
                    f"Failed to generate PDF for candidate {candidate['id']}")
                return ""

        except Exception as e:
            print(f"Error generating annotated resume: {e}")
            return ""

    def _query_openai_for_latex(
        self,
        job_description: str,
        candidate: Dict,
    ) -> str:
        """
        Query OpenAI to generate LaTeX annotated resume
        """
        try:
            client = openai.OpenAI(api_key=OPENAI_API_KEY)

            # 更严格的提示词，强调输出格式
            prompt = f"""
            Create a professional LaTeX resume document. IMPORTANT: Your response must contain ONLY the LaTeX code, no explanations or markdown formatting.

            Job Description:
            {job_description}

            Candidate Resume (already LaTeX-escaped):
            {candidate.get('resume', '')}

            Requirements:
            1. Start with \\documentclass{{article}}
            2. Include necessary packages: inputenc, xcolor, geometry, enumitem
            3. Use \\textbf{{}} to highlight relevant skills
            4. Use \\textcolor{{blue}}{{}} for skills matching job requirements
            5. Add \\textcolor{{red}}{{[ANNOTATION: explanation]}} for key matches
            6. Create sections: Summary, Experience, Skills, Education
            7. DO NOT use \\input or \\include commands
            8. DO NOT include any text outside the LaTeX code
            9. Ensure the document is complete and self-contained

            Output only valid LaTeX code starting with \\documentclass and ending with \\end{{document}}.
            """

            response = client.chat.completions.create(
                model="gpt-4",
                messages=[{
                    "role": "user",
                    "content": prompt
                }],
                max_tokens=4000,
                temperature=0.3,
            )

            latex_response = response.choices[0].message.content
            
            # 清理返回的LaTeX代码
            cleaned_latex = clean_latex_response(latex_response)
            
            return cleaned_latex

        except Exception as e:
            print(f"Error querying OpenAI: {e}")
            # 使用占位符实现作为后备
            return self._generate_placeholder_latex(candidate)

    def _generate_placeholder_latex(self, candidate: Dict) -> str:
        """Generate a simple LaTeX document as placeholder"""
        # 确保候选人简历文本被转义
        resume_text = escape_latex_chars(candidate.get('resume', 'No resume content available'))
        candidate_name = escape_latex_chars(candidate.get('name', 'Candidate'))
        
        # 改进的占位符模板，更像真实简历
        latex_content = f"""\\documentclass{{article}}
\\usepackage[utf8]{{inputenc}}
\\usepackage{{xcolor}}
\\usepackage{{geometry}}
\\usepackage{{enumitem}}
\\geometry{{margin=1in}}

\\title{{\\textbf{{{candidate_name}}}}}
\\author{{}}
\\date{{}}

\\begin{{document}}

\\maketitle

\\section{{Professional Summary}}
\\textcolor{{blue}}{{[ANNOTATION: This candidate demonstrates strong alignment with the position requirements]}}

\\section{{Experience and Qualifications}}
{resume_text}

\\section{{Key Strengths}}
\\textcolor{{red}}{{[ANNOTATION: Highlighted relevant skills and experiences that match the job description]}}

\\begin{{itemize}}
\\item Strong technical background relevant to the position
\\item Proven experience in related fields
\\item Excellent communication and collaboration skills
\\end{{itemize}}

\\section{{Match Analysis}}
\\textcolor{{blue}}{{[ANNOTATION: This candidate's profile shows good potential for the role based on their background and experience]}}

\\end{{document}}"""
        
        return latex_content

    def _compile_latex_to_pdf(
        self,
        latex_content: str,
        candidate_id: str,
    ) -> Path:
        """
        Compile LaTeX content to PDF using pdflatex
        """
        try:
            # 预处理LaTeX内容，移除可能的问题
            latex_content = self._preprocess_latex_content(latex_content)
            
            # Create temporary directory for LaTeX compilation
            temp_dir = Path(tempfile.mkdtemp())
            tex_file = temp_dir / f"resume_{candidate_id}.tex"
            pdf_file = temp_dir / f"resume_{candidate_id}.pdf"

            # Write LaTeX content to file
            with open(tex_file, 'w', encoding='utf-8') as f:
                f.write(latex_content)

            # 多次编译以处理引用
            for attempt in range(2):  # 通常2次编译足够
                result = subprocess.run(
                    [
                        'pdflatex', '-output-directory',
                        str(temp_dir), '-interaction=nonstopmode',
                        str(tex_file)
                    ],
                    capture_output=True,
                    text=True,
                    cwd=temp_dir,
                    timeout=30
                )
                
                # 如果第一次编译成功，进行第二次编译处理引用
                if attempt == 0 and result.returncode == 0:
                    continue
                elif attempt == 1 or result.returncode == 0:
                    break

            if result.returncode == 0 and pdf_file.exists():
                # Move PDF to uploads directory
                final_pdf_path = Path("uploads") / f"annotated_resume_{candidate_id}.pdf"
                final_pdf_path.parent.mkdir(exist_ok=True)

                import shutil
                shutil.copy2(pdf_file, final_pdf_path)
                shutil.rmtree(temp_dir)

                return final_pdf_path
            else:
                # 详细的错误信息
                print(f"LaTeX compilation failed for candidate {candidate_id}")
                print(f"Return code: {result.returncode}")
                if result.stderr:
                    print(f"STDERR: {result.stderr}")
                if result.stdout:
                    print(f"STDOUT (last 1000 chars): {result.stdout[-1000:]}")
                
                # 保存调试文件
                debug_tex_path = Path("uploads") / f"debug_resume_{candidate_id}.tex"
                debug_tex_path.parent.mkdir(exist_ok=True)
                with open(debug_tex_path, 'w', encoding='utf-8') as f:
                    f.write(latex_content)
                print(f"Debug .tex file saved to: {debug_tex_path}")
                
                # 如果OpenAI生成的LaTeX失败，尝试使用占位符
                if not hasattr(self, '_tried_placeholder'):
                    print(f"Trying placeholder LaTeX for candidate {candidate_id}")
                    self._tried_placeholder = True
                    placeholder_latex = self._generate_placeholder_latex(candidate)
                    delattr(self, '_tried_placeholder')  # 清除标记
                    return self._compile_latex_to_pdf(placeholder_latex, candidate_id)
                else:
                    delattr(self, '_tried_placeholder')  # 清除标记
                    return None
                
        except subprocess.TimeoutExpired:
            print(f"LaTeX compilation timed out for candidate {candidate_id}")
            import shutil
            shutil.rmtree(temp_dir, ignore_errors=True)
            return None
        except Exception as e:
            print(f"Error compiling LaTeX: {e}")
            return None
        finally:
            # 清理临时目录
            if 'temp_dir' in locals():
                import shutil
                shutil.rmtree(temp_dir, ignore_errors=True)

    def _preprocess_latex_content(self, latex_content: str) -> str:
        """预处理LaTeX内容，移除可能导致编译失败的元素"""
        
        # 移除可能的外部文件引用
        latex_content = re.sub(r'\\input\{[^}]+\}', '', latex_content)
        latex_content = re.sub(r'\\include\{[^}]+\}', '', latex_content)
        
        # 确保必要的包被包含
        required_packages = [
            r'\usepackage[utf8]{inputenc}',
            r'\usepackage{xcolor}', 
            r'\usepackage{geometry}',
            r'\usepackage{enumitem}'
        ]
        
        # 检查是否包含必要的包，如果没有则添加
        for package in required_packages:
            if package not in latex_content:
                # 在\documentclass之后添加包
                latex_content = re.sub(
                    r'(\\documentclass\{[^}]+\})',
                    f'\\1\n{package}',
                    latex_content
                )
        
        # 确保有geometry设置
        if r'\geometry{' not in latex_content and r'\usepackage{geometry}' in latex_content:
            latex_content = re.sub(
                r'(\\usepackage\{geometry\})',
                r'\1\n\\geometry{margin=1in}',
                latex_content
            )
        
        return latex_content


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
        while latex_lines and latex_lines[-1].strip() in ['```', '```latex', '']:
            latex_lines.pop()
        
        latex_content = '\n'.join(latex_lines)
    else:
        # 如果找不到合适的开始位置，使用原始内容
        latex_content = latex_response
    
    # 移除可能的markdown代码块标记
    latex_content = re.sub(r'^```(?:latex)?\s*\n', '', latex_content, flags=re.MULTILINE)
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


class EmbeddingProcessor:

    def __init__(self, model_name: str = 'all-mpnet-base-v2'):
        """初始化嵌入处理器"""
        self.model = SentenceTransformer(model_name)

    def generate_embedding(self, text: str) -> np.ndarray:
        """生成文本嵌入"""
        # 清理文本
        cleaned_text = self._clean_text(text)
        # 生成嵌入
        embedding = self.model.encode(
            cleaned_text,
            show_progress_bar=True,
        )
        return embedding

    def _clean_text(self, text: str) -> str:
        """清理文本，移除特殊字符和多余空格"""
        # 移除HTML标签
        text = re.sub(r'<[^>]+>', '', text)
        # 移除特殊字符，保留字母、数字、空格和基本标点
        text = re.sub(r'[^\w\s\.\,\!\?\;\:\-\(\)]', '', text)
        # 移除多余空格
        text = re.sub(r'\s+', ' ', text).strip()
        return text

    def calculate_similarity(
        self,
        embedding1: np.ndarray,
        embedding2: np.ndarray,
    ) -> float:
        """计算两个嵌入之间的余弦相似度"""
        # 确保是2D数组
        if embedding1.ndim == 1:
            embedding1 = embedding1.reshape(1, -1)
        if embedding2.ndim == 1:
            embedding2 = embedding2.reshape(1, -1)

        similarity = cosine_similarity(embedding1, embedding2)[0][0]
        return float(similarity)


class CandidateProcessor:

    def __init__(self, embedding_processor: EmbeddingProcessor):
        self.embedding_processor = embedding_processor

    def process_candidates(self, candidates: List[Dict]) -> List[Dict]:
        """处理候选人列表，为每个候选人生成嵌入"""
        processed_candidates = []

        for candidate in candidates:
            # 提取候选人信息
            candidate_id = candidate.get('id', str(uuid.uuid4()))
            name = candidate.get('name', f'Candidate_{candidate_id[:8]}')
            info = candidate.get('info', '')
            resume: str = candidate.get('resume', '')
            resume_text = extract_text_from_pdf_base64(resume)
            if not resume_text.strip():
                continue

            # 生成嵌入
            embedding = self.embedding_processor.generate_embedding(
                resume_text)

            processed_candidate = {
                'id': candidate_id,
                'name': name,
                'resume': resume_text,
                'embedding': embedding.tolist(),  # 转换为列表以便JSON序列化
                'summary': self._generate_summary(name, resume_text)
            }

            processed_candidates.append(processed_candidate)

        return processed_candidates

    def _generate_summary(self, name: str, resume_text: str) -> str:
        """生成候选人摘要（简化版本）"""
        # 提取关键信息
        lines = resume_text.split('\n')
        key_info = []

        # 查找常见的关键词
        keywords = [
            'experience', 'skills', 'education', 'project', 'work', 'job'
        ]

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


class RecommendationEngine:

    def __init__(self, embedding_processor: EmbeddingProcessor):
        self.embedding_processor = embedding_processor

    def find_top_candidates(
        self,
        job_description: str,
        candidates: List[Dict],
        top_k: int = 10,
        min_similarity: float = 0.1,
    ) -> List[Dict]:
        """找到最匹配的候选人"""
        if not candidates:
            return []

        # 生成职位描述的嵌入
        job_embedding = self.embedding_processor.generate_embedding(
            job_description)

        # 计算每个候选人的相似度
        candidate_scores = []

        for candidate in candidates:
            if 'embedding' not in candidate:
                continue

            # 将嵌入转换回numpy数组
            candidate_embedding = np.array(candidate['embedding'])

            # 计算相似度
            similarity = self.embedding_processor.calculate_similarity(
                job_embedding,
                candidate_embedding,
            )

            if True or (similarity >= min_similarity):
                # Generate annotated resume using OpenAI and LaTeX
                annotated_resume_base64 = self._generate_annotated_resume(
                    job_description, candidate)

                candidate_scores.append(
                    {
                        'id': candidate['id'],
                        'name': candidate['name'],
                        'similarity_score': similarity,
                        'summary': candidate.get('summary', ''),
                        'annotated_resume': annotated_resume_base64,
                    }, )

        # 按相似度排序
        candidate_scores.sort(
            key=lambda x: x['similarity_score'],
            reverse=True,
        )

        # 返回前top_k个候选人
        return candidate_scores[:top_k]

    def _generate_annotated_resume(self, job_description: str,
                                   candidate: Dict) -> str:
        """
        Generate an annotated resume using OpenAI and LaTeX compilation
        
        Args:
            job_description: The job description to match against
            candidate: Candidate dictionary with resume text
            
        Returns:
            Base64 encoded PDF of the annotated resume
        """
        try:
            # Step 1: 在查询OpenAI前先处理简历文本
            processed_candidate = candidate.copy()
            if 'resume' in processed_candidate:
                processed_candidate['resume'] = escape_latex_chars(processed_candidate['resume'])
            
            # Step 1: Query OpenAI for LaTeX annotated resume
            latex_content = self._query_openai_for_latex(
                job_description, processed_candidate)

            # Step 2: Compile LaTeX to PDF
            pdf_path = self._compile_latex_to_pdf(latex_content,
                                                  candidate['id'])

            # Step 3: Convert PDF to base64
            if pdf_path and pdf_path.exists():
                with open(pdf_path, 'rb') as pdf_file:
                    pdf_base64 = base64.b64encode(
                        pdf_file.read()).decode('utf-8')

                # Clean up temporary files
                pdf_path.unlink()
                return pdf_base64
            else:
                print(
                    f"Failed to generate PDF for candidate {candidate['id']}")
                return ""

        except Exception as e:
            print(f"Error generating annotated resume: {e}")
            return ""

    def _query_openai_for_latex(
        self,
        job_description: str,
        candidate: Dict,
    ) -> str:
        """
        Query OpenAI to generate LaTeX annotated resume
        """
        try:
            client = openai.OpenAI(api_key=OPENAI_API_KEY)

            # 更严格的提示词，强调输出格式
            prompt = f"""
            Create a professional LaTeX resume document. IMPORTANT: Your response must contain ONLY the LaTeX code, no explanations or markdown formatting.

            Job Description:
            {job_description}

            Candidate Resume (already LaTeX-escaped):
            {candidate.get('resume', '')}

            Requirements:
            1. Start with \\documentclass{{article}}
            2. Include necessary packages: inputenc, xcolor, geometry, enumitem
            3. Use \\textbf{{}} to highlight relevant skills
            4. Use \\textcolor{{blue}}{{}} for skills matching job requirements
            5. Add \\textcolor{{red}}{{[ANNOTATION: explanation]}} for key matches
            6. Create sections: Summary, Experience, Skills, Education
            7. DO NOT use \\input or \\include commands
            8. DO NOT include any text outside the LaTeX code
            9. Ensure the document is complete and self-contained

            Output only valid LaTeX code starting with \\documentclass and ending with \\end{{document}}.
            """

            response = client.chat.completions.create(
                model="gpt-4",
                messages=[{
                    "role": "user",
                    "content": prompt
                }],
                max_tokens=4000,
                temperature=0.3,
            )

            latex_response = response.choices[0].message.content
            
            # 清理返回的LaTeX代码
            cleaned_latex = clean_latex_response(latex_response)
            
            return cleaned_latex

        except Exception as e:
            print(f"Error querying OpenAI: {e}")
            # 使用占位符实现作为后备
            return self._generate_placeholder_latex(candidate)

    def _generate_placeholder_latex(self, candidate: Dict) -> str:
        """Generate a simple LaTeX document as placeholder"""
        # 确保候选人简历文本被转义
        resume_text = escape_latex_chars(candidate.get('resume', 'No resume content available'))
        candidate_name = escape_latex_chars(candidate.get('name', 'Candidate'))
        
        # 改进的占位符模板，更像真实简历
        latex_content = f"""\\documentclass{{article}}
\\usepackage[utf8]{{inputenc}}
\\usepackage{{xcolor}}
\\usepackage{{geometry}}
\\usepackage{{enumitem}}
\\geometry{{margin=1in}}

\\title{{\\textbf{{{candidate_name}}}}}
\\author{{}}
\\date{{}}

\\begin{{document}}

\\maketitle

\\section{{Professional Summary}}
\\textcolor{{blue}}{{[ANNOTATION: This candidate demonstrates strong alignment with the position requirements]}}

\\section{{Experience and Qualifications}}
{resume_text}

\\section{{Key Strengths}}
\\textcolor{{red}}{{[ANNOTATION: Highlighted relevant skills and experiences that match the job description]}}

\\begin{{itemize}}
\\item Strong technical background relevant to the position
\\item Proven experience in related fields
\\item Excellent communication and collaboration skills
\\end{{itemize}}

\\section{{Match Analysis}}
\\textcolor{{blue}}{{[ANNOTATION: This candidate's profile shows good potential for the role based on their background and experience]}}

\\end{{document}}"""
        
        return latex_content

    def _compile_latex_to_pdf(
        self,
        latex_content: str,
        candidate_id: str,
    ) -> Path:
        """
        Compile LaTeX content to PDF using pdflatex
        """
        try:
            # 预处理LaTeX内容，移除可能的问题
            latex_content = self._preprocess_latex_content(latex_content)
            
            # Create temporary directory for LaTeX compilation
            temp_dir = Path(tempfile.mkdtemp())
            tex_file = temp_dir / f"resume_{candidate_id}.tex"
            pdf_file = temp_dir / f"resume_{candidate_id}.pdf"

            # Write LaTeX content to file
            with open(tex_file, 'w', encoding='utf-8') as f:
                f.write(latex_content)

            # 多次编译以处理引用
            for attempt in range(2):  # 通常2次编译足够
                result = subprocess.run(
                    [
                        'pdflatex', '-output-directory',
                        str(temp_dir), '-interaction=nonstopmode',
                        str(tex_file)
                    ],
                    capture_output=True,
                    text=True,
                    cwd=temp_dir,
                    timeout=30
                )
                
                # 如果第一次编译成功，进行第二次编译处理引用
                if attempt == 0 and result.returncode == 0:
                    continue
                elif attempt == 1 or result.returncode == 0:
                    break

            if result.returncode == 0 and pdf_file.exists():
                # Move PDF to uploads directory
                final_pdf_path = Path("uploads") / f"annotated_resume_{candidate_id}.pdf"
                final_pdf_path.parent.mkdir(exist_ok=True)

                import shutil
                shutil.copy2(pdf_file, final_pdf_path)
                shutil.rmtree(temp_dir)

                return final_pdf_path
            else:
                # 详细的错误信息
                print(f"LaTeX compilation failed for candidate {candidate_id}")
                print(f"Return code: {result.returncode}")
                if result.stderr:
                    print(f"STDERR: {result.stderr}")
                if result.stdout:
                    print(f"STDOUT (last 1000 chars): {result.stdout[-1000:]}")
                
                # 保存调试文件
                debug_tex_path = Path("uploads") / f"debug_resume_{candidate_id}.tex"
                debug_tex_path.parent.mkdir(exist_ok=True)
                with open(debug_tex_path, 'w', encoding='utf-8') as f:
                    f.write(latex_content)
                print(f"Debug .tex file saved to: {debug_tex_path}")
                
                # 如果OpenAI生成的LaTeX失败，尝试使用占位符
                if not hasattr(self, '_tried_placeholder'):
                    print(f"Trying placeholder LaTeX for candidate {candidate_id}")
                    self._tried_placeholder = True
                    placeholder_latex = self._generate_placeholder_latex(candidate)
                    delattr(self, '_tried_placeholder')  # 清除标记
                    return self._compile_latex_to_pdf(placeholder_latex, candidate_id)
                else:
                    delattr(self, '_tried_placeholder')  # 清除标记
                    return None
                
        except subprocess.TimeoutExpired:
            print(f"LaTeX compilation timed out for candidate {candidate_id}")
            import shutil
            shutil.rmtree(temp_dir, ignore_errors=True)
            return None
        except Exception as e:
            print(f"Error compiling LaTeX: {e}")
            return None
        finally:
            # 清理临时目录
            if 'temp_dir' in locals():
                import shutil
                shutil.rmtree(temp_dir, ignore_errors=True)

    def _preprocess_latex_content(self, latex_content: str) -> str:
        """预处理LaTeX内容，移除可能导致编译失败的元素"""
        
        # 移除可能的外部文件引用
        latex_content = re.sub(r'\\input\{[^}]+\}', '', latex_content)
        latex_content = re.sub(r'\\include\{[^}]+\}', '', latex_content)
        
        # 确保必要的包被包含
        required_packages = [
            r'\usepackage[utf8]{inputenc}',
            r'\usepackage{xcolor}', 
            r'\usepackage{geometry}',
            r'\usepackage{enumitem}'
        ]
        
        # 检查是否包含必要的包，如果没有则添加
        for package in required_packages:
            if package not in latex_content:
                # 在\documentclass之后添加包
                latex_content = re.sub(
                    r'(\\documentclass\{[^}]+\})',
                    f'\\1\n{package}',
                    latex_content
                )
        
        # 确保有geometry设置
        if r'\geometry{' not in latex_content and r'\usepackage{geometry}' in latex_content:
            latex_content = re.sub(
                r'(\\usepackage\{geometry\})',
                r'\1\n\\geometry{margin=1in}',
                latex_content
            )
        
        return latex_content


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