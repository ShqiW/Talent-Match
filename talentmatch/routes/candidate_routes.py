"""
候选人相关路由
"""
from flask import Blueprint, request, jsonify
from talentmatch.services.candidate_service import CandidateService
from talentmatch.utils import allowed_file, extract_text_from_file, create_upload_folder
import os
import uuid
from werkzeug.utils import secure_filename


def create_candidate_routes(candidate_service: CandidateService, app_config):
    """创建候选人路由"""
    candidate_bp = Blueprint('candidates', __name__)
    
    @candidate_bp.route('/api/candidates', methods=['POST'])
    def add_candidates():
        """添加候选人简历"""
        try:
            data = request.get_json()
            
            if not data:
                return jsonify({'error': 'No data provided'}), 400
            
            candidates_data = data.get('candidates', [])
            
            if not candidates_data:
                return jsonify({'error': 'No candidates provided'}), 400
            
            # 使用服务层处理
            result = candidate_service.add_candidates_from_data(candidates_data)
            
            return jsonify(result), 201
            
        except ValueError as e:
            return jsonify({'error': str(e)}), 400
        except Exception as e:
            return jsonify({'error': f'Error processing candidates: {str(e)}'}), 500
    
    @candidate_bp.route('/api/candidates/upload', methods=['POST'])
    def upload_candidates():
        """通过文件上传添加候选人"""
        try:
            if 'files' not in request.files:
                return jsonify({'error': 'No files provided'}), 400
            
            files = request.files.getlist('files')
            
            if not files or files[0].filename == '':
                return jsonify({'error': 'No files selected'}), 400
            
            uploaded_candidates = []
            
            for file in files:
                if file and allowed_file(file.filename, app_config['ALLOWED_EXTENSIONS']):
                    # 安全地保存文件名
                    filename = secure_filename(file.filename)
                    file_path = os.path.join(app_config['UPLOAD_FOLDER'], filename)
                    
                    # 保存文件
                    file.save(file_path)
                    
                    # 提取文本
                    resume_text = extract_text_from_file(file_path)
                    
                    if resume_text.strip():
                        # 创建候选人对象
                        candidate = {
                            'id': str(uuid.uuid4()),
                            'name': os.path.splitext(filename)[0],  # 使用文件名作为姓名
                            'resume': resume_text
                        }
                        
                        uploaded_candidates.append(candidate)
                    
                    # 删除临时文件
                    os.remove(file_path)
            
            if not uploaded_candidates:
                return jsonify({'error': 'No valid candidates found in uploaded files'}), 400
            
            # 使用服务层处理
            result = candidate_service.add_candidates_from_files(uploaded_candidates)
            
            return jsonify(result), 201
            
        except ValueError as e:
            return jsonify({'error': str(e)}), 400
        except Exception as e:
            return jsonify({'error': f'Error uploading candidates: {str(e)}'}), 500
    
    @candidate_bp.route('/api/candidates', methods=['GET'])
    def get_candidates():
        """获取所有候选人列表"""
        try:
            result = candidate_service.get_all_candidates()
            return jsonify(result), 200
            
        except Exception as e:
            return jsonify({'error': f'Error retrieving candidates: {str(e)}'}), 500
    
    @candidate_bp.route('/api/candidates', methods=['DELETE'])
    def clear_candidates():
        """清空所有候选人"""
        try:
            result = candidate_service.clear_all_candidates()
            return jsonify(result), 200
            
        except Exception as e:
            return jsonify({'error': f'Error clearing candidates: {str(e)}'}), 500
    
    @candidate_bp.route('/api/candidates/<candidate_id>', methods=['DELETE'])
    def delete_candidate(candidate_id):
        """删除特定候选人"""
        try:
            result = candidate_service.delete_candidate(candidate_id)
            return jsonify(result), 200
            
        except ValueError as e:
            return jsonify({'error': str(e)}), 404
        except Exception as e:
            return jsonify({'error': f'Error deleting candidate: {str(e)}'}), 500
    
    return candidate_bp 