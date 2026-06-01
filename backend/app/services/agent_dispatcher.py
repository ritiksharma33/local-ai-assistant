import json
import httpx
from app.services.tools.system_stats import get_system_diagnostics
from app.services.tools.weather_mock import get_current_weather

class AgentDispatcherService:
    def __init__(self, http_client: httpx.AsyncClient):
        self.client = http_client
        self.tool_registry = {
            "get_system_diagnostics": get_system_diagnostics,
            "get_current_weather": get_current_weather
        }

    async def execute_agent_loop(self, user_prompt: str, model_name: str = "llama3.2") -> str:
        tools_schema = [
            {
                "name": "get_system_diagnostics",
                "description": "Checks the host machine's live CPU usage, RAM availability, and disk storage stats."
            },
            {
                "name": "get_current_weather",
                "description": "Fetches live weather reports. Requires a 'location' string parameter.",
                "parameters": {"location": "str"}
            }
        ]

        # A hyper-rigid, few-shot system instruction designed specifically for 3B parameter models
        system_instruction = (
            "You are a strict automated routing agent with access to local functions.\n\n"
            f"AVAILABLE TOOLS:\n{json.dumps(tools_schema, indent=2)}\n\n"
            "CRITICAL RULES:\n"
            "1. If the user's request requires information from one of the tools above, you MUST reply with a JSON object ONLY. Do not write any conversational text, explanations, or code markdown block backticks.\n"
            "2. If the user's request does not require a tool, reply with plain conversational text normally.\n\n"
            "FEW-SHOT EXAMPLES:\n"
            "User: Is my laptop lagging right now?\n"
            'Assistant: {"tool_name": "get_system_diagnostics", "arguments": {}}\n\n'
            "User: What is the weather like in New Delhi?\n"
            'Assistant: {"tool_name": "get_current_weather", "arguments": {"location": "New Delhi"}}\n\n'
            "User: Hello, who are you?\n"
            "Assistant: I am your local AI assistant. How can I help you today?\n"
        )

        messages = [
            {"role": "system", "content": system_instruction},
            {"role": "user", "content": user_prompt}
        ]

        # Step 1: Force low temperature to prevent formatting deviations
        response = await self.client.post("/api/chat", json={
            "model": model_name, 
            "messages": messages, 
            "stream": False,
            "options": {"temperature": 0.0} # Absolute determinism
        })
        response.raise_for_status()
        assistant_content = response.json()["message"]["content"].strip()

        # Step 2: Clean up potential model edge-case errors (like wrapping code blocks)
        cleaned_content = assistant_content
        if cleaned_content.startswith("```"):
            cleaned_content = cleaned_content.replace("```json", "").replace("```", "").strip()

        # Step 3: Parse and execute tool if triggered
        try:
            tool_call = json.loads(cleaned_content)
            tool_name = tool_call.get("tool_name")
            
            if tool_name in self.tool_registry:
                print(f"\n[Agent Logic] Model correctly requested tool: {tool_name}")
                args = tool_call.get("arguments", {})
                
                # Execute tool matching parameters
                if "location" in args:
                    tool_output = self.tool_registry[tool_name](args["location"])
                else:
                    tool_output = self.tool_registry[tool_name]()
                
                print(f"[Agent Logic] Native Tool Output: {tool_output}")

                # Step 4: Inject the structural answer back to the conversational engine
                messages.append({"role": "assistant", "content": assistant_content})
                messages.append({
                    "role": "user", 
                    "content": f"The exact current tool data is: {tool_output}. Synthesize this data to answer the user accurately."
                })
                
                final_response = await self.client.post("/api/chat", json={
                    "model": model_name, 
                    "messages": messages, 
                    "stream": False,
                    "options": {"temperature": 0.3}
                })
                return final_response.json()["message"]["content"]
                
        except (json.JSONDecodeError, TypeError, KeyError):
            # Fall back to native conversational response if JSON processing wasn't emitted
            pass

        return assistant_content