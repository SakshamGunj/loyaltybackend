from fastapi import FastAPI
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles
import os

# This file is only needed if you want to serve dashboard.html directly via FastAPI

def add_dashboard_static(app: FastAPI):
    static_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
    dashboard_path = os.path.join(static_dir, 'dashboard.html')
    if os.path.exists(dashboard_path):
        @app.get('/dashboard', include_in_schema=False)
        def dashboard_html():
            return FileResponse(dashboard_path, media_type='text/html')
    app.mount("/static", StaticFiles(directory=static_dir), name="static")
