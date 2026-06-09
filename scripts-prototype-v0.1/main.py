import json
import sys
import os

# This tells Python where to find our other scripts
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "scripts"))

from jarvis import JARVIS, Agent
from generate_agents import generate_demo_agents
from memory_integration import MemoryIntegration
from amd_compat import configure_gpu

def main():
    print("""
    ============================================
    M.A.C. DEMO - 2 Agent Minecraft AI
    ============================================
    """)

    # 1. Plug in the GPU (NVIDIA for your laptop)
    configure_gpu("cuda")

    # 2. Load API Keys (PASTE YOUR REAL GROQ KEY BELOW!)
    GROQ_KEY = "GROK KEY HERE"
    ZEP_KEY = "fallback" 

    # 3. Start JARVIS Manager
    jarvis = JARVIS(
        llm_base_url="https://api.groq.com/openai/v1",
        llm_model="llama-3.3-70b-versatile",
        llm_api_key=GROQ_KEY
    )

    # 4. Create the Agents
    agent_defs = generate_demo_agents()
    for ad in agent_defs:
        agent = Agent(id=ad["id"], name=ad["name"], personality=ad["personality"], position=ad["position"])
        jarvis.register_agent(agent)

    # 5. Start Memory
    memory = MemoryIntegration(ZEP_KEY)

    # 6. Set the World State (MADE MORE DANGEROUS)
    jarvis.update_world_state({
        "arena": "Tiny Cave (10x10 blocks)",
        "nearby_resources": ["None left"],
        "threats": "The other agent is right in front of you! The cave is collapsing!"
    })

    # 7. RUN!
    jarvis.run_simulation(max_turns=15)

if __name__ == "__main__":
    main()