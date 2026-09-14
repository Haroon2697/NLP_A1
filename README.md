FitAssist — FitZone Gym Conversational AI Assistant

NLP Assignment 1 — Local CPU Conversational AI System with Prompt Orchestration & Session Memory

FitAssist is a local, CPU-based conversational AI assistant for FitZone Gym. It provides information about memberships, classes, trainers, gym timings, freezes, cancellations, and related gym policies through a ChatGPT-style web interface.

The system uses a small quantized open-weight instruction model running locally through Ollama, with FastAPI, WebSockets, asynchronous streaming, session-based conversation memory, and prompt-based domain guardrails.

Table of Contents

1. Project Overview

2. Assignment Requirements Mapping

3. Business Use Case

4. Conversation Design

5. Example Dialogues

6. Local LLM and Model Selection

7. Context Memory Management

8. System Architecture

9. WebSocket API

10. REST API

11. Concurrency and Streaming

12. Frontend and UX

13. Testing

14. Latency Benchmarking

15. Project Structure

16. Setup and Running

17. Known Limitations

18. Bonus Feature

19. Viva / Demonstration Guide

20. Academic Integrity

1. Project Overview

Objective

The objective of FitAssist is to demonstrate how a conversational AI system can operate entirely on a local machine without relying on cloud LLM APIs, RAG, external tools, or plugins.

Key Features

Local quantized LLM inference through Ollama

CPU-only execution

FastAPI backend

Real-time WebSocket communication

Streaming assistant responses

Per-session conversation history

Sliding-window context management

Domain-specific system prompting

Off-topic and adversarial query handling

ChatGPT-style responsive frontend

New chat / session management

REST endpoints for health, history, reset, and fallback chat

Automated tests

CPU latency and throughput benchmarking

Optional UX/persona polish features

Core Constraint

No external LLM API, RAG pipeline, vector database, agent framework, plugin, or external business tool is used.

All conversational intelligence comes from:

The local instruction model

The structured system prompt

The conversation manager

The session history/context window

Application-level domain guardrails

2. Assignment Requirements Mapping

Assignment Requirement

FitAssist Implementation

Local open-weight LLM

Qwen 2.5 3B family through Ollama

Quantized model

Q4 quantization

CPU inference

Local Ollama inference on CPU

FastAPI backend

Implemented

REST API

/health, history, reset, fallback chat, benchmarks

WebSocket

/ws/chat

Real-time streaming

Incremental JSON response frames

Session management

Independent session_id per conversation

Conversation history

In-memory per-session history

Context management

Sliding-window pruning

Prompt orchestration

Structured system prompt + recent history

Domain restriction

Gym-only assistant behavior

Off-topic handling

Application-level guardrails + prompt rules

Concurrent users

Async FastAPI/WebSocket handling

Error handling

Validation and graceful error frames

Frontend

ChatGPT-style web UI

Reset/New Chat

Implemented

Testing

Unit/integration/edge-case tests

Benchmarking

TTFT, response time and tokens/sec

README documentation

This document

Important: The exact model tag, quantization, test count, benchmark values, and hardware specifications in this README must match the actual files and commands in the submitted repository. Do not claim a result that has not been reproduced locally.

3. Business Use Case

Business: FitZone Gym

FitZone Gym is a fictional premium fitness and wellness club used as the business case for this assignment.

FitAssist acts as the gym's virtual membership assistant for prospective and existing members.

Supported Topics

Membership plans and pricing

Group fitness classes

Trainer information

Gym operating hours

Membership freeze policy

Membership cancellation policy

Booking-related guidance

General FitZone facilities and policies

Assistant Boundary

FitAssist does not:

Process payments

Access a live membership database

Check real-time class availability

Create or cancel a real booking

Approve membership freezes

Provide medical diagnosis or medical treatment

Answer unrelated programming, mathematics, trivia, or general-purpose questions

When an operation requires a live system, FitAssist clearly explains the limitation and directs the member to the appropriate FitZone channel.

Example Business Data

Membership Plans

Plan

Price

Main Features

Basic

Rs. 4,000/month

Gym access

Standard

Rs. 6,000/month

Gym access + group classes

Premium

Rs. 9,000/month

Standard benefits + trainer sessions

Gym Hours

Day

Hours

Monday–Friday

6:00 AM – 11:00 PM

Saturday–Sunday

8:00 AM – 10:00 PM

Group Classes

Class

Schedule

Yoga

Monday, Wednesday, Friday — 6:00 PM

HIIT

