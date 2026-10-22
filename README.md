# LLM Chat App

A chat app with a FastAPI backend and a Streamlit frontend, powered by Groq.

![Screenshot](docs/screenshot.png)

## Features

- Streaming responses
- Modes: Assistant, Tutor, Coder, Interviewer
- Conversation memory with history trimming
- Input validation with Pydantic

## Tech stack

FastAPI, Streamlit, Groq API (gpt-oss-20b), Pydantic

## Run locally

1. Copy `.env.example` to `.env` and add your Groq key
2. Backend: `cd backend && pip install -r requirements.txt && uvicorn app.main:app --reload`
3. Frontend: `cd frontend && pip install -r requirements.txt && streamlit run app.py`

## What I learned

(2–3 lines about problems you hit, like the 422 error, and how you fixed them)
