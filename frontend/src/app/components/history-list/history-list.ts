import { Component, EventEmitter, inject, OnInit, Output, signal } from '@angular/core';
import { CommonModule } from '@angular/common';
import { HistoryService } from '../../services/history.service';
import { WorkflowStats, WorkflowSummary } from '../../models/chat.models';
import { HistoryStatsComponent } from '../history-stats/history-stats';

@Component({
  selector: 'app-history-list',
  standalone: true,
  imports: [CommonModule, HistoryStatsComponent],
  template: `
    <div class="history-list-container">
      <!-- Stats summary banner -->
      <app-history-stats [stats]="stats()"></app-history-stats>

      <!-- Filter Controls Bar -->
      <div class="controls-bar">
        <div class="search-box">
          <span class="search-icon">🔍</span>
          <input
            type="text"
            placeholder="Search workflows by prompt..."
            [value]="searchQuery()"
            (input)="onSearchInput($event)"
            class="search-input"
          />
        </div>

        <div class="filter-group">
          <select [value]="statusFilter()" (change)="onStatusFilterChange($event)" class="filter-select">
            <option value="">All Statuses</option>
            <option value="COMPLETE">✓ Complete</option>
            <option value="NEEDS_ATTENTION">⚠️ Needs Attention</option>
            <option value="FAILED">✗ Failed</option>
            <option value="RUNNING">🔄 Running</option>
          </select>

          <select [value]="dateRangeFilter()" (change)="onDateRangeFilterChange($event)" class="filter-select date-filter">
            <option value="">All Time</option>
            <option value="today">Today</option>
            <option value="7d">Last 7 Days</option>
            <option value="30d">Last 30 Days</option>
          </select>

          <button class="action-btn refresh-btn" (click)="loadData()" [disabled]="loading()">
            <span [class.spinner]="loading()">🔄</span> Refresh
          </button>
        </div>
      </div>

      <!-- Error State -->
      <div class="error-banner animate-fade-in" *ngIf="error()">
        <span class="error-icon">⚠️</span>
        <div class="error-text">
          <strong>Failed to load history</strong>
          <p>{{ error() }}</p>
        </div>
        <button class="action-btn retry-btn" (click)="loadData()">Retry</button>
      </div>

      <!-- Loading State -->
      <div class="loading-state animate-fade-in" *ngIf="loading() && workflows().length === 0">
        <div class="spinner-large"></div>
        <p>Loading workflow history...</p>
      </div>

      <!-- Empty State -->
      <div class="empty-state animate-fade-in" *ngIf="!loading() && !error() && workflows().length === 0">
        <div class="empty-icon">📜</div>
        <h4>No workflows found</h4>
        <p *ngIf="searchQuery() || statusFilter() || dateRangeFilter()">Try adjusting your search query or filters.</p>
        <p *ngIf="!searchQuery() && !statusFilter() && !dateRangeFilter()">Run a workflow in the "New Workflow" tab to see history here.</p>
      </div>

      <!-- Workflows List / Cards -->
      <div class="workflows-list animate-fade-in" *ngIf="workflows().length > 0">
        <div class="workflow-card" *ngFor="let wf of workflows()">
          <div class="card-left">
            <div class="badge-wrapper">
              <span class="status-badge" [ngClass]="wf.status.toLowerCase()">
                <span class="status-icon" *ngIf="wf.status === 'COMPLETE'">✓</span>
                <span class="status-icon" *ngIf="wf.status === 'NEEDS_ATTENTION'">⚠️</span>
                <span class="status-icon" *ngIf="wf.status === 'FAILED'">✗</span>
                <span class="status-icon" *ngIf="wf.status === 'RUNNING'">🔄</span>
                {{ formatStatus(wf.status) }}
              </span>

              <button
                class="fav-toggle-btn"
                [class.is-fav]="wf.favorite"
                (click)="toggleFavorite($event, wf)"
                [title]="wf.favorite ? 'Remove Favorite' : 'Mark as Favorite'"
              >
                {{ wf.favorite ? '⭐' : '☆' }}
              </button>
            </div>
            <h3 class="workflow-prompt" (click)="onOpenDetail(wf.id)">{{ wf.prompt }}</h3>
            <div class="workflow-meta">
              <span>📅 {{ formatDate(wf.created_at) }}</span>
              <span>🔄 {{ wf.total_iterations }} Iteration{{ wf.total_iterations === 1 ? '' : 's' }}</span>
              <span>📦 {{ wf.generated_file_count }} File{{ wf.generated_file_count === 1 ? '' : 's' }}</span>
            </div>
          </div>

          <div class="card-actions">
            <button class="action-btn open-btn" (click)="onOpenDetail(wf.id)">
              📖 Open Detail
            </button>
            <button class="action-btn run-again-btn" (click)="onRunAgain(wf.prompt)">
              ⚡ Run Again
            </button>
            <div class="export-dropdown">
              <button class="action-btn export-btn" (click)="toggleExportMenu($event, wf.id)">
                📥 Export ▾
              </button>
              <div class="export-menu animate-fade-in" *ngIf="activeExportId() === wf.id">
                <button class="menu-item" (click)="onExportJson($event, wf.id)">📄 Export JSON</button>
                <button class="menu-item" (click)="onDownloadZip($event, wf.id)">📦 Download ZIP</button>
              </div>
            </div>
          </div>
        </div>
      </div>

      <!-- Pagination -->
      <div class="pagination-bar" *ngIf="totalCount() > limit()">
        <span class="pagination-info">
          Showing {{ offset() + 1 }} - {{ getEndIndex() }} of {{ totalCount() }}
        </span>
        <div class="pagination-buttons">
          <button
            class="action-btn page-btn"
            [disabled]="offset() === 0 || loading()"
            (click)="prevPage()"
          >
            ← Previous
          </button>
          <button
            class="action-btn page-btn"
            [disabled]="offset() + limit() >= totalCount() || loading()"
            (click)="nextPage()"
          >
            Next →
          </button>
        </div>
      </div>
    </div>
  `,
  styles: [`
    .history-list-container {
      display: flex;
      flex-direction: column;
      gap: 1.25rem;
    }
    .controls-bar {
      display: flex;
      justify-content: space-between;
      align-items: center;
      gap: 1rem;
      flex-wrap: wrap;
    }
    .search-box {
      display: flex;
      align-items: center;
      gap: 0.5rem;
      background: #ffffff;
      border: 1px solid #cbd5e1;
      border-radius: 10px;
      padding: 0.5rem 0.85rem;
      flex: 1;
      min-width: 260px;
      box-shadow: 0 1px 2px rgba(0, 0, 0, 0.03);
    }
    .search-icon {
      color: #94a3b8;
    }
    .search-input {
      border: none;
      outline: none;
      width: 100%;
      font-size: 0.9rem;
      color: #0f172a;
    }
    .filter-group {
      display: flex;
      gap: 0.75rem;
      align-items: center;
    }
    .filter-select {
      background: #ffffff;
      border: 1px solid #cbd5e1;
      border-radius: 10px;
      padding: 0.55rem 0.85rem;
      font-size: 0.85rem;
      color: #0f172a;
      font-weight: 500;
      outline: none;
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
    .refresh-btn {
      background: #f1f5f9;
      color: #475569;
      border-color: #cbd5e1;
    }
    .refresh-btn:hover {
      background: #e2e8f0;
      color: #0f172a;
    }
    .open-btn {
      background: #eff6ff;
      color: #2563eb;
      border-color: #bfdbfe;
    }
    .open-btn:hover {
      background: #dbeafe;
    }
    .run-again-btn {
      background: #f0fdf4;
      color: #16a34a;
      border-color: #bbf7d0;
    }
    .run-again-btn:hover {
      background: #dcfce7;
    }
    .retry-btn {
      background: #dc2626;
      color: #ffffff;
    }
    .page-btn {
      background: #ffffff;
      border-color: #cbd5e1;
      color: #475569;
    }
    .page-btn:disabled {
      opacity: 0.5;
      cursor: not-allowed;
    }

    .error-banner {
      display: flex;
      align-items: center;
      gap: 1rem;
      background: #fef2f2;
      border: 1px solid #fca5a5;
      border-radius: 12px;
      padding: 1rem;
      color: #991b1b;
    }
    .error-icon { font-size: 1.3rem; }
    .error-text { flex: 1; }
    .error-text strong { display: block; font-size: 0.9rem; }
    .error-text p { margin: 0.2rem 0 0 0; font-size: 0.85rem; }

    .loading-state, .empty-state {
      display: flex;
      flex-direction: column;
      align-items: center;
      justify-content: center;
      padding: 4rem 2rem;
      background: #ffffff;
      border: 1px solid #e2e8f0;
      border-radius: 16px;
      text-align: center;
      color: #64748b;
    }
    .empty-icon { font-size: 3rem; margin-bottom: 0.5rem; }
    .empty-state h4 { margin: 0; color: #334155; font-size: 1.1rem; }
    .empty-state p { margin: 0.3rem 0 0 0; font-size: 0.85rem; }

    .spinner-large {
      width: 32px;
      height: 32px;
      border: 3px solid rgba(59, 130, 246, 0.2);
      border-top-color: #3b82f6;
      border-radius: 50%;
      animation: spin 0.8s linear infinite;
      margin-bottom: 1rem;
    }

    .workflows-list {
      display: flex;
      flex-direction: column;
      gap: 0.85rem;
    }
    .workflow-card {
      background: #ffffff;
      border: 1px solid #e2e8f0;
      border-radius: 14px;
      padding: 1.15rem;
      display: flex;
      justify-content: space-between;
      align-items: center;
      gap: 1rem;
      box-shadow: 0 1px 3px rgba(0, 0, 0, 0.02);
      transition: all 0.2s ease;
    }
    .workflow-card:hover {
      border-color: #bfdbfe;
      box-shadow: 0 4px 12px rgba(59, 130, 246, 0.08);
    }
    .card-left {
      display: flex;
      flex-direction: column;
      gap: 0.4rem;
      flex: 1;
    }
    .workflow-prompt {
      margin: 0;
      font-size: 1rem;
      font-weight: 600;
      color: #0f172a;
      cursor: pointer;
    }
    .workflow-prompt:hover {
      color: #2563eb;
    }
    .workflow-meta {
      display: flex;
      gap: 1rem;
      font-size: 0.8rem;
      color: #64748b;
      flex-wrap: wrap;
    }
    .card-actions {
      display: flex;
      gap: 0.5rem;
    }

    .badge-wrapper {
      display: flex;
      align-items: center;
      gap: 0.5rem;
    }
    .fav-toggle-btn {
      background: none;
      border: none;
      font-size: 1.1rem;
      cursor: pointer;
      padding: 0.1rem 0.3rem;
      border-radius: 4px;
      transition: transform 0.2s ease;
      color: #94a3b8;
    }
    .fav-toggle-btn:hover {
      transform: scale(1.2);
    }
    .fav-toggle-btn.is-fav {
      color: #eab308;
    }
    .export-dropdown {
      position: relative;
      display: inline-block;
    }
    .export-btn {
      background: #f8fafc;
      color: #475569;
      border-color: #cbd5e1;
    }
    .export-btn:hover {
      background: #f1f5f9;
      color: #0f172a;
    }
    .export-menu {
      position: absolute;
      right: 0;
      top: 100%;
      margin-top: 0.35rem;
      background: #ffffff;
      border: 1px solid #cbd5e1;
      border-radius: 10px;
      box-shadow: 0 10px 15px -3px rgba(0, 0, 0, 0.1), 0 4px 6px -2px rgba(0, 0, 0, 0.05);
      z-index: 50;
      display: flex;
      flex-direction: column;
      min-width: 150px;
      overflow: hidden;
    }
    .menu-item {
      padding: 0.6rem 0.85rem;
      background: none;
      border: none;
      text-align: left;
      font-size: 0.82rem;
      font-weight: 600;
      color: #334155;
      cursor: pointer;
      transition: background 0.15s ease;
    }
    .menu-item:hover {
      background: #eff6ff;
      color: #2563eb;
    }

    .status-badge {
      display: inline-flex;
      align-items: center;
      gap: 0.3rem;
      font-size: 0.72rem;
      font-weight: 700;
      padding: 0.2rem 0.55rem;
      border-radius: 9999px;
      text-transform: uppercase;
      letter-spacing: 0.04em;
    }
    .status-badge.complete { background: #ecfdf5; color: #059669; }
    .status-badge.needs_attention { background: #fffbeb; color: #d97706; }
    .status-badge.failed { background: #fef2f2; color: #dc2626; }
    .status-badge.running { background: #eff6ff; color: #2563eb; }

    .pagination-bar {
      display: flex;
      justify-content: space-between;
      align-items: center;
      padding: 0.75rem 0.25rem;
      font-size: 0.85rem;
      color: #64748b;
    }
    .pagination-buttons { display: flex; gap: 0.5rem; }

    .spinner {
      display: inline-block;
      animation: spin 1s linear infinite;
    }
    .animate-fade-in {
      animation: fadeIn 0.3s ease forwards;
    }
    @keyframes spin { to { transform: rotate(360deg); } }
    @keyframes fadeIn {
      from { opacity: 0; transform: translateY(4px); }
      to { opacity: 1; transform: translateY(0); }
    }

    @media (max-width: 640px) {
      .workflow-card {
        flex-direction: column;
        align-items: flex-start;
      }
      .card-actions {
        width: 100%;
        justify-content: flex-end;
      }
    }
  `]
})
export class HistoryListComponent implements OnInit {
  private readonly historyService = inject(HistoryService);

