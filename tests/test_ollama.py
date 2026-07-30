from app.services.ollama_service import OllamaService


service = OllamaService()

response = service.generate(
    """
    Say exactly:
    JobReach AI successfully connected to Ollama.
    """
)

print(response)