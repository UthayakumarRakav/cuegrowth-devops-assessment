# services/worker/main.py
import os
import json
import asyncio
from nats.aio.client import Client as NATS
from redis.asyncio import Redis
from prometheus_client import Counter, start_http_server
import signal

# Always expose metrics — even if NATS is down
tasks_processed = Counter('worker_tasks_processed_total', 'Total tasks processed')
tasks_failed = Counter('worker_tasks_failed_total', 'Total tasks failed')

VALKEY_HOST = os.getenv("VALKEY_HOST", "valkey-primary")
VALKEY_PORT = int(os.getenv("VALKEY_PORT", "6379"))
NATS_URL = os.getenv("NATS_URL", "nats://nats:4222")

async def main():
    # ✅ START METRICS SERVER IMMEDIATELY
    start_http_server(8001)
    print("✅ Metrics server started on :8001", flush=True)

    # Connect to Valkey
    redis = Redis(host=VALKEY_HOST, port=VALKEY_PORT, password=os.getenv('VALKEY_PASSWORD'))

    # Connect to NATS (no auth)
    nc = NATS()
    print(f"🔌 Connecting to NATS at {NATS_URL}...", flush=True)
    await nc.connect(servers=[NATS_URL], connect_timeout=10)
    print("✅ Connected to NATS", flush=True)

    # JetStream setup
    js = nc.jetstream()
    await js.add_stream(name="TASKS", subjects=["tasks.process"], retention="workqueue")
    sub = await js.pull_subscribe_bind("tasks.process", durable="worker_group")

    # Signal handler for graceful shutdown
    running = True
    def signal_handler(signum, frame):
        nonlocal running
        print("🛑 Shutdown signal received", flush=True)
        running = False
    signal.signal(signal.SIGINT, signal_handler)
    signal.signal(signal.SIGTERM, signal_handler)

    print("🟢 Worker is ready to process tasks", flush=True)

    while running:
        try:
            msgs = await sub.fetch(batch=1, timeout=1)
            for msg in msgs:
                try:
                    data = json.loads(msg.data.decode())
                    task_id = data.get('id', 'unknown')
                    print(f"📥 Processing task {task_id}", flush=True)
                    await asyncio.sleep(0.1)
                    await redis.set(f"result:{task_id}", json.dumps({"status": "success"}))
                    await redis.incr("tasks_processed")
                    tasks_processed.inc()
                    await msg.ack()
                    print(f"📤 Task {task_id} completed", flush=True)
                except Exception as e:
                    print(f"❌ Error: {e}", flush=True)
                    tasks_failed.inc()
                    await msg.nak()
        except asyncio.TimeoutError:
            continue
        except Exception as e:
            if running:
                print(f"⚠️ Fetch error: {e}", flush=True)
            await asyncio.sleep(1)

    await nc.close()
    await redis.close()
    print("👋 Worker shut down cleanly", flush=True)

if __name__ == "__main__":
    asyncio.run(main())