  @Output() selectWorkflow = new EventEmitter<string>();
  @Output() runAgain = new EventEmitter<string>();

  public readonly workflows = signal<WorkflowSummary[]>([]);
  public readonly stats = signal<WorkflowStats | null>(null);
  public readonly loading = signal(false);
  public readonly error = signal<string | null>(null);

  // Filter params
  public readonly searchQuery = signal('');
  public readonly statusFilter = signal('');
  public readonly dateRangeFilter = signal('');
  public readonly activeExportId = signal<string | null>(null);
  public readonly limit = signal(10);
  public readonly offset = signal(0);
  public readonly totalCount = signal(0);

  private searchDebounceTimer: any = null;

  ngOnInit() {
    this.loadData();
  }

  loadData() {
    this.loading.set(true);
    this.error.set(null);

    // Fetch stats
    this.historyService.getStats().subscribe({
      next: (s) => this.stats.set(s),
      error: (e) => console.error('Failed to load stats:', e),
    });

    // Fetch workflows
    this.historyService
      .listWorkflows({
        limit: this.limit(),
        offset: this.offset(),
        search: this.searchQuery(),
        status: this.statusFilter(),
        date_range: this.dateRangeFilter(),
      })
      .subscribe({
        next: (res) => {
          this.workflows.set(res.items);
          this.totalCount.set(res.total);
          this.loading.set(false);
        },
        error: (err) => {
          this.error.set(err.message || 'Failed to fetch workflow history.');
          this.loading.set(false);
        },
      });
  }

