from __future__ import annotations

from collections import defaultdict
import os
from typing import Dict, List, Literal

import httpx
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel, Field

app = FastAPI(title="Companion Chatbot API", version="0.1.0")

# For beginners: keep connection settings in environment variables,
# so you can switch machines/ports without changing Python code.
OLLAMA_BASE_URL = os.getenv("OLLAMA_BASE_URL", "http://127.0.0.1:11434")

Persona = Literal[
    "friend",
    "friend_family",
    "romantic_partner",
    "boyfriend",
    "girlfriend",
    "intimate_friend",
    "pet_companion",
    "dog_companion",
]
CompanionGender = Literal["neutral", "feminine", "masculine"]
ResponseLength = Literal["short", "medium", "long"]

# Beginner-friendly character cards:
# We keep persona definition in one dictionary so style updates happen in one place.
CHARACTER_CARDS: Dict[str, dict] = {
    "friend": {
        "label": "Friend",
        "core_style": "a warm, optimistic close friend",
        "tone_tags": ["encouraging", "casual", "kind"],
    },
    "friend_family": {
        "label": "Friend/Family",
        "core_style": "a caring family member or trusted longtime friend with gentle, practical support",
        "tone_tags": ["steady", "safe", "supportive"],
    },
    "romantic_partner": {
        "label": "Romantic Partner",
        "core_style": "a caring romantic partner who is affectionate but non-explicit",
        "tone_tags": ["affectionate", "gentle", "reassuring"],
    },
    "boyfriend": {
        "label": "Boyfriend",
        "core_style": "a caring boyfriend who is affectionate, respectful, and non-explicit",
        "tone_tags": ["protective", "gentle", "warm"],
    },
    "girlfriend": {
        "label": "Girlfriend",
        "core_style": "a caring girlfriend who is affectionate, respectful, and non-explicit",
        "tone_tags": ["soft", "warm", "uplifting"],
    },
    "intimate_friend": {
        "label": "Intimate Friend",
        "core_style": "an emotionally intimate friend who listens deeply and validates feelings",
        "tone_tags": ["deep-listening", "validating", "calm"],
    },
    "pet_companion": {
        "label": "Cat Companion",
        "core_style": "a playful, loyal cat companion tone",
        "tone_tags": ["cute", "comforting", "playful"],
    },
    "dog_companion": {
        "label": "Dog Companion",
        "core_style": "a cheerful, loyal dog companion tone",
        "tone_tags": ["energetic", "loyal", "comforting"],
    },
}


class ChatRequest(BaseModel):
    user_id: str = Field(..., description="Unique user id for memory separation")
    persona: Persona = Field(..., description="Companion style")
    message: str = Field(..., min_length=1, description="User input text")
    model: str = Field(default="llama3.1:8b", description="Ollama model name")
    companion_gender: CompanionGender = Field(
        default="neutral",
        description="Preferred companion voice style. We keep this respectful and avoid stereotypes.",
    )
    comfort_level: int = Field(
        default=4,
        ge=1,
        le=5,
        description="How soothing the response should be. 1=light, 5=very comforting.",
    )
    response_length: ResponseLength = Field(
        default="medium",
        description="Preferred answer length.",
    )
    character_seed: str = Field(
        default="",
        description="Optional extra character instruction (for example: 'speaks very softly and uses simple words').",
    )


class ChatResponse(BaseModel):
    reply: str
    follow_up_question: str
    safety_note: str | None = None


# Beginner-friendly in-memory memory store.
# Key is user_id, value is list of role/content messages.
MEMORY: Dict[str, List[dict]] = defaultdict(list)
MAX_HISTORY_TURNS = 12


def effective_gender_for_persona(persona: Persona, companion_gender: CompanionGender) -> CompanionGender:
    """Pick final gender style. Boyfriend/girlfriend get helpful defaults if user leaves neutral."""

    if persona == "boyfriend" and companion_gender == "neutral":
        return "masculine"
    if persona == "girlfriend" and companion_gender == "neutral":
        return "feminine"
    return companion_gender


