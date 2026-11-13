import asyncio
import re
from pathlib import Path
from uuid import UUID

from agents import (
    Agent,
    GuardrailFunctionOutput,
    InputGuardrailTripwireTriggered,
    Runner,
    RunContextWrapper,
    TResponseInputItem,
    input_guardrail,
    trace,
)
from agents.memory import SQLiteSession
from agents.mcp import MCPServerStdio
from dotenv import load_dotenv
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel, Field, field_validator


PROJECT_ROOT = Path(__file__).resolve().parents[1]
load_dotenv(PROJECT_ROOT / ".env")

SERVER_PARAMS = {
    "command": "uv",
    "args": [
        "run",
        "--directory",
        str(PROJECT_ROOT),
        "-m",
        "Backend.Jaguars_DB_Invoke",
    ],
}

INSTRUCTIONS = """You are the Jaguars Cricket Club assistant.
Use the MCP tools for club, player, performance, and fixture information.
The initial database records are demo data, not verified real club records.
Do not invent details that are missing from the database.
"""

# Add or remove terms here to control which words are blocked in incoming messages.
BANNED_KEYWORDS = ("hack", "hacking", "bomb", "bombs", "explosive", "explosives")
API_KEY_PATTERN = re.compile(r"sk-[a-zA-Z0-9]{32}")
BANNED_KEYWORD_PATTERN = re.compile(
    r"\b(?:" + "|".join(re.escape(keyword) for keyword in BANNED_KEYWORDS) + r")\b",
    re.IGNORECASE,
)


@input_guardrail(name="unsafe_input_guardrail", run_in_parallel=False)
async def block_unsafe_input(
    _context: RunContextWrapper[None],
    _agent: Agent[None],
    input_data: str | list[TResponseInputItem],
) -> GuardrailFunctionOutput:
    message = str(input_data)
    has_api_key = bool(API_KEY_PATTERN.search(message))
    banned_keyword_match = BANNED_KEYWORD_PATTERN.search(message)
    blocked = has_api_key or banned_keyword_match is not None
    return GuardrailFunctionOutput(
        output_info={
            "api_key_detected": has_api_key,
            "banned_keyword": banned_keyword_match.group(0) if banned_keyword_match else None,
        },
        tripwire_triggered=blocked,
    )


app = FastAPI(title="Jaguars Cricket Club Chat")
sessions: dict[str, SQLiteSession] = {}
session_locks: dict[str, asyncio.Lock] = {}


class ChatRequest(BaseModel):
    conversation_id: UUID
    message: str = Field(min_length=1, max_length=4000)

    @field_validator("message")
    @classmethod
    def message_must_not_be_blank(cls, value: str) -> str:
        message = value.strip()
        if not message:
            raise ValueError("Message cannot be blank.")
        return message


class ChatResponse(BaseModel):
    reply: str


@app.get("/api/health")
async def health_check() -> dict[str, str]:
    return {"status": "ok"}


@app.post("/api/chat", response_model=ChatResponse)
async def chat(request: ChatRequest) -> ChatResponse:
    conversation_id = str(request.conversation_id)
    lock = session_locks.setdefault(conversation_id, asyncio.Lock())

    async with lock:
        session = sessions.get(conversation_id)
        if session is None:
            session = SQLiteSession(session_id=conversation_id)
            sessions[conversation_id] = session

        async with MCPServerStdio(
            params=SERVER_PARAMS,
            client_session_timeout_seconds=60,
        ) as mcp_server:
            agent = Agent(
                name="jaguars_cricket_assistant",
                instructions=INSTRUCTIONS,
                model="gpt-5.4-mini",
                mcp_servers=[mcp_server],
                input_guardrails=[block_unsafe_input],
            )
            # Group the assistant run and its tool calls under one trace.
            with trace("jaguars_cricket_club"):
                try:
                    result = await Runner.run(
                        agent,
                        request.message,
                        session=session,
                    )
                except InputGuardrailTripwireTriggered as error:
                    raise HTTPException(
                        status_code=400,
                        detail="Message blocked by the input safety guardrail.",
                    ) from error

    return ChatResponse(reply=str(result.final_output))
