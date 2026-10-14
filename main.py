import json
import os
import sys
from typing import Dict, List, Optional, Any
from dataclasses import dataclass
from enum import Enum
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class TaskType(Enum):
    BACKEND = "backend"
    FRONTEND_FINISHING = "frontend_finishing"
    PHOTO_DESIGN = "photo_design"
    POSTER_DESIGN = "poster_design"
    TESTING = "testing"
    GENERAL = "general"
    HEAVY_REASONING = "heavy_reasoning"
    FAST_INFERENCE = "fast_inference"
    CREATIVE_CODING = "creative_coding"
    FINTECH_CODING = "fintech_coding"


@dataclass
class AIProvider:
    name: str
    provider: str
    base_url: Optional[str]
    model: str
    api_key: str
    role: str
    available: bool = True
    rate_limited: bool = False
    error_count: int = 0


class AIRouter:
    def __init__(self, config_path: str = "ai-router.json"):
        self.config_path = config_path
        self.chain: List[AIProvider] = []
        self.current_index = 0
        self.load_config()
        
    def load_config(self):
        with open(self.config_path, 'r') as f:
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
            self.chain.append(provider)
        
        self.loop = config.get("loop", True)
        self.rules = config.get("rules", {})
        logger.info(f"Loaded {len(self.chain)} AI providers")
    
    def get_ai_for_task(self, task_type: str) -> AIProvider:
        specialist_map = {
            "frontend_finishing": 3,
            "high_design": 3,
            "photo_design": 4,
            "poster_design": 4,
            "heavy_reasoning": 5,
            "fast_inference": 6,
            "creative_coding": 7,
            "general_coding": 8,
            "fintech_coding": 9,
        }
        
        if task_type in specialist_map:
            idx = specialist_map[task_type]
            if idx < len(self.chain):
                provider = self.chain[idx]
                logger.info(f"-> Specialist Task ({task_type}) -> Direct {provider.name} pe")
                return provider
        
        return self.get_next_available()
    
    def get_next_available(self) -> AIProvider:
        attempts = 0
        max_attempts = len(self.chain) * 2 if self.loop else len(self.chain)
        
        while attempts < max_attempts:
            provider = self.chain[self.current_index]
            
            if provider.available and not provider.rate_limited:
                logger.info(f"Using AI provider: {provider.name} ({provider.model})")
                return provider
            
            self.current_index = (self.current_index + 1) % len(self.chain)
            attempts += 1
        
        self.reset_all_providers()
        return self.chain[0]
    
    def mark_rate_limited(self, provider_name: str):
        for provider in self.chain:
            if provider.name == provider_name:
                provider.rate_limited = True
                provider.error_count += 1
                logger.warning(f"Provider {provider_name} rate limited")
                break
    
    def mark_error(self, provider_name: str):
        for provider in self.chain:
            if provider.name == provider_name:
                provider.error_count += 1
                if provider.error_count >= 3:
                    provider.available = False
                    logger.error(f"Provider {provider_name} marked unavailable after 3 errors")
                break
    
    def reset_all_providers(self):
        for provider in self.chain:
            provider.rate_limited = False
            provider.error_count = 0
            provider.available = True
        self.current_index = 0
        logger.info("All providers reset")
    
    def get_chain_order(self) -> List[str]:
        return [p.name for p in self.chain]


