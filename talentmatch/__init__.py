import environs
from pathlib import Path
import os

cwd = Path.cwd()
env = environs.Env()
env.read_env(cwd / ".env")  # Read environment variables from .env file
OPENAI_API_KEY = env.str('OPENAI_API_KEY', os.getenv("OPENAI_API_KEY"))
DEEPSEEK_API_KEY = env.str('DEEPSEEK_API_KEY', os.getenv("OPENAI_API_KEY"))
EMBEDDING_MODEL = env.str('EMBEDDING_MODEL', os.getenv("OPENAI_API_KEY"))
INVITATION_CODE = env.str('INVITATION_CODE').strip().split(",")
STATIC_DIR = cwd / "talentmatch" / "static"
