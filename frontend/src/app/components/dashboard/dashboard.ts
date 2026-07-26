import { Component, inject, signal } from '@angular/core';
import { CommonModule } from '@angular/common';
import { ApiService } from '../../services/api.service';
import { MessageResponse } from '../../models/chat.models';
import { HealthStatus } from '../health-status/health-status';
import { ChatInput } from '../chat-input/chat-input';
import { ResponseCards } from '../response-cards/response-cards';

interface ProgressStep {
  id: string;
  label: string;
  status: 'idle' | 'running' | 'completed' | 'failed';
  icon: string;
  agentName: string;
}

@Component({
  selector: 'app-dashboard',
  standalone: true,
  imports: [CommonModule, HealthStatus, ChatInput, ResponseCards],
  template: `
    <div class="dashboard-wrapper">
      <!-- Header -->
      <header class="header">
        <div class="header-left">
          <span class="logo">⚡</span>
          <div class="title-area">
            <h1>AutoGen Orchestrator</h1>
            <p class="subtitle">Local Multi-Agent AI Team</p>
          </div>
        </div>
        <app-health-status></app-health-status>
      </header>

      <!-- Main Grid Layout -->
      <main class="content-grid">
        <!-- Left column: Input & Progress -->
        <section class="control-panel">
          <app-chat-input
            [disabled]="loading()"
            (run)="onExecuteTask($event)"
            (clear)="onClearResults()"
          ></app-chat-input>

          <!-- Error Alert -->
          <div class="error-alert animate-fade-in" *ngIf="error()">
            <span class="error-icon">❌</span>
            <div class="error-msg">
              <strong>Execution Error</strong>
              <p>{{ error() }}</p>
            </div>
          </div>

          <!-- Progress Indicator Card -->
          <div class="progress-card animate-fade-in" *ngIf="loading() || messages().length > 0">
            <div class="card-header">
              <h3>Agent Orchestration Pipeline</h3>
              <span class="workflow-status" [ngClass]="workflowStatus()">
                {{ workflowStatusText() }}
              </span>
            </div>
            
            <div class="steps-list">
              <div class="step-item" *ngFor="let step of steps(); let idx = index" [ngClass]="step.status">
                <div class="step-line" *ngIf="idx < steps().length - 1"></div>
                <div class="step-icon-wrapper">
                  <span class="step-icon" *ngIf="step.status !== 'running' && step.status !== 'completed' && step.status !== 'failed'">
                    {{ step.icon }}
                  </span>
                  <span class="step-icon spinner" *ngIf="step.status === 'running'">🔄</span>
                  <span class="step-icon check" *ngIf="step.status === 'completed'">✓</span>
                  <span class="step-icon cross" *ngIf="step.status === 'failed'">✗</span>
                </div>
                <div class="step-content">
                  <span class="step-label">{{ step.label }}</span>
                  <span class="step-desc" *ngIf="step.status === 'idle'">Waiting for turn...</span>
                  <span class="step-desc pulse" *ngIf="step.status === 'running'">Agent is executing...</span>
                  <span class="step-desc success-text" *ngIf="step.status === 'completed'">Turn completed successfully</span>
                  <span class="step-desc failed-text" *ngIf="step.status === 'failed'">Execution failed</span>
                </div>
              </div>
            </div>
          </div>
        </section>

        <!-- Right column: Output feed -->
        <section class="output-section">
          <div class="section-header">
            <h3>Response Feed</h3>
            <span class="status-indicator" *ngIf="loading()">
              <span class="spinner-small"></span> Orchestrating agent workflow...
            </span>
          </div>

          <!-- Empty state -->
          <div class="empty-state animate-fade-in" *ngIf="messages().length === 0 && !loading()">
            <div class="empty-icon">🤖</div>
            <h4>No active workflow</h4>
            <p>Describe a task in the input box and click "Run Workflow" to initiate the multi-agent execution pipeline.</p>
          </div>

          <!-- Initial Loading Placeholder -->
          <div class="loading-placeholder animate-fade-in" *ngIf="messages().length === 0 && loading()">
            <div class="pulse-loader">
              <div class="pulse-bar"></div>
              <div class="pulse-bar"></div>
              <div class="pulse-bar"></div>
            </div>
            <p>Initializing team and spawning Manager Agent...</p>
          </div>

          <!-- Response feed cards -->
          <app-response-cards [messages]="messages()"></app-response-cards>
        </section>
      </main>
    </div>
  `,
  styles: [`
    .dashboard-wrapper {
      max-width: 1280px;
      margin: 0 auto;
      padding: 2rem;
      display: flex;
      flex-direction: column;
      gap: 2rem;
      min-height: 100vh;
      box-sizing: border-box;
    }
    .header {
      display: flex;
      justify-content: space-between;
      align-items: center;
      border-bottom: 1px solid #e2e8f0;
      padding-bottom: 1.25rem;
    }
    .header-left {
      display: flex;
      align-items: center;
      gap: 1rem;
    }
    .logo {
      font-size: 2.2rem;
      background: linear-gradient(135deg, #3b82f6, #6366f1);
      padding: 0.5rem;
      border-radius: 12px;
      display: inline-flex;
      align-items: center;
      justify-content: center;
      color: #ffffff;
      box-shadow: 0 4px 12px rgba(59, 130, 246, 0.25);
    }
    .title-area h1 {
      font-size: 1.6rem;
      font-weight: 700;
      color: #0f172a;
      margin: 0;
      letter-spacing: -0.02em;
    }
    .subtitle {
      font-size: 0.9rem;
      color: #64748b;
      margin: 0.2rem 0 0 0;
      font-weight: 500;
    }
    .content-grid {
      display: grid;
      grid-template-columns: 1fr;
      gap: 2rem;
      align-items: start;
    }
    @media (min-width: 960px) {
      .content-grid {
        grid-template-columns: 460px 1fr;
      }
    }
    .control-panel {
      display: flex;
      flex-direction: column;
      gap: 1.5rem;
      position: sticky;
      top: 2rem;
    }
    .progress-card {
      background: #ffffff;
      border: 1px solid #e2e8f0;
      border-radius: 16px;
      padding: 1.5rem;
      box-shadow: 0 1px 3px rgba(0, 0, 0, 0.02), 0 4px 12px rgba(0, 0, 0, 0.03);
    }
    .progress-card .card-header {
      display: flex;
      justify-content: space-between;
      align-items: center;
      border-bottom: 1px solid #f1f5f9;
      padding-bottom: 0.75rem;
      margin-bottom: 1.25rem;
    }
    .progress-card h3 {
      font-size: 1rem;
      font-weight: 600;
      color: #0f172a;
      margin: 0;
    }
    .workflow-status {
      font-size: 0.75rem;
      font-weight: 600;
      padding: 0.25rem 0.65rem;
      border-radius: 9999px;
      text-transform: uppercase;
      letter-spacing: 0.05em;
    }
    .workflow-status.idle {
      background: #f1f5f9;
      color: #64748b;
    }
    .workflow-status.running {
      background: #eff6ff;
      color: #2563eb;
      animation: pulse-bg 2s infinite ease-in-out;
    }
    .workflow-status.completed {
      background: #ecfdf5;
      color: #059669;
    }
    .workflow-status.failed {
      background: #fef2f2;
      color: #dc2626;
    }
    .steps-list {
      display: flex;
      flex-direction: column;
      gap: 1.5rem;
    }
    .step-item {
      display: flex;
      gap: 1rem;
      position: relative;
    }
    .step-line {
      position: absolute;
      left: 14px;
      top: 28px;
      bottom: -20px;
      width: 2px;
      background-color: #e2e8f0;
      z-index: 1;
      transition: background-color 0.3s ease;
    }
    .step-icon-wrapper {
      position: relative;
      z-index: 2;
      width: 30px;
      height: 30px;
      border-radius: 50%;
      background: #ffffff;
      border: 2px solid #e2e8f0;
      display: flex;
      align-items: center;
      justify-content: center;
      transition: all 0.3s ease;
    }
    .step-icon {
      font-size: 0.95rem;
      display: inline-flex;
      align-items: center;
      justify-content: center;
    }
    .step-content {
      display: flex;
      flex-direction: column;
      gap: 0.15rem;
    }
    .step-label {
      font-size: 0.9rem;
      font-weight: 600;
      color: #64748b;
      transition: color 0.3s ease;
    }
    .step-desc {
      font-size: 0.75rem;
      color: #94a3b8;
    }
    
    /* Step status classes */
    .step-item.running .step-icon-wrapper {
      border-color: #3b82f6;
      background: #eff6ff;
      box-shadow: 0 0 0 4px rgba(59, 130, 246, 0.15);
    }
    .step-item.running .step-label {
      color: #2563eb;
    }
    .step-item.running .step-line {
      background-color: #3b82f6;
    }
    .step-item.completed .step-icon-wrapper {
      border-color: #10b981;
      background: #ecfdf5;
    }
    .step-item.completed .step-label {
      color: #0f172a;
    }
    .step-item.completed .step-icon {
      color: #10b981;
    }
    .step-item.completed .step-line {
      background-color: #10b981;
    }
    .step-item.failed .step-icon-wrapper {
      border-color: #ef4444;
      background: #fef2f2;
    }
    .step-item.failed .step-label {
      color: #ef4444;
    }
    
    .spinner {
      animation: spin 2s linear infinite;
      font-size: 0.85rem;
    }
    .check {
      color: #10b981;
      font-weight: bold;
    }
    .cross {
      color: #ef4444;
      font-weight: bold;
    }
    .success-text {
      color: #10b981 !important;
    }
    .failed-text {
      color: #ef4444 !important;
    }

    .output-section {
      display: flex;
      flex-direction: column;
      gap: 1.5rem;
      background: #ffffff;
      border: 1px solid #e2e8f0;
      border-radius: 16px;
      padding: 1.5rem;
      min-height: 500px;
      box-sizing: border-box;
      box-shadow: 0 1px 3px rgba(0, 0, 0, 0.02), 0 4px 12px rgba(0, 0, 0, 0.03);
    }
    .section-header {
      display: flex;
      justify-content: space-between;
      align-items: center;
      border-bottom: 1px solid #f1f5f9;
      padding-bottom: 0.75rem;
      margin-bottom: 0.5rem;
    }
    .section-header h3 {
      font-size: 1.1rem;
      font-weight: 600;
      color: #0f172a;
      margin: 0;
    }
    .status-indicator {
      display: inline-flex;
      align-items: center;
      gap: 0.5rem;
      font-size: 0.85rem;
      color: #2563eb;
      font-weight: 500;
    }
    .spinner-small {
      width: 14px;
      height: 14px;
      border: 2px solid rgba(59, 130, 246, 0.2);
      border-top-color: #3b82f6;
      border-radius: 50%;
      animation: spin 0.8s linear infinite;
    }
    .error-alert {
      display: flex;
      gap: 0.75rem;
      background: #fef2f2;
      border: 1px solid #fca5a5;
      border-radius: 12px;
      padding: 1rem;
    }
    .error-icon {
      font-size: 1.2rem;
    }
    .error-msg strong {
      display: block;
      color: #b91c1c;
      font-size: 0.9rem;
      margin-bottom: 0.25rem;
    }
    .error-msg p {
      color: #991b1b;
      font-size: 0.85rem;
      margin: 0;
      line-height: 1.4;
    }
    .empty-state {
      display: flex;
      flex-direction: column;
      align-items: center;
      justify-content: center;
      gap: 0.75rem;
      padding: 6rem 2rem;
      text-align: center;
      color: #64748b;
    }
    .empty-icon {
      font-size: 3.5rem;
      margin-bottom: 0.5rem;
    }
    .empty-state h4 {
      font-size: 1.1rem;
      font-weight: 600;
      color: #334155;
      margin: 0;
    }
    .empty-state p {
      font-size: 0.9rem;
      max-width: 380px;
      margin: 0;
      line-height: 1.5;
      color: #64748b;
    }
    .loading-placeholder {
      display: flex;
      flex-direction: column;
      align-items: center;
      justify-content: center;
      gap: 1.25rem;
      padding: 6rem 2rem;
      text-align: center;
      color: #64748b;
    }
    .pulse-loader {
      display: flex;
      gap: 0.35rem;
    }
    .pulse-bar {
      width: 4px;
      height: 24px;
      background-color: #3b82f6;
      border-radius: 2px;
      animation: pulse 1.2s ease-in-out infinite;
    }
    .pulse-bar:nth-child(2) {
      animation-delay: 0.2s;
    }
    .pulse-bar:nth-child(3) {
      animation-delay: 0.4s;
    }
    .loading-placeholder p {
      font-size: 0.9rem;
      margin: 0;
      font-weight: 500;
    }

    /* Animations */
    .animate-fade-in {
      animation: fadeIn 0.4s ease forwards;
    }

    @keyframes spin {
      to { transform: rotate(360deg); }
    }
    @keyframes pulse {
      0%, 100% { transform: scaleY(1); }
      50% { transform: scaleY(0.4); }
    }
    @keyframes pulse-bg {
      0%, 100% { opacity: 1; }
      50% { opacity: 0.6; }
    }
    @keyframes fadeIn {
      from { opacity: 0; transform: translateY(4px); }
      to { opacity: 1; transform: translateY(0); }
    }
  `]
})
export class DashboardComponent {
  private readonly apiService = inject(ApiService);
  public readonly messages = signal<MessageResponse[]>([]);
  public readonly loading = signal(false);
  public readonly error = signal<string | null>(null);

