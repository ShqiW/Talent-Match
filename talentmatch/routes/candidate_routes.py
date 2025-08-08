"""
Candidate related routes
"""
from flask import Blueprint, request, jsonify
from talentmatch.services.candidate_service import CandidateService
from talentmatch.utils import allowed_file, extract_text_from_file, create_upload_folder
import os
import uuid
from werkzeug.utils import secure_filename


def create_candidate_routes(candidate_service: CandidateService, app_config):
    """Create candidate routes"""
    candidate_bp = Blueprint('candidates', __name__)
    
    @candidate_bp.route('/api/candidates', methods=['POST'])
    def add_candidates():
        """Add candidate resumes"""
        try:
            data = request.get_json()
            
            if not data:
                return jsonify({'error': 'No data provided'}), 400
            
            candidates_data = data.get('candidates', [])
            
            if not candidates_data:
                return jsonify({'error': 'No candidates provided'}), 400
            
            # Use service layer for processing
            result = candidate_service.add_candidates_from_data(candidates_data)
            
            return jsonify(result), 201
            
        except ValueError as e:
            return jsonify({'error': str(e)}), 400
        except Exception as e:
            return jsonify({'error': f'Error processing candidates: {str(e)}'}), 500
    
    @candidate_bp.route('/api/candidates/upload', methods=['POST'])
    def upload_candidates():
        """Add candidates via file upload"""
        try:
            if 'files' not in request.files:
                return jsonify({'error': 'No files provided'}), 400
            
            files = request.files.getlist('files')
            
            if not files or files[0].filename == '':
                return jsonify({'error': 'No files selected'}), 400
            
            uploaded_candidates = []
            
            for file in files:
                if file and allowed_file(file.filename, app_config['ALLOWED_EXTENSIONS']):
                    # Safely save filename
                    filename = secure_filename(file.filename)
                    file_path = os.path.join(app_config['UPLOAD_FOLDER'], filename)
                    
                    # Save file
                    file.save(file_path)
                    
                    # Extract text
                    resume_text = extract_text_from_file(file_path)
                    
                    if resume_text.strip():
                        # Create candidate object
                        candidate = {
                            'id': str(uuid.uuid4()),
                            'name': os.path.splitext(filename)[0],  # Use filename as name
                            'resume': resume_text
                        }
                        
                        uploaded_candidates.append(candidate)
                    
                    # Delete temporary file
                    os.remove(file_path)
            
            if not uploaded_candidates:
                return jsonify({'error': 'No valid candidates found in uploaded files'}), 400
            
            # Use service layer for processing
            result = candidate_service.add_candidates_from_files(uploaded_candidates)
            
            return jsonify(result), 201
            
        except ValueError as e:
            return jsonify({'error': str(e)}), 400
        except Exception as e:
            return jsonify({'error': f'Error uploading candidates: {str(e)}'}), 500
    
    @candidate_bp.route('/api/candidates', methods=['GET'])
    def get_candidates():
        """Get all candidate list"""
        try:
            result = candidate_service.get_all_candidates()
            return jsonify(result), 200
            
        except Exception as e:
            return jsonify({'error': f'Error retrieving candidates: {str(e)}'}), 500
    
    @candidate_bp.route('/api/candidates', methods=['DELETE'])
    def clear_candidates():
        """Clear all candidates"""
        try:
            result = candidate_service.clear_all_candidates()
            return jsonify(result), 200
            
        except Exception as e:
            return jsonify({'error': f'Error clearing candidates: {str(e)}'}), 500
    
    @candidate_bp.route('/api/candidates/<candidate_id>', methods=['DELETE'])
    def delete_candidate(candidate_id):
        """Delete specific candidate"""
        try:
            result = candidate_service.delete_candidate(candidate_id)
            return jsonify(result), 200
            
        except ValueError as e:
            return jsonify({'error': str(e)}), 404
        except Exception as e:
            return jsonify({'error': f'Error deleting candidate: {str(e)}'}), 500
    
    return candidate_bp 