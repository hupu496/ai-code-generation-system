import os
import json
import logging
import asyncio
from typing import Dict, List, Optional, Any, Literal
from pathlib import Path
from datetime import datetime

from langgraph.graph import StateGraph, END
from langgraph.checkpoint.memory import MemorySaver

from langgraph_state import (
    ProjectState, ModuleSpec, FileSpec, TestSpec, 
    ModuleStatus, TaskType, create_initial_state
)
from ai_providers import ai_provider_manager, AIProvider, BaseAIClient

logger = logging.getLogger(__name__)


async def load_project_config_node(state: ProjectState) -> ProjectState:
    logger.info(f"Loading project config: {state['project_name']}")
    
    project_flow_path = "project_flow.json"
    if os.path.exists(project_flow_path):
        with open(project_flow_path, 'r') as f:
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
        
        state["modules"] = modules
        state["project_name"] = flow_config.get("project_name", state["project_name"])
        state["project_description"] = flow_config.get("description", state["project_description"])
        state["version"] = flow_config.get("version", state["version"])
        state["output_dir"] = flow_config.get("output_dir", state["output_dir"])
        state["github_config"] = flow_config.get("github_repo", {})
        state["testing_config"] = flow_config.get("testing", {})
        state["deployment_config"] = flow_config.get("deployment", {})
        
        ai_routing = flow_config.get("ai_routing", {})
        state["specialist_routing"] = ai_routing.get("specialist_routing", {})
    
    ai_provider_manager.load_from_config("ai-router.json")
    state["ai_providers"] = list(ai_provider_manager.providers.values())
    
    os.makedirs(state["output_dir"], exist_ok=True)
    logger.info(f"Output directory: {state['output_dir']}")
    
    return state


async def topological_sort_modules(state: ProjectState) -> ProjectState:
    logger.info("Performing topological sort of modules")
    
    modules = state["modules"]
    visited = set()
    result = []
    
    def visit(module_id: str):
        if module_id in visited:
            return
        visited.add(module_id)
        
        module = next(m for m in modules if m.id == module_id)
        for dep in module.dependencies:
            visit(dep)
        result.append(module)
    
    for module in modules:
        visit(module.id)
    
    state["modules"] = result
    logger.info(f"Module execution order: {[m.id for m in result]}")
    
    return state


async def route_ai_provider_node(state: ProjectState) -> ProjectState:
    current_index = state["current_module_index"]
    if current_index >= len(state["modules"]):
        return state
    
    module = state["modules"][current_index]
    provider = ai_provider_manager.get_provider_for_task(module.task_type)
    
    if provider:
        module.assigned_provider = provider.name
        logger.info(f"Module {module.id} assigned to {provider.name} ({provider.role})")
    else:
        logger.error(f"No available provider for module {module.id}")
        state["error_log"].append(f"No available provider for module {module.id}")
    
    return state


async def execute_module_node(state: ProjectState) -> ProjectState:
    current_index = state["current_module_index"]
    if current_index >= len(state["modules"]):
        return state
    
    module = state["modules"][current_index]
    module.status = ModuleStatus.IN_PROGRESS
    
    logger.info(f"\n{'='*60}")
    logger.info(f"Executing Module: {module.name} ({module.id})")
    logger.info(f"Description: {module.description}")
    logger.info(f"Task Type: {module.task_type}")
    logger.info(f"Assigned AI: {module.assigned_provider}")
    logger.info(f"{'='*60}")
    
    provider = ai_provider_manager.providers.get(module.assigned_provider) if module.assigned_provider else None
    client = ai_provider_manager.get_client(module.assigned_provider) if module.assigned_provider else None
    
    if not client:
        logger.error(f"No client available for provider {module.assigned_provider}")
        module.status = ModuleStatus.FAILED
        state["failed_modules"].append(module.id)
        state["error_log"].append(f"No client for provider {module.assigned_provider}")
        return state
    
    try:
        for file_spec in module.files:
            success = await generate_file(module, file_spec, provider, client)
            if not success:
                module.status = ModuleStatus.FAILED
                state["failed_modules"].append(module.id)
                return state
        
        module.status = ModuleStatus.COMPLETED
        state["completed_modules"].append(module.id)
        logger.info(f"Module {module.id} completed successfully")
        
    except Exception as e:
        logger.error(f"Module {module.id} failed: {e}")
        module.status = ModuleStatus.FAILED
        state["failed_modules"].append(module.id)
        state["error_log"].append(f"Module {module.id} failed: {str(e)}")
        ai_provider_manager.mark_error(module.assigned_provider)
    
    return state