  onSearchInput(event: Event) {
    const val = (event.target as HTMLInputElement).value;
    this.searchQuery.set(val);
    this.offset.set(0);

    if (this.searchDebounceTimer) {
      clearTimeout(this.searchDebounceTimer);
    }
    this.searchDebounceTimer = setTimeout(() => {
      this.loadData();
    }, 350);
  }

  onStatusFilterChange(event: Event) {
    const val = (event.target as HTMLSelectElement).value;
    this.statusFilter.set(val);
    this.offset.set(0);
    this.loadData();
  }

  onDateRangeFilterChange(event: Event) {
    const val = (event.target as HTMLSelectElement).value;
    this.dateRangeFilter.set(val);
    this.offset.set(0);
    this.loadData();
  }

  toggleFavorite(event: Event, wf: WorkflowSummary) {
    event.stopPropagation();
    const action$ = wf.favorite
      ? this.historyService.removeFavorite(wf.id)
      : this.historyService.markFavorite(wf.id);

    action$.subscribe({
      next: (updated) => {
        wf.favorite = updated.favorite;
        // Refresh stats
        this.historyService.getStats().subscribe({
          next: (s) => this.stats.set(s),
        });
      },
      error: (err) => console.error('Failed to toggle favorite:', err),
    });
  }

  toggleExportMenu(event: Event, workflowId: string) {
    event.stopPropagation();
    if (this.activeExportId() === workflowId) {
      this.activeExportId.set(null);
    } else {
      this.activeExportId.set(workflowId);
    }
  }

