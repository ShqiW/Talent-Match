from flask import Flask, jsonify
from flask_cors import CORS
from talentmatch.config import Config
from talentmatch.utils import create_upload_folder
from talentmatch.services.candidate_service import CandidateService
from talentmatch.services.recommendation_service import RecommendationService
from talentmatch.routes.health_routes import create_health_routes
from talentmatch.routes.candidate_routes import create_candidate_routes
from talentmatch.routes.recommendation_routes import create_recommendation_routes
from talentmatch import EMBEDDING_MODEL
from talentmatch.etc.embeddingprocessor import EmbeddingProcessor
from talentmatch.etc.recommendengine import RecommendationEngine


def create_app():
    """创建Flask应用"""
    app = Flask(__name__)
    app.config.from_object(Config)

    # 启用CORS
    CORS(app)

    # 创建上传文件夹
    create_upload_folder(app.config['UPLOAD_FOLDER'])

    # 初始化处理器
    embedding_processor = EmbeddingProcessor(EMBEDDING_MODEL)
    recommendation_engine = RecommendationEngine(embedding_processor)

    # 初始化服务
    candidate_service = CandidateService(embedding_processor)
    recommendation_service = RecommendationService(recommendation_engine, )

    # 注册路由
    app.register_blueprint(create_health_routes())
    app.register_blueprint(
        create_candidate_routes(
            candidate_service,
            app.config,
        ))
    app.register_blueprint(
        create_recommendation_routes(
            recommendation_service,
            candidate_service,
            app.config,
        ))

    # 错误处理
    @app.errorhandler(404)
    def not_found(error):
        """404错误处理"""
        return jsonify({'error': 'Endpoint not found'}), 404

    @app.errorhandler(500)
    def internal_error(error):
        """500错误处理"""
        return jsonify({'error': 'Internal server error'}), 500

    return app


if __name__ == '__main__':
    app = create_app()

    print("🚀 Starting Candidate Recommendation Engine...")
    print(f"🎯 Using embedding model: {EMBEDDING_MODEL}")
    print("📊 API endpoints:")
    print("  GET  / - Health check")
    print("  GET  /api/health - Health check")
    print("  POST /api/candidates - Add candidates via JSON")
    print("  POST /api/candidates/upload - Upload candidate files")
    print("  GET  /api/candidates - Get all candidates")
    # print("  POST /api/recommendations - Get recommendations (supports both stored and frontend data)")
    print("  POST /api/match - Real-time matching with frontend data")
    print("  DELETE /api/candidates - Clear all candidates")
    print("  DELETE /api/candidates/<id> - Delete specific candidate")
    print("")
    print("💡 First run will download the model (~1.5GB)")
    print("🌐 Server will start at: http://localhost:5000")

    app.run(debug=True, host='0.0.0.0', port=5000)
