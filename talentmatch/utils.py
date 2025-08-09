import os
import re
from werkzeug.datastructures import FileStorage
from io import BytesIO
from pypdf import PdfReader
import base64
from typing import List, Dict
import uuid
from talentmatch import STATIC_DIR


def escape_latex_chars(text: str) -> str:
    """Escape LaTeX special characters"""
    if not text:
        return text

    # First handle possible Unicode problem character sequences
    text = text.replace('\\u', r'\textbackslash{}u')
    text = text.replace('\\n', '\n')  # Keep real line breaks
    text = text.replace('\\t', ' ')  # Convert tabs to spaces
    text = text.replace('\\r', '')  # Remove carriage returns

    # Then handle backslashes to avoid conflicts with other escapes
    text = text.replace('\\', r'\textbackslash{}')

    # Handle other LaTeX special characters
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

    # Handle Unicode characters - replace with ASCII equivalents or remove
    text = text.encode('ascii', errors='ignore').decode('ascii')

    return text


def clean_latex_response(latex_response: str) -> str:
    """Clean LaTeX code returned by OpenAI"""
    # Remove leading explanation text
    lines = latex_response.split('\n')
    latex_start_idx = -1

    # Find the starting position of LaTeX code
    for i, line in enumerate(lines):
        line_stripped = line.strip()
        if line_stripped.startswith('\\documentclass'):
            latex_start_idx = i
            break
        elif '```latex' in line_stripped.lower():
            # If markdown code block found, skip this line
            latex_start_idx = i + 1
            break

    if latex_start_idx == -1:
        # If correct start not found, try to find any LaTeX command starting with \
        for i, line in enumerate(lines):
            if line.strip().startswith('\\'):
                latex_start_idx = i
                break

    if latex_start_idx != -1:
        # Extract LaTeX code from found position
        latex_lines = lines[latex_start_idx:]

        # Remove trailing markdown markers
        while latex_lines and latex_lines[-1].strip() in [
                '```', '```latex', ''
        ]:
            latex_lines.pop()

        latex_content = '\n'.join(latex_lines)
    else:
        # If no suitable start position found, use original content
        latex_content = latex_response

    # Remove possible markdown code block markers
    latex_content = re.sub(r'^```(?:latex)?\s*\n',
                           '',
                           latex_content,
                           flags=re.MULTILINE)
    latex_content = re.sub(r'\n```\s*$', '', latex_content, flags=re.MULTILINE)

    # Ensure document structure exists
    if '\\documentclass' not in latex_content:
        # If no document class declaration, add basic structure
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
    """Check if file extension is allowed"""
    return '.' in filename and \
           filename.rsplit('.', 1)[1].lower() in allowed_extensions


def extract_text_from_file(file_path: str) -> str:
    """Extract text from file (simplified version, mainly handles txt files)"""
    try:
        with open(file_path, 'r', encoding='utf-8') as file:
            return file.read()
    except Exception as e:
        print(f"Error reading file {file_path}: {e}")
        return ""


def create_upload_folder(folder_path: str):
    """Create upload folder"""
    if not os.path.exists(folder_path):
        os.makedirs(folder_path)


def extract_text_from_pdf_file(pdf_file: FileStorage) -> str:
    """
    Extract text from PDF (binary) file uploaded from React Post
    :param pdf_file: werkzeug.datastructures.FileStorage object
    :return: Extracted text content
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
                # Clean text format
                cleaned_text = re.sub(r'\s+', ' ', page_text.strip())
                text_parts.append(cleaned_text)

        # Connect pages with double line breaks, maintain structure
        full_text = '\n\n'.join(text_parts)
        return full_text.strip()

    except Exception as e:
        print(f"Error extracting text from PDF: {e}")
        return ""


def extract_text_from_pdf_base64(pdf_base64: str) -> str:
    """
    Extract text from PDF (binary) file uploaded from React Post
    :param pdf_base64: base64 encoded PDF string
    :return: Extracted text content
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
                # Clean text format
                cleaned_text = re.sub(r'\s+', ' ', page_text.strip())
                text_parts.append(cleaned_text)

        # Connect pages with double line breaks, maintain structure
        full_text = '\n\n'.join(text_parts)
        return full_text.strip()

    except Exception as e:
        print(f"Error extracting text from PDF: {e}")
        return ""


