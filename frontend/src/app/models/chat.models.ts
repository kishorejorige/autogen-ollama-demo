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

export interface WorkflowState {
  workflow_id: string;
  current_agent: string | null;
  current_iteration: number;
  max_iterations: number;
  status: 'PENDING' | 'RUNNING' | 'COMPLETE' | 'NEEDS_ATTENTION' | 'FAILED' | 'CANCELLED';
  reviewer_status: 'APPROVED' | 'CHANGES_REQUIRED' | null;
  tester_status: 'PASS' | 'FAIL' | null;
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
)
