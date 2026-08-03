export type WorkflowStatusType = 'RUNNING' | 'COMPLETE' | 'NEEDS_ATTENTION' | 'FAILED';
export type RunReadinessType = 'RUNNABLE' | 'PARTIALLY_RUNNABLE' | 'NOT_RUNNABLE' | 'UNKNOWN';

export interface GeneratedFile {
  filename: string;
  content: string;
  iteration: number;
  is_final: boolean;
}

export interface IterationHistory {
  iteration: number;
  reviewer_status: string | null;
  tester_status: string | null;
  developer_response: string;
  reviewer_response: string;
  tester_response: string;
}

export interface RequirementCompliance {
  id: string;
  name: string;
  status: 'IMPLEMENTED' | 'PARTIAL' | 'MISSING' | 'INCORRECT' | 'UNKNOWN';
  evidence: string[];
  issues: string[];
}

export interface ProjectValidationResult {
  overall_status: 'PASS' | 'FAIL';
  run_readiness: RunReadinessType;
  files_checked: string[];
  unresolved_imports: string[];
  undefined_symbols: string[];
  missing_model_attributes: string[];
  module_conflicts: string[];
  placeholder_files: string[];
  placeholder_reasons: string[];
  syntax_errors: string[];
  missing_dependency_files: string[];
  missing_required_files: string[];
  frontend_issues: string[];
  backend_issues: string[];
  database_issues: string[];
  docker_issues: string[];
  ci_issues: string[];
  test_issues: string[];
  documentation_issues: string[];
  security_issues: string[];
  recommended_fixes: string[];
}

export interface QualityGateResult {
  overall_status: 'PASS' | 'FAIL' | 'NEEDS_ATTENTION' | 'UNKNOWN';
  run_readiness?: RunReadinessType;
  project_validation?: ProjectValidationResult;
  requirements: RequirementCompliance[];
  framework_mismatches: string[];
  missing_deliverables: string[];
  unsupported_claims: string[];
  security_issues: string[];
  recommended_fixes: string[];
  production_ready_eligible: boolean;
}

export interface WorkflowState {
  workflow_id: string;
  current_agent: string | null;
  current_iteration: number;
  max_iterations: number;
  status: 'PENDING' | 'RUNNING' | 'COMPLETE' | 'NEEDS_ATTENTION' | 'FAILED' | 'CANCELLED';
  quality_gate_status?: string;
  reviewer_status: 'APPROVED' | 'CHANGES_REQUIRED' | null;
  tester_status: 'PASS' | 'FAIL' | null;
  quality_gate_result?: QualityGateResult | null;
  framework_mismatches?: string[];
  unsupported_claims?: string[];
  messages: MessageResponse[];
  generated_files: GeneratedFile[];
  iteration_history: IterationHistory[];
  started_at: string | null;
  completed_at: string | null;
  error: string | null;
}

export interface MessageResponse {
  id: string;
  source: string;
  type: string;
  content: string;
  created_at: string;
  metadata: {
    stop_reason?: string;
    [key: string]: any;
  };
  event_type?: string;
  workflow_state?: WorkflowState;
}

export interface TaskRequest {
  task: string;
}

export interface TaskResponse {
  messages: MessageResponse[];
  stop_reason: string | null;
}

export interface HealthResponse {
  status: string;
}

// --- History API Models ---

export interface WorkflowSummary {
  id: string;
  prompt: string;
  status: WorkflowStatusType;
  quality_gate_status?: string;
  total_iterations: number;
  generated_file_count: number;
  favorite: boolean;
  created_at: string;
  completed_at: string | null;
}

export interface WorkflowListResponse {
  items: WorkflowSummary[];
  total: number;
  limit: number;
  offset: number;
}

export interface WorkflowIteration {
  id: number;
  workflow_id: string;
  iteration_number: number;
  review_status: string | null;
  test_status: string | null;
  developer_output: string | null;
  reviewer_feedback: string | null;
  tester_feedback: string | null;
  created_at: string;
}

export interface AgentMessage {
  id: string;
  workflow_id: string;
  iteration_id: number | null;
  agent_name: string;
  role: string;
  content: string;
  sequence_number: number;
  created_at: string;
}

export interface StoredGeneratedFile {
  id: string;
  workflow_id: string;
  iteration_id: number | null;
  filename: string;
  language: string;
  content: string;
  is_final: boolean;
  created_at: string;
}

export interface WorkflowDetail {
  id: string;
  prompt: string;
  status: WorkflowStatusType;
  quality_gate_status?: string;
  quality_gate_data?: QualityGateResult | null;
  final_summary: string | null;
  total_iterations: number;
  generated_file_count: number;
  favorite: boolean;
  created_at: string;
  completed_at: string | null;
  iterations: WorkflowIteration[];
  messages: AgentMessage[];
  generated_files: StoredGeneratedFile[];
}

export interface WorkflowStats {
  total_workflows: number;
  completed_workflows: number;
  failed_workflows: number;
  needs_attention_workflows: number;
  running_workflows: number;
  favorite_count: number;
  average_iterations: number;
}
