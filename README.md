# Voice Assistant POC

Real-time voice AI assistant using **Pipecat** + **OpenAI Realtime API** (`gpt-4o-realtime-preview`).

Browser captures mic via WebRTC, streams audio to a Python backend, which pipes it through
OpenAI's speech-to-speech model and streams synthesised audio back — all in real time with
barge-in / interruption support.

## Project structure

```
voice-poc/
├── backend/
│   ├── main.py            # FastAPI + Pipecat pipeline
│   └── pyproject.toml     # Python dependencies
├── frontend/
│   └── index.html         # Browser UI (vanilla JS + WebRTC)
└── README.md
```

## Prerequisites

- Python 3.11+
- An OpenAI API key with access to `gpt-4o-realtime-preview`
- Chrome (or any browser supporting WebRTC + getUserMedia)

## Setup & run

### 1. Environment variable

```bash
export OPENAI_API_KEY="sk-..."
```

### 2. Install backend dependencies

```bash
cd backend
python -m venv .venv
source .venv/bin/activate      # Windows: .venv\Scripts\activate
pip install -e .
```

### 3. Start the backend

```bash
cd backend
uvicorn main:app --host 0.0.0.0 --port 7860
```

### 4. Open the frontend

Open `frontend/index.html` directly in Chrome (`file://` protocol works for localhost WebRTC).

Or serve it:

```bash
cd frontend
python -m http.server 8000
# then visit http://localhost:8000
```

### 5. Use it

1. Click **Start**
2. Grant microphone permission
3. Talk — the assistant will respond in real time
4. Interrupt at any time — the AI stops and listens
5. Click **Stop** to end the session

---

## Architecture

```
┌─────────────┐  WebRTC (audio)  ┌──────────────────────────┐  WebSocket  ┌───────────────┐
│   Browser    │ ◄──────────────► │  FastAPI + Pipecat       │ ◄──────────► │ OpenAI        │
│  (index.html)│                  │  SmallWebRTCTransport    │              │ Realtime API  │
│              │                  │  ┌────────────────────┐  │              │ gpt-4o-rt     │
│  getUserMedia│                  │  │ Silero VAD         │  │              │               │
│  <audio>     │                  │  │ Context Aggregator │  │              │ Server VAD    │
│              │                  │  │ Transcript Proc.   │  │              │ (semantic)    │
└─────────────┘                  │  └────────────────────┘  │              └───────────────┘
                                 └──────────────────────────┘
```

---

## How interruption (barge-in) works

Interruptions are handled at **two layers**:

1. **OpenAI server-side (Semantic Turn Detection)**
   `SemanticTurnDetection(interrupt_response=True)` tells OpenAI's Realtime API
   to use an AI-based model to detect when the user starts speaking. When it
   detects a barge-in, it immediately truncates its own audio generation and
   begins processing the new user utterance.

2. **Pipecat transport-side (Silero VAD)**
   The `SileroVADAnalyzer` on the `SmallWebRTCTransport` detects user voice
   activity locally. When the user starts speaking, Pipecat flushes any queued
   outgoing audio frames so there's no residual AI audio playing while the
   user talks. This eliminates the "talking over each other" artifact.

Together these two mechanisms provide sub-200ms barge-in responsiveness.

## Where VAD is handled

| Layer | VAD type | Purpose |
|-------|----------|---------|
| Transport (`TransportParams.vad_analyzer`) | Silero (local, neural) | Detect user speech for frame cancellation |
| OpenAI session (`SessionProperties.turn_detection`) | Semantic (server-side, AI) | Detect end-of-turn & barge-in for response generation |

Both run concurrently. The local Silero VAD is responsible for the immediate
UX (cancel audio playback). The server-side semantic VAD is responsible for
conversational flow (when to respond, when to stop).

## How AI speech cancellation occurs

1. User starts speaking mid-response.
2. Silero VAD fires a `SPEAKING` state on the transport within ~100ms.
3. Pipecat's transport output processor receives an interruption signal and
   drops all buffered `AudioRawFrame`s from the output queue.
4. Simultaneously, OpenAI's server receives the incoming user audio, detects
   the interruption via semantic turn detection, and stops generating further
   audio tokens.
5. The pipeline converges: no stale AI audio reaches the browser, and OpenAI
   begins processing the user's new utterance.

## Latency tuning considerations

| Parameter | Where | Effect |
|-----------|-------|--------|
| `VADParams.stop_secs` | `SileroVADAnalyzer` | Lower = faster end-of-speech detection, but may clip words. 0.2–0.4s is typical. |
| `VADParams.confidence` | `SileroVADAnalyzer` | Higher = fewer false positives, but may miss quiet speech. 0.6–0.8 is typical. |
| `SemanticTurnDetection.eagerness` | OpenAI session | `"high"` = faster responses but may interrupt user. `"low"` = waits longer. |
| WebRTC jitter buffer | Browser/aiortc | Automatically tuned. Lower jitter = lower latency. Use wired/stable networks. |
| Audio sample rate | Transport + OpenAI | OpenAI Realtime uses 24 kHz PCM16. Matching this avoids resampling overhead. |
| Geographic proximity | Deployment | Deploy backend close to OpenAI's API endpoint (US) to minimize WebSocket RTT. |

**Typical end-to-end latency**: 300–600ms from end of user speech to first AI audio,
depending on network conditions and model response time.

## Audio frame size considerations

- OpenAI Realtime API operates on **24 kHz, 16-bit mono PCM** audio.
- Pipecat's default audio frame duration is **20ms** (480 samples at 24 kHz).
- Smaller frames (10ms) reduce latency but increase CPU overhead from more
  frequent processing. Larger frames (40ms) are more efficient but add latency.
- The WebRTC transport handles codec negotiation (typically Opus) and
  repacketisation automatically via aiortc. The browser sends Opus-encoded
  audio which aiortc decodes to PCM before passing to the pipeline.

## Why WebRTC instead of raw WebSockets

| Aspect | WebRTC | Raw WebSockets |
|--------|--------|----------------|
| **Codec** | Opus (hardware-accelerated in browsers), automatic negotiation | Must manually encode/decode audio |
| **Latency** | UDP-based (DTLS-SRTP), no head-of-line blocking | TCP-based, head-of-line blocking adds jitter |
| **Echo cancellation** | Built into browser's `getUserMedia` pipeline | Must implement yourself |
| **Noise suppression** | Built-in browser DSP | Must implement yourself |
| **NAT traversal** | ICE/STUN/TURN handles firewalls automatically | Requires manual proxy setup |
| **Jitter buffer** | Automatic adaptive jitter buffer | Must implement yourself |
| **Packet loss** | Opus FEC + PLC handles gracefully | Lost TCP segments cause stalls |

For real-time conversational audio, WebRTC provides 50–150ms lower latency than
WebSocket-based approaches and eliminates an entire class of audio engineering
problems (echo, jitter, codec negotiation) that you'd otherwise have to solve manually.
