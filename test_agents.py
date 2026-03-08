# test_agent.py
from agent import load_agent, ask

agent = load_agent()

# Test questions
questions = [
    "How many products are in the database?",
    "What is the highest rated product?",
    "Which category has the most products?"
]

for q in questions:
    print(f"\n❓ {q}")
    print(f"💬 {ask(agent, q)}")