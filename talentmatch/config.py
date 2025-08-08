import os
import environs
from pathlib import Path

env = environs.Env()
env.read_env(Path.cwd() / ".env")  # 读取 .env 文件中的环境变量


class Config:
    SECRET_KEY = env.str('SECRET_KEY', 'dev-secret-key-change-in-production')
    UPLOAD_FOLDER = 'uploads'
    MAX_CONTENT_LENGTH = 16 * 1024 * 1024  # 16MB max file size
    ALLOWED_EXTENSIONS = {'txt', 'pdf'}

    # API configuration
    MAX_CANDIDATES = 10
    MIN_SIMILARITY_THRESHOLD = 0.1
    # Invitation code for access control (empty disables the check)
    INVITATION_CODE = env.str('INVITATION_CODE', '')
