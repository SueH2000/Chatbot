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
python -m uvicorn app:app --reload --port 8000
```



### Troubleshooting: `uvicorn: command not found`

If you see:

```text
bash: uvicorn: command not found
```

it usually means your virtual environment is not activated, or dependencies were installed in another Python environment.

1. Create and activate virtual environment:

```bash
python -m venv .venv
source .venv/bin/activate
```

2. Install dependencies inside the activated environment:

```bash
pip install -r requirements.txt
```

3. Run with module mode (more reliable than plain `uvicorn` in PATH issues):

```bash
python -m uvicorn app:app --reload --port 8000
```

4. Verify executable path:

```bash
which python
which pip
python -m pip show uvicorn
```

Beginner note: `python -m uvicorn ...` guarantees you use uvicorn from the same Python interpreter you are currently running.



### Why you saw `GET /` 404 and `GET /favicon.ico` 404

Your server was actually running correctly. The 404 logs happened because browser default requests hit:

- `/` (home page)
- `/favicon.ico` (tab icon)

This project now includes both routes, so these browser checks no longer show 404 noise.

Useful URLs after startup:

- `http://127.0.0.1:8000/` (API landing info)
- `http://127.0.0.1:8000/docs` (interactive Swagger UI)
- `http://127.0.0.1:8000/health`
- `http://127.0.0.1:8000/personas`
- `http://127.0.0.1:8000/chat-ui` (simple UI with mode selector + message input)



### I thought there should be a place to choose mode and enter input

Yes. This project now includes a simple browser page at:

- `http://127.0.0.1:8000/chat-ui`

It provides:

- persona/mode dropdown
- message input box
- comfort/length controls
- direct send button that calls `POST /chat`

Beginner note: this UI is intentionally small and uses plain HTML + JavaScript so you can learn the request flow before moving to React/Vue.

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

> If you are using GitHub Codespaces but Ollama is on your laptop, do **not** use `127.0.0.1` here. See the Codespaces architecture note below.

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












### Important architecture note: Codespaces app cannot directly reach your local Ollama

If your FastAPI app runs in **GitHub Codespaces** but Ollama runs on **your own laptop**, this default URL will fail inside Codespaces:

- `http://127.0.0.1:11434`

Why: `127.0.0.1` in Codespaces means "the Codespace container itself", not your laptop.

#### Option A (simplest): run Ollama in the same Codespace/container

This avoids cross-network routing issues entirely.

#### Option B: run the app locally with your local Ollama

- Start app on your laptop
- Keep `OLLAMA_BASE_URL=http://127.0.0.1:11434`

#### Option C: expose local Ollama to a public/tunneled URL, then set `OLLAMA_BASE_URL`

Example (conceptual):

```bash
# In Codespaces terminal
export OLLAMA_BASE_URL="https://<your-tunnel-domain>"
python -m uvicorn app:app --reload --port 8000
```

Then `GET /health/ollama` should succeed if tunnel + firewall rules are correct.

Beginner note: this is a networking boundary issue (where services run), not a bug in persona logic or prompt code.

### Troubleshooting: `11434` works but `8000/health/ollama` cannot connect

If this happens:

- `curl http://127.0.0.1:11434/api/tags` returns `200` (Ollama is healthy)
- but `curl http://127.0.0.1:8000/health/ollama` says cannot connect

then usually **FastAPI is not running** (or running on another host/port).

Check in this order (PowerShell):

```powershell
# 1) Is FastAPI process listening on 8000?
netstat -ano | findstr :8000
```

If no output, start the app:

```powershell
# In your project folder
python -m uvicorn app:app --reload --port 8000
```

Then open a new terminal and test:

```powershell
# Use real curl executable to avoid PowerShell alias confusion
curl.exe http://127.0.0.1:8000/health
curl.exe http://127.0.0.1:8000/health/ollama
```

