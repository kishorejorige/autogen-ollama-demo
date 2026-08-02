import { Component, EventEmitter, inject, Input, OnInit, Output, signal } from '@angular/core';
import { CommonModule } from '@angular/common';
import { HistoryService } from '../../services/history.service';
import { StoredGeneratedFile, WorkflowDetail } from '../../models/chat.models';

type DetailTabType = 'summary' | 'iterations' | 'messages' | 'artifacts';

@Component({
  selector: 'app-history-detail',
  standalone: true,
  imports: [CommonModule],
  template: `
    <div class="history-detail-container animate-fade-in" *ngIf="detail()">
      <!-- Top Actions Bar -->
      <div class="top-bar">
        <button class="action-btn back-btn" (click)="onBack()">
          ← Back to History
        </button>

        <div class="top-actions">
          <button class="action-btn fav-btn" [class.is-fav]="detail()?.favorite" (click)="toggleFavorite()">
            {{ detail()?.favorite ? '⭐ Favorite' : '☆ Mark Favorite' }}
          </button>
          <button class="action-btn export-btn" (click)="exportJson()">
            📄 Export JSON
          </button>
          <button class="action-btn download-zip-btn" (click)="downloadZip()">
            📦 Download ZIP
          </button>
          <button class="action-btn run-again-btn" (click)="onRunAgain()">
            ⚡ Run Again
          </button>
          <button class="action-btn delete-btn" (click)="showDeleteModal.set(true)">
            🗑️ Delete Workflow
          </button>
        </div>
      </div>

      <!-- Header Card -->
      <div class="header-card">
        <div class="header-main">
          <span class="status-badge" [ngClass]="detail()!.status.toLowerCase()">
            <span class="status-icon" *ngIf="detail()!.status === 'COMPLETE'">✓</span>
            <span class="status-icon" *ngIf="detail()!.status === 'NEEDS_ATTENTION'">⚠️</span>
            <span class="status-icon" *ngIf="detail()!.status === 'FAILED'">✗</span>
            <span class="status-icon" *ngIf="detail()!.status === 'RUNNING'">🔄</span>
            {{ formatStatus(detail()!.status) }}
          </span>

          <h2 class="prompt-heading">{{ detail()!.prompt }}</h2>

          <div class="header-meta">
            <span>📅 Created: {{ formatDate(detail()!.created_at) }}</span>
            <span *ngIf="detail()!.completed_at">⏱️ Completed: {{ formatDate(detail()!.completed_at!) }}</span>
            <span>🔄 Iterations: {{ detail()!.total_iterations }}</span>
            <span>📦 Artifacts: {{ detail()!.generated_file_count }}</span>
          </div>
        </div>
      </div>

      <!-- Navigation Tabs -->
      <div class="detail-tabs">
        <button
          class="tab-btn"
          [class.active]="activeTab() === 'summary'"
          (click)="activeTab.set('summary')"
        >
          📋 Summary
        </button>
        <button
          class="tab-btn"
          [class.active]="activeTab() === 'iterations'"
          (click)="activeTab.set('iterations')"
        >
          🔄 Iterations ({{ detail()!.iterations.length }})
        </button>
        <button
          class="tab-btn"
          [class.active]="activeTab() === 'messages'"
          (click)="activeTab.set('messages')"
        >
          💬 Agent Messages ({{ detail()!.messages.length }})
        </button>
        <button
          class="tab-btn"
          [class.active]="activeTab() === 'artifacts'"
          (click)="activeTab.set('artifacts')"
        >
          📦 Generated Files ({{ detail()!.generated_files.length }})
        </button>
      </div>

      <!-- Tab Content Area -->
      <div class="tab-content">
        <!-- 1. SUMMARY TAB -->
        <div class="summary-view" *ngIf="activeTab() === 'summary'">
          <div class="summary-section">
            <h4>Workflow Overview</h4>
            <div class="info-grid">
              <div class="info-item">
                <span class="info-label">Workflow ID</span>
                <span class="info-value id-code">{{ detail()!.id }}</span>
              </div>
              <div class="info-item">
                <span class="info-label">Status</span>
                <span class="info-value">{{ detail()!.status }}</span>
              </div>
              <div class="info-item">
                <span class="info-label">Total Iterations</span>
                <span class="info-value">{{ detail()!.total_iterations }}</span>
              </div>
              <div class="info-item">
                <span class="info-label">Files Generated</span>
                <span class="info-value">{{ detail()!.generated_file_count }}</span>
              </div>
            </div>
          </div>

          <div class="summary-section" *ngIf="detail()!.final_summary">
            <h4>Execution Result Summary</h4>
            <div class="summary-box">
              <p>{{ detail()!.final_summary }}</p>
            </div>
          </div>
        </div>

        <!-- 2. ITERATIONS TAB -->
        <div class="iterations-view" *ngIf="activeTab() === 'iterations'">
          <div class="empty-state" *ngIf="detail()!.iterations.length === 0">
            <p>No recorded iteration details for this workflow.</p>
          </div>

          <div class="iteration-timeline" *ngIf="detail()!.iterations.length > 0">
            <div
              class="iteration-card"
              *ngFor="let iter of detail()!.iterations; let idx = index"
              [class.final-iter]="idx === detail()!.iterations.length - 1 && detail()!.status === 'COMPLETE'"
            >
              <div class="iter-header" (click)="toggleIter(iter.id)">
                <div class="iter-title">
                  <span class="iter-badge">Iteration {{ iter.iteration_number }}</span>
                  <span class="final-tag" *ngIf="idx === detail()!.iterations.length - 1 && detail()!.status === 'COMPLETE'">
                    ★ Accepted / Final
                  </span>
                </div>

                <div class="iter-statuses">
                  <span class="status-pill" [ngClass]="iter.review_status" *ngIf="iter.review_status">
                    Review: {{ iter.review_status }}
                  </span>
                  <span class="status-pill" [ngClass]="iter.test_status" *ngIf="iter.test_status">
                    Test: {{ iter.test_status }}
                  </span>
                  <span class="toggle-icon">{{ expandedIters()[iter.id] ? '▲' : '▼' }}</span>
                </div>
              </div>

              <!-- Collapsible Content -->
              <div class="iter-body" *ngIf="expandedIters()[iter.id]">
                <div class="response-block" *ngIf="iter.developer_output">
                  <h5>💻 Developer Output</h5>
                  <pre class="response-pre"><code>{{ iter.developer_output }}</code></pre>
                </div>

                <div class="response-block" *ngIf="iter.reviewer_feedback">
                  <h5>🔍 Reviewer Feedback</h5>
                  <pre class="response-pre"><code>{{ iter.reviewer_feedback }}</code></pre>
                </div>

                <div class="response-block" *ngIf="iter.tester_feedback">
                  <h5>🧪 Tester Feedback</h5>
                  <pre class="response-pre"><code>{{ iter.tester_feedback }}</code></pre>
                </div>
              </div>
            </div>
          </div>
        </div>

        <!-- 3. MESSAGES TAB -->
        <div class="messages-view" *ngIf="activeTab() === 'messages'">
          <div class="empty-state" *ngIf="detail()!.messages.length === 0">
            <p>No agent messages stored.</p>
          </div>

          <div class="messages-list" *ngIf="detail()!.messages.length > 0">
            <div class="message-card" *ngFor="let msg of detail()!.messages">
              <div class="msg-header">
                <div class="msg-author">
                  <span class="msg-seq">#{{ msg.sequence_number }}</span>
                  <span class="agent-name">{{ formatAgentName(msg.agent_name) }}</span>
                  <span class="role-tag">{{ msg.role }}</span>
                </div>
                <span class="msg-time">{{ formatDate(msg.created_at) }}</span>
              </div>
              <div class="msg-content">
                <pre class="content-pre"><code>{{ msg.content }}</code></pre>
              </div>
            </div>
          </div>
        </div>

        <!-- 4. GENERATED FILES TAB -->
        <div class="artifacts-view" *ngIf="activeTab() === 'artifacts'">
          <div class="empty-state" *ngIf="detail()!.generated_files.length === 0">
            <p>No generated files saved for this workflow.</p>
          </div>

          <div class="artifacts-viewer" *ngIf="detail()!.generated_files.length > 0">
            <div class="artifacts-sidebar">
              <div
                class="file-item"
                *ngFor="let file of detail()!.generated_files"
                [class.active]="activeFile()?.id === file.id"
                (click)="activeFile.set(file)"
              >
                <span class="file-icon">📄</span>
                <div class="file-info">
                  <span class="file-name">{{ file.filename }}</span>
                  <span class="final-badge-small" *ngIf="file.is_final">Final</span>
                </div>
              </div>
            </div>

            <div class="code-editor-container" *ngIf="activeFile() as file">
              <div class="editor-header">
                <div class="editor-title">
                  <span class="editor-filename">💻 {{ file.filename }}</span>
                  <span class="final-badge" *ngIf="file.is_final">★ Accepted Final Artifact</span>
                </div>

                <div class="editor-actions">
                  <button class="action-btn copy-btn" (click)="copyCode(file)">
                    <span *ngIf="copyConfirmation() !== file.id">📋 Copy Code</span>
                    <span *ngIf="copyConfirmation() === file.id">✓ Copied!</span>
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
      </div>

      <!-- Delete Confirmation Modal -->
      <div class="modal-overlay animate-fade-in" *ngIf="showDeleteModal()">
        <div class="modal-card">
          <div class="modal-header">
            <h3>⚠️ Confirm Deletion</h3>
          </div>
          <div class="modal-body">
            <p>Are you sure you want to delete this workflow history?</p>
            <p class="modal-subtext">This will permanently delete all messages, iterations, and generated code files associated with this execution.</p>
          </div>
          <div class="modal-actions">
            <button class="action-btn cancel-btn" (click)="showDeleteModal.set(false)" [disabled]="deleting()">
              Cancel
            </button>
            <button class="action-btn confirm-delete-btn" (click)="confirmDelete()" [disabled]="deleting()">
              <span *ngIf="!deleting()">Yes, Delete Workflow</span>
              <span *ngIf="deleting()">Deleting...</span>
            </button>
          </div>
        </div>
      </div>
    </div>

    <!-- Loading Detail State -->
    <div class="loading-state animate-fade-in" *ngIf="loading()">
      <div class="spinner-large"></div>
      <p>Fetching workflow details...</p>
    </div>

    <!-- Error Detail State -->
    <div class="error-banner animate-fade-in" *ngIf="error()">
      <span class="error-icon">⚠️</span>
      <div class="error-text">
        <strong>Error loading workflow</strong>
        <p>{{ error() }}</p>
      </div>
      <button class="action-btn back-btn" (click)="onBack()">Back to History</button>
    </div>
  `,
  styles: [`
    .history-detail-container {
      display: flex;
      flex-direction: column;
      gap: 1.5rem;
    }
    .top-bar {
      display: flex;
      justify-content: space-between;
      align-items: center;
    }
    .top-actions {
      display: flex;
      gap: 0.75rem;
    }
    .action-btn {
      display: inline-flex;
      align-items: center;
      gap: 0.35rem;
      padding: 0.5rem 0.85rem;
      border-radius: 8px;
      font-size: 0.85rem;
      font-weight: 600;
      cursor: pointer;
      border: 1px solid transparent;
      transition: all 0.2s ease;
    }
    .back-btn { background: #f1f5f9; color: #475569; border-color: #cbd5e1; }
    .back-btn:hover { background: #e2e8f0; color: #0f172a; }

    .fav-btn { background: #fef9c3; color: #a16207; border-color: #fef08a; }
    .fav-btn:hover { background: #fef08a; }
    .fav-btn.is-fav { background: #fef08a; color: #854d0e; font-weight: 700; }

    .export-btn { background: #f0f9ff; color: #0369a1; border-color: #bae6fd; }
    .export-btn:hover { background: #e0f2fe; }

    .download-zip-btn { background: #faf5ff; color: #7e22ce; border-color: #e9d5ff; }
    .download-zip-btn:hover { background: #f3e8ff; }

    .run-again-btn { background: #f0fdf4; color: #16a34a; border-color: #bbf7d0; }
    .run-again-btn:hover { background: #dcfce7; }

    .delete-btn { background: #fef2f2; color: #dc2626; border-color: #fca5a5; }
    .delete-btn:hover { background: #fee2e2; }

    .header-card {
      background: #ffffff;
      border: 1px solid #e2e8f0;
      border-radius: 16px;
      padding: 1.5rem;
      box-shadow: 0 1px 3px rgba(0, 0, 0, 0.02);
    }
    .header-main { display: flex; flex-direction: column; gap: 0.6rem; }
    .prompt-heading { margin: 0; font-size: 1.3rem; font-weight: 700; color: #0f172a; line-height: 1.3; }
    .header-meta { display: flex; gap: 1.25rem; font-size: 0.85rem; color: #64748b; flex-wrap: wrap; }

    .status-badge {
      display: inline-flex;
      align-items: center;
      gap: 0.3rem;
      font-size: 0.75rem;
      font-weight: 700;
      padding: 0.25rem 0.65rem;
      border-radius: 9999px;
      text-transform: uppercase;
      letter-spacing: 0.04em;
      width: fit-content;
    }
    .status-badge.complete { background: #ecfdf5; color: #059669; }
    .status-badge.needs_attention { background: #fffbeb; color: #d97706; }
    .status-badge.failed { background: #fef2f2; color: #dc2626; }
    .status-badge.running { background: #eff6ff; color: #2563eb; }

    .detail-tabs {
      display: flex;
      gap: 0.5rem;
      border-bottom: 1px solid #e2e8f0;
      padding-bottom: 0.25rem;
    }
    .tab-btn {
      background: none;
      border: none;
      font-size: 0.9rem;
      font-weight: 600;
      color: #64748b;
      padding: 0.6rem 1rem;
      cursor: pointer;
      border-radius: 8px;
      transition: all 0.2s ease;
    }
    .tab-btn:hover { color: #0f172a; background: #f8fafc; }
    .tab-btn.active { color: #2563eb; background: #eff6ff; }

    .tab-content {
      background: #ffffff;
      border: 1px solid #e2e8f0;
      border-radius: 16px;
      padding: 1.5rem;
      min-height: 400px;
    }

    /* Summary Tab */
    .summary-view { display: flex; flex-direction: column; gap: 1.5rem; }
    .summary-section h4 { margin: 0 0 0.75rem 0; font-size: 1rem; color: #0f172a; }
    .info-grid { display: grid; grid-template-columns: repeat(auto-fit, minmax(180px, 1fr)); gap: 1rem; }
    .info-item { background: #f8fafc; border: 1px solid #e2e8f0; border-radius: 10px; padding: 0.85rem; display: flex; flex-direction: column; gap: 0.25rem; }
    .info-label { font-size: 0.75rem; color: #64748b; font-weight: 600; text-transform: uppercase; }
    .info-value { font-size: 1rem; font-weight: 700; color: #0f172a; }
    .id-code { font-family: monospace; font-size: 0.85rem; }
    .summary-box { background: #f8fafc; border: 1px solid #cbd5e1; border-radius: 10px; padding: 1rem; color: #334155; font-size: 0.95rem; line-height: 1.5; }

    /* Iterations Tab */
    .iteration-timeline { display: flex; flex-direction: column; gap: 1rem; }
    .iteration-card { border: 1px solid #e2e8f0; border-radius: 12px; overflow: hidden; background: #ffffff; }
    .iteration-card.final-iter { border-color: #86efac; box-shadow: 0 0 0 2px rgba(34, 197, 94, 0.15); }
    .iter-header { display: flex; justify-content: space-between; align-items: center; padding: 1rem; background: #f8fafc; cursor: pointer; }
    .iter-title { display: flex; align-items: center; gap: 0.75rem; }
    .iter-badge { font-weight: 700; color: #0f172a; font-size: 0.95rem; }
    .final-tag { background: #dcfce7; color: #15803d; font-size: 0.75rem; font-weight: 700; padding: 0.2rem 0.5rem; border-radius: 6px; }
    .iter-statuses { display: flex; align-items: center; gap: 0.5rem; }
    .status-pill { font-size: 0.75rem; font-weight: 700; padding: 0.2rem 0.5rem; border-radius: 6px; }
    .status-pill.APPROVED, .status-pill.PASS { background: #dcfce7; color: #15803d; }
    .status-pill.CHANGES_REQUIRED, .status-pill.FAIL { background: #fee2e2; color: #b91c1c; }
    .toggle-icon { font-size: 0.8rem; color: #94a3b8; margin-left: 0.5rem; }
    .iter-body { padding: 1rem; border-top: 1px solid #e2e8f0; display: flex; flex-direction: column; gap: 1rem; }
    .response-block h5 { margin: 0 0 0.4rem 0; font-size: 0.85rem; color: #475569; }
    .response-pre { background: #0f172a; color: #e2e8f0; padding: 0.85rem; border-radius: 8px; font-size: 0.8rem; overflow-x: auto; margin: 0; }

    /* Messages Tab */
    .messages-list { display: flex; flex-direction: column; gap: 0.85rem; }
    .message-card { background: #f8fafc; border: 1px solid #e2e8f0; border-radius: 12px; padding: 1rem; }
    .msg-header { display: flex; justify-content: space-between; align-items: center; margin-bottom: 0.5rem; }
    .msg-author { display: flex; align-items: center; gap: 0.5rem; }
    .msg-seq { font-weight: 700; color: #94a3b8; font-size: 0.8rem; }
    .agent-name { font-weight: 700; color: #0f172a; font-size: 0.9rem; }
    .role-tag { font-size: 0.7rem; background: #e2e8f0; color: #475569; padding: 0.15rem 0.4rem; border-radius: 4px; }
    .msg-time { font-size: 0.75rem; color: #94a3b8; }
    .content-pre { margin: 0; background: #ffffff; border: 1px solid #cbd5e1; border-radius: 8px; padding: 0.75rem; font-size: 0.85rem; color: #1e293b; white-space: pre-wrap; word-break: break-word; }

    /* Artifacts Tab */
    .artifacts-viewer { display: grid; grid-template-columns: 220px 1fr; gap: 1.5rem; min-height: 440px; }
    .artifacts-sidebar { border-right: 1px solid #e2e8f0; padding-right: 1rem; display: flex; flex-direction: column; gap: 0.5rem; overflow-y: auto; }
    .file-item { display: flex; align-items: center; gap: 0.6rem; padding: 0.6rem 0.8rem; border-radius: 8px; cursor: pointer; font-size: 0.85rem; color: #475569; border: 1px solid transparent; }
    .file-item:hover { background: #f8fafc; color: #0f172a; }
    .file-item.active { background: #eff6ff; color: #2563eb; border-color: #bfdbfe; font-weight: 600; }
    .file-info { display: flex; flex-direction: column; gap: 0.1rem; }
    .final-badge-small { font-size: 0.65rem; background: #dcfce7; color: #15803d; padding: 0.1rem 0.35rem; border-radius: 4px; font-weight: 700; width: fit-content; }

    .code-editor-container { display: flex; flex-direction: column; border: 1px solid #cbd5e1; border-radius: 12px; overflow: hidden; background: #0f172a; }
    .editor-header { display: flex; justify-content: space-between; align-items: center; padding: 0.6rem 1.25rem; background: #1e293b; border-bottom: 1px solid #334155; }
    .editor-title { display: flex; align-items: center; gap: 0.75rem; }
    .editor-filename { font-size: 0.85rem; font-weight: 600; color: #cbd5e1; font-family: monospace; }
    .final-badge { background: #22c55e; color: #ffffff; font-size: 0.7rem; font-weight: 700; padding: 0.2rem 0.5rem; border-radius: 6px; }
    .editor-actions { display: flex; gap: 0.5rem; }
    .copy-btn { background: #3b82f6; color: #ffffff; }
    .copy-btn:hover { background: #2563eb; }
    .download-btn { background: #475569; color: #cbd5e1; }
    .download-btn:hover { background: #334155; color: #ffffff; }

    .editor-body { flex: 1; overflow: auto; padding: 1rem; }
    .code-pre { margin: 0; font-family: 'Fira Code', 'Courier New', monospace; font-size: 0.8rem; line-height: 1.5; }
    .code-line { display: flex; }
    .line-number { width: 35px; color: #475569; text-align: right; padding-right: 0.75rem; user-select: none; border-right: 1px solid #334155; }
    .line-content { padding-left: 0.75rem; color: #e2e8f0; white-space: pre; }

    /* Modal */
    .modal-overlay { position: fixed; inset: 0; background: rgba(15, 23, 42, 0.5); display: flex; align-items: center; justify-content: center; z-index: 100; padding: 1rem; }
    .modal-card { background: #ffffff; border-radius: 16px; width: 100%; max-width: 440px; padding: 1.5rem; box-shadow: 0 20px 25px -5px rgba(0, 0, 0, 0.1); }
    .modal-header h3 { margin: 0 0 0.75rem 0; font-size: 1.1rem; color: #991b1b; }
    .modal-body p { margin: 0 0 0.5rem 0; font-size: 0.95rem; color: #0f172a; }
    .modal-subtext { font-size: 0.85rem !important; color: #64748b !important; }
    .modal-actions { display: flex; justify-content: flex-end; gap: 0.75rem; margin-top: 1.5rem; }
    .cancel-btn { background: #f1f5f9; color: #475569; border-color: #cbd5e1; }
    .confirm-delete-btn { background: #dc2626; color: #ffffff; }

    .loading-state { display: flex; flex-direction: column; align-items: center; padding: 5rem 2rem; color: #64748b; }
    .spinner-large { width: 32px; height: 32px; border: 3px solid rgba(59, 130, 246, 0.2); border-top-color: #3b82f6; border-radius: 50%; animation: spin 0.8s linear infinite; margin-bottom: 1rem; }
    .error-banner { display: flex; align-items: center; gap: 1rem; background: #fef2f2; border: 1px solid #fca5a5; border-radius: 12px; padding: 1rem; color: #991b1b; }
    .animate-fade-in { animation: fadeIn 0.3s ease forwards; }
    @keyframes spin { to { transform: rotate(360deg); } }
    @keyframes fadeIn { from { opacity: 0; transform: translateY(4px); } to { opacity: 1; transform: translateY(0); } }

    @media (max-width: 768px) {
      .artifacts-viewer { grid-template-columns: 1fr; }
      .artifacts-sidebar { border-right: none; border-bottom: 1px solid #e2e8f0; padding-bottom: 1rem; }
    }
  `]
})
export class HistoryDetailComponent implements OnInit {
  private readonly historyService = inject(HistoryService);