def build_response_rules(comfort_level: int, response_length: ResponseLength) -> str:
    """Convert user controls into explicit style rules for the model."""

    comfort_map = {
        1: "Keep comfort light; one empathy sentence is enough.",
        2: "Use a gentle and friendly tone with mild reassurance.",
        3: "Use balanced reassurance and one practical suggestion.",
        4: "Use a soothing tone, strong validation, and one calming step.",
        5: "Use very warm, grounding language and include a short breathing/grounding suggestion.",
    }
    length_map = {
        "short": "Keep reply around 2-4 sentences.",
        "medium": "Keep reply around 4-7 sentences.",
        "long": "Keep reply around 7-10 sentences.",
    }
    return f"{comfort_map[comfort_level]} {length_map[response_length]}"


def build_system_prompt(
    persona: Persona,
    companion_gender: CompanionGender,
    comfort_level: int,
    response_length: ResponseLength,
    character_seed: str,
) -> str:
    """Return persona prompt instructions for the model."""

    card = CHARACTER_CARDS[persona]

    gender_tone_map = {
        "neutral": "Use a gender-neutral voice style.",
        "feminine": "Use a gentle feminine voice style without stereotypes.",
        "masculine": "Use a calm masculine voice style without stereotypes.",
    }
    effective_gender = effective_gender_for_persona(persona, companion_gender)
    gender_tone = gender_tone_map[effective_gender]
    response_rules = build_response_rules(comfort_level, response_length)
    tone_tags = ", ".join(card["tone_tags"])

    seed_part = ""
    if character_seed.strip():
        seed_part = f"Extra character seed from user: {character_seed.strip()}. "

    return (
        "You are a supportive companion chatbot. "
        f"Speak like {card['core_style']}. "
        f"Tone tags: {tone_tags}. "
        f"{gender_tone} "
        f"{response_rules} "
        f"{seed_part}"
        "Goals: (1) give empathetic, practical replies, "
        "(2) keep the conversation naturally continuing, "
        "(3) ask one thoughtful follow-up question each turn, "
        "(4) avoid explicit sexual content, "
        "(5) if user seems in crisis, encourage real-world support and emergency resources."
    )


def supportive_safety_line(user_text: str) -> str | None:
    """Very simple keyword-based safety check for emotional crisis signals."""

    risky_words = ["suicide", "kill myself", "self-harm", "want to die", "end my life"]
    lowered = user_text.lower()
    if any(word in lowered for word in risky_words):
        return (
            "I care about your safety. If you might act on these feelings, "
            "please call your local emergency number right now or contact a crisis hotline in your country."
        )
    return None


def detect_emotion_context(user_text: str) -> str:
    """Classify rough user context for cute cat/dog wording."""

    lowered = user_text.lower()

    sad_words = ["sad", "lonely", "down", "depressed", "cry", "hurt", "tired", "stress"]
    happy_words = ["happy", "excited", "great", "awesome", "good news", "win", "celebrate"]
    help_words = ["help", "advice", "what should i do", "stuck", "confused", "problem"]

    if any(word in lowered for word in sad_words):
        return "comfort"
    if any(word in lowered for word in happy_words):
        return "celebrate"
    if any(word in lowered for word in help_words):
        return "coach"
    return "curious"


def cat_sound_prefix(context: str) -> str:
    """Return context-specific cat sounds to make pet persona cute and varied."""

    sound_map = {
        "comfort": "Mew... purr purr 🐾 ",
        "celebrate": "Meow~ nyaa! ✨ ",
        "coach": "Mrrp! meow meow 🐱 ",
        "curious": "Nyaa? purr~ 😺 ",
    }
    return sound_map.get(context, "Meow~ ")


def apply_pet_style(reply: str, user_text: str) -> str:
    """Add cute cat-sound style for `pet_companion` responses."""

    context = detect_emotion_context(user_text)
    prefix = cat_sound_prefix(context)
    cleaned = reply.strip()
    if not cleaned:
        cleaned = "I am here with you."
    return f"{prefix}{cleaned}"


def dog_sound_prefix(context: str) -> str:
    """Return context-specific dog sounds for dog companion persona."""

    sound_map = {
        "comfort": "Ruff... woof woof 🐶 ",
        "celebrate": "Woof! arf arf 🎉 ",
        "coach": "Arf! ruff ruff 🦴 ",
        "curious": "Woof? ruff~ 🐕 ",
    }
    return sound_map.get(context, "Woof~ ")


