# python/controller.py
import asyncio
import json
import time
import websockets

# --- 1) Hard-coded MAC-L envelope generator for now ---

def generate_macl_envelope(task_id: int) -> str:
    # Longer-running envelope: chat, wait, chat, wait
    return (
        f"BATCH {task_id} "
        f"DO CHAT hello_from_MACL "
        f"DO WAIT 5000 "
        f"DO CHAT still_running "
        f"DO WAIT 5000 "
        f"END"
    )

# --- 2) Main orchestrator: send envelope, then trigger threat, measure latency ---

async def main():
    uri = "ws://localhost:8765"
    async with websockets.connect(uri) as ws:
        print("Connected to MAC-L bot server.")

        task_id = 1
        envelope = generate_macl_envelope(task_id)
        print("Generated envelope:", envelope)

        # Send envelope to bot
        await ws.send(envelope)
        print("Envelope sent, waiting briefly before triggering threat...")

        # Wait a bit to let first action start, then trigger THREAT
        await asyncio.sleep(0.2)
        threat_payload = {"type": "THREAT"}
        t_threat_send = time.time()
        await ws.send(json.dumps(threat_payload))
        print("THREAT sent.")

        # Listen for INT / RESULT
        while True:
            msg = await ws.recv()
            t_recv = time.time()
            try:
                obj = json.loads(msg)
            except json.JSONDecodeError:
                print("Received non-JSON:", msg)
                continue

            if obj.get("type") == "INT":
                interrupt_ms = obj.get("interruptMs")
                reflex_ms = obj.get("reflexMs")
                total_ms = (t_recv - t_threat_send) * 1000.0
                print(f"[INT] task={obj.get('taskId')} "
                      f"completedSteps={obj.get('completedSteps')}/{obj.get('totalSteps')}")
                print(f"  interruptMs (bot clock): {interrupt_ms} ms")
                print(f"  reflexMs (bot clock): {reflex_ms} ms")
                print(f"  end-to-end (Python clock): {total_ms:.2f} ms")
                break

            elif obj.get("type") == "RESULT":
                print(f"[RESULT] task={obj.get('taskId')} "
                      f"status={obj.get('status')} "
                      f"steps={obj.get('completedSteps')}/{obj.get('totalSteps')} "
                      f"latencyMs={obj.get('latencyMs')}")
            else:
                print("Received:", obj)

if __name__ == "__main__":
    asyncio.run(main())