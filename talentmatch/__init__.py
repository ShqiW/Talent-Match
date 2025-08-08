import environs
from pathlib import Path

env = environs.Env()
env.read_env(Path.cwd() / ".env")  # Read environment variables from .env file
OPENAI_API_KEY = env.str('OPENAI_API_KEY')
EMBEDDING_MODEL = env.str('EMBEDDING_MODEL')