def apply_dog_style(reply: str, user_text: str) -> str:
    """Add cute dog-sound style for `dog_companion` responses."""

    context = detect_emotion_context(user_text)
    prefix = dog_sound_prefix(context)
    cleaned = reply.strip()
    if not cleaned:
        cleaned = "I am here with you."
    return f"{prefix}{cleaned}"


def compose_messages(payload: ChatRequest) -> List[dict]:
    """Build chat history for Ollama chat endpoint."""

    history = MEMORY[payload.user_id][-MAX_HISTORY_TURNS:]
    system_message = {
        "role": "system",
        "content": build_system_prompt(
            payload.persona,
            payload.companion_gender,
            payload.comfort_level,
            payload.response_length,
            payload.character_seed,
        ),
    }
    user_message = {"role": "user", "content": payload.message}
    return [system_message, *history, user_message]


async def call_ollama(messages: List[dict], model: str) -> str:
    """Call local Ollama server via HTTP API."""

    payload = {
        "model": model,
        "messages": messages,
        "stream": False,
        "options": {"temperature": 0.8},
    }

    async with httpx.AsyncClient(timeout=90) as client:
        response = await client.post(f"{OLLAMA_BASE_URL}/api/chat", json=payload)

    if response.status_code != 200:
        raise HTTPException(
            status_code=502,
            detail=f"Ollama API error {response.status_code}: {response.text}",
        )

    data = response.json()
    return data.get("message", {}).get("content", "")


def extract_follow_up(reply: str) -> str:
    """Pick a follow-up question from model output or create a default one."""

    lines = [line.strip() for line in reply.splitlines() if line.strip()]
    questions = [line for line in lines if "?" in line]
    if questions:
        return questions[-1]
    return "What feels most important for you to talk about next?"


@app.get("/health")
async def health() -> dict:
    return {"ok": True}


@app.get("/health/ollama")
async def health_ollama() -> dict:
    """Quick connectivity check so beginners can confirm Ollama is reachable."""

    try:
        async with httpx.AsyncClient(timeout=10) as client:
            response = await client.get(f"{OLLAMA_BASE_URL}/api/tags")
        response.raise_for_status()
        data = response.json()
        model_count = len(data.get("models", []))
        return {"ok": True, "ollama_base_url": OLLAMA_BASE_URL, "models_found": model_count}
    except Exception as exc:  # pylint: disable=broad-except
        raise HTTPException(
            status_code=502,
            detail=(
                "Cannot connect to Ollama. Make sure `ollama serve` is running and the "
                "`OLLAMA_BASE_URL` env var is correct. "
                f"Current value: {OLLAMA_BASE_URL}. Error: {exc}"
            ),
        ) from exc


@app.get("/personas")
async def list_personas() -> dict:
    """List supported personas and gender options so frontend can build selectors."""

    return {
        "personas": list(CHARACTER_CARDS.keys()),
        "companion_genders": ["neutral", "feminine", "masculine"],
        "response_lengths": ["short", "medium", "long"],
        "comfort_level_range": {"min": 1, "max": 5},
    }


@app.get("/characters")
async def list_character_cards() -> dict:
    """Expose full character cards so builders can tune persona style externally."""

    return {"character_cards": CHARACTER_CARDS}


@app.post("/chat", response_model=ChatResponse)
async def chat(payload: ChatRequest) -> ChatResponse:
    safety_note = supportive_safety_line(payload.message)
    messages = compose_messages(payload)

    reply = await call_ollama(messages, payload.model)

    if payload.persona == "pet_companion":
        reply = apply_pet_style(reply, payload.message)
    if payload.persona == "dog_companion":
        reply = apply_dog_style(reply, payload.message)

    follow_up = extract_follow_up(reply)

    MEMORY[payload.user_id].append({"role": "user", "content": payload.message})
    MEMORY[payload.user_id].append({"role": "assistant", "content": reply})

    return ChatResponse(reply=reply, follow_up_question=follow_up, safety_note=safety_note)
