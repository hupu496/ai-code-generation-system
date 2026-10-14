import asyncio
import logging
import os
import sys
from pathlib import Path

from langgraph_state import create_initial_state, ProjectState, ModuleSpec, FileSpec, TestSpec
from langgraph_nodes import create_workflow
from ai_providers import ai_provider_manager

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


def load_initial_state() -> ProjectState:
    with open("project_flow.json", 'r') as f:
        flow_config = json.load(f)
    
    modules = []
    for m in flow_config.get("modules", []):
        files = [FileSpec(path=f) for f in m.get("files", [])]
        tests = [TestSpec(name=t) for t in m.get("tests", [])]
        module = ModuleSpec(
            id=m["id"],
            name=m["name"],
            description=m["description"],
            dependencies=m.get("dependencies", []),
            task_type=m.get("task_type", "general"),
            files=files,
            tests=tests
        )
        modules.append(module)
    
    ai_provider_manager.load_from_config("ai-router.json")
    
    ai_routing = flow_config.get("ai_routing", {})
    specialist_routing = ai_routing.get("specialist_routing", {})
    
    return create_initial_state(
        project_name=flow_config.get("project_name", "LocalLeadsProject"),
        project_description=flow_config.get("description", ""),
        version=flow_config.get("version", "1.0.0"),
        output_dir=flow_config.get("output_dir", "D:\\ComsysProject\\output"),
        modules=modules,
        ai_providers=list(ai_provider_manager.providers.values()),
        specialist_routing=specialist_routing,
        github_config=flow_config.get("github_repo", {}),
        testing_config=flow_config.get("testing", {}),
        deployment_config=flow_config.get("deployment", {})
    )


async def main():
    logger.info("Starting AI Code Generation System with LangGraph")
    logger.info("=" * 60)
    
    if not os.getenv("GEMINI_API_KEY") and not os.getenv("GROQ_API_KEY"):
        logger.warning("No API keys found in environment variables!")
        logger.warning("Please set GEMINI_API_KEY or GROQ_API_KEY in your .env file")
        logger.warning("Continuing with available providers...")
    
    initial_state = load_initial_state()
    
    workflow = create_workflow()
    
    config = {"configurable": {"thread_id": "project_execution_1"}}
    
    logger.info("Starting workflow execution...")
    final_state = await workflow.ainvoke(initial_state, config=config)
    
    logger.info("Workflow execution completed")
    
    if final_state.get("failed_modules"):
        logger.error(f"Failed modules: {final_state['failed_modules']}")
        return 1
    
    logger.info("All modules completed successfully!")
    return 0


if __name__ == "__main__":
    import json
    exit_code = asyncio.run(main())
    sys.exit(exit_code)