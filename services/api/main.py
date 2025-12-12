# services/api/main.py
import os
import json
import asyncio
from fastapi import FastAPI, HTTPException, Depends, Request
from fastapi.responses import JSONResponse
import jwt
from redis.asyncio import Redis  # ✅ NEW
from nats.aio.client import Client as NATS
from datetime import datetime

app = FastAPI()

# Config
VALKEY_HOST = os.getenv("VALKEY_HOST", "localhost")
VALKEY_PORT = int(os.getenv("VALKEY_PORT", "6379"))
NATS_URL = os.getenv("NATS_URL", "nats://localhost:4222")
JWT_SECRET = os.getenv("JWT_SECRET")
JWT_AUDIENCE = os.getenv("JWT_AUDIENCE", "cuegrowth-api")
JWT_ISSUER = os.getenv("JWT_ISSUER", "cuegrowth")

async def get_current_user(request: Request):
    auth = request.headers.get("Authorization")
    if not auth or not auth.startswith("Bearer "):
        raise HTTPException(status_code=401, detail="Missing or invalid token")
    token = auth.split(" ")[1]
    try:
        payload = jwt.decode(
            token,
            JWT_SECRET,
            algorithms=["HS256"],
            audience=JWT_AUDIENCE,
            issuer=JWT_ISSUER
        )
        return payload
    except jwt.PyJWTError:
        raise HTTPException(status_code=401, detail="Invalid token")

@app.post("/task")
async def post_task(request: Request, user: dict = Depends(get_current_user)):
    body = await request.json()
    task_id = str(int(datetime.now().timestamp() * 1000))
    task = {"id": task_id, "payload": body, "created_at": datetime.utcnow().isoformat()}

    # Push to NATS
    nc = NATS()
    await nc.connect(servers=[NATS_URL], user=os.getenv("NATS_USER"), password=os.getenv("NATS_PASSWORD"))
    await nc.publish("tasks.process", json.dumps(task).encode())
    await nc.drain()

    # Increment task counter in Valkey
    redis = Redis(host=VALKEY_HOST, port=VALKEY_PORT, password=os.getenv('VALKEY_PASSWORD'))
    await redis.incr("tasks_submitted")
    await redis.close()

    return {"task_id": task_id, "status": "queued"}

@app.get("/stats")
async def get_stats():
    redis = Redis(host=VALKEY_HOST, port=VALKEY_PORT, password=os.getenv('VALKEY_PASSWORD'))
    keys = await redis.dbsize()
    submitted = await redis.get("tasks_submitted") or "0"
    processed = await redis.get("tasks_processed") or "0"
    await redis.close()

    # Convert to int (redis returns strings if decode_responses=True, else bytes)
    submitted = int(submitted.decode()) if isinstance(submitted, bytes) else int(submitted)
    processed = int(processed.decode()) if isinstance(processed, bytes) else int(processed)

    return {
        "valkey_keys_count": keys,
        "queue_backlog_length": 0,  # Simplified; NATS JetStream would give real value
        "worker_processed_count": processed,
        "tasks_submitted": submitted
    }