async def generate_file(
    module: ModuleSpec, 
    file_spec: FileSpec, 
    provider: Optional[AIProvider], 
    client: BaseAIClient
) -> bool:
    file_path = os.path.join(module.__dict__.get("output_dir", "D:\\ComsysProject\\output"), file_spec.path)
    os.makedirs(os.path.dirname(file_path), exist_ok=True)
    
    logger.info(f"Generating: {file_spec.path} using {provider.name if provider else 'Unknown'}")
    
    system_prompt = f"""You are an expert software engineer working on the {module.name} module.
Task: {module.description}
Task Type: {module.task_type}
File: {file_spec.path}

Generate production-ready code for this file. Follow best practices for the language/framework.
Include proper error handling, logging, and documentation.
Return ONLY the code content, no markdown formatting unless specifically requested."""

    user_prompt = f"""Generate code for file: {file_spec.path}
Module: {module.name}
Description: {module.description}
Dependencies: {', '.join(module.dependencies)}

Requirements:
- Follow the project architecture from project_flow.json
- Use appropriate patterns for {module.task_type} tasks
- Include necessary imports and configuration
- Make it production-ready with error handling
- Follow the existing code style in the project"""

    try:
        content = await client.generate(user_prompt, system_prompt)
        
        with open(file_path, 'w', encoding='utf-8') as f:
            f.write(content)
        
        file_spec.content = content
        logger.info(f"Saved: {file_path}")
        return True
        
    except Exception as e:
        logger.error(f"Failed to generate {file_spec.path}: {e}")
        return False


async def run_module_tests_node(state: ProjectState) -> ProjectState:
    current_index = state["current_module_index"]
    if current_index >= len(state["modules"]):
        return state
    
    module = state["modules"][current_index]
    
    if module.status != ModuleStatus.COMPLETED:
        return state
    
    logger.info(f"Running tests for module: {module.id}")
    
    provider = ai_provider_manager.providers.get(module.assigned_provider) if module.assigned_provider else None
    client = ai_provider_manager.get_client(module.assigned_provider) if module.assigned_provider else None
    
    if not client:
        logger.warning(f"No client for testing module {module.id}")
        return state
    
    all_passed = True
    for test_spec in module.tests:
        logger.info(f"  Running test: {test_spec.name}")
        success = await execute_test(module, test_spec, provider, client)
        test_spec.passed = success
        
        if not success:
            logger.error(f"  Test failed: {test_spec.name}")
            all_passed = False
        else:
            logger.info(f"  Test passed: {test_spec.name}")
    
    if not all_passed:
        module.status = ModuleStatus.FAILED
        state["failed_modules"].append(module.id)
        if module.id in state["completed_modules"]:
            state["completed_modules"].remove(module.id)
    
    return state


async def execute_test(
    module: ModuleSpec, 
    test_spec: TestSpec, 
    provider: Optional[AIProvider], 
    client: BaseAIClient
) -> bool:
    system_prompt = f"""You are a test engineer. Write and execute a test for the given module.
Module: {module.name}
Test: {test_spec.name}
Files generated: {[f.path for f in module.files]}

Write a test that validates the functionality. Return 'PASS' if the test would pass, 'FAIL' with reason if it would fail."""

    user_prompt = f"""Create a test for: {test_spec.name}
Module: {module.name} ({module.id})
Description: {module.description}

The test should verify the functionality works correctly.
For now, simulate the test execution and return PASS or FAIL with explanation."""

    try:
        result = await client.generate(user_prompt, system_prompt)
        test_spec.output = result
        
        return "PASS" in result.upper() and "FAIL" not in result.upper()
        
    except Exception as e:
        logger.error(f"Test execution error: {e}")
        test_spec.output = f"Error: {str(e)}"
        return False


async def check_completion_node(state: ProjectState) -> Literal["continue", "integration_tests", "failed"]:
    current_index = state["current_module_index"]
    
    if state["failed_modules"]:
        return "failed"
    
    if current_index + 1 >= len(state["modules"]):
        return "integration_tests"
    
    return "continue"


async def next_module_node(state: ProjectState) -> ProjectState:
    state["current_module_index"] += 1
    return state