  @Input() workflowId: string | null = null;
  @Output() back = new EventEmitter<void>();
  @Output() runAgain = new EventEmitter<string>();
  @Output() deleted = new EventEmitter<void>();

  public readonly detail = signal<WorkflowDetail | null>(null);
  public readonly loading = signal(false);
  public readonly error = signal<string | null>(null);

  // UI state
  public readonly activeTab = signal<DetailTabType>('summary');
  public readonly activeFile = signal<StoredGeneratedFile | null>(null);
  public readonly copyConfirmation = signal<string | null>(null);
  public readonly showDeleteModal = signal(false);
  public readonly deleting = signal(false);

  // Collapsible iteration states
  public readonly expandedIters = signal<{ [key: number]: boolean }>({});

  ngOnInit() {
    if (this.workflowId) {
      this.loadWorkflowDetail(this.workflowId);
    }
  }

  loadWorkflowDetail(id: string) {
    this.loading.set(true);
    this.error.set(null);

    this.historyService.getWorkflow(id).subscribe({
      next: (data) => {
        this.detail.set(data);
        this.loading.set(false);

        // Auto select first file if available
        if (data.generated_files && data.generated_files.length > 0) {
          this.activeFile.set(data.generated_files[0]);
        }

        // Expand last iteration by default
        const expandMap: { [key: number]: boolean } = {};
        data.iterations.forEach((iter, idx) => {
          expandMap[iter.id] = idx === data.iterations.length - 1;
        });
        this.expandedIters.set(expandMap);
      },
      error: (err) => {
        this.error.set(err.message || 'Failed to load workflow details.');
        this.loading.set(false);
      },
    });
  }

