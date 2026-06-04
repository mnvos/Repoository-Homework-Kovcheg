import os
from dotenv import load_dotenv
from fastapi import FastAPI, HTTPException, Request, Depends, Header, Form, Query
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.templating import Jinja2Templates
from telegram import Update
from bot.main import build_application
from pydantic import BaseModel, Field
from typing import Dict, Any, Optional

load_dotenv()

TELEGRAM_BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")
WEBHOOK_URL = os.getenv("WEBHOOK_URL", "")
KNOWLEDGE_PATH = os.getenv("DATABASE_URL", "./data/knowledge_base.json")
WEBHOOK_SECRET = os.getenv("WEBHOOK_SECRET", "")
PERSISTENCE_PATH = os.getenv("PERSISTENCE_PATH", "./data/bot_persistence")

if not TELEGRAM_BOT_TOKEN:
    raise RuntimeError("TELEGRAM_BOT_TOKEN is required in environment variables")

app = FastAPI(title="LK HR Assistant API")
telegram_app = build_application(TELEGRAM_BOT_TOKEN, KNOWLEDGE_PATH, PERSISTENCE_PATH)

templates = Jinja2Templates(directory="templates")

ADMIN_API_KEY = os.getenv("ADMIN_API_KEY", "")


def require_admin(x_api_key: Optional[str] = Header(None, alias="X-API-KEY")) -> None:
    if not ADMIN_API_KEY:
        raise HTTPException(status_code=401, detail="Admin API key not configured")
    if x_api_key != ADMIN_API_KEY:
        raise HTTPException(status_code=401, detail="Unauthorized")


def require_admin_form(api_key: Optional[str] = Form(None), x_api_key: Optional[str] = Header(None, alias="X-API-KEY")) -> None:
    if not ADMIN_API_KEY:
        raise HTTPException(status_code=401, detail="Admin API key not configured")
    if (api_key or x_api_key) != ADMIN_API_KEY:
        raise HTTPException(status_code=401, detail="Unauthorized")


def require_admin_key(api_key: Optional[str] = Query(None), x_api_key: Optional[str] = Header(None, alias="X-API-KEY")) -> None:
    if not ADMIN_API_KEY:
        raise HTTPException(status_code=401, detail="Admin API key not configured")
    if (api_key or x_api_key) != ADMIN_API_KEY:
        raise HTTPException(status_code=401, detail="Unauthorized")


class QuestionIn(BaseModel):
    title: str
    patterns: list = Field(default_factory=list)
    keywords: list = Field(default_factory=list)
    answer: str
    checklist: list = Field(default_factory=list)
    review: str = ""


@app.get("/kb/topics")
async def kb_topics() -> Dict[str, Any]:
    kb = telegram_app.bot_data.get("knowledge")
    return {"topics": kb.list_topics()}


@app.get("/kb/questions/{question_id}")
async def kb_get_question(question_id: str) -> Dict[str, Any]:
    kb = telegram_app.bot_data.get("knowledge")
    q = kb.get_question(question_id)
    if not q:
        raise HTTPException(status_code=404, detail="Question not found")
    return q


@app.post("/kb/questions/{topic_id}")
async def kb_add_question(topic_id: str, payload: QuestionIn, admin: None = Depends(require_admin)) -> Dict[str, Any]:
    kb = telegram_app.bot_data.get("knowledge")
    try:
        question = payload.dict()
        created = kb.add_question(topic_id, question)
        return created
    except ValueError as exc:
        raise HTTPException(status_code=404, detail=str(exc))


@app.put("/kb/questions/{question_id}")
async def kb_update_question(question_id: str, updates: Dict[str, Any], admin: None = Depends(require_admin)) -> Dict[str, Any]:
    kb = telegram_app.bot_data.get("knowledge")
    try:
        updated = kb.update_question(question_id, updates)
        return updated
    except ValueError as exc:
        raise HTTPException(status_code=404, detail=str(exc))


@app.delete("/kb/questions/{question_id}")
async def kb_delete_question(question_id: str, admin: None = Depends(require_admin)) -> Dict[str, Any]:
    kb = telegram_app.bot_data.get("knowledge")
    ok = kb.delete_question(question_id)
    if not ok:
        raise HTTPException(status_code=404, detail="Question not found")
    return {"ok": True}


@app.get("/kb/export")
async def kb_export() -> Dict[str, Any]:
    kb = telegram_app.bot_data.get("knowledge")
    return kb.export_data()


@app.post("/kb/import")
async def kb_import(payload: Dict[str, Any], admin: None = Depends(require_admin)) -> Dict[str, Any]:
    kb = telegram_app.bot_data.get("knowledge")
    if not isinstance(payload, dict) or "topics" not in payload:
        raise HTTPException(status_code=400, detail="Invalid knowledge base format")
    try:
        kb.replace_data(payload)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc))
    return {"ok": True}


@app.on_event("startup")
async def startup_event() -> None:
    if WEBHOOK_URL:
        await telegram_app.initialize()
        await telegram_app.bot.set_webhook(WEBHOOK_URL)
        
        


