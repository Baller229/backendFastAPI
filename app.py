# app.py
import logging
from fastapi import FastAPI, WebSocket
from contextlib import asynccontextmanager
from dbhandler import PostgresRepository
from worker import MessageProcessor
from websocket import WsController
from logger import setup_logging, get_logger

setup_logging()
log = get_logger("app")

repo = PostgresRepository()
processor = MessageProcessor(repo)
controller = WsController(processor)


@asynccontextmanager
async def lifespan(app: FastAPI):
    log.info("Startup: DB + worker")
    await repo.start()
    await processor.start()
    try:
        yield
    finally:
        log.info("Shutdown")
        await processor.stop()
        await repo.stop()

app = FastAPI(lifespan=lifespan)


@app.websocket("/ws")
async def ws_endpoint(ws: WebSocket):
    log.info("WebSocket connection established")
    await controller.handle(ws)


@app.get("/health")
async def health():
    log.info("Health check")
    return {"status": "ok"}