  toggleIter(iterId: number) {
    this.expandedIters.update((map) => ({
      ...map,
      [iterId]: !map[iterId],
    }));
  }

  onBack() {
    this.back.emit();
  }

  onRunAgain() {
    if (this.detail()) {
      this.runAgain.emit(this.detail()!.prompt);
    }
  }

  toggleFavorite() {
    if (!this.detail() || !this.workflowId) return;

    const currentFav = this.detail()!.favorite;
    const action$ = currentFav
      ? this.historyService.removeFavorite(this.workflowId)
      : this.historyService.markFavorite(this.workflowId);

    action$.subscribe({
      next: (updated) => {
        this.detail.update((d) => (d ? { ...d, favorite: updated.favorite } : d));
      },
      error: (err) => alert('Failed to toggle favorite: ' + (err.message || 'Unknown error')),
    });
  }

  exportJson() {
    if (!this.workflowId) return;

    this.historyService.exportJson(this.workflowId).subscribe({
      next: (data) => {
        const jsonStr = JSON.stringify(data, null, 2);
        const blob = new Blob([jsonStr], { type: 'application/json' });
        const url = window.URL.createObjectURL(blob);
        const a = document.createElement('a');
        a.href = url;
        a.download = `workflow_${this.workflowId}.json`;
        a.click();
        window.URL.revokeObjectURL(url);
      },
      error: (err) => alert('Failed to export JSON: ' + (err.message || 'Unknown error')),
    });
  }

