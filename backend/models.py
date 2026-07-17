from pydantic import BaseModel
from typing import Optional


class PromptRequest(BaseModel):
    prompt: str
    demo_mode: str = "live"


class SubtaskResult(BaseModel):
    subtask_id: int
    name: str
    model: str
    prompt: str
    output: str
    tokens_per_second: float
    time_to_first_token: float
    total_duration_ms: float
    core: str


class SandboxResult(BaseModel):
    passed: bool
    stdout: str
    stderr: str
    returncode: int
    failure_kind: Optional[str] = None
    duration_ms: float


class DAGNode(BaseModel):
    id: int
    name: str
    model: str
    prompt: str
    depends_on: list[int]
    port: int
    core_range: str


class GenerationResponse(BaseModel):
    prompt: str
    dag_shape: str
    subtasks: list[SubtaskResult]
    sandbox: Optional[SandboxResult] = None
    regeneration_attempts: int
    fully_verified: bool
    total_duration_ms: float
    merged_output: str
    demo_mode: str
