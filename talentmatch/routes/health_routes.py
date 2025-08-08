"""
健康检查和基础路由
"""
from flask import Blueprint, jsonify


def create_health_routes():
    """创建健康检查路由"""
    health_bp = Blueprint('health', __name__)
    
    @health_bp.route('/')
    def index():
        """健康检查端点"""
        return jsonify({
            'message': 'Candidate Recommendation Engine API',
            'status': 'running',
            'version': '1.0.0'
        })
    
    @health_bp.route('/api/health')
    def health_check():
        """健康检查端点"""
        return jsonify({
            'status': 'healthy',
            'message': 'API is running successfully'
        })
    
    return health_bp 