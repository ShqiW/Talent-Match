"""
推荐相关路由
"""
from flask import Blueprint, request, jsonify
from talentmatch.services.recommendation_service import RecommendationService
from talentmatch.services.candidate_service import CandidateService


def create_recommendation_routes(
    recommendation_service: RecommendationService,
    candidate_service: CandidateService,
    app_config,
):
    """创建推荐路由"""
    recommendation_bp = Blueprint('recommendations', __name__)

    # @recommendation_bp.route('/api/recommendations', methods=['POST'])
    # def get_recommendations():
    #     """获取候选人推荐"""
    #     try:
    #         data = request.get_json()

    #         if not data:
    #             return jsonify({'error': 'No data provided'}), 400

    #         job_description = data.get('job_description', '').strip()

    #         if not job_description:
    #             return jsonify({'error': 'Job description is required'}), 400

    #         # 获取候选人数据 - 支持两种方式：
    #         # 1. 从前端直接传入候选人数据
    #         # 2. 使用已存储的候选人数据
    #         candidates_data = data.get('candidates', [])

    #         # 获取参数
    #         top_k = data.get('top_k', app_config['MAX_CANDIDATES'])
    #         min_similarity = data.get(
    #             'min_similarity',
    #             app_config['MIN_SIMILARITY_THRESHOLD'],
    #         )

    #         # 确定使用哪些候选人数据
    #         if candidates_data:
    #             # 使用前端传入的候选人数据
    #             candidates_to_process = candidates_data
    #             use_stored_candidates = False
    #         else:
    #             # 使用已存储的候选人数据
    #             candidates_to_process = candidate_service.get_candidates_for_recommendation(
    #                 use_stored=True)
    #             use_stored_candidates = True

    #         # 使用服务层处理
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

    @recommendation_bp.route('/api/match', methods=['POST'])
    def match_candidates():
        """实时匹配候选人 - 专门用于前端直接传入数据"""
        # try:
        data = request.get_json()

        if not data:
            return jsonify({'error': 'No data provided'}), 400

        # 校验邀请代码（如果在配置中启用）
        configured_code = app_config.get('INVITATION_CODE', '')
        if configured_code:
            provided_code = (data.get('invitation_code') or '').strip()
            if provided_code != configured_code:
                return jsonify({'error': 'Invalid or missing invitation code'}), 403

        job_description = data.get('job_description', '').strip()
        candidates_data = data.get('candidates')

        if not job_description:
            return jsonify({'error': 'Job description is required'}), 400

        if not candidates_data:
            return jsonify({'error': 'Candidates data is required'}), 400

        # 获取参数
        top_k = data.get('top_k', app_config['MAX_CANDIDATES'])
        min_similarity = data.get(
            'min_similarity',
            app_config['MIN_SIMILARITY_THRESHOLD'],
        )

        # 使用服务层处理
        result = recommendation_service.match_candidates_realtime(
            job_description=job_description,
            candidates_data=candidates_data,
            top_k=top_k,
            min_similarity=min_similarity,
        )

        return jsonify(result), 200

    return recommendation_bp
