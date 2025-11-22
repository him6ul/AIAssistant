"""
Hybrid LLM Router - Routes requests to OpenAI (online) or Ollama (offline).
Automatically detects network status and falls back to local models when offline.
"""

import json
from typing import Optional, Dict, Any, List
from openai import OpenAI, AzureOpenAI
import httpx
from app.network import get_network_monitor
from app.utils.logger import get_logger

logger = get_logger(__name__)


class HybridLLMRouter:
    """
    Routes LLM requests to OpenAI (online) or Ollama (offline) based on network status.
    """
    
    def __init__(
        self,
        openai_api_key: Optional[str] = None,
        openai_model: str = "gpt-4-turbo-preview",
        ollama_base_url: str = "http://localhost:11434",
        ollama_model: str = "llama3",
        temperature: float = 0.7,
        max_tokens: int = 2000,
        use_azure: bool = False,
        azure_endpoint: Optional[str] = None,
        azure_api_version: str = "2024-02-15-preview"
    ):
        """
        Initialize the hybrid LLM router.
        
        Args:
            openai_api_key: OpenAI API key (or Azure OpenAI API key)
            openai_model: OpenAI model name (or Azure deployment name)
            ollama_base_url: Ollama base URL
            ollama_model: Ollama model name
            temperature: Temperature for generation
            max_tokens: Maximum tokens to generate
            use_azure: Whether to use Azure OpenAI
            azure_endpoint: Azure OpenAI endpoint URL
            azure_api_version: Azure OpenAI API version
        """
        self.openai_api_key = openai_api_key
        self.openai_model = openai_model
        self.ollama_base_url = ollama_base_url
        self.ollama_model = ollama_model
        self.temperature = temperature
        self.max_tokens = max_tokens
        self.use_azure = use_azure
        self.azure_endpoint = azure_endpoint
        self.azure_api_version = azure_api_version
        
        # Initialize OpenAI client if API key is provided
        self.openai_client: Optional[OpenAI] = None
        if openai_api_key:
            if use_azure and azure_endpoint:
                # Use Azure OpenAI
                self.openai_client = AzureOpenAI(
                    api_key=openai_api_key,
                    api_version=azure_api_version,
                    azure_endpoint=azure_endpoint
                )
                logger.info(f"Initialized Azure OpenAI client: {azure_endpoint}")
            else:
                # Use standard OpenAI
                self.openai_client = OpenAI(api_key=openai_api_key)
                logger.info("Initialized standard OpenAI client")
        
        self.network_monitor = get_network_monitor()
        self._current_mode: Optional[str] = None
        self._last_mode_switch: Optional[float] = None
    
    async def _try_openai(self, prompt: str, system_prompt: Optional[str] = None) -> Optional[Dict[str, Any]]:
        """
        Attempt to use OpenAI API.
        
        Args:
            prompt: User prompt
            system_prompt: System prompt (optional)
        
        Returns:
            Response dict with content and metadata, or None if failed
        """
        if not self.openai_client:
            return None
        
        try:
            messages = []
            if system_prompt:
                messages.append({"role": "system", "content": system_prompt})
            messages.append({"role": "user", "content": prompt})
            
            response = self.openai_client.chat.completions.create(
                model=self.openai_model,
                messages=messages,
                temperature=self.temperature,
                max_tokens=self.max_tokens
            )
            
            content = response.choices[0].message.content
            
            return {
                "content": content,
                "model": self.openai_model,
                "provider": "openai",
                "usage": {
                    "prompt_tokens": response.usage.prompt_tokens,
                    "completion_tokens": response.usage.completion_tokens,
                    "total_tokens": response.usage.total_tokens
                }
            }
        except Exception as e:
            logger.error(f"OpenAI API call failed: {e}")
            return None
    
    async def _try_ollama(self, prompt: str, system_prompt: Optional[str] = None) -> Optional[Dict[str, Any]]:
        """
        Attempt to use Ollama API.
        
        Args:
            prompt: User prompt
            system_prompt: System prompt (optional)
        
        Returns:
            Response dict with content and metadata, or None if failed
        """
        try:
            # Combine system prompt and user prompt for Ollama
            full_prompt = prompt
            if system_prompt:
                full_prompt = f"{system_prompt}\n\n{prompt}"
            
            async with httpx.AsyncClient(timeout=60.0) as client:
                response = await client.post(
                    f"{self.ollama_base_url}/api/generate",
                    json={
                        "model": self.ollama_model,
                        "prompt": full_prompt,
                        "stream": False,
                        "options": {
                            "temperature": self.temperature,
                            "num_predict": self.max_tokens
                        }
                    }
                )
                response.raise_for_status()
                data = response.json()
                
                return {
                    "content": data.get("response", ""),
                    "model": self.ollama_model,
                    "provider": "ollama",
                    "usage": {
                        "prompt_tokens": data.get("prompt_eval_count", 0),
                        "completion_tokens": data.get("eval_count", 0),
                        "total_tokens": data.get("prompt_eval_count", 0) + data.get("eval_count", 0)
                    }
                }
        except Exception as e:
            logger.error(f"Ollama API call failed: {e}")
            return None
    
    async def generate(
        self,
        prompt: str,
        system_prompt: Optional[str] = None,
        force_offline: bool = False
    ) -> Dict[str, Any]:
        """
        Generate a response using the appropriate LLM provider.
        
        Args:
            prompt: User prompt
            system_prompt: System prompt (optional)
            force_offline: Force use of offline mode (Ollama)
        
        Returns:
            Response dict with content, model info, and mode status
        """
        is_online = await self.network_monitor.is_online()
        
        # Try OpenAI first if online and not forced offline
        if is_online and not force_offline:
            response = await self._try_openai(prompt, system_prompt)
            if response:
                self._current_mode = "online"
                response["mode"] = f"Online mode ({self.openai_model})"
                logger.info(f"Using OpenAI: {self.openai_model}")
                return response
        
        # Fallback to Ollama
        response = await self._try_ollama(prompt, system_prompt)
        if response:
            self._current_mode = "offline"
            response["mode"] = f"Offline/local mode ({self.ollama_model})"
            logger.info(f"Using Ollama: {self.ollama_model}")
            return response
        
        # Both failed
        error_msg = "Both OpenAI and Ollama failed to generate a response"
        logger.error(error_msg)
        return {
            "content": "I'm sorry, I'm unable to generate a response at the moment. Please check your network connection and ensure Ollama is running.",
            "model": "none",
            "provider": "none",
            "mode": "Error: No LLM available",
            "error": error_msg
        }
    
    async def extract_json(
        self,
        prompt: str,
        system_prompt: Optional[str] = None,
        schema: Optional[Dict] = None
    ) -> Optional[Dict]:
        """
        Generate a response and parse it as JSON.
        Useful for structured data extraction.
        
        Args:
            prompt: User prompt
            system_prompt: System prompt (optional)
            schema: Expected JSON schema (for validation)
        
        Returns:
            Parsed JSON dict, or None if parsing failed
        """
        # Add JSON formatting instruction to prompt
        json_prompt = f"{prompt}\n\nPlease respond with valid JSON only."
        if schema:
            json_prompt += f"\n\nExpected schema: {json.dumps(schema, indent=2)}"
        
        response = await self.generate(json_prompt, system_prompt)
        content = response.get("content", "")
        
        # Try to extract JSON from response
        try:
            # Remove markdown code blocks if present
            if "```json" in content:
                content = content.split("```json")[1].split("```")[0].strip()
            elif "```" in content:
                content = content.split("```")[1].split("```")[0].strip()
            
            return json.loads(content)
        except json.JSONDecodeError as e:
            logger.error(f"Failed to parse JSON response: {e}")
            logger.debug(f"Response content: {content}")
            return None
    
    def get_current_mode(self) -> Optional[str]:
        """
        Get the current LLM mode.
        
        Returns:
            Current mode string or None
        """
        return self._current_mode


