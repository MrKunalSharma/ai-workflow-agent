import ollama

# Test if Ollama works at all
try:
    response = ollama.generate(
        model='mistral',
        prompt='Respond with JSON only: {"status": "working", "message": "hello"}',
        options={'temperature': 0.1}
    )
    print("Ollama response:", response['response'])
except Exception as e:
    print(f"Error: {e}")
