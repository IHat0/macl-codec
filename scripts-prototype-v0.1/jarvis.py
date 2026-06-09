import json
import time
import requests
from datetime import datetime
from typing import Optional, Dict, List
from dataclasses import dataclass, field
from enum import Enum

class AgentState(Enum):
    IDLE = "idle"
    THINKING = "thinking"
    ACTING = "acting"
    DEAD = "dead"

@dataclass
class MinecraftAction:
    action_type: str = "wait"
    target: Optional[str] = None
    parameters: Dict = field(default_factory=dict)
    reasoning: str = ""

@dataclass
class Agent:
    id: str
    name: str
    personality: Dict
    state: AgentState = AgentState.IDLE
    health: float = 20.0
    hunger: float = 20.0
    energy: float = 20.0
    position: Dict = field(default_factory=lambda: {"x": 0, "y": 64, "z": 0})
    inventory: List[Dict] = field(default_factory=list)
    memory: List[str] = field(default_factory=list)
    kills: int = 0

class JARVIS:
    def __init__(self, llm_base_url: str, llm_model: str, llm_api_key: str):
        self.llm_base_url = llm_base_url
        self.llm_model = llm_model
        self.llm_api_key = llm_api_key
        self.agents: Dict[str, Agent] = {}
        self.world_state: Dict = {}
        self.running = False
        self.turn_count = 0

    def register_agent(self, agent: Agent):
        self.agents[agent.id] = agent
        print(f"[JARVIS] Registered agent: {agent.name}")

    def update_world_state(self, state: Dict):
        self.world_state = state

    def _build_prompt(self, agent: Agent) -> str:
        personality = agent.personality
        inv_str = json.dumps(agent.inventory) if agent.inventory else "Empty"
        mem_str = "\n".join(agent.memory[-3:]) if agent.memory else "No memories."
        
        return f"""You are {agent.name}, an AI agent in a Minecraft survival arena.
Personality: {personality.get('archetype')}. Traits: {', '.join(personality.get('traits'))}.
Strategy: {personality.get('strategy')}.

Stats: Health={agent.health}/20, Hunger={agent.hunger}/20
Inventory: {inv_str}
Recent Memories: {mem_str}
World: {json.dumps(self.world_state)[:300]}

Pick ONE action. You MUST respond ONLY in this exact JSON format:
{{
    "reasoning": "Why you are doing this",
    "action": "action_type",
    "target": "what you are targeting",
    "parameters": {{}},
    "speech": "What you say out loud"
}}
Action types: move, attack, gather, craft, chat, wait"""

    def query_groq(self, system_prompt: str) -> str:
        headers = {
            "Content-Type": "application/json",
            "Authorization": f"Bearer {self.llm_api_key}"
        }
        payload = {
            "model": self.llm_model,
            "messages": [
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": "What is your next action?"}
            ],
            "temperature": 0.7,
            "max_tokens": 500,
            "response_format": {"type": "json_object"} 
        }
        try:
            response = requests.post(
                f"{self.llm_base_url}/chat/completions",
                headers=headers, json=payload, timeout=15
            )
            response.raise_for_status()
            return response.json()["choices"][0]["message"]["content"]
        except Exception as e:
            print(f"[JARVIS] Groq API Error: {e}")
            return '{"action": "wait", "reasoning": "API error", "target": null, "parameters": {}, "speech": "..."}'

    def parse_action(self, raw_response: str) -> MinecraftAction:
        try:
            parsed = json.loads(raw_response)
            return MinecraftAction(
                action_type=parsed.get("action", "wait"),
                target=parsed.get("target"),
                parameters=parsed.get("parameters", {}),
                reasoning=parsed.get("reasoning", "")
            )
        except json.JSONDecodeError:
            print("[JARVIS] Chef sent gibberish. Defaulting to wait.")
            return MinecraftAction(action_type="wait")

    def apply_effects(self, agent_id: str, action: MinecraftAction):
        agent = self.agents[agent_id]
        agent.memory.append(f"Turn {self.turn_count}: {action.action_type} -> {action.target}. Because: {action.reasoning[:80]}")

        if action.action_type == "move":
            agent.energy = max(0, agent.energy - 0.5)
            agent.hunger = max(0, agent.hunger - 0.3)
        elif action.action_type == "attack":
            agent.energy = max(0, agent.energy - 1.0)
            if action.target and action.target in self.agents:
                target = self.agents[action.target]
                target.health = max(0, target.health - 4.0) 
                print(f"  ⚔️ {agent.name} hit {target.name}! Target HP: {target.health}/20")
                if target.health <= 0:
                    target.state = AgentState.DEAD
                    agent.kills += 1
                    print(f"  💀 {target.name} was eliminated by {agent.name}!")
        elif action.action_type == "gather":
            resource = action.target or "wood"
            agent.inventory.append({"name": resource})
            print(f"  🪵 {agent.name} gathered {resource}")
        elif action.action_type == "chat":
            speech = action.parameters.get("speech", action.parameters.get("message", ""))
            print(f"  💬 {agent.name}: \"{speech}\"")

    def run_simulation(self, max_turns: int = 20):
        self.running = True
        print("\n" + "="*50)
        print("  M.A.C. DEMO STARTING")
        print("="*50 + "\n")

        for turn in range(1, max_turns + 1):
            self.turn_count = turn
            living = [a for a in self.agents.values() if a.state != AgentState.DEAD]

            if len(living) <= 1:
                if living: print(f"\n🏆 {living[0].name} WINS!")
                else: print("\n💀 Everyone died.")
                break

            print(f"\n--- TURN {turn} ---")

            for agent in living:
                if agent.state == AgentState.DEAD: continue
                
                agent.state = AgentState.THINKING
                prompt = self._build_prompt(agent)
                raw = self.query_groq(prompt)
                action = self.parse_action(raw)
                agent.state = AgentState.ACTING
                print(f"[{agent.name}] Action: {action.action_type} | Reason: {action.reasoning[:60]}")

                self.apply_effects(agent.id, action)
                time.sleep(2) 

            print(f"\n--- END TURN {turn} STATUS ---")
            for a in self.agents.values():
                status = "💀 DEAD" if a.state == AgentState.DEAD else f"❤️ {a.health} | 🍖 {a.hunger}"
                print(f"  {a.name}: {status}")

        print("\nSimulation Complete.")