from typing import List, Dict
import numpy as np
import base64
import tempfile, subprocess, re
import openai
from pathlib import Path
from talentmatch import OPENAI_API_KEY
from talentmatch import DEEPSEEK_API_KEY
from talentmatch.utils import escape_latex_chars, clean_latex_response
from talentmatch.etc.embeddingprocessor import EmbeddingProcessor


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
        """Find the most matching candidates"""
        if not candidates:
            return []

        # Generate job description embedding
        job_embedding = self.embedding_processor.generate_embedding(
            job_description)

        ideal_candidate = self._query_openai_for_ideal_candidate(
            job_description)

        ideal_candidate_embedding = self.embedding_processor.generate_embedding(
            ideal_candidate[:max([len(x["resume_text"]) for x in candidates])])

        optimal_similarity = self.embedding_processor.calculate_similarity(
            job_embedding, ideal_candidate_embedding)

        # Calculate similarity for each candidate
        candidate_scores = []

        for candidate in candidates:
            if 'embedding' not in candidate:
                continue

            # Convert embedding back to numpy array
            candidate_embedding = np.array(candidate['embedding'])

            # Calculate similarity
            similarity = self.embedding_processor.calculate_similarity(
                job_embedding,
                candidate_embedding,
            ) / optimal_similarity

            if True or (similarity >= min_similarity):
                # Generate annotated resume using OpenAI and LaTeX
                # annotated_resume_base64 = self._generate_annotated_resume(
                #     job_description, candidate)

                summary = self._query_openai_for_summary(
                    job_description, candidate["resume_text"])

                candidate_scores.append(
                    {
                        'id': candidate['id'],
                        'name': candidate['name'],
                        'similarity_score': similarity,
                        # 'summary': candidate.get('summary', ''),
                        "summary": summary,
                        # 'annotated_resume': annotated_resume_base64,
                        'resume_text': candidate["resume_text"],
                        'resume': candidate.get('resume', ''),
                    }, )

        # Sort by similarity
        candidate_scores.sort(
            key=lambda x: x['similarity_score'],
            reverse=True,
        )

        # Return top k candidates
        return candidate_scores[:top_k]

    def _query_openai_for_latex(
        self,
        job_description: str,
        candidate: Dict,
    ) -> str:
        """
        Query DeepSeek to generate LaTeX annotated resume
        """
        try:
            # client = openai.OpenAI(api_key=OPENAI_API_KEY)
            client = openai.OpenAI(api_key=DEEPSEEK_API_KEY,
                                   base_url="https://api.deepseek.com")

            # More strict prompts, emphasize output format
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
                model="deepseek-chat",
                messages=[{
                    "role": "user",
                    "content": prompt
                }],
                max_tokens=4000,
                temperature=0.3,
            )

            latex_response = response.choices[0].message.content

            # Clean returned LaTeX code
            cleaned_latex = clean_latex_response(latex_response)

            return cleaned_latex

        except Exception as e:
            print(f"Error querying OpenAI: {e}")
            # Use placeholder implementation as fallback
            return self._generate_placeholder_latex(candidate)

    def _query_openai_for_summary(
        self,
        job_description: str,
        candidate: str,
    ) -> str:
        """
        Query DeepSeek to generate LaTeX annotated resume
        """
        # client = openai.OpenAI(api_key=OPENAI_API_KEY)
        client = openai.OpenAI(api_key=DEEPSEEK_API_KEY,
                               base_url="https://api.deepseek.com")

        # More strict prompts, emphasize output format
        prompt = f"""
        Given the following job description and candidate resume, return a summary of the candidate's qualifications and whether they match the job requirements in plain text  in plain text in plain text in plain text in plain text.

        Job Description:
        {job_description}

        Candidate Resume (already LaTeX-escaped):
        {candidate}


        """

        response = client.chat.completions.create(
            model="deepseek-chat",
            messages=[{
                "role": "user",
                "content": prompt
            }],
            max_tokens=4000,
            temperature=0.2,
        )

        latex_response = response.choices[0].message.content

        return latex_response

    def _query_openai_for_ideal_candidate(
        self,
        job_description: str,
    ) -> str:
        """
        Query OpenAI to generate LaTeX annotated resume
        """
        # client = openai.OpenAI(api_key=OPENAI_API_KEY)
        client = openai.OpenAI(api_key=DEEPSEEK_API_KEY,
                               base_url="https://api.deepseek.com")

        # More strict prompts, emphasize output format
        prompt = f"""
        In a pipeline where multiple candidates are being evaluated for a job position, it is useful to imagine the ideal candidate who perfectly fits the job requirements as the upper bound. Given the following job description, return a resume style description of the ideal candidate in plain text.

        Job Description:
        {job_description}

        """

        response = client.chat.completions.create(
            model="deepseek-chat",
            messages=[{
                "role": "user",
                "content": prompt
            }],
            max_tokens=4000,
            temperature=0.3,
        )

        latex_response = response.choices[0].message.content

        return latex_response

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
            # Step 1: Process resume text before querying OpenAI
            processed_candidate = candidate.copy()
            if 'resume' in processed_candidate:
                processed_candidate['resume'] = escape_latex_chars(
                    processed_candidate['resume'])

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
            # client = openai.OpenAI(api_key=OPENAI_API_KEY)
            client = openai.OpenAI(api_key=DEEPSEEK_API_KEY,
                                   base_url="https://api.deepseek.com")

            # More strict prompts, emphasize output format
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
                model="deepseek-chat",
                messages=[{
                    "role": "user",
                    "content": prompt
                }],
                max_tokens=4000,
                temperature=0.3,
            )

            latex_response = response.choices[0].message.content

            # Clean returned LaTeX code
            cleaned_latex = clean_latex_response(latex_response)

            return cleaned_latex

        except Exception as e:
            print(f"Error querying OpenAI: {e}")
            # Use placeholder implementation as fallback
            return self._generate_placeholder_latex(candidate)

    def _generate_placeholder_latex(self, candidate: Dict) -> str:
        """Generate a simple LaTeX document as placeholder"""
        # Ensure candidate resume text is escaped
        resume_text = escape_latex_chars(
            candidate.get('resume', 'No resume content available'))
        candidate_name = escape_latex_chars(candidate.get('name', 'Candidate'))

        # Improved placeholder template, more like real resume
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
            # Preprocess LaTeX content, remove possible issues
            latex_content = self._preprocess_latex_content(latex_content)

            # Create temporary directory for LaTeX compilation
            temp_dir = Path(tempfile.mkdtemp())
            tex_file = temp_dir / f"resume_{candidate_id}.tex"
            pdf_file = temp_dir / f"resume_{candidate_id}.pdf"

            # Write LaTeX content to file
            with open(tex_file, 'w', encoding='utf-8') as f:
                f.write(latex_content)

            # Multiple compilations to handle references
            for attempt in range(2):  # Usually 2 compilations are enough
                result = subprocess.run([
                    'pdflatex', '-output-directory',
                    str(temp_dir), '-interaction=nonstopmode',
                    str(tex_file)
                ],
                                        capture_output=True,
                                        text=True,
                                        cwd=temp_dir,
                                        timeout=30)

                # If first compilation succeeds, perform second compilation to handle references
                if attempt == 0 and result.returncode == 0:
                    continue
                elif attempt == 1 or result.returncode == 0:
                    break

            if result.returncode == 0 and pdf_file.exists():
                # Move PDF to uploads directory
                final_pdf_path = Path(
                    "uploads") / f"annotated_resume_{candidate_id}.pdf"
                final_pdf_path.parent.mkdir(exist_ok=True)

                import shutil
                shutil.copy2(pdf_file, final_pdf_path)
                shutil.rmtree(temp_dir)

                return final_pdf_path
            else:
                # Detailed error information
                print(f"LaTeX compilation failed for candidate {candidate_id}")
                print(f"Return code: {result.returncode}")
                if result.stderr:
                    print(f"STDERR: {result.stderr}")
                if result.stdout:
                    print(f"STDOUT (last 1000 chars): {result.stdout[-1000:]}")

                # Save debug files
                debug_tex_path = Path(
                    "uploads") / f"debug_resume_{candidate_id}.tex"
                debug_tex_path.parent.mkdir(exist_ok=True)
                with open(debug_tex_path, 'w', encoding='utf-8') as f:
                    f.write(latex_content)
                print(f"Debug .tex file saved to: {debug_tex_path}")

                # If OpenAI-generated LaTeX fails, try using placeholder
                if not hasattr(self, '_tried_placeholder'):
                    print(
                        f"Trying placeholder LaTeX for candidate {candidate_id}"
                    )
                    self._tried_placeholder = True
                    placeholder_latex = self._generate_placeholder_latex(
                        candidate)
                    delattr(self, '_tried_placeholder')  # Clear flag
                    return self._compile_latex_to_pdf(placeholder_latex,
                                                      candidate_id)
                else:
                    delattr(self, '_tried_placeholder')  # Clear flag
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
            # Clean temporary directory
            if 'temp_dir' in locals():
                import shutil
                shutil.rmtree(temp_dir, ignore_errors=True)

    def _preprocess_latex_content(self, latex_content: str) -> str:
        """Preprocess LaTeX content, remove elements that may cause compilation failures"""

        # Remove possible external file references
        latex_content = re.sub(r'\\input\{[^}]+\}', '', latex_content)
        latex_content = re.sub(r'\\include\{[^}]+\}', '', latex_content)

        # Ensure necessary packages are included
        required_packages = [
            r'\usepackage[utf8]{inputenc}', r'\usepackage{xcolor}',
            r'\usepackage{geometry}', r'\usepackage{enumitem}'
        ]

        # Check if necessary packages are included, if not add them
        for package in required_packages:
            if package not in latex_content:
                # Add package after \documentclass
                latex_content = re.sub(r'(\\documentclass\{[^}]+\})',
                                       f'\\1\n{package}', latex_content)

        # Ensure geometry is set
        if r'\geometry{' not in latex_content and r'\usepackage{geometry}' in latex_content:
            latex_content = re.sub(r'(\\usepackage\{geometry\})',
                                   r'\1\n\\geometry{margin=1in}',
                                   latex_content)

        return latex_content
