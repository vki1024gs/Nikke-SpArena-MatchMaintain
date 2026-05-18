"""Web 页面路由。"""
from __future__ import annotations

from pathlib import Path

import jinja2
from fastapi import FastAPI, Request
from fastapi.responses import HTMLResponse

from ..config import Settings
from ..core.dependencies import get_match_service


def register_web_routes(app: FastAPI, settings: Settings) -> None:
    templates_dir = Path(__file__).parent / "templates"
    env = jinja2.Environment(
        loader=jinja2.FileSystemLoader(str(templates_dir)),
        autoescape=True,
        cache_size=-1,
    )

    def render(name: str, context: dict) -> HTMLResponse:
        tmpl = env.get_template(name)
        return HTMLResponse(tmpl.render(**context))

    @app.get("/")
    async def index(request: Request, file: str | None = None):
        # Cookie 保存选择
        active_file = file or request.cookies.get("active_file", "")
        if active_file:
            from ..core.dependencies import set_active_file
            set_active_file(active_file)

        service = get_match_service()
        stats = await service.get_stats()
        data_dir = str(settings.data_dir)
        resp = render("pages/index.html", {
            "request": request,
            "stats": stats,
            "active_file": active_file,
            "data_dir": data_dir,
        })
        if active_file:
            resp.set_cookie("active_file", active_file, max_age=86400 * 30)
        return resp

    @app.get("/validate")
    async def validate_page(request: Request):
        if file := request.cookies.get("active_file"):
            from ..core.dependencies import set_active_file
            set_active_file(file)
        from ..core.schema import get_schema
        schema = get_schema()
        return render("pages/validate.html", {
            "request": request,
            "schema": {
                "order": schema.order,
                "fields": {n: {"type": f.type, "label": _label(n)} for n, f in schema.fields.items()},
            },
        })

    @app.get("/matches")
    async def matches_page(request: Request, page: int = 1):
        if file := request.cookies.get("active_file"):
            from ..core.dependencies import set_active_file
            set_active_file(file)
        from ..core.dependencies import get_match_service
        from ..core.schema import get_schema
        service = get_match_service()
        result = await service.get_paginated(page=page, per_page=settings.page_size)
        schema = get_schema()
        return render("pages/matches.html", {
            "request": request,
            "data": result,
            "schema": {
                "order": schema.order,
                "fields": {n: {"type": f.type, "label": _label(n)} for n, f in schema.fields.items()},
            },
        })

    @app.get("/archive")
    async def archive_page(request: Request):
        return render("pages/archive.html", {"request": request})

    @app.get("/history")
    async def history_page(request: Request):
        from ..core.dependencies import get_repository
        repo = get_repository()
        return render("pages/history.html", {"request": request, "git_initialized": repo.is_git_initialized})

    @app.get("/crawler")
    async def crawler_page(request: Request):
        return render("pages/crawler.html", {"request": request})

    @app.get("/ocr")
    async def ocr_page(request: Request):
        return render("pages/ocr.html", {"request": request})


_LABEL_MAP = {
    "id": "ID", "date": "日期", "source": "来源",
    "defender_team": "防守方", "attacker_team": "进攻方",
    "defender_burst": "防守爆裂", "attacker_burst": "进攻爆裂",
    "result": "结果", "margin": "优势", "trust": "可信度",
    "custom_def_tag": "防守标签", "uploader_tag": "上传者标签", "notes": "备注",
}


def _label(name: str) -> str:
    return _LABEL_MAP.get(name, name)
