import os

import anthropic
import uvicorn
from dotenv import load_dotenv
from fastapi import FastAPI, Request
from fastapi.staticfiles import StaticFiles
from modal import Image, Mount, Stub, asgi_app

from client import AutoContextRAGClient

load_dotenv()  # This loads the environment variables from .env.

web_app = FastAPI()
web_app.mount("/static", StaticFiles(directory="static"), name="static")

ANTHROPIC_API_KEY = os.environ.get("ANTHROPIC_API_KEY")
anthropic_client = anthropic.Anthropic(api_key=ANTHROPIC_API_KEY)

USE_SLACK = bool(int(os.environ.get("USE_SLACK", "0")))
if USE_SLACK:
    from slack_integration import router as slack_router
    web_app.include_router(slack_router)

rag_client = AutoContextRAGClient()


@web_app.get("/hello/{name}")
async def say_hello(name: str):
    return {"message": f"Hello {name}"}


@web_app.post("/add_entry")
async def add_embedding(request: Request):
    print("inside add_entry")
    req = await request.json()
    result = rag_client.add_entry(req)
    return result


@web_app.post("/get_entry")
async def get_embedding(request: Request):
    req = await request.json()
    search_response = rag_client.get_entry(req)
    
    return search_response


if __name__ == "__main__":
    print("Uvicorn server is running")
    uvicorn.run(
        "main:web_app",
        port=8080,
        reload=True,
        ssl_keyfile="key.pem",
        ssl_certfile="cert.pem",
    )
# create a DB locally


stub = Stub()
image = Image.from_registry("python:3.11")
image = image.pip_install_from_requirements("requirements.txt")


@stub.function(
    image=image,
    mounts=[
        Mount.from_local_dir("./static", remote_path="/root/static"),
        Mount.from_local_file(".env", "/root/.env"),
    ],
)
@asgi_app()
def fastapi_app():
    return web_app
