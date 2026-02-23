"""
Voice POC — Real-time voice AI coding interviewer.

This is the FastAPI application entry-point.  Domain logic lives in:
  - prompt.py     → system prompt
  - tools.py      → tool / function-calling schemas
  - handlers.py   → function-call handler implementations
  - problems.py   → problem bank

Run:
  cd backend
  uvicorn main:app --host 0.0.0.0 --port 7860
"""

from __future__ import annotations

import asyncio
import os
import logging
from pathlib import Path

from dotenv import load_dotenv

load_dotenv()

from fastapi import BackgroundTasks, FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel

from pipecat.audio.vad.silero import SileroVADAnalyzer
from pipecat.audio.vad.vad_analyzer import VADParams
from pipecat.pipeline.pipeline import Pipeline
from pipecat.pipeline.runner import PipelineRunner
from pipecat.pipeline.task import PipelineParams, PipelineTask
from pipecat.processors.aggregators.llm_context import LLMContext
from pipecat.processors.aggregators.llm_response_universal import LLMContextAggregatorPair
from pipecat.services.google.gemini_live.llm import GeminiLiveLLMService
from pipecat.transports.base_transport import TransportParams
from pipecat.transports.smallwebrtc.transport import SmallWebRTCTransport
from pipecat.transports.smallwebrtc.request_handler import (
    SmallWebRTCRequestHandler,
    SmallWebRTCRequest,
    SmallWebRTCPatchRequest,
)

from pipecat.frames.frames import LLMMessagesAppendFrame

from prompt import SYSTEM_PROMPT
from tools import TOOLS
from handlers import register_all_handlers

# ---------------------------------------------------------------------------
# Logging
# ---------------------------------------------------------------------------
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("voice-poc")

# ---------------------------------------------------------------------------
# FastAPI app
# ---------------------------------------------------------------------------
app = FastAPI(title="Voice POC")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

webrtc_handler = SmallWebRTCRequestHandler()

# Per-session code storage: pc_id → latest code string
code_store: dict[str, str] = {}

# Per-session language tracking: pc_id → language
language_store: dict[str, str] = {}

# Per-session review request queues: pc_id → asyncio.Queue
review_queues: dict[str, asyncio.Queue] = {}


class CodePayload(BaseModel):
    pc_id: str
    code: str
    language: str = "python"  # Optional language field


class ReviewPayload(BaseModel):
    pc_id: str


# ---------------------------------------------------------------------------
# Bot pipeline — spawned once per WebRTC connection
# ---------------------------------------------------------------------------
async def run_bot(webrtc_connection, pc_id: str) -> None:
    """Build and run a full Pipecat pipeline for one caller."""

    api_key = os.environ.get("GOOGLE_API_KEY")
    if not api_key:
        raise RuntimeError("GOOGLE_API_KEY environment variable is not set")

    # -- Per-session state ------------------------------------------------
    session: dict = {
        "current_problem": None,
        "hints_given": 0,
        "language": "python",  # Default language
    }

    # -- Transport --------------------------------------------------------
    transport = SmallWebRTCTransport(
        webrtc_connection=webrtc_connection,
        params=TransportParams(
            audio_in_enabled=True,
            audio_out_enabled=True,
            vad_enabled=True,
            vad_analyzer=SileroVADAnalyzer(
                params=VADParams(
                    confidence=0.7,
                    stop_secs=0.3,
                )
            ),
        ),
    )

    # -- LLM --------------------------------------------------------------
    llm = GeminiLiveLLMService(
        api_key=api_key,
        system_instruction=SYSTEM_PROMPT,
        voice_id="Charon",
        inference_on_context_initialization=True,
        tools=TOOLS,
    )

    # -- Register function-call handlers ----------------------------------
    register_all_handlers(llm, webrtc_connection, session, code_store, pc_id, language_store)

    # -- Context (required for function calling) --------------------------
    context = LLMContext()
    context_aggregator = LLMContextAggregatorPair(context)

    # -- Pipeline ---------------------------------------------------------
    pipeline = Pipeline([
        transport.input(),
        context_aggregator.user(),
        llm,
        context_aggregator.assistant(),
        transport.output(),
    ])

    task = PipelineTask(
        pipeline,
        params=PipelineParams(
            enable_metrics=True,
            enable_usage_metrics=True,
        ),
    )

    # -- Review request watcher -------------------------------------------
    review_queue: asyncio.Queue = asyncio.Queue()
    review_queues[pc_id] = review_queue

    async def review_watcher():
        """Wait for review requests and inject a user message into the LLM."""
        while True:
            await review_queue.get()
            await task.queue_frame(
                LLMMessagesAppendFrame(
                    messages=[{
                        "role": "user",
                        "content": (
                            "The candidate has clicked the 'Review My Code' button. "
                            "Please call review_code now to see their latest code "
                            "and give them feedback."
                        ),
                    }],
                )
            )

    # -- Transport events -------------------------------------------------
    @transport.event_handler("on_client_connected")
    async def on_connected(transport, client):
        logger.info("Client connected")

    @transport.event_handler("on_client_disconnected")
    async def on_disconnected(transport, client):
        logger.info("Client disconnected")
        review_queues.pop(pc_id, None)
        await task.cancel()

    # -- Run until disconnect ---------------------------------------------
    watcher = asyncio.create_task(review_watcher())
    runner = PipelineRunner(handle_sigint=False)
    try:
        await runner.run(task)
    finally:
        watcher.cancel()
        review_queues.pop(pc_id, None)


# ---------------------------------------------------------------------------
# WebRTC signaling endpoints
# ---------------------------------------------------------------------------

@app.post("/api/offer")
async def offer(request: SmallWebRTCRequest, background_tasks: BackgroundTasks):
    # Capture pc_id from the request so we can pass it into run_bot.
    captured_pc_id: str | None = None

    async def on_connection(connection):
        # Wrap in a closure so captured_pc_id is read when the task runs
        # (after handle_web_request has returned and set it), not at add_task time.
        async def _start():
            await run_bot(connection, captured_pc_id or "")
        background_tasks.add_task(_start)

    answer = await webrtc_handler.handle_web_request(
        request=request,
        webrtc_connection_callback=on_connection,
    )
    captured_pc_id = answer.get("pc_id", "") if isinstance(answer, dict) else ""
    return answer


@app.post("/api/code")
async def receive_code(payload: CodePayload):
    """Store the candidate's latest code and language, keyed by pc_id."""
    code_store[payload.pc_id] = payload.code
    language_store[payload.pc_id] = payload.language
    return {"status": "ok"}


@app.post("/api/review")
async def request_review(payload: ReviewPayload):
    """Request the LLM to review the candidate's code."""
    queue = review_queues.get(payload.pc_id)
    if queue:
        await queue.put(True)
        return {"status": "ok"}
    return {"status": "error", "message": "Session not found"}


@app.patch("/api/offer")
async def ice_candidate(request: SmallWebRTCPatchRequest):
    await webrtc_handler.handle_patch_request(request)
    return {"status": "ok"}


@app.get("/health")
async def health():
    return {"status": "ok"}


# ---------------------------------------------------------------------------
# Serve built React frontend (production)
# ---------------------------------------------------------------------------
_frontend_dist = Path(__file__).parent.parent / "frontend" / "dist"
if _frontend_dist.is_dir():
    app.mount("/", StaticFiles(directory=str(_frontend_dist), html=True), name="frontend")