# Global router instance
_router: Optional[HybridLLMRouter] = None


def reset_llm_router():
    """
    Reset the global LLM router instance to force reload from .env.
    Useful when .env file is updated.
    """
    global _router
    _router = None
    logger.info("LLM router instance reset - will reload on next access")


def get_llm_router() -> HybridLLMRouter:
    """
    Get or create the global LLM router instance.
    
    Returns:
        HybridLLMRouter instance
    """
    global _router
    if _router is None:
        import os
        from dotenv import load_dotenv
        # Force reload .env file to pick up latest changes
        load_dotenv(override=True)
        
        # Check if Azure OpenAI should be used
        use_azure = os.getenv("USE_AZURE_OPENAI", "false").lower() == "true"
        azure_endpoint = os.getenv("AZURE_OPENAI_ENDPOINT")
        azure_api_version = os.getenv("AZURE_OPENAI_API_VERSION", "2024-02-15-preview")
        
        api_key = os.getenv("OPENAI_API_KEY") or os.getenv("AZURE_OPENAI_API_KEY")
        logger.info(f"Initializing LLM router with API key: {api_key[:10] if api_key else 'None'}...")
        
        _router = HybridLLMRouter(
            openai_api_key=api_key,
            openai_model=os.getenv("OPENAI_MODEL") or os.getenv("AZURE_OPENAI_DEPLOYMENT", "gpt-4-turbo-preview"),
            ollama_base_url=os.getenv("OLLAMA_BASE_URL", "http://localhost:11434"),
            ollama_model=os.getenv("OLLAMA_MODEL", "llama3"),
            temperature=0.7,
            max_tokens=2000,
            use_azure=use_azure,
            azure_endpoint=azure_endpoint,
            azure_api_version=azure_api_version
        )
    return _router