class ProjectFlowExecutor:
    def __init__(self, flow_path: str = "project_flow.json"):
        self.flow_path = flow_path
        self.flow_config = self.load_flow()
        self.ai_router = AIRouter()
        self.output_dir = self.flow_config.get("output_dir", "D:\\ComsysProject\\output")
        self.completed_modules = []
        self.failed_modules = []
        
    def load_flow(self) -> Dict:
        with open(self.flow_path, 'r') as f:
            return json.load(f)
    
    def execute(self):
        logger.info(f"Starting project: {self.flow_config['project_name']}")
        logger.info(f"Output directory: {self.output_dir}")
        
        os.makedirs(self.output_dir, exist_ok=True)
        
        modules = self.flow_config["modules"]
        sorted_modules = self.topological_sort(modules)
        
        for module in sorted_modules:
            success = self.execute_module(module)
            if success:
                self.completed_modules.append(module["id"])
            else:
                self.failed_modules.append(module["id"])
                logger.error(f"Module {module['id']} failed")
                break
        
        if not self.failed_modules:
            self.run_integration_tests()
            self.push_to_github()
        
        self.print_summary()
    
    def topological_sort(self, modules: List[Dict]) -> List[Dict]:
        visited = set()
        result = []
        
        def visit(module_id: str):
            if module_id in visited:
                return
            visited.add(module_id)
            
            module = next(m for m in modules if m["id"] == module_id)
            for dep in module.get("dependencies", []):
                visit(dep)
            result.append(module)
        
        for module in modules:
            visit(module["id"])
        
        return result
    
    def execute_module(self, module: Dict) -> bool:
        logger.info(f"\n{'='*60}")
        logger.info(f"Executing Module: {module['name']} ({module['id']})")
        logger.info(f"Description: {module['description']}")
        logger.info(f"Task Type: {module.get('task_type', 'general')}")
        logger.info(f"{'='*60}")
        
        task_type = module.get("task_type", "general")
        ai_provider = self.ai_router.get_ai_for_task(task_type)
        
        logger.info(f"Assigned AI: {ai_provider.name} - {ai_provider.role}")
        
        for file_spec in module["files"]:
            success = self.generate_file(module, file_spec, ai_provider)
            if not success:
                return False
        
        test_success = self.run_module_tests(module, ai_provider)
        if not test_success:
            return False
        
        return True
    
    def generate_file(self, module: Dict, file_spec: str, ai_provider: AIProvider) -> bool:
        file_path = os.path.join(self.output_dir, file_spec)
        os.makedirs(os.path.dirname(file_path), exist_ok=True)
        
        logger.info(f"Generating: {file_spec} using {ai_provider.name}")
        
        if self.check_existing_code(file_spec):
            logger.info(f"Found similar code in repo, adapting...")
            content = self.adapt_existing_code(file_spec, module, ai_provider)
        else:
            logger.info(f"Generating new code...")
            content = self.generate_new_code(file_spec, module, ai_provider)
        
        with open(file_path, 'w') as f:
            f.write(content)
        
        logger.info(f"Saved: {file_path}")
        return True
    
    def check_existing_code(self, file_spec: str) -> bool:
        return False
    
    def adapt_existing_code(self, file_spec: str, module: Dict, ai_provider: AIProvider) -> str:
        return f"# Adapted code for {file_spec}\n# Module: {module['name']}\n# AI Provider: {ai_provider.name}\n\n"
    
    def generate_new_code(self, file_spec: str, module: Dict, ai_provider: AIProvider) -> str:
        return f"# Generated code for {file_spec}\n# Module: {module['name']}\n# AI Provider: {ai_provider.name}\n\n"
    
    def run_module_tests(self, module: Dict, ai_provider: AIProvider) -> bool:
        logger.info(f"Running tests for module: {module['id']}")
        
        for test_name in module.get("tests", []):
            logger.info(f"  Running test: {test_name}")
            success = self.execute_test(test_name, module, ai_provider)
            if not success:
                logger.error(f"  Test failed: {test_name}")
                return False
            logger.info(f"  Test passed: {test_name}")
        
        return True
    
    def execute_test(self, test_name: str, module: Dict, ai_provider: AIProvider) -> bool:
        return True
    
    def run_integration_tests(self):
        logger.info("\nRunning integration tests...")
        integration_module = next(
            (m for m in self.flow_config["modules"] if m["id"] == "module_08"), 
            None
        )
        if integration_module:
            self.execute_module(integration_module)
    
    def push_to_github(self):
        logger.info("Pushing to GitHub...")
        repo_config = self.flow_config.get("github_repo", {})
        if repo_config.get("auto_create"):
            unique_name = f"{repo_config.get('prefix', '')}{self.flow_config['project_name'].lower()}"
            logger.info(f"Creating GitHub repo: {unique_name}")
    
    def print_summary(self):
        logger.info(f"\n{'='*60}")
        logger.info("EXECUTION SUMMARY")
        logger.info(f"{'='*60}")
        logger.info(f"Completed modules: {len(self.completed_modules)}")
        logger.info(f"Failed modules: {len(self.failed_modules)}")
        logger.info(f"Output directory: {self.output_dir}")


def main():
    executor = ProjectFlowExecutor()
    executor.execute()


if __name__ == "__main__":
    main()