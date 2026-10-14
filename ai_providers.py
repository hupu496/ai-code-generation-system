import os
import json
import logging
from typing import Dict, List, Optional, Any, AsyncGenerator
from dataclasses import dataclass
from abc import ABC, abstractmethod
import google.generativeai as genai
from google.generativeai.types import HarmCategory, HarmBlockThreshold
import asyncio

logger = logging.getLogger(__name__)


@dataclass
class AIProvider:
    name: str
    provider: str
    model: str
    api_key: str
    base_url: Optional[str] = None
    role: str = ""
    available: bool = True
    rate_limited: bool = False
    error_count: int = 0


class BaseAIClient(ABC):
    @abstractmethod
    async def generate(self, prompt: str, system_prompt: Optional[str] = None, **kwargs) -> str:
        pass

    @abstractmethod
    async def stream_generate(self, prompt: str, system_prompt: Optional[str] = None, **kwargs) -> AsyncGenerator[str, None]:
        pass

    @abstractmethod
    def get_model_info(self) -> Dict[str, Any]:
        pass


class GeminiClient(BaseAIClient):
    def __init__(
        self,
        api_key: str,
        model: str = "gemini-2.0-flash-exp",
        temperature: float = 0.7,
        max_tokens: int = 8192,
        top_p: float = 0.95,
        top_k: int = 40
    ):
        self.api_key = api_key
        self.model_name = model
        self.temperature = temperature
        self.max_tokens = max_tokens
        self.top_p = top_p
        self.top_k = top_k
        
        genai.configure(api_key=api_key)
        
        self.generation_config = genai.types.GenerationConfig(
            temperature=temperature,
            max_output_tokens=max_tokens,
            top_p=top_p,
            top_k=top_k,
        )
        
        self.safety_settings = {
            HarmCategory.HARM_CATEGORY_HATE_SPEECH: HarmBlockThreshold.BLOCK_MEDIUM_AND_ABOVE,
            HarmCategory.HARM_CATEGORY_DANGEROUS_CONTENT: HarmBlockThreshold.BLOCK_MEDIUM_AND_ABOVE,
            HarmCategory.HARM_CATEGORY_SEXUALLY_EXPLICIT: HarmBlockThreshold.BLOCK_MEDIUM_AND_ABOVE,
            HarmCategory.HARM_CATEGORY_HARASSMENT: HarmBlockThreshold.BLOCK_MEDIUM_AND_ABOVE,
        }
        
        self.model = genai.GenerativeModel(
            model_name=model,
            generation_config=self.generation_config,
            safety_settings=self.safety_settings
        )
        
        logger.info(f"Initialized Gemini client with model: {model}")

    async def generate(self, prompt: str, system_prompt: Optional[str] = None, **kwargs) -> str:
        try:
            full_prompt = prompt
            if system_prompt:
                full_prompt = f"System: {system_prompt}\n\nUser: {prompt}"
            
            response = await asyncio.to_thread(
                self.model.generate_content,
                full_prompt
            )
            
            if response.text:
                return response.text
            else:
                logger.warning("Empty response from Gemini")
                return ""
                
        except Exception as e:
            logger.error(f"Gemini generation error: {e}")
            raise

    async def stream_generate(self, prompt: str, system_prompt: Optional[str] = None, **kwargs) -> AsyncGenerator[str, None]:
        try:
            full_prompt = prompt
            if system_prompt:
                full_prompt = f"System: {system_prompt}\n\nUser: {prompt}"
            
            response = await asyncio.to_thread(
                self.model.generate_content,
                full_prompt,
                stream=True
            )
            
            for chunk in response:
                if chunk.text:
                    yield chunk.text
                    
        except Exception as e:
            logger.error(f"Gemini streaming error: {e}")
            raise

    def get_model_info(self) -> Dict[str, Any]:
        return {
            "provider": "google",
            "model": self.model_name,
            "temperature": self.temperature,
            "max_tokens": self.max_tokens
        }


class OpenAICompatibleClient(BaseAIClient):
    def __init__(
        self,
        api_key: str,
        base_url: str,
        model: str,
        temperature: float = 0.7,
        max_tokens: int = 4096
    ):
        self.api_key = api_key
        self.base_url = base_url
        self.model = model
        self.temperature = temperature
        self.max_tokens = max_tokens
        
        from openai import AsyncOpenAI
        self.client = AsyncOpenAI(
            api_key=api_key,
            base_url=base_url
        )
        
        logger.info(f"Initialized OpenAI-compatible client: {model} at {base_url}")

    async def generate(self, prompt: str, system_prompt: Optional[str] = None, **kwargs) -> str:
        try:
            messages = []
            if system_prompt:
                messages.append({"role": "system", "content": system_prompt})
            messages.append({"role": "user", "content": prompt})
            
            response = await self.client.chat.completions.create(
                model=self.model,
                messages=messages,
                temperature=self.temperature,
                max_tokens=self.max_tokens,
                **kwargs
            )
            
            return response.choices[0].message.content or ""
            
        except Exception as e:
            logger.error(f"OpenAI-compatible generation error: {e}")
            raise

    async def stream_generate(self, prompt: str, system_prompt: Optional[str] = None, **kwargs) -> AsyncGenerator[str, None]:
        try:
            messages = []
            if system_prompt:
                messages.append({"role": "system", "content": system_prompt})
            messages.append({"role": "user", "content": prompt})
            
            stream = await self.client.chat.completions.create(
                model=self.model,
                messages=messages,
                temperature=self.temperature,
                max_tokens=self.max_tokens,
                stream=True,
                **kwargs
            )
            
            async for chunk in stream:
                if chunk.choices[0].delta.content:
                    yield chunk.choices[0].delta.content
                    
        except Exception as e:
            logger.error(f"OpenAI-compatible streaming error: {e}")
            raise

    def get_model_info(self) -> Dict[str, Any]:
        return {
            "provider": "openai-compatible",
            "model": self.model,
            "base_url": self.base_url,
            "temperature": self.temperature,
            "max_tokens": self.max_tokens
        }