  onExportJson(event: Event, workflowId: string) {
    event.stopPropagation();
    this.activeExportId.set(null);
    this.historyService.exportJson(workflowId).subscribe({
      next: (data) => {
        const jsonStr = JSON.stringify(data, null, 2);
        const blob = new Blob([jsonStr], { type: 'application/json' });
        const url = window.URL.createObjectURL(blob);
        const a = document.createElement('a');
        a.href = url;
        a.download = `workflow_${workflowId}.json`;
        a.click();
        window.URL.revokeObjectURL(url);
      },
      error: (err) => alert('Failed to export JSON: ' + (err.message || 'Unknown error')),
    });
  }

  onDownloadZip(event: Event, workflowId: string) {
    event.stopPropagation();
    this.activeExportId.set(null);
    this.historyService.downloadZip(workflowId).subscribe({
      next: (blob) => {
        const url = window.URL.createObjectURL(blob);
        const a = document.createElement('a');
        a.href = url;
        a.download = `workflow_${workflowId}.zip`;
        a.click();
        window.URL.revokeObjectURL(url);
      },
      error: (err) => alert('Failed to download ZIP: ' + (err.message || 'Unknown error')),
    });
  }

  prevPage() {
    const newOffset = Math.max(0, this.offset() - this.limit());
    this.offset.set(newOffset);
    this.loadData();
  }

  nextPage() {
    if (this.offset() + this.limit() < this.totalCount()) {
      this.offset.set(this.offset() + this.limit());
      this.loadData();
    }
  }

  getEndIndex(): number {
    return Math.min(this.offset() + this.limit(), this.totalCount());
  }

  onOpenDetail(id: string) {
    this.selectWorkflow.emit(id);
  }

  onRunAgain(prompt: string) {
    this.runAgain.emit(prompt);
  }

  formatDate(dateStr: string): string {
    if (!dateStr) return 'N/A';
    try {
      const d = new Date(dateStr);
      return d.toLocaleDateString(undefined, {
        month: 'short',
        day: 'numeric',
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
}
