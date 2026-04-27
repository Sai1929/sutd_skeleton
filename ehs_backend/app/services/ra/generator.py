"""Generate Risk Assessment using the same client + system prompt as the chatbot."""
from app.services.chat.client import GroqChatClient


async def generate_ra(project_text: str, project_name: str) -> str:
    client = GroqChatClient()
    message = f"Project: {project_name}\n\n{project_text}"
    return await client.chat([{"role": "user", "content": message}])