class AIProviderManager:
    def __init__(self):
        self.providers: Dict[str, AIProvider] = {}
        self.clients: Dict[str, BaseAIClient] = {}
        self.specialist_routing: Dict[str, str] = {}
        self.current_index = 0
        self.loop = True

    def load_from_config(self, config_path: str = "ai-router.json"):
        with open(config_path, 'r') as f:
            config = json.load(f)
        
        for provider_config in config["chain"]:
            api_key = provider_config["apiKey"]
            if api_key.startswith("${") and api_key.endswith("}"):
                env_var = api_key[2:-1]
                api_key = os.getenv(env_var, "")
                if not api_key:
                    logger.warning(f"Environment variable {env_var} not set for {provider_config['name']}")
            
            provider = AIProvider(
                name=provider_config["name"],
                provider=provider_config["provider"],
                base_url=provider_config.get("baseURL"),
                model=provider_config["model"],
                api_key=api_key,
                role=provider_config["role"]
            )
            self.providers[provider.name] = provider
            
            client = self._create_client(provider)
            if client:
                self.clients[provider.name] = client
        
        self.loop = config.get("loop", True)
        self.specialist_routing = config.get("rules", {})
        logger.info(f"Loaded {len(self.providers)} AI providers")

    def _create_client(self, provider: AIProvider) -> Optional[BaseAIClient]:
        if not provider.api_key:
            return None
            
        try:
            if provider.provider == "google":
                return GeminiClient(
                    api_key=provider.api_key,
                    model=provider.model
                )
            elif provider.provider == "openai":
                return OpenAICompatibleClient(
                    api_key=provider.api_key,
                    base_url=provider.base_url or "https://api.openai.com/v1",
                    model=provider.model
                )
        except Exception as e:
            logger.error(f"Failed to create client for {provider.name}: {e}")
        
        return None

    def get_provider_for_task(self, task_type: str) -> Optional[AIProvider]:
        specialist_map = {
            "frontend_finishing": "deepseek",
            "photo_design": "gemini",
            "poster_design": "gemini",
            "heavy_reasoning": "nemotron-3-ultra",
            "fast_inference": "nemotron-3.5-lightning",
            "creative_coding": "big-pickle",
            "general_coding": "muse-spark-1.3",
            "fintech_coding": "ling-3.0-flash-fin",
        }
        
        if task_type in specialist_map:
            provider_name = specialist_map[task_type]
            if provider_name in self.providers:
                provider = self.providers[provider_name]
                if provider.available and not provider.rate_limited:
                    logger.info(f"Specialist Task ({task_type}) -> Direct {provider.name}")
                    return provider
        
        return self.get_next_available()

    def get_next_available(self) -> Optional[AIProvider]:
        attempts = 0
        max_attempts = len(self.providers) * 2 if self.loop else len(self.providers)
        
        while attempts < max_attempts:
            provider_names = list(self.providers.keys())
            if not provider_names:
                return None
                
            provider = self.providers[provider_names[self.current_index % len(provider_names)]]
            
            if provider.available and not provider.rate_limited:
                logger.info(f"Using AI provider: {provider.name} ({provider.model})")
                return provider
            
            self.current_index += 1
            attempts += 1
        
        self.reset_all_providers()
        provider_names = list(self.providers.keys())
        return self.providers[provider_names[0]] if provider_names else None

    def get_client(self, provider_name: str) -> Optional[BaseAIClient]:
        return self.clients.get(provider_name)

    def mark_rate_limited(self, provider_name: str):
        if provider_name in self.providers:
            self.providers[provider_name].rate_limited = True
            self.providers[provider_name].error_count += 1
            logger.warning(f"Provider {provider_name} rate limited")

    def mark_error(self, provider_name: str):
        if provider_name in self.providers:
            self.providers[provider_name].error_count += 1
            if self.providers[provider_name].error_count >= 3:
                self.providers[provider_name].available = False
                logger.error(f"Provider {provider_name} marked unavailable after 3 errors")

    def reset_all_providers(self):
        for provider in self.providers.values():
            provider.rate_limited = False
            provider.error_count = 0
            provider.available = True
        self.current_index = 0
        logger.info("All providers reset")

    def get_available_providers(self) -> List[AIProvider]:
        return [p for p in self.providers.values() if p.available and not p.rate_limited]


ai_provider_manager = AIProviderManager()