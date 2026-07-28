import { Component, inject, signal, computed } from '@angular/core';
import { CommonModule } from '@angular/common';
import { ApiService } from '../../services/api.service';
import { MessageResponse, GeneratedFile, WorkflowState } from '../../models/chat.models';
import { HealthStatus } from '../health-status/health-status';
import { ChatInput } from '../chat-input/chat-input';
import { ResponseCards } from '../response-cards/response-cards';
import { MainNavComponent, ActiveTabType } from '../main-nav/main-nav';
import { HistoryListComponent } from '../history-list/history-list';
import { HistoryDetailComponent } from '../history-detail/history-detail';

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
  imports: [
    CommonModule,
    HealthStatus,
    ChatInput,
    ResponseCards,
    MainNavComponent,
    HistoryListComponent,
    HistoryDetailComponent,
  ],
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

        <app-main-nav
          [activeTab]="currentNavTab()"
          [artifactCount]="files().length"
          (tabChange)="onNavTabChange($event)"
        ></app-main-nav>

        <app-health-status></app-health-status>
      </header>

      <!-- Main Navigation Views -->

      <!-- VIEW 1: NEW WORKFLOW (Default) -->
      <main class="content-grid" *ngIf="currentNavTab() === 'new_workflow'">
        <!-- Left column: Input & Progress -->
        <section class="control-panel">
          <!-- History Loaded Banner -->
          <div class="history-notice animate-fade-in" *ngIf="historyNotice()">
            <span>ℹ️ {{ historyNotice() }}</span>
          </div>

          <app-chat-input
            [disabled]="loading()"
            [initialText]="promptFromHistory()"
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

            <!-- Iteration status info -->
            <div class="iteration-info" *ngIf="workflowState() as ws">
              <div class="iteration-badge">Iteration {{ ws.current_iteration }} / {{ ws.max_iterations }}</div>
              <div class="iteration-details">
                <span *ngIf="ws.reviewer_status">Review: <span [ngClass]="ws.reviewer_status">{{ ws.reviewer_status }}</span></span>
                <span *ngIf="ws.tester_status"> | Test: <span [ngClass]="ws.tester_status">{{ ws.tester_status }}</span></span>
              </div>
            </div>

            <!-- Needs Attention Warning -->
            <div class="needs-attention-box" *ngIf="workflowStatus() === 'needs_attention'">
              <strong>⚠️ Needs Attention</strong>
              <p>The code reviewer or tester failed on the final iteration. Review and adjust requirements.</p>
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
            <div class="section-tabs">
              <button class="tab-btn" [ngClass]="{active: activeTab() === 'feed'}" (click)="activeTab.set('feed')">
                💬 Response Feed
              </button>
              <button class="tab-btn" *ngIf="files().length > 0" [ngClass]="{active: activeTab() === 'artifacts'}" (click)="activeTab.set('artifacts')">
                📦 Generated Artifacts ({{ files().length }})
              </button>
            </div>
            <span class="status-indicator" *ngIf="loading()">
              <span class="spinner-small"></span> Orchestrating agent workflow...
            </span>
          </div>

          <!-- Empty state -->
          <div class="empty-state animate-fade-in" *ngIf="messages().length === 0 && !loading() && activeTab() === 'feed'">
            <div class="empty-icon">🤖</div>
            <h4>No active workflow</h4>
            <p>Describe a task in the input box and click "Run Workflow" to initiate the multi-agent execution pipeline.</p>
          </div>

          <!-- Initial Loading Placeholder -->
          <div class="loading-placeholder animate-fade-in" *ngIf="messages().length === 0 && loading() && activeTab() === 'feed'">
            <div class="pulse-loader">
              <div class="pulse-bar"></div>
              <div class="pulse-bar"></div>
              <div class="pulse-bar"></div>
            </div>
            <p>Initializing team and spawning Manager Agent...</p>
          </div>

          <!-- Response feed cards -->
          <app-response-cards [messages]="messages()" *ngIf="activeTab() === 'feed'"></app-response-cards>

          <!-- Generated Artifacts Viewer -->
          <div class="artifacts-viewer animate-fade-in" *ngIf="activeTab() === 'artifacts' && files().length > 0">
            <div class="artifacts-sidebar">
              <div
                class="file-item"
                *ngFor="let file of files()"
                [ngClass]="{active: activeFile()?.filename === file.filename}"
                (click)="activeFile.set(file)"
              >
                <span class="file-icon">📄</span>
                <span class="file-name">{{ file.filename }}</span>
              </div>
            </div>
            <div class="code-editor-container" *ngIf="activeFile() as file">
              <div class="editor-header">
                <span class="editor-filename">💻 {{ file.filename }}</span>
                <div class="editor-actions">
                  <button class="action-btn copy-btn" (click)="copyCode(file)">
                    <span *ngIf="copyConfirmation() !== file.filename">📋 Copy Code</span>
                    <span *ngIf="copyConfirmation() === file.filename">✓ Copied!</span>
                  </button>
                  <button class="action-btn download-btn" (click)="downloadFile(file)">
                    📥 Download
                  </button>
                </div>
              </div>
              <div class="editor-body">
                <pre class="code-pre"><code><div class="code-line" *ngFor="let line of getCodeLines(file.content); let idx = index"><span class="line-number">{{ idx + 1 }}</span><span class="line-content">{{ line }}</span></div></code></pre>
              </div>
            </div>
          </div>
        </section>
      </main>

      <!-- VIEW 2: GENERATED FILES TAB -->
      <main class="artifacts-page animate-fade-in" *ngIf="currentNavTab() === 'generated_files'">
        <div class="output-section">
          <div class="section-header">
            <h3>📦 Current Session Generated Artifacts</h3>
            <span class="file-count" *ngIf="files().length > 0">{{ files().length }} File{{ files().length === 1 ? '' : 's' }}</span>
          </div>

          <div class="empty-state" *ngIf="files().length === 0">
            <div class="empty-icon">📂</div>
            <h4>No generated files yet</h4>
            <p>Run a workflow to generate code artifacts with the multi-agent developer team.</p>
          </div>

          <div class="artifacts-viewer animate-fade-in" *ngIf="files().length > 0">
            <div class="artifacts-sidebar">
              <div
                class="file-item"
                *ngFor="let file of files()"
                [ngClass]="{active: activeFile()?.filename === file.filename}"
                (click)="activeFile.set(file)"
              >
                <span class="file-icon">📄</span>
                <span class="file-name">{{ file.filename }}</span>
              </div>
            </div>
            <div class="code-editor-container" *ngIf="activeFile() as file">
              <div class="editor-header">
                <span class="editor-filename">💻 {{ file.filename }}</span>
                <div class="editor-actions">
                  <button class="action-btn copy-btn" (click)="copyCode(file)">
                    <span *ngIf="copyConfirmation() !== file.filename">📋 Copy Code</span>
                    <span *ngIf="copyConfirmation() === file.filename">✓ Copied!</span>
                  </button>
                  <button class="action-btn download-btn" (click)="downloadFile(file)">
                    📥 Download
                  </button>
                </div>
              </div>
              <div class="editor-body">
                <pre class="code-pre"><code><div class="code-line" *ngFor="let line of getCodeLines(file.content); let idx = index"><span class="line-number">{{ idx + 1 }}</span><span class="line-content">{{ line }}</span></div></code></pre>
              </div>
            </div>
          </div>
        </div>
      </main>

      <!-- VIEW 3: HISTORY & MEMORY TAB -->
      <main class="history-page animate-fade-in" *ngIf="currentNavTab() === 'history'">
        <app-history-list
          *ngIf="!selectedWorkflowId()"
          (selectWorkflow)="onSelectWorkflow($event)"
          (runAgain)="onRunAgainFromHistory($event)"
        ></app-history-list>

        <app-history-detail
          *ngIf="selectedWorkflowId()"
          [workflowId]="selectedWorkflowId()"
          (back)="onBackToHistoryList()"
          (runAgain)="onRunAgainFromHistory($event)"
          (deleted)="onWorkflowDeleted()"
        ></app-history-detail>
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
      gap: 1rem;
      flex-wrap: wrap;
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
    .history-notice {
      background: #eff6ff;
      border: 1px solid #bfdbfe;
      border-radius: 12px;
      padding: 0.75rem 1rem;
      color: #1d4ed8;
      font-size: 0.85rem;
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
    .workflow-status.needs_attention {
      background: #fef3c7;
      color: #d97706;
    }
    .iteration-info {
      margin-top: -0.5rem;
      margin-bottom: 1.25rem;
      padding: 0.75rem 1rem;
      background: #f8fafc;
      border: 1px solid #e2e8f0;
      border-radius: 12px;
      display: flex;
      justify-content: space-between;
      align-items: center;
      font-size: 0.85rem;
    }
    .iteration-badge {
      font-weight: 700;
      color: #475569;
      background: #e2e8f0;
      padding: 0.2rem 0.5rem;
      border-radius: 6px;
    }
    .iteration-details {
      color: #64748b;
      font-weight: 500;
    }
    .APPROVED, .PASS {
      color: #10b981;
      font-weight: 700;
    }
    .CHANGES_REQUIRED, .FAIL {
      color: #ef4444;
      font-weight: 700;
    }
    .needs-attention-box {
      margin-bottom: 1.25rem;
      padding: 0.75rem 1rem;
      background: #fffbeb;
      border: 1px solid #fde68a;
      border-radius: 12px;
      color: #b45309;
      font-size: 0.85rem;
    }
    .needs-attention-box strong {
      display: block;
      margin-bottom: 0.25rem;
    }
    .needs-attention-box p {
      margin: 0;
      line-height: 1.4;
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
      padding-bottom: 0.5rem;
      margin-bottom: 0.5rem;
    }
    .section-header h3 {
      margin: 0;
      font-size: 1.1rem;
      color: #0f172a;
    }
    .file-count {
      font-size: 0.85rem;
      background: #eff6ff;
      color: #2563eb;
      font-weight: 700;
      padding: 0.2rem 0.6rem;
      border-radius: 9999px;
    }
    .section-tabs {
      display: flex;
      gap: 0.5rem;
    }
    .tab-btn {
      background: none;
      border: none;
      font-size: 0.95rem;
      font-weight: 600;
      color: #64748b;
      padding: 0.5rem 1rem;
      cursor: pointer;
      position: relative;
      transition: all 0.2s ease;
      border-radius: 8px;
    }
    .tab-btn:hover {
      color: #0f172a;
      background: #f1f5f9;
    }
    .tab-btn.active {
      color: #2563eb;
      background: #eff6ff;
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

    .artifacts-viewer {
      display: grid;
      grid-template-columns: 200px 1fr;
      gap: 1.5rem;
      height: calc(100vh - 280px);
      min-height: 480px;
    }
    .artifacts-sidebar {
      border-right: 1px solid #e2e8f0;
      padding-right: 1rem;
      overflow-y: auto;
      display: flex;
      flex-direction: column;
      gap: 0.5rem;
    }
    .file-item {
      display: flex;
      align-items: center;
      gap: 0.5rem;
      padding: 0.6rem 0.8rem;
      border-radius: 8px;
      cursor: pointer;
      font-size: 0.85rem;
      font-weight: 500;
      color: #475569;
      transition: all 0.2s ease;
      border: 1px solid transparent;
    }
    .file-item:hover {
      background: #f8fafc;
      color: #0f172a;
    }
    .file-item.active {
      background: #eff6ff;
      color: #2563eb;
      border-color: #bfdbfe;
    }
    .file-icon {
      font-size: 1.1rem;
    }
    .code-editor-container {
      display: flex;
      flex-direction: column;
      border: 1px solid #cbd5e1;
      border-radius: 12px;
      overflow: hidden;
      background: #0f172a;
      box-shadow: inset 0 2px 4px rgba(0, 0, 0, 0.1);
    }
    .editor-header {
      display: flex;
      justify-content: space-between;
      align-items: center;
      padding: 0.6rem 1.25rem;
      background: #1e293b;
      border-bottom: 1px solid #334155;
    }
    .editor-filename {
      font-size: 0.85rem;
      font-weight: 600;
      color: #cbd5e1;
      font-family: monospace;
    }
    .editor-actions {
      display: flex;
      gap: 0.5rem;
    }
    .action-btn {
      font-size: 0.75rem;
      font-weight: 600;
      padding: 0.35rem 0.75rem;
      border-radius: 6px;
      cursor: pointer;
      border: none;
      transition: all 0.2s ease;
    }
    .copy-btn {
      background: #3b82f6;
      color: #ffffff;
    }
    .copy-btn:hover {
      background: #2563eb;
    }
    .download-btn {
      background: #475569;
      color: #cbd5e1;
    }
    .download-btn:hover {
      background: #334155;
      color: #ffffff;
    }
    .editor-body {
      flex: 1;
      overflow: auto;
      padding: 1rem;
    }
    .code-pre {
      margin: 0;
      font-family: 'Fira Code', 'Courier New', Courier, monospace;
      font-size: 0.8rem;
      line-height: 1.5;
    }
    .code-line {
      display: flex;
    }
    .line-number {
      width: 35px;
      color: #475569;
      text-align: right;
      padding-right: 0.75rem;
      user-select: none;
      border-right: 1px solid #334155;
    }
    .line-content {
      padding-left: 0.75rem;
      color: #e2e8f0;
      white-space: pre;
    }

    .animate-fade-in {
      animation: fadeIn 0.4s ease forwards;
    }

    @keyframes spin { to { transform: rotate(360deg); } }
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

  public readonly currentNavTab = signal<ActiveTabType>('new_workflow');
  public readonly selectedWorkflowId = signal<string | null>(null);
  public readonly promptFromHistory = signal<string>('');
  public readonly historyNotice = signal<string | null>(null);

  public readonly messages = signal<MessageResponse[]>([]);
  public readonly loading = signal(false);
  public readonly error = signal<string | null>(null);

  // Workflow state signal
  public readonly workflowState = signal<WorkflowState | null>(null);

  // UI state signals
  public readonly activeTab = signal<'feed' | 'artifacts'>('feed');
  public readonly activeFile = signal<GeneratedFile | null>(null);
  public readonly copyConfirmation = signal<string | null>(null);

  // Computed generated files: Show final accepted artifacts by default, otherwise show all files
  public readonly files = computed(() => {
    const allFiles = this.workflowState()?.generated_files || [];
    const finalFiles = allFiles.filter(f => f.is_final);
    return finalFiles.length > 0 ? finalFiles : allFiles;
  });

  // Workflow steps
  public readonly steps = signal<ProgressStep[]>([
    { id: 'manager', label: '1. Manager Agent', status: 'idle', icon: '📋', agentName: 'manager_agent' },
    { id: 'developer', label: '2. Python Developer', status: 'idle', icon: '💻', agentName: 'python_developer' },
    { id: 'reviewer', label: '3. Code Reviewer', status: 'idle', icon: '🔍', agentName: 'code_reviewer' },
    { id: 'tester', label: '4. Tester Agent', status: 'idle', icon: '🧪', agentName: 'tester_agent' },
    { id: 'documenter', label: '5. Documentation Specialist', status: 'idle', icon: '📝', agentName: 'documentation_agent' }
  ]);

  // Overall workflow status
  public readonly workflowStatus = signal<'idle' | 'running' | 'completed' | 'failed' | 'needs_attention'>('idle');

  workflowStatusText(): string {
    switch (this.workflowStatus()) {
      case 'running': return 'Orchestrating...';
      case 'completed': return '✓ Complete';
      case 'failed': return '✗ Failed';
      case 'needs_attention': return '⚠️ Needs Attention';
      default: return 'Ready';
    }
  }

  onNavTabChange(tab: ActiveTabType) {
    this.currentNavTab.set(tab);
    if (tab === 'history') {
      this.selectedWorkflowId.set(null);
    }
  }

  onSelectWorkflow(id: string) {
    this.selectedWorkflowId.set(id);
  }

  onBackToHistoryList() {
    this.selectedWorkflowId.set(null);
  }

  onWorkflowDeleted() {
    this.selectedWorkflowId.set(null);
  }

  onRunAgainFromHistory(prompt: string) {
    this.promptFromHistory.set(prompt);
    this.currentNavTab.set('new_workflow');
    this.historyNotice.set('Loaded prompt from history. Review and click "Run Workflow" to execute.');

    setTimeout(() => {
      this.historyNotice.set(null);
    }, 5000);
  }

  onExecuteTask(task: string) {
    this.loading.set(true);
    this.error.set(null);
    this.messages.set([]);
    this.workflowState.set(null);
    this.activeFile.set(null);
    this.activeTab.set('feed');
    this.workflowStatus.set('running');

    // Reset steps
    this.steps.update(steps => steps.map((s, idx) => ({
      ...s,
      status: idx === 0 ? 'running' : 'idle' as any
    })));

    this.apiService.executeChatStream(task).subscribe({
      next: (res) => {
        if (res.source === 'user') return;

        if (res.workflow_state) {
          this.workflowState.set(res.workflow_state);
          this.updateProgressFromState(res.workflow_state);

          const currentFiles = res.workflow_state.generated_files || [];
          if (currentFiles.length > 0 && !this.activeFile()) {
            this.activeFile.set(currentFiles[0]);
          }
        }

        if (res.type === 'TaskResult' || res.id === 'result') {
          const ws = this.workflowState();
          if (ws) {
            if (ws.status === 'COMPLETE') {
              this.workflowStatus.set('completed');
              this.steps.update(steps => steps.map(s => ({ ...s, status: 'completed' })));
            } else if (ws.status === 'NEEDS_ATTENTION') {
              this.workflowStatus.set('needs_attention');
            } else {
              this.workflowStatus.set('failed');
            }
          } else {
            this.workflowStatus.set('completed');
            this.steps.update(steps => steps.map(s => {
              if (s.status === 'running' || s.status === 'idle') {
                return { ...s, status: 'completed' };
              }
              return s;
            }));
          }
          this.loading.set(false);
          return;
        }

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

        this.messages.update(msgs => [...msgs, res]);

        if (!res.workflow_state) {
          this.updateProgressSteps(res);
        }
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

  updateProgressFromState(state: WorkflowState) {
    const agentSequence = ['manager_agent', 'python_developer', 'code_reviewer', 'tester_agent', 'documentation_agent'];
    const currentIndex = agentSequence.indexOf(state.current_agent || '');

    this.steps.update(steps => steps.map((step, idx) => {
      if (state.status === 'COMPLETE') {
        return { ...step, status: 'completed' };
      }
      if (state.status === 'NEEDS_ATTENTION') {
        if (step.agentName === 'code_reviewer' && state.reviewer_status === 'CHANGES_REQUIRED') {
          return { ...step, status: 'failed' };
        }
        if (step.agentName === 'tester_agent' && state.tester_status === 'FAIL') {
          return { ...step, status: 'failed' };
        }
        if (idx < 4) return { ...step, status: 'completed' };
        return { ...step, status: 'idle' };
      }
      if (state.status === 'FAILED') {
        if (step.agentName === state.current_agent) {
          return { ...step, status: 'failed' };
        }
      }

      if (idx === currentIndex) {
        return { ...step, status: 'running' };
      } else if (idx < currentIndex) {
        return { ...step, status: 'completed' };
      } else {
        return { ...step, status: 'idle' };
      }
    }));
  }

  updateProgressSteps(msg: MessageResponse) {
    const sender = msg.source;

    this.steps.update(steps => {
      return steps.map((step, idx) => {
        if (step.agentName === sender) {
          return { ...step, status: 'completed' };
        }
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
    this.workflowState.set(null);
    this.activeFile.set(null);
    this.activeTab.set('feed');
    this.workflowStatus.set('idle');
    this.promptFromHistory.set('');
    this.historyNotice.set(null);
    this.steps.update(steps => steps.map(s => ({ ...s, status: 'idle' })));
  }

  getCodeLines(content: string): string[] {
    if (!content) return [];
    return content.split('\n');
  }

  copyCode(file: GeneratedFile) {
    if (!file) return;
    navigator.clipboard.writeText(file.content)
      .then(() => {
        this.copyConfirmation.set(file.filename);
        setTimeout(() => {
          if (this.copyConfirmation() === file.filename) {
            this.copyConfirmation.set(null);
          }
        }, 2000);
      })
      .catch((err) => {
        console.error('Failed to copy code: ', err);
      });
  }

  downloadFile(file: GeneratedFile) {
    if (!file) return;
    const blob = new Blob([file.content], { type: 'text/plain' });
    const url = window.URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url;
    a.download = file.filename;
    a.click();
    window.URL.revokeObjectURL(url);
  }
}
