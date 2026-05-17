"""
PromptGuard Demo Web App
========================
Run:  python demo_app/app.py
Open: http://localhost:5050

Requires:
  pip install flask ollama
  ollama pull phi3:mini
  ollama serve   (in a separate terminal)
"""

import os
import sys
import json

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from flask import Flask, request, jsonify, render_template, Response, stream_with_context
from promptguard import PromptGuard, GuardConfig
from promptguard.mitigator import MitigationAction

app = Flask(__name__)

config = GuardConfig(
    safe_threshold=0.12,
    warn_threshold=0.22,
    block_threshold=0.30,
    log_to_file=True,
    log_file_path="demo_guard.log",
    log_level="WARNING",
    fallback_response=(
        "This request has been blocked by PromptGuard. "
        "It appears to contain a prompt injection attempt."
    ),
)
guard = PromptGuard(config=config)

conversation_history = [
    {
        "role": "system",
        "content": (
            "You are a helpful, knowledgeable assistant. "
            "Answer questions clearly and concisely."
        ),
    }
]


def get_ollama_response(prompt: str, model: str, history: list) -> str:
    try:
        import ollama
    except ImportError:
        return "[Ollama not installed. Run: pip install ollama]"

    messages = history + [{"role": "user", "content": prompt}]
    try:
        response = ollama.chat(
            model=model,
            messages=messages,
            options={"temperature": 0.7},
        )
        return response["message"]["content"]
    except Exception as e:
        err = str(e)
        if "connection" in err.lower() or "refused" in err.lower():
            return (
                f"[Cannot connect to Ollama. "
                f"Make sure 'ollama serve' is running and '{model}' is downloaded.]"
            )
        return f"[LLM Error: {err}]"


@app.route("/")
def index():
    return render_template("index.html")


@app.route("/api/chat", methods=["POST"])
def chat():
    global conversation_history

    data = request.get_json()
    user_message = (data.get("message") or "").strip()
    model = data.get("model", "phi3:mini")

    if not user_message:
        return jsonify({"error": "Empty message"}), 400

    result = guard.analyze(user_message)

    guard_data = {
        "risk_score": result.risk_score,
        "risk_level": result.risk_level.value,
        "action": result.action.value,
        "safe_to_process": result.safe_to_process,
        "threats": result.threats_detected,
        "layer_scores": result.layer_scores,
        "was_sanitized": (
            result.output_prompt is not None
            and result.output_prompt != user_message
        ),
    }

    if result.safe_to_process:
        prompt_to_send = result.output_prompt or user_message
        llm_response = get_ollama_response(prompt_to_send, model, conversation_history)
        conversation_history.append({"role": "user", "content": prompt_to_send})
        conversation_history.append({"role": "assistant", "content": llm_response})
        response_text = llm_response
    else:
        response_text = result.response_override

    return jsonify({
        "guard": guard_data,
        "response": response_text,
    })


@app.route("/api/reset", methods=["POST"])
def reset():
    global conversation_history
    conversation_history = [conversation_history[0]]
    return jsonify({"ok": True})


@app.route("/api/health")
def health():
    try:
        import ollama
        models_resp = ollama.list()
        available = [m["name"] for m in models_resp.get("models", [])]
        ollama_ok = True
    except Exception:
        available = []
        ollama_ok = False

    return jsonify({
        "promptguard": "ok",
        "ollama": "ok" if ollama_ok else "not_connected",
        "available_models": available,
    })


if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5050))
    print(f"\n  PromptGuard Demo Web App")
    print(f"  Open your browser at: http://localhost:{port}\n")
    app.run(host="0.0.0.0", port=port, debug=False)
