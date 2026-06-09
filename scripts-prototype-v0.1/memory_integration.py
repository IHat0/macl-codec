import json
import os
from datetime import datetime

class MemoryIntegration:
    def __init__(self, zep_api_key: str):
        self.zep_api_key = zep_api_key
        self.client = None
        if zep_api_key and zep_api_key != "fallback":
            try:
                from zep_cloud.client import Zep
                self.client = Zep(api_key=zep_api_key)
                print("[Memory] ✅ Connected to Zep Cloud")
            except Exception as e:
                print(f"[Memory] ⚠️ Zep failed: {e}. Using local files.")
                self.client = None
        else:
            print("[Memory] ⚠️ No Zep key. Using local files.")

    def save_action(self, agent_id: str, agent_name: str, action: dict):
        text = f"{agent_name} did {action.get('action_type')} because {action.get('reasoning','')[:100]}"
        
        if self.client:
            try:
                self.client.memory.add(session_id=agent_id, messages=[{"role": "assistant", "content": text}])
            except Exception as e:
                self._save_local(agent_id, text)
        else:
            self._save_local(agent_id, text)

    def get_memories(self, agent_id: str) -> str:
        if self.client:
            try:
                mems = self.client.memory.search(session_id=agent_id, text="What happened recently?", limit=3)
                if mems.results:
                    return "\n".join([r.message.content for r in mems.results if hasattr(r, 'message')])
            except: pass
        return self._read_local(agent_id)

    def _save_local(self, agent_id: str, text: str):
        # Windows-friendly path
        os.makedirs("logs\\memory", exist_ok=True)
        filepath = os.path.join("logs", "memory", f"{agent_id}.jsonl")
        with open(filepath, "a") as f:
            f.write(json.dumps({"time": datetime.now().isoformat(), "text": text}) + "\n")

    def _read_local(self, agent_id: str) -> str:
        filepath = os.path.join("logs", "memory", f"{agent_id}.jsonl")
        if os.path.exists(filepath):
            with open(filepath, "r") as f: lines = f.readlines()[-3:]
            return "\n".join(lines)
        return "No memories yet."