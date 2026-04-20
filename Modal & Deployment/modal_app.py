"""
Modal App — modular endpoint template.

Structure:
  - Use @modal.asgi_app() to mount a full FastAPI app under one Modal URL
  - All routes (GET /, POST /greet, etc.) share one deployment URL
  - Add new endpoints as FastAPI routes inside the factory function
  - For n8n API-only endpoints, use @modal.fastapi_endpoint on a separate @app.function
"""

import modal
from fastapi import FastAPI, Header, HTTPException
from fastapi.responses import HTMLResponse

# ---------------------------------------------------------------------------
# App & shared image
# ---------------------------------------------------------------------------

app = modal.App("my-workflow")

base_image = modal.Image.debian_slim().pip_install("fastapi")

# ---------------------------------------------------------------------------
# Auth helper (reuse across endpoints)
# ---------------------------------------------------------------------------

def verify_token(authorization: str | None, expected_token: str) -> None:
    if not authorization or not authorization.startswith("Bearer "):
        raise HTTPException(status_code=401, detail="Missing or invalid authorization header")
    if authorization.removeprefix("Bearer ") != expected_token:
        raise HTTPException(status_code=403, detail="Invalid authentication token")

# ---------------------------------------------------------------------------
# Toy app — single Modal URL, multiple routes
# Deploy: modal deploy modal_app.py
# URL:    https://woodychang891121--my-workflow-toy-app.modal.run
# ---------------------------------------------------------------------------

_TOY_UI = """<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="UTF-8" />
  <meta name="viewport" content="width=device-width, initial-scale=1.0"/>
  <title>Hello Woody</title>
  <style>
    body { font-family: sans-serif; display: flex; flex-direction: column; align-items: center; justify-content: center; min-height: 100vh; gap: 24px; background: #f5f5f5; }
    button { padding: 12px 32px; font-size: 16px; border: none; border-radius: 8px; background: #0084ff; color: white; cursor: pointer; }
    button:hover { background: #0073e6; }
    #result { font-size: 24px; font-weight: 600; color: #333; min-height: 36px; }
  </style>
</head>
<body>
  <button onclick="greet()">Click me</button>
  <div id="result"></div>
  <script>
    async function greet() {
      const res = await fetch("/greet", { method: "POST" });
      const data = await res.json();
      document.getElementById("result").textContent = data.message;
    }
  </script>
</body>
</html>"""


@app.function(image=base_image)
@modal.asgi_app()
def toy_app():
    """
    Toy example: one Modal URL hosts both the UI and its API route.

    GET  /       → HTML page with a button
    POST /greet  → returns {"message": "My name is Woody"}
    """
    web = FastAPI()

    @web.get("/", response_class=HTMLResponse)
    def ui():
        return _TOY_UI

    @web.post("/greet")
    def greet():
        return {"message": "My name is Woody"}

    return web


# ---------------------------------------------------------------------------
# Add new endpoints below — copy this pattern for each new workflow
# ---------------------------------------------------------------------------

# @app.function(
#     image=base_image.pip_install("anthropic"),
#     secrets=[
#         modal.Secret.from_name("anthropic-api-key"),
#         modal.Secret.from_name("api-auth-token"),
#     ],
#     timeout=120,
# )
# @modal.asgi_app()
# def my_workflow():
#     web = FastAPI()
#
#     @web.post("/run")
#     def run(data: dict, authorization: str = Header(None)):
#         import os
#         verify_token(authorization, os.environ["API_AUTH_TOKEN"])
#         # ... your logic here
#         return {"result": "..."}
#
#     return web