If `python -m uvicorn ...` fails with missing module:

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install -r requirements.txt
python -m uvicorn app:app --reload --port 8000
```

If port 8000 is occupied, run another port:

```powershell
python -m uvicorn app:app --reload --port 8010
curl.exe http://127.0.0.1:8010/health
curl.exe http://127.0.0.1:8010/health/ollama
```

Beginner note: your logs already show Ollama works. The failing part is only the FastAPI service reachability.

### Troubleshooting: PowerShell says `-X` / `-H` / `-d` parameter not found

This happens because PowerShell maps `curl` to `Invoke-WebRequest`, which does not use GNU curl flags like `-X`, `-H`, and `-d` the same way.

Use one of these PowerShell-safe commands:

```powershell
# Option 1: real curl executable
curl.exe -X POST http://127.0.0.1:8000/chat `
  -H "Content-Type: application/json" `
  -d '{"user_id":"demo-user","persona":"friend_family","companion_gender":"neutral","comfort_level":5,"response_length":"medium","character_seed":"speak softly and reassure me before giving advice","message":"I feel lonely tonight.","model":"llama3.1:8b"}'
```

```powershell
# Option 2: PowerShell native API call (recommended)
$body = @{
  user_id = "demo-user"
  persona = "friend_family"
  companion_gender = "neutral"
  comfort_level = 5
  response_length = "medium"
  character_seed = "speak softly and reassure me before giving advice"
  message = "I feel lonely tonight."
  model = "llama3.1:8b"
} | ConvertTo-Json

Invoke-RestMethod -Method POST -Uri "http://127.0.0.1:8000/chat" -ContentType "application/json" -Body $body
```

Beginner note: this is a shell command syntax difference, not a FastAPI backend bug.

### Troubleshooting: PowerShell `curl` warning (this is usually NOT an Ollama error)

In Windows PowerShell, `curl` is often an alias of `Invoke-WebRequest`, so you may see a script/security parsing warning.

If your output still shows:

- `StatusCode : 200`
- and JSON content like `{"models": [...]}`

then Ollama is already working correctly.

Use one of these safer commands to avoid the warning:

```powershell
# Option 1: call real curl executable
curl.exe http://127.0.0.1:11434/api/tags

# Option 2: use PowerShell REST cmdlet (best for JSON)
Invoke-RestMethod http://127.0.0.1:11434/api/tags
```

If you still prefer `Invoke-WebRequest`, add `-UseBasicParsing`:

```powershell
Invoke-WebRequest http://127.0.0.1:11434/api/tags -UseBasicParsing
```

Beginner note: this warning is from the shell command wrapper behavior, not from your FastAPI app code.

### Troubleshooting: `ollama serve` says port 11434 is already in use (Windows)

If you see:

```text
Error: listen tcp 127.0.0.1:11434: bind: Only one usage of each socket address ...
```

it usually means Ollama is **already running** in background, or another process is using that port.

1. Check which process is using port `11434`:

```powershell
netstat -ano | findstr :11434
```

2. If the PID belongs to `ollama.exe`, you usually do **not** need another `ollama serve`.
   Just test directly:

```powershell
curl http://127.0.0.1:11434/api/tags
```

3. If it is a stuck/old process, stop it:

```powershell
taskkill /PID <PID_NUMBER> /F
```

4. Start Ollama again:

```powershell
ollama serve
```

5. Or run on another port and point app to that port:

```powershell
$env:OLLAMA_HOST = "127.0.0.1:11435"
ollama serve

# In another terminal (PowerShell)
$env:OLLAMA_BASE_URL = "http://127.0.0.1:11435"
python -m uvicorn app:app --reload --port 8000
```

Beginner note: socket/port errors are usually environment/runtime conflicts, not Python syntax problems.

## Beginner Notes (Why code is structured this way)

- We keep logic in small functions (`build_system_prompt`, `compose_messages`, `call_ollama`) so each part is easy to test and change.
- We use an in-memory dictionary for chat history because it is simple for learning. In production, replace it with Redis or a database.
- We use a safety helper (`supportive_safety_line`) to add gentle guidance when users express severe distress.
- We read `OLLAMA_BASE_URL` from environment variables, so beginners can move from local laptop to server without rewriting Python code.
- We pass `companion_gender` into the system prompt so style is configurable at request time without copying endpoint code.
- We use character cards + comfort/length controls so persona quality is more stable than one hardcoded prompt sentence.



## Tests

Run this to execute automated checks:

```bash
python -m unittest discover -s tests -p "test_*.py"
```

Beginner note: these tests verify persona metadata, character card exposure, response rule generation, and pet-style post-processing without needing a live Ollama server.

## Important Safety Reminder

This is **not** a therapist and should not pretend to be a licensed professional. If users mention self-harm or emergency risk, show crisis resources and encourage contacting local emergency services.
