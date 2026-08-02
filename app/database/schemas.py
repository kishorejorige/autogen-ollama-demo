from pydantic import BaseModel, Field


class AgentMessageSchema(BaseModel):
    id: str
    workflow_id: str
    iteration_id: int | None = None
    agent_name: str
    role: str
    content: str
    sequence_number: int
    created_at: str


class GeneratedFileSchema(BaseModel):
    id: str
    workflow_id: str
    iteration_id: int | None = None
    filename: str
    language: str
    content: str
    is_final: bool
    created_at: str


class WorkflowIterationSchema(BaseModel):
    id: int
    workflow_id: str
    iteration_number: int
    review_status: str | None = None
    test_status: str | None = None
    developer_output: str | None = None
    reviewer_feedback: str | None = None
    tester_feedback: str | None = None
    created_at: str


class WorkflowSummarySchema(BaseModel):
    id: str
    prompt: str
    status: str
    total_iterations: int
    generated_file_count: int
    favorite: bool = False
    created_at: str
    completed_at: str | None = None


class WorkflowListSchema(BaseModel):
    items: list[WorkflowSummarySchema]
    total: int
    limit: int
    offset: int


class WorkflowDetailSchema(BaseModel):
    id: str
    prompt: str
    status: str
    final_summary: str | None = None
    total_iterations: int
    generated_file_count: int
    favorite: bool = False
    created_at: str
    completed_at: str | None = None
    iterations: list[WorkflowIterationSchema] = Field(default_factory=list)
    messages: list[AgentMessageSchema] = Field(default_factory=list)
    generated_files: list[GeneratedFileSchema] = Field(default_factory=list)


class WorkflowStatsSchema(BaseModel):
    total_workflows: int
    completed_workflows: int
    failed_workflows: int
    needs_attention_workflows: int
    running_workflows: int
    favorite_count: int = 0
    average_iterations: float