  downloadZip() {
    if (!this.workflowId) return;

    this.historyService.downloadZip(this.workflowId).subscribe({
      next: (blob) => {
        const url = window.URL.createObjectURL(blob);
        const a = document.createElement('a');
        a.href = url;
        a.download = `workflow_${this.workflowId}.zip`;
        a.click();
        window.URL.revokeObjectURL(url);
      },
      error: (err) => alert('Failed to download ZIP: ' + (err.message || 'Unknown error')),
    });
  }

  confirmDelete() {
    if (!this.workflowId) return;

    this.deleting.set(true);
    this.historyService.deleteWorkflow(this.workflowId).subscribe({
      next: () => {
        this.deleting.set(false);
        this.showDeleteModal.set(false);
        this.deleted.emit();
      },
      error: (err) => {
        this.deleting.set(false);
        alert('Failed to delete workflow: ' + (err.message || 'Unknown error'));
      },
    });
  }

  formatDate(dateStr: string): string {
    if (!dateStr) return 'N/A';
    try {
      const d = new Date(dateStr);
      return d.toLocaleString(undefined, {
        month: 'short',
        day: 'numeric',
        year: 'numeric',
        hour: '2-digit',
        minute: '2-digit',
      });
    } catch {
      return dateStr;
    }
  }

  formatStatus(status: string): string {
    switch (status) {
      case 'COMPLETE': return 'Complete';
      case 'NEEDS_ATTENTION': return 'Needs Attention';
      case 'FAILED': return 'Failed';
      case 'RUNNING': return 'Running';
      default: return status;
    }
  }

  formatAgentName(name: string): string {
    switch (name) {
      case 'manager_agent': return '📋 Manager Agent';
      case 'python_developer': return '💻 Python Developer';
      case 'code_reviewer': return '🔍 Code Reviewer';
      case 'tester_agent': return '🧪 Tester Agent';
      case 'documentation_agent': return '📝 Documentation Specialist';
      default: return name;
    }
  }

  getCodeLines(content: string): string[] {
    if (!content) return [];
    return content.split('\n');
  }

  copyCode(file: StoredGeneratedFile) {
    if (!file) return;
    navigator.clipboard
      .writeText(file.content)
      .then(() => {
        this.copyConfirmation.set(file.id);
        setTimeout(() => {
          if (this.copyConfirmation() === file.id) {
            this.copyConfirmation.set(null);
          }
        }, 2000);
      })
      .catch((err) => {
        console.error('Failed to copy code: ', err);
      });
  }

  downloadFile(file: StoredGeneratedFile) {
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
