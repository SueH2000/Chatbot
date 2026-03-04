# Companion Chatbot with Free Ollama Models

This project is a beginner-friendly starter app for a supportive chatbot that can act like:

- an intimate friend
- a romantic partner (non-explicit, emotionally supportive)
- a close friend

It is designed to keep conversations going by asking thoughtful follow-up questions, sharing new topics, and offering gentle support when the user feels down.

## Can we build this using only free Ollama models?

Yes. You can build a useful version with free local models in Ollama.

Examples of free models you can try:

- `llama3.1:8b`
- `qwen2.5:7b`
- `mistral:7b`

Tradeoffs:

- Quality may be lower than paid APIs.
- Large models need more RAM/VRAM.
- You must tune prompts and memory strategy for better continuity.

## Features in this starter

- Persona modes: `friend`, `friend_family`, `romantic_partner`, `boyfriend`, `girlfriend`, `intimate_friend`, `pet_companion`, `dog_companion`
- Character-card driven prompt builder (better persona consistency)
- Adjustable `comfort_level` and `response_length` per request
- Optional `character_seed` for custom character flavor
- Conversation memory (last N turns)
- Automatic follow-up question generation to keep chat alive
- Lightweight safety support for emotional distress (not medical advice)
- FastAPI backend for easy frontend integration

## Quick Start

1. Install Ollama and pull a free model:

```bash
ollama pull llama3.1:8b
```

2. Create a virtual environment and install dependencies:

```bash
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

3. Run the app:

```bash
uvicorn app:app --reload --port 8000
```

## Connect to your local Ollama (step-by-step)

If you already installed Ollama locally, follow this exact order:

1. Start Ollama server (keep this terminal open):

```bash
ollama serve
```

2. In a second terminal, verify Ollama is alive:

```bash
curl http://127.0.0.1:11434/api/tags
```

3. Pull at least one free model (if you have not done this yet):

```bash
ollama pull llama3.1:8b
```

4. (Optional) If your Ollama host/port is different, set env var before starting FastAPI:

```bash
export OLLAMA_BASE_URL=http://127.0.0.1:11434
```

5. Check app -> Ollama connection using this project endpoint:

```bash
curl http://127.0.0.1:8000/health/ollama
```

6. Send a chat request:

```bash
curl -X POST http://127.0.0.1:8000/chat \
  -H "Content-Type: application/json" \
  -d '{
    "user_id": "demo-user",
    "persona": "friend_family",
    "companion_gender": "neutral",
    "comfort_level": 5,
    "response_length": "medium",
    "character_seed": "speak softly and reassure me before giving advice",
    "message": "I feel lonely tonight.",
    "model": "llama3.1:8b"
  }'
```





### Better way to create consistent character answers

Yes — a better way is to use **character cards + controllable style knobs**, not only one static prompt line.

This project now supports:

1. **Character cards** (`/characters`)
   - each persona has `core_style` + `tone_tags`
   - easier to maintain and test than editing long prompt text in many places

2. **Comfort intensity** (`comfort_level` 1-5)
   - lets you decide how soothing/grounding the response should be

3. **Response length control** (`response_length`: short/medium/long)
   - stabilizes output size for UI and user preference

4. **Custom character seed** (`character_seed`)
   - quick customization without changing backend code

Why this is better for beginners: persona logic is modular (data + small helper functions), so you can tune style safely without breaking Ollama call flow.


### Persona selection (how to change answer style)

You can choose different conversation styles by changing `persona` in `POST /chat`:

- `romantic_partner`: affectionate partner tone (non-explicit)
- `boyfriend`: affectionate boyfriend tone (defaults to masculine style unless overridden)
- `girlfriend`: affectionate girlfriend tone (defaults to feminine style unless overridden)
- `friend_family`: family / trusted friend tone (steady and practical)
- `pet_companion`: playful cat-like comfort tone with cute sounds (meow/nyaa/purr)
- `dog_companion`: playful dog-like comfort tone with cute sounds (woof/ruff/arf)
- `friend`: close friend tone
- `intimate_friend`: deeper emotional listening tone





#### Companion gender style option (for friend/romantic/any persona)

In `POST /chat`, you can set `companion_gender` to tune voice style:

- If persona is `boyfriend` and `companion_gender` is `neutral`, backend auto-uses `masculine`.
- If persona is `girlfriend` and `companion_gender` is `neutral`, backend auto-uses `feminine`.

- `neutral` (default): gender-neutral tone
- `feminine`: gentle feminine tone
- `masculine`: calm masculine tone

Beginner note: this option adjusts style wording only. We explicitly avoid harmful stereotypes in prompts.

#### Pet persona behavior (cat sounds by scenario)

For `pet_companion`, the app now adds cute cat sounds differently by situation:

- if user sounds sad/down -> gentle comfort sounds (`Mew... purr purr`)
- if user shares good news -> celebration sounds (`Meow~ nyaa!`)
- if user asks for help -> focused coach sounds (`Mrrp! meow meow`)
- otherwise -> curious playful sounds (`Nyaa? purr~`)

Why this design (beginner-friendly): we keep this in small helper functions so you can edit tone rules without touching Ollama request logic.



#### Dog persona behavior (dog sounds by scenario)

For `dog_companion`, the app adds dog sounds differently by situation:

- if user sounds sad/down -> gentle comfort sounds (`Ruff... woof woof`)
- if user shares good news -> celebration sounds (`Woof! arf arf`)
- if user asks for help -> focused coach sounds (`Arf! ruff ruff`)
- otherwise -> curious playful sounds (`Woof? ruff~`)

You can also fetch supported personas from:

```bash
curl http://127.0.0.1:8000/characters
```


```bash
curl http://127.0.0.1:8000/personas
```


## Beginner Notes (Why code is structured this way)

- We keep logic in small functions (`build_system_prompt`, `compose_messages`, `call_ollama`) so each part is easy to test and change.
- We use an in-memory dictionary for chat history because it is simple for learning. In production, replace it with Redis or a database.
- We use a safety helper (`supportive_safety_line`) to add gentle guidance when users express severe distress.
- We read `OLLAMA_BASE_URL` from environment variables, so beginners can move from local laptop to server without rewriting Python code.
- We pass `companion_gender` into the system prompt so style is configurable at request time without copying endpoint code.
- We use character cards + comfort/length controls so persona quality is more stable than one hardcoded prompt sentence.

## Important Safety Reminder

This is **not** a therapist and should not pretend to be a licensed professional. If users mention self-harm or emergency risk, show crisis resources and encourage contacting local emergency services.
