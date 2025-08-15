"""
Recommendation related routes
"""
from flask import Blueprint, request, jsonify
from talentmatch.services.recommendation_service import RecommendationService
from talentmatch import INVITATION_CODE


def create_recommendation_routes(
    recommendation_service: RecommendationService,
    app_config,
):
    """Create recommendation routes"""
    recommendation_bp = Blueprint('recommendations', __name__)

    # @recommendation_bp.route('/api/recommendations', methods=['POST'])
    # def get_recommendations():
    #     """Get candidate recommendations"""
    #     try:
    #         data = request.get_json()

    #         if not data:
    #             return jsonify({'error': 'No data provided'}), 400

    #         job_description = data.get('job_description', '').strip()

    #         if not job_description:
    #             return jsonify({'error': 'Job description is required'}), 400

    #         # Get candidate data - supports two methods:
    #         # 1. Directly passed candidate data from frontend
    #         # 2. Use stored candidate data
    #         candidates_data = data.get('candidates', [])

    #         # Get parameters
    #         top_k = data.get('top_k', app_config['MAX_CANDIDATES'])
    #         min_similarity = data.get(
    #             'min_similarity',
    #             app_config['MIN_SIMILARITY_THRESHOLD'],
    #         )

    #         # Determine which candidate data to use
    #         if candidates_data:
    #             # Use candidate data passed from frontend
    #             candidates_to_process = candidates_data
    #             use_stored_candidates = False
    #         else:
    #             # Use stored candidate data
    #             candidates_to_process = candidate_service.get_candidates_for_recommendation(
    #                 use_stored=True)
    #             use_stored_candidates = True

    #         # Use service layer for processing
    #         result = recommendation_service.get_recommendations(
    #             job_description=job_description,
    #             candidates_data=candidates_to_process
    #             if not use_stored_candidates else None,
    #             top_k=top_k,
    #             min_similarity=min_similarity,
    #         )

    #         return jsonify(result), 200

    #     except ValueError as e:
    #         return jsonify({'error': str(e)}), 400
    #     except Exception as e:
    #         return jsonify(
    #             {'error': f'Error generating recommendations: {str(e)}'}), 500

    @recommendation_bp.route('/api/verify-invitation', methods=['POST'])
    def verify_invitation():
        """Verify invitation code"""
        data = request.get_json() or {}
        configured_codes = INVITATION_CODE
        if len(configured_codes) <= 0:
            # Reject if invitation code not set, prevent bypass
            return jsonify({'error': 'Invitation code not configured'}), 200

        provided_code = (data.get('invitation_code') or '').strip()
        if provided_code not in configured_codes:
            return jsonify({'error':
                            'Invalid or missing invitation code'}), 403

        return jsonify({'valid': True}), 200

    @recommendation_bp.route('/api/match', methods=['POST'])
    def match_candidates():
        """Real-time candidate matching - specifically for frontend direct data input"""
        # try:
        data = request.get_json()

        if not data:
            return jsonify({'error': 'No data provided'}), 400

        # Validate invitation code (if enabled in configuration)
        configured_codes = INVITATION_CODE
        provided_code = (data.get('invitation_code') or '').strip()
        if len(configured_codes) <= 0:
            # Reject if invitation code not set, prevent bypass
            return jsonify({'error': 'Invitation code not configured'}), 200
        if provided_code not in configured_codes:
            return jsonify({'error':
                            'Invalid or missing invitation code'}), 403

        job_description = data.get('job_description', '').strip()
        candidates_data = data.get('candidates')

        if not job_description:
            return jsonify({'error': 'Job description is required'}), 400

        if not candidates_data:
            return jsonify({'error': 'Candidates data is required'}), 400

        # Get parameters
        top_k = data.get('top_k', app_config['MAX_CANDIDATES'])
        min_similarity = data.get(
            'min_similarity',
            app_config['MIN_SIMILARITY_THRESHOLD'],
        )

        # Use service layer for processing
        result = recommendation_service.match_candidates_realtime(
            job_description=job_description,
            candidates_data=candidates_data,
            top_k=top_k,
            min_similarity=min_similarity,
        )

        return jsonify(result), 200

    return recommendation_bp
