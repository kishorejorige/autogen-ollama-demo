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
