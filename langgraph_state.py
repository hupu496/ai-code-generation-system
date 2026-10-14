from typing import Dict, List, Optional, Any, Literal, TypedDict, Annotated
from dataclasses import dataclass, field
from enum import Enum
import operator
import json
import os
from pathlib import Path


class TaskType(str, Enum):
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


class ModuleStatus(str, Enum):
    PENDING = "pending"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"
    FAILED = "failed"
    SKIPPED = "skipped"


@dataclass
class AIProviderConfig:
    name: str
    provider: str
    model: str
    api_key: str
    base_url: Optional[str] = None
    role: str = ""
    available: bool = True
    rate_limited: bool = False
    error_count: int = 0


@dataclass
class FileSpec:
    path: str
    description: str = ""
    content: str = ""


@dataclass
class TestSpec:
    name: str
    description: str = ""
    passed: bool = False
    output: str = ""


@dataclass
class ModuleSpec:
    id: str
    name: str
    description: str
    dependencies: List[str]
    task_type: str
    files: List[FileSpec]
    tests: List[TestSpec]
    status: ModuleStatus = ModuleStatus.PENDING
    assigned_provider: Optional[str] = None


class ProjectState(TypedDict):
    project_name: str
    project_description: str
    version: str
    output_dir: str
    modules: Annotated[List[ModuleSpec], operator.add]
    current_module_index: int
    completed_modules: Annotated[List[str], operator.add]
    failed_modules: Annotated[List[str], operator.add]
    ai_providers: List[AIProviderConfig]
    specialist_routing: Dict[str, str]
    github_config: Dict[str, Any]
    testing_config: Dict[str, Any]
    deployment_config: Dict[str, Any]
    error_log: Annotated[List[str], operator.add]
    execution_summary: Dict[str, Any]


def create_initial_state(
    project_name: str,
    project_description: str,
    version: str,
    output_dir: str,
    modules: List[ModuleSpec],
    ai_providers: List[AIProviderConfig],
    specialist_routing: Dict[str, str],
    github_config: Dict[str, Any],
    testing_config: Dict[str, Any],
    deployment_config: Dict[str, Any]
) -> ProjectState:
    return ProjectState(
        project_name=project_name,
        project_description=project_description,
        version=version,
        output_dir=output_dir,
        modules=modules,
        current_module_index=0,
        completed_modules=[],
        failed_modules=[],
        ai_providers=ai_providers,
        specialist_routing=specialist_routing,
        github_config=github_config,
        testing_config=testing_config,
        deployment_config=deployment_config,
        error_log=[],
        execution_summary={}
    )