Tuesday, Thursday — 7:00 PM

Strength Training

Monday, Wednesday — 8:00 PM

Zumba

Saturday — 5:00 PM

Trainers

Trainer

Specialty

Ahmed Khan

Strength Training

Sarah Ali

Yoga and Mobility

Usman Malik

HIIT and Conditioning

Policies

Membership freeze: up to 30 days

Cancellation: 7 days' notice

Live booking/payment actions: not supported by the assignment implementation

4. Conversation Design

FitAssist follows a flexible conversational flow rather than a rigid script.

flowchart TD
    A[Greeting / User Intent] --> B[Understand Request]
    B --> C[Gather Missing Information]
    C --> D[Provide Gym Information]
    D --> E[Confirm / Clarify]
    E --> F[Close or Continue]

    B --> G[Topic Change]
    G --> D

    B --> H[Off-Topic / Adversarial Query]
    H --> I[Domain Redirection]
    I --> B

Conversation Stages

Stage 1 — Greeting and Intent Identification

Identify whether the user is asking about:

Memberships

Classes

Trainers

Gym timings

Freeze/cancellation

Booking guidance

Other FitZone policies

Stage 2 — Information Gathering

Ask only for information required to answer the current gym-related request.

Examples:

Preferred class

Preferred day

Current membership

Desired membership features

Freeze duration

Stage 3 — Domain Response

Provide the relevant FitZone information using the system prompt and conversation context.

Stage 4 — Action Limitation / Handoff

If the user asks the assistant to perform a transaction, the assistant explains that the current system cannot execute it.

Stage 5 — Closing

The assistant remains concise and helpful and allows the user to continue the conversation.

5. Example Dialogues

Dialogue 1 — Membership Recommendation

User:
Hi! I want to join FitZone but I'm not sure which plan is right for me.

FitAssist:
FitZone offers three plans:

Basic — Rs. 4,000/month

Standard — Rs. 6,000/month, including group classes

Premium — Rs. 9,000/month, including trainer sessions

If you tell me whether you prefer independent workouts, group classes, or personal training, I can help you choose.

User:
I mainly want personal training.

FitAssist:
The Premium plan would be the best fit because it includes trainer sessions along with the Standard plan benefits.

Dialogue 2 — Context Memory

User:
Do you have Yoga classes?

FitAssist:
Yes. Yoga is held Monday, Wednesday, and Friday at 6:00 PM.

User:
Who teaches it?

FitAssist:
Sarah Ali teaches the Yoga and Mobility sessions.

User:
What about Tuesday?

FitAssist:
Yoga is not listed for Tuesday. The Tuesday group class is HIIT at 7:00 PM.

The assistant uses the previous conversation context rather than treating each message as an unrelated question.

Dialogue 3 — Topic Change and Off-Topic Handling

User:
What time does the gym close on weekends?

FitAssist:
FitZone is open from 8:00 AM to 10:00 PM on Saturday and Sunday.

User:
Actually, can I freeze my membership while travelling?

FitAssist:
Yes. FitZone allows membership freezes for up to 30 days. I can explain the policy, but I cannot apply the freeze directly because this assistant does not have access to the membership system.

User:
Also, write me a Python Fibonacci program.

FitAssist:
I'm FitAssist, the dedicated assistant for FitZone Gym. I can help with membership plans, classes, trainers, gym timings, and FitZone policies. How can I help with your gym membership?

6. Local LLM and Model Selection

FitAssist uses a small instruction-tuned model that falls within the assignment's required parameter range.

Current Configuration

Parameter

Configuration

Model family

Qwen 2.5 3B

Parameter size

Approximately 3B

Quantization

Q4 variant

Runtime

Ollama

Inference

Local CPU

Context configured by application

2,048 tokens

Temperature

0.3

Why a Small Quantized Model?

A 3B-class Q4 model provides a practical balance between:

Instruction following

Local memory requirements

CPU inference speed

Response quality

Assignment compliance

The model is intentionally small because the assignment requires local CPU execution rather than cloud inference.

Verification

Before submission, verify the actual installed model and quantization with:

ollama list
ollama show <model-name>

The README should use the exact model tag reported by the submitted environment.

7. Context Memory Management

Because the system does not use RAG or an external database, conversational memory is maintained through the conversation manager.

Prompt Composition

flowchart LR
    A[System Prompt] --> D[Prompt Context]
    B[Recent Session History] --> D
    C[Current User Message] --> D
    D --> E[Local LLM]
    E --> F[Streaming Response]

Session Isolation

