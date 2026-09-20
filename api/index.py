import os
import sys

# Set environment flag for Vercel serverless environment
os.environ.setdefault("VERCEL", "1")

# Add backend directory to Python sys.path
root_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
backend_dir = os.path.join(root_dir, "backend")

if backend_dir not in sys.path:
    sys.path.insert(0, backend_dir)
if root_dir not in sys.path:
    sys.path.insert(0, root_dir)

from fastapi import FastAPI
from app.main import app as main_app

# Create Vercel ASGI serverless handler
# Mounts main_app at both '/api' and '/' to handle any routed path seamlessly
app = FastAPI(docs_url=None, redoc_url=None, openapi_url=None)
app.mount("/api", main_app)
app.mount("/", main_app)
