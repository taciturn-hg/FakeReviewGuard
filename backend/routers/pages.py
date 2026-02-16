from fastapi import APIRouter, Request
from fastapi.templating import Jinja2Templates
from fastapi.responses import HTMLResponse
import os
from pathlib import Path

router = APIRouter(tags=["pages"])

# 获取项目根目录 (假设当前文件在 backend/routers/pages.py)
# backend/routers/pages.py -> backend/routers -> backend -> root
BASE_DIR = Path(__file__).resolve().parent.parent.parent
TEMPLATES_DIR = BASE_DIR / "frontend" / "templates"

templates = Jinja2Templates(directory=str(TEMPLATES_DIR))

@router.get("/", response_class=HTMLResponse)
async def read_root(request: Request):
    return templates.TemplateResponse("index.html", {"request": request, "page": "home"})

@router.get("/analyze", response_class=HTMLResponse)
async def analyze_page(request: Request):
    return templates.TemplateResponse("analyze.html", {"request": request, "page": "analyze"})

@router.get("/dashboard", response_class=HTMLResponse)
async def dashboard_page(request: Request):
    return templates.TemplateResponse("dashboard.html", {"request": request, "page": "dashboard"})

@router.get("/product", response_class=HTMLResponse)
async def product_page(request: Request):
    return templates.TemplateResponse("product.html", {"request": request, "page": "product"})