def clean_latex_response(latex_response: str) -> str:
    """Clean LaTeX code returned by OpenAI"""
    # Remove leading explanation text
    lines = latex_response.split('\n')
    latex_start_idx = -1

    # Find the starting position of LaTeX code
    for i, line in enumerate(lines):
        line_stripped = line.strip()
        if line_stripped.startswith('\\documentclass'):
            latex_start_idx = i
            break
        elif '```latex' in line_stripped.lower():
            # If markdown code block found, skip this line
            latex_start_idx = i + 1
            break

    if latex_start_idx == -1:
        # If correct start not found, try to find any LaTeX command starting with \
        for i, line in enumerate(lines):
            if line.strip().startswith('\\'):
                latex_start_idx = i
                break

    if latex_start_idx != -1:
        # Extract LaTeX code from found position
        latex_lines = lines[latex_start_idx:]

        # Remove trailing markdown markers
        while latex_lines and latex_lines[-1].strip() in [
                '```', '```latex', ''
        ]:
            latex_lines.pop()

        latex_content = '\n'.join(latex_lines)
    else:
        # If no suitable start position found, use original content
        latex_content = latex_response

    # Remove possible markdown code block markers
    latex_content = re.sub(r'^```(?:latex)?\s*\n',
                           '',
                           latex_content,
                           flags=re.MULTILINE)
    latex_content = re.sub(r'\n```\s*$', '', latex_content, flags=re.MULTILINE)

    # Ensure document structure exists
    if '\\documentclass' not in latex_content:
        # If no document class declaration, add basic structure
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
    """Generate candidate summary (simplified version)"""
    # Extract key information
    lines = resume_text.split('\n')
    key_info = []

    # Find common keywords
    keywords = ['experience', 'skills', 'education', 'project', 'work', 'job']

    for line in lines:
        line_lower = line.lower()
        if any(keyword in line_lower for keyword in keywords):
            if len(line.strip()) > 10:  # Filter lines that are too short
                key_info.append(line.strip())

    # Generate summary
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
    """Process candidate list, generate embeddings for each candidate"""
    processed_candidates = []

    for candidate in candidates:
        # Extract candidate information
        candidate_id = candidate.get('id', str(uuid.uuid4()))
        name = candidate.get('name', f'Candidate_{candidate_id[:8]}')
        info = candidate.get('info', '')
        resume: str = candidate.get('resume', '')
        # Save resume PDF to STATIC_DIR/pdf/randomname.pdf if resume exists
        if (len(resume) > 0):
            pdf_dir = STATIC_DIR / 'pdf'
            create_upload_folder(pdf_dir)
            pdf_filename = f"{uuid.uuid4().hex}.pdf"
            pdf_path = pdf_dir / pdf_filename
            with open(pdf_path, "wb") as f:
                f.write(base64.b64decode(resume))
            resume_name = pdf_path.name
            resume_text = extract_text_from_pdf_base64(resume).strip()
        else:
            resume_text = ""
            resume_name = ""

        merge_text = info + "\n" + resume_text

        # Generate embedding
        embedding = embedding_processor.generate_embedding(merge_text)

        processed_candidate = {
            'id': candidate_id,
            'name': name,
            'resume_text': merge_text,
            'embedding':
            embedding.tolist(),  # Convert to list for JSON serialization
            'summary': _generate_summary(name, resume_text),
            'resume': resume,
            'resume_name': resume_name
        }

        processed_candidates.append(processed_candidate)

    return processed_candidates