@app.post("/webhook")
async def telegram_webhook(request: Request, x_telegram_bot_api_secret_token: Optional[str] = Header(None, alias="X-Telegram-Bot-Api-Secret-Token")) -> dict:
    if WEBHOOK_SECRET and x_telegram_bot_api_secret_token != WEBHOOK_SECRET:
        raise HTTPException(status_code=401, detail="Invalid webhook secret")

    payload = await request.json()
    try:
        update = Update.de_json(payload, telegram_app.bot)
    except Exception as exc:
        raise HTTPException(status_code=400, detail=str(exc))

    await telegram_app.process_update(update)
    return {"ok": True}


@app.get("/health")
async def health_check() -> dict:
    return {
        "status": "ok",
        "webhook": WEBHOOK_URL,
        "knowledge_path": KNOWLEDGE_PATH,
    }


@app.get("/admin", response_class=HTMLResponse)
async def admin_index(request: Request, admin: None = Depends(require_admin_key)):
    kb = telegram_app.bot_data.get("knowledge")
    topics = kb.list_topics()
    return templates.TemplateResponse("admin_index.html", {"request": request, "topics": topics})


@app.post("/admin/topic/add")
async def admin_add_topic(request: Request, id: str = Form(...), title: str = Form(...), api_key: Optional[str] = Form(None)):
    require_admin_form(api_key)
    kb = telegram_app.bot_data.get("knowledge")
    # ensure unique id
    for t in kb.list_topics():
        if t.get("id") == id:
            raise HTTPException(status_code=400, detail="Topic id already exists")
    topic = {"id": id, "title": title, "questions": []}
    kb.data.setdefault("topics", []).append(topic)
    kb.save()
    redirect_url = "/admin"
    if api_key:
        redirect_url += f"?api_key={api_key}"
    return RedirectResponse(url=redirect_url, status_code=303)


@app.get("/admin/topic/{topic_id}", response_class=HTMLResponse)
async def admin_view_topic(request: Request, topic_id: str, admin: None = Depends(require_admin_key)):
    kb = telegram_app.bot_data.get("knowledge")
    topic = None
    for t in kb.list_topics():
        if t.get("id") == topic_id:
            topic = t
            break
    if not topic:
        raise HTTPException(status_code=404, detail="Topic not found")
    return templates.TemplateResponse("topic_view.html", {"request": request, "topic": topic})


@app.post("/admin/question/{topic_id}/add")
async def admin_add_question(topic_id: str, title: str = Form(...), patterns: str = Form(""), keywords: str = Form(""), answer: str = Form(""), checklist: str = Form(""), review: str = Form(""), api_key: Optional[str] = Form(None)):
    require_admin_form(api_key)
    kb = telegram_app.bot_data.get("knowledge")
    patt = [p.strip() for p in patterns.split(",") if p.strip()]
    keys = [k.strip() for k in keywords.split(",") if k.strip()]
    cl = [c.strip() for c in checklist.splitlines() if c.strip()]
    question = {"title": title, "patterns": patt, "keywords": keys, "answer": answer, "checklist": cl, "review": review}
    created = kb.add_question(topic_id, question)
    redirect_url = f"/admin/topic/{topic_id}"
    if api_key:
        redirect_url += f"?api_key={api_key}"
    return RedirectResponse(url=redirect_url, status_code=303)


@app.get("/admin/question/{question_id}/edit", response_class=HTMLResponse)
async def admin_edit_question(request: Request, question_id: str, admin: None = Depends(require_admin_key)):
    kb = telegram_app.bot_data.get("knowledge")
    q = kb.get_question(question_id)
    if not q:
        raise HTTPException(status_code=404, detail="Question not found")
    return templates.TemplateResponse("question_edit.html", {"request": request, "question": q})


@app.post("/admin/question/{question_id}/edit")
async def admin_update_question(question_id: str, title: str = Form(...), patterns: str = Form(""), keywords: str = Form(""), answer: str = Form(""), checklist: str = Form(""), review: str = Form(""), api_key: Optional[str] = Form(None)):
    require_admin_form(api_key)
    kb = telegram_app.bot_data.get("knowledge")
    updates = {
        "title": title,
        "patterns": [p.strip() for p in patterns.split(",") if p.strip()],
        "keywords": [k.strip() for k in keywords.split(",") if k.strip()],
        "answer": answer,
        "checklist": [c.strip() for c in checklist.splitlines() if c.strip()],
        "review": review,
    }
    kb.update_question(question_id, updates)
    q = kb.get_question(question_id)
    topic_title = q.get("topic")
    # find topic id
    topic_id = None
    for t in kb.list_topics():
        if t.get("title") == topic_title:
            topic_id = t.get("id")
            break
    redirect_url = "/admin" if not topic_id else f"/admin/topic/{topic_id}"
    if api_key:
        redirect_url += f"?api_key={api_key}"
    return RedirectResponse(url=redirect_url, status_code=303)
