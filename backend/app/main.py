from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles
from pathlib import Path
from backend.routers import pages, api

app = FastAPI(title="FakeReviewGuard")

# 获取项目根目录
BASE_DIR = Path(__file__).resolve().parent.parent.parent
STATIC_DIR = BASE_DIR / "frontend" / "js"

# 挂载静态资源
# 将 frontend/js 挂载到 /js
app.mount("/js", StaticFiles(directory=str(STATIC_DIR)), name="js")

# 注册路由
app.include_router(pages.router)
app.include_router(api.router)