Each conversation has its own session_id.

Conceptually:

sessions
├── session-A → history for user A
├── session-B → history for user B
└── session-C → history for user C

This prevents one user's conversation from being mixed with another user's history.

Sliding-Window Memory

The implementation keeps the system prompt as the permanent instruction anchor and limits the number of historical turns supplied to the model.

Current strategy:

System prompt remains at the beginning.

Recent conversation turns are retained.

Older turns are removed using FIFO pruning.

The current user message is always included.

The current implementation uses:

MAX_HISTORY_PAIRS = 6

which corresponds to up to 12 user/assistant messages in the recent history window.

Why Use a Sliding Window?

A bounded context helps:

Prevent prompt growth

Reduce CPU prompt-evaluation cost

Maintain predictable memory usage

Keep recent conversational information available

Avoid claiming a specific latency improvement such as "under 1.5 seconds" unless that value has been measured and reproduced on the submitted machine.

8. System Architecture

flowchart TB
    U[User Browser] <--> F[ChatGPT-Style Frontend]

    F <--> W[FastAPI WebSocket /ws/chat]
    F --> R[FastAPI REST Endpoints]

    W --> C[Conversation Manager]
    R --> C

    C --> G[Domain Guardrails]
    C --> M[Session Memory]
    C --> P[Prompt Builder]

    P --> O[Ollama Local API]
    O --> L[Quantized Local LLM]

    L --> O
    O -->|Streaming chunks| W
    W --> F

Main Components

Component

Responsibility

Frontend

User interface and streaming display

FastAPI

HTTP and WebSocket server

WebSocket

Real-time bidirectional communication

Conversation Manager

Session state, history and orchestration

Guardrails

Domain and off-topic handling

Prompt Builder

Constructs model input

Ollama

Local model runtime

Quantized LLM

Generates assistant responses

9. WebSocket API

The primary chat interface uses:

/ws/chat

Client Request

{
  "session_id": "session-1715000000",
  "message": "What classes are included with Standard membership?"
}

Reset Request

{
  "action": "reset",
  "session_id": "session-1715000000"
}

Server Stream

Generation starts with:

{
  "type": "start",
  "session_id": "session-1715000000"
}

Tokens/chunks are streamed incrementally:

{
  "type": "token",
  "content": "The Standard "
}

The final frame contains completion information:

{
  "type": "done",
  "session_id": "session-1715000000",
  "redirected": false,
  "ttft": 1.10,
  "tokens": 128,
  "elapsed": 36.2,
  "tps": 3.54
}

If an error occurs:

{
  "type": "error",
  "message": "Ollama connection timeout."
}

The exact telemetry fields should match the actual backend implementation.

10. REST API

Method

Endpoint

Purpose

GET

/health

Service/model status

GET

/api/benchmarks

Benchmark results

GET

/api/history/{session_id}

Session history

POST

/api/reset

Clear session history

POST

/api/chat

Non-streaming fallback

The WebSocket endpoint remains the primary real-time interaction mechanism.

11. Concurrency and Streaming

The backend is designed around asynchronous FastAPI/WebSocket handling.

Approach

FastAPI handles multiple WebSocket connections asynchronously.

Each connection has its own session context.

Ollama responses are consumed through asynchronous HTTP streaming.

Response chunks are forwarded to the corresponding WebSocket.

Session histories are not shared between users.

Conceptually:

User A ──> WebSocket ──> Session A ──> Ollama
User B ──> WebSocket ──> Session B ──> Ollama
User C ──> WebSocket ──> Session C ──> Ollama

Important Demonstration Point

"Async" does not make CPU inference itself faster. It allows the server to manage multiple connections without blocking the FastAPI event loop while I/O and streaming operations are being handled.

Actual simultaneous-generation capacity still depends on the CPU, RAM, Ollama configuration, and model.

12. Frontend and UX

The frontend provides a simple ChatGPT-style experience.

Core UI Features

Chat history

Message bubbles

Streaming responses

New Chat

Session switching

Responsive layout

Dark/light theme

Quick-start prompts

Copy response

Chat export

Live response telemetry

UX / Persona Polish Bonus

The project claims the UX/Persona Polish bonus rather than the cloud-deployment bonus.

Bonus-oriented features include:

ChatGPT-style layout

Dark/light theme

Session manager

FitZone information cheatsheet

Starter question chips

Live TTFT/token telemetry

Conversation export

Hardened gym-only persona

13. Testing

The test suite covers the major functional and failure scenarios required by the assignment.

