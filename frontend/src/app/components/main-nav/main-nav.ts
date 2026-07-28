import { Component, EventEmitter, Input, Output } from '@angular/core';
import { CommonModule } from '@angular/common';

export type ActiveTabType = 'new_workflow' | 'generated_files' | 'history';

@Component({
  selector: 'app-main-nav',
  standalone: true,
  imports: [CommonModule],
  template: `
    <nav class="main-nav">
      <button
        class="nav-tab-btn"
        [class.active]="activeTab === 'new_workflow'"
        (click)="selectTab('new_workflow')"
      >
        <span class="tab-icon">⚡</span>
        <span class="tab-label">New Workflow</span>
      </button>

      <button
        class="nav-tab-btn"
        [class.active]="activeTab === 'generated_files'"
        (click)="selectTab('generated_files')"
      >
        <span class="tab-icon">📦</span>
        <span class="tab-label">Generated Files</span>
        <span class="badge" *ngIf="artifactCount > 0">{{ artifactCount }}</span>
      </button>

      <button
        class="nav-tab-btn"
        [class.active]="activeTab === 'history'"
        (click)="selectTab('history')"
      >
        <span class="tab-icon">📜</span>
        <span class="tab-label">History & Memory</span>
      </button>
    </nav>
  `,
  styles: [`
    .main-nav {
      display: flex;
      gap: 0.5rem;
      background: #f8fafc;
      padding: 0.35rem;
      border-radius: 12px;
      border: 1px solid #e2e8f0;
      width: fit-content;
    }
    .nav-tab-btn {
      display: flex;
      align-items: center;
      gap: 0.5rem;
      background: transparent;
      border: none;
      padding: 0.5rem 1rem;
      border-radius: 8px;
      font-size: 0.9rem;
      font-weight: 600;
      color: #64748b;
      cursor: pointer;
      transition: all 0.2s ease;
    }
    .nav-tab-btn:hover {
      color: #0f172a;
      background: #ffffff;
    }
    .nav-tab-btn.active {
      background: #ffffff;
      color: #2563eb;
      box-shadow: 0 1px 3px rgba(0, 0, 0, 0.08);
    }
    .badge {
      background: #3b82f6;
      color: #ffffff;
      font-size: 0.75rem;
      font-weight: 700;
      padding: 0.15rem 0.45rem;
      border-radius: 9999px;
    }
    @media (max-width: 640px) {
      .main-nav {
        width: 100%;
        justify-content: space-between;
      }
      .nav-tab-btn {
        padding: 0.5rem 0.65rem;
        font-size: 0.8rem;
      }
    }
  `]
})
export class MainNavComponent {
  @Input() activeTab: ActiveTabType = 'new_workflow';
  @Input() artifactCount = 0;
  @Output() tabChange = new EventEmitter<ActiveTabType>();

  selectTab(tab: ActiveTabType) {
    this.tabChange.emit(tab);
  }
}