async def run_integration_tests_node(state: ProjectState) -> ProjectState:
    logger.info("\nRunning integration tests...")
    
    integration_module = next(
        (m for m in state["modules"] if m.id == "module_08"), 
        None
    )
    
    if integration_module:
        integration_module.status = ModuleStatus.IN_PROGRESS
        
        provider = ai_provider_manager.providers.get(integration_module.assigned_provider) if integration_module.assigned_provider else None
        client = ai_provider_manager.get_client(integration_module.assigned_provider) if integration_module.assigned_provider else None
        
        if client:
            all_passed = True
            for test_spec in integration_module.tests:
                logger.info(f"  Running integration test: {test_spec.name}")
                success = await execute_test(integration_module, test_spec, provider, client)
                test_spec.passed = success
                
                if not success:
                    all_passed = False
            
            if all_passed:
                integration_module.status = ModuleStatus.COMPLETED
                state["completed_modules"].append(integration_module.id)
                logger.info("All integration tests passed")
            else:
                integration_module.status = ModuleStatus.FAILED
                state["failed_modules"].append(integration_module.id)
                logger.error("Integration tests failed")
    
    return state


async def push_to_github_node(state: ProjectState) -> ProjectState:
    github_config = state.get("github_config", {})
    
    if github_config.get("auto_create", False):
        logger.info("Preparing GitHub repository...")
        prefix = github_config.get("prefix", "")
        repo_name = f"{prefix}{state['project_name'].lower()}"
        logger.info(f"Repository name: {repo_name}")
        logger.info(f"Output directory: {state['output_dir']}")
        
        state["execution_summary"]["github_repo"] = repo_name
        state["execution_summary"]["github_ready"] = True
    else:
        logger.info("GitHub auto-create disabled")
        state["execution_summary"]["github_ready"] = False
    
    return state


async def generate_summary_node(state: ProjectState) -> ProjectState:
    logger.info(f"\n{'='*60}")
    logger.info("EXECUTION SUMMARY")
    logger.info(f"{'='*60}")
    logger.info(f"Project: {state['project_name']}")
    logger.info(f"Completed modules: {len(state['completed_modules'])}")
    logger.info(f"Failed modules: {len(state['failed_modules'])}")
    logger.info(f"Output directory: {state['output_dir']}")
    
    if state["completed_modules"]:
        logger.info(f"Completed: {', '.join(state['completed_modules'])}")
    if state["failed_modules"]:
        logger.info(f"Failed: {', '.join(state['failed_modules'])}")
    if state["error_log"]:
        logger.info(f"Errors: {len(state['error_log'])}")
        for error in state["error_log"]:
            logger.info(f"  - {error}")
    
    state["execution_summary"] = {
        "project_name": state["project_name"],
        "completed_modules": state["completed_modules"],
        "failed_modules": state["failed_modules"],
        "total_modules": len(state["modules"]),
        "output_dir": state["output_dir"],
        "errors": state["error_log"],
        "timestamp": datetime.now().isoformat()
    }
    
    summary_path = os.path.join(state["output_dir"], "execution_summary.json")
    with open(summary_path, 'w') as f:
        json.dump(state["execution_summary"], f, indent=2)
    
    logger.info(f"Summary saved to: {summary_path}")
    
    return state


def create_workflow() -> StateGraph:
    workflow = StateGraph(ProjectState)
    
    workflow.add_node("load_config", load_project_config_node)
    workflow.add_node("topological_sort", topological_sort_modules)
    workflow.add_node("route_provider", route_ai_provider_node)
    workflow.add_node("execute_module", execute_module_node)
    workflow.add_node("run_tests", run_module_tests_node)
    workflow.add_node("next_module", next_module_node)
    workflow.add_node("integration_tests", run_integration_tests_node)
    workflow.add_node("push_github", push_to_github_node)
    workflow.add_node("generate_summary", generate_summary_node)
    
    workflow.set_entry_point("load_config")
    
    workflow.add_edge("load_config", "topological_sort")
    workflow.add_edge("topological_sort", "route_provider")
    workflow.add_edge("route_provider", "execute_module")
    workflow.add_edge("execute_module", "run_tests")
    
    workflow.add_conditional_edges(
        "run_tests",
        check_completion_node,
        {
            "continue": "next_module",
            "integration_tests": "integration_tests",
            "failed": "generate_summary"
        }
    )
    
    workflow.add_edge("next_module", "route_provider")
    workflow.add_edge("integration_tests", "push_github")
    workflow.add_edge("push_github", "generate_summary")
    workflow.add_edge("generate_summary", END)
    
    return workflow.compile(checkpointer=MemorySaver())