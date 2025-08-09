"""
Health check and basic routes
"""
from flask import Blueprint, jsonify
from flask import  render_template

def create_health_routes():
    """Create health check routes"""
    health_bp = Blueprint('health', __name__)
    
    @health_bp.route('/')
    def index():
        return render_template('index.html')
        return jsonify({
            'message': 'Candidate Recommendation Engine API',
            'status': 'running',
            'version': '1.0.0'
        })
    
    @health_bp.route('/api/health')
    def health_check():
        """Health check endpoint"""
        return jsonify({
            'status': 'healthy',
            'message': 'API is running successfully'
        })
    
    return health_bp 