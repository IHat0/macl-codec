import json
import os

def generate_demo_agents():
    agents = [
        {
            "id": "agent_ironclad",
            "name": "Ironclad",
            "personality": {
                "archetype": "Berserker",
                "traits": ["Aggressive", "Fearless", "Impulsive"],
                "combat_style": "Charge headfirst",
                "strategy": "Eliminate threats quickly",
                "speech_style": "Gruff, battle-hardened",
                "backstory": "A veteran of countless arena battles.",
                "strengths": ["High damage", "Intimidation"],
                "weaknesses": ["Reckless", "Poor resource management"]
            },
            "position": {"x": 10, "y": 64, "z": 10}
        },
        {
            "id": "agent_whisper",
            "name": "Whisper",
            "personality": {
                "archetype": "Assassin",
                "traits": ["Calculated", "Patient", "Deceptive"],
                "combat_style": "Strike from shadows",
                "strategy": "Observe, gather intel, strike when weak",
                "speech_style": "Cryptic, poetic",
                "backstory": "Learned survival in the deepest caves.",
                "strengths": ["Strategic thinking", "Adaptability"],
                "weaknesses": ["Poor in direct combat", "Isolationist"]
            },
            "position": {"x": -10, "y": 64, "z": -10}
        }
    ]
    return agents

if __name__ == "__main__":
    agents = generate_demo_agents()
    # Windows-friendly path using os.path.join
    filepath = os.path.join("config", "agents.json")
    with open(filepath, "w") as f:
        json.dump(agents, f, indent=2)
    print("✅ Generated 2 agents -> config/agents.json")