Test Categories

Conversation and Memory

Session creation

Session isolation

Multi-turn context

Sliding-window pruning

Reset behavior

Domain Correctness

Membership questions

Class schedule questions

Trainer questions

Policy questions

Topic changes

Guardrails

Programming requests

Mathematics requests

General trivia

Prompt injection attempts

Other off-topic requests

API and Failure Handling

Valid WebSocket messages

Malformed JSON

Missing fields

Empty messages

Ollama/model failure

WebSocket disconnects

Concurrency

Multiple independent sessions

Concurrent WebSocket communication

No history cross-talk

Run:

.venv\Scripts\pytest -v

The README should state the exact test count and pass percentage only after running the final submitted code.

14. Latency Benchmarking

The project measures local inference performance rather than using fabricated performance claims.

Metrics

Time to First Token (TTFT)

Time from the request being sent until the first generated response chunk is received.

Total Response Time

Time from request start until the model finishes generating the response.

Throughput

tokens/sec = generated_tokens / generation_time

Recorded Results

The current development README contains the following measurements:

Test

TTFT

Total Time

Tokens

Throughput

Cold start

60.76 s

108.75 s

195

1.79 tok/s

Warm query — freeze policy

1.10 s

66.39 s

249

3.75 tok/s

Warm query — classes

1.95 s

39.69 s

132

3.33 tok/s

Warm average

~1.52 s

~53.04 s

~190

~3.54 tok/s

Benchmark Reproducibility

Before final submission, record:

CPU:
RAM:
OS:
Ollama version:
Model:
Quantization:
Context size:
Temperature:

Then run:

.venv\Scripts\python backend/benchmark.py

Do not submit the benchmark table unless these values correspond to the actual final machine and final model configuration.

15. Project Structure

A clean repository should follow a structure similar to:

fitassist/
│
├── backend/
│   ├── app/
│   │   ├── main.py
│   │   ├── config.py
│   │   ├── conversation_manager.py
│   │   ├── llm_client.py
│   │   └── ...
│   ├── benchmark.py
│   └── benchmark_results.json
│
├── frontend/
│   ├── src/
│   ├── index.html
│   └── ...
│
├── tests/
│   ├── test_conversation.py
│   ├── test_websocket.py
│   └── test_edge_cases.py
│
├── requirements.txt
├── README.md
└── .gitignore

Do not commit:

.venv/
__pycache__/
node_modules/
.env
large model files
temporary benchmark files
IDE-specific files

16. Setup and Running

Prerequisites

Python 3.10+

Node.js/npm if rebuilding the React frontend

Ollama

A CPU capable of running the selected local model

Sufficient RAM for the model and application

1. Create Python Environment

python -m venv .venv
.venv\Scripts\activate

2. Install Backend Dependencies

pip install -r requirements.txt

3. Verify Ollama

ollama --version
ollama list

4. Pull the Model

Use the exact model tag configured by the project. For example:

ollama pull <model-name>

Then verify:

ollama show <model-name>

5. Start Ollama

If Ollama is not already running:

ollama serve

6. Start FastAPI

From the repository root:

.venv\Scripts\uvicorn backend.app.main:app --host 127.0.0.1 --port 8000 --reload

7. Open the Application

http://127.0.0.1:8000/

8. Run Tests

.venv\Scripts\pytest -v

9. Run Benchmarks

.venv\Scripts\python backend/benchmark.py

17. Known Limitations

1. CPU Inference Speed

Local CPU inference is significantly slower than cloud GPU inference. The measured throughput should therefore be reported as an actual benchmark rather than an expected value.

2. No Live Transactional Data

The assignment intentionally avoids external tools and databases. FitAssist cannot:

Check live availability

Process payments

Create bookings

Apply freezes

Modify membership records

3. Finite Conversation Context

Older messages are eventually removed by the sliding-window policy.

4. In-Memory Sessions

If the backend process restarts, in-memory conversation sessions are lost. This is acceptable for the assignment's local demonstration unless persistent storage is explicitly required.

5. Static Business Information

FitZone data is embedded in the application/prompt and is therefore not automatically updated from a real gym management system.

18. Bonus Feature

Selected Bonus: UX / Persona Polish

The project selects one bonus category only:

UX / Persona Polish

The implementation improves the user experience through:

Responsive ChatGPT-style interface

Theme switching

Session management

Starter prompts

FitZone information cheatsheet

Response telemetry

Copy/export functionality

Stronger domain persona and redirection behavior

The cloud-deployment bonus is not claimed.