  // Workflow steps
  public readonly steps = signal<ProgressStep[]>([
    { id: 'manager', label: '1. Manager Agent', status: 'idle', icon: '📋', agentName: 'manager_agent' },
    { id: 'developer', label: '2. Python Developer', status: 'idle', icon: '💻', agentName: 'python_developer' },
    { id: 'reviewer', label: '3. Code Reviewer', status: 'idle', icon: '🔍', agentName: 'code_reviewer' },
    { id: 'documenter', label: '4. Documentation Specialist', status: 'idle', icon: '📝', agentName: 'documentation_agent' }
  ]);

  // Overall workflow status
  public readonly workflowStatus = signal<'idle' | 'running' | 'completed' | 'failed'>('idle');

  workflowStatusText(): string {
    switch (this.workflowStatus()) {
      case 'running': return 'Orchestrating...';
      case 'completed': return '✓ Complete';
      case 'failed': return '✗ Failed';
      default: return 'Ready';
    }
  }

  onExecuteTask(task: string) {
    this.loading.set(true);
    this.error.set(null);
    this.messages.set([]);
    this.workflowStatus.set('running');

    // Reset steps
    this.steps.update(steps => steps.map((s, idx) => ({
      ...s,
      status: idx === 0 ? 'running' : 'idle' as any
    })));

    this.apiService.executeChatStream(task).subscribe({
      next: (res) => {
        // Skip user message in response feed as it's already shown or we only want agent responses
        if (res.source === 'user') return;

        // If the event is a TaskResult (meaning the workflow is done)
        if (res.type === 'TaskResult' || res.id === 'result') {
          // Complete any remaining step
          this.steps.update(steps => steps.map(s => {
            if (s.status === 'running' || s.status === 'idle') {
              return { ...s, status: 'completed' };
            }
            return s;
          }));
          this.workflowStatus.set('completed');
          this.loading.set(false);
          return;
        }

        // Check if error message
        if (res.type === 'Error' || res.source === 'error') {
          this.error.set(res.content || 'An unexpected error occurred during agent execution.');
          this.workflowStatus.set('failed');
          this.steps.update(steps => steps.map(s => {
            if (s.status === 'running') {
              return { ...s, status: 'failed' };
            }
            return s;
          }));
          this.loading.set(false);
          return;
        }

        // Add message to feed
        this.messages.update(msgs => [...msgs, res]);

        // Progress step management
        this.updateProgressSteps(res);
      },
      error: (err) => {
        const detail = err.message || 'An unexpected error occurred during execution. Please check that Ollama is running and the backend is healthy.';
        this.error.set(detail);
        this.workflowStatus.set('failed');
        this.steps.update(steps => steps.map(s => {
          if (s.status === 'running') {
            return { ...s, status: 'failed' };
          }
          return s;
        }));
        this.loading.set(false);
      }
    });
  }

  updateProgressSteps(msg: MessageResponse) {
    const sender = msg.source;
    
    this.steps.update(steps => {
      return steps.map((step, idx) => {
        if (step.agentName === sender) {
          // This agent just finished, mark as completed
          return { ...step, status: 'completed' };
        }
        
        // Find if this is the next step to set to running
        const prevStep = steps[idx - 1];
        if (prevStep && prevStep.agentName === sender && step.status === 'idle') {
          return { ...step, status: 'running' };
        }
        
        return step;
      });
    });
  }

  onClearResults() {
    this.messages.set([]);
    this.error.set(null);
    this.loading.set(false);
    this.workflowStatus.set('idle');
    this.steps.update(steps => steps.map(s => ({ ...s, status: 'idle' })));
  }
}
