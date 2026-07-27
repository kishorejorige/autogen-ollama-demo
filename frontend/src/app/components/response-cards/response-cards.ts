import { Component, Input } from '@angular/core';
import { CommonModule } from '@angular/common';
import { MessageResponse } from '../../models/chat.models';

@Component({
  selector: 'app-response-cards',
  standalone: true,
  imports: [CommonModule],
  template: `
    <div class="cards-list">
      <div *ngFor="let msg of messages; let idx = index" class="message-card" [ngClass]="getAgentClass(msg.source)">

        <!-- Card Header -->
        <div class="card-header">
          <div class="agent-info">
            <span class="agent-avatar">{{ getAgentAvatar(msg.source) }}</span>
            <div class="agent-details">
              <span class="agent-name">{{ formatAgentName(msg.source) }}</span>
              <span class="message-type" *ngIf="msg.type && msg.type !== 'TextMessage'">{{ msg.type }}</span>
            </div>
          </div>

          <div class="header-badges">
            <!-- Review status badge -->
            <span *ngIf="getReviewStatus(msg.content) as status" class="status-badge" [ngClass]="status">
              {{ status === 'APPROVED' ? '✅ APPROVED' : '⚠️ CHANGES REQUIRED' }}
            </span>

            <!-- Test status badge -->
            <span *ngIf="getTestStatus(msg.content) as status" class="status-badge" [ngClass]="status">
              {{ status === 'PASS' ? '✅ PASS' : '⚠️ FAIL' }}
            </span>

            <span class="timestamp" *ngIf="msg.created_at">{{ formatTimestamp(msg.created_at) }}</span>
          </div>
        </div>

        <!-- Card Body -->
        <div class="card-body">
          <div [ngClass]="{'code-block': msg.source === 'python_developer', 'pre-wrap': true}">
            {{ getCleanContent(msg.content) }}
          </div>
        </div>
      </div>
    </div>
  `,
  styles: [`
    .cards-list {
      display: flex;
      flex-direction: column;
      gap: 1.5rem;
    }
    .message-card {
      background: #ffffff;
      border: 1px solid #e2e8f0;
      border-radius: 16px;
      padding: 1.5rem;
      transition: all 0.3s ease;
      display: flex;
      flex-direction: column;
      gap: 1rem;
      box-shadow: 0 1px 3px rgba(0, 0, 0, 0.02), 0 4px 12px rgba(0, 0, 0, 0.03);
    }
    .message-card:hover {
      transform: translateY(-2px);
      box-shadow: 0 10px 25px rgba(0, 0, 0, 0.05);
      border-color: #cbd5e1;
    }
    .card-header {
      display: flex;
      justify-content: space-between;
      align-items: center;
      flex-wrap: wrap;
      gap: 0.75rem;
      border-bottom: 1px solid #f1f5f9;
      padding-bottom: 0.75rem;
    }
    .agent-info {
      display: flex;
      align-items: center;
      gap: 0.75rem;
    }
    .agent-avatar {
      font-size: 1.4rem;
      width: 38px;
      height: 38px;
      background: #f8fafc;
      border-radius: 10px;
      display: flex;
      align-items: center;
      justify-content: center;
      border: 1px solid #e2e8f0;
    }
    .agent-details {
      display: flex;
      flex-direction: column;
      gap: 0.15rem;
    }
    .agent-name {
      font-weight: 600;
      color: #0f172a;
      font-size: 0.95rem;
    }
    .message-type {
      font-size: 0.75rem;
      color: #64748b;
      font-weight: 500;
      text-transform: uppercase;
      letter-spacing: 0.05em;
    }
    .header-badges {
      display: flex;
      align-items: center;
      gap: 0.75rem;
    }
    .status-badge {
      font-size: 0.75rem;
      font-weight: 700;
      padding: 0.25rem 0.65rem;
      border-radius: 6px;
      letter-spacing: 0.02em;
    }
    .status-badge.APPROVED {
      background: #d1fae5;
      color: #065f46;
      border: 1px solid #a7f3d0;
    }
    .status-badge.CHANGES_REQUIRED {
      background: #fee2e2;
      color: #991b1b;
      border: 1px solid #fca5a5;
    }
    .status-badge.PASS {
      background: #d1fae5;
      color: #065f46;
      border: 1px solid #a7f3d0;
    }
    .status-badge.FAIL {
      background: #fee2e2;
      color: #991b1b;
      border: 1px solid #fca5a5;
    }
    .timestamp {
      font-size: 0.75rem;
      color: #94a3b8;
      font-weight: 500;
    }
    .card-body {
      font-size: 0.95rem;
      color: #334155;
      line-height: 1.6;
    }
    .pre-wrap {
      white-space: pre-wrap;
      word-break: break-word;
    }
    .code-block {
      font-family: 'Fira Code', 'Courier New', Courier, monospace;
      background: #f8fafc;
      padding: 1.25rem;
      border-radius: 12px;
      border: 1px solid #e2e8f0;
      color: #0f172a;
      font-size: 0.85rem;
      max-height: 400px;
      overflow-y: auto;
    }

    /* Agent specific highlights */
    .manager {
      border-left: 4px solid #3b82f6;
    }
    .manager .agent-avatar {
      background: #eff6ff;
      border-color: #bfdbfe;
    }
    .developer {
      border-left: 4px solid #10b981;
    }
    .developer .agent-avatar {
      background: #ecfdf5;
      border-color: #a7f3d0;
    }
    .reviewer {
      border-left: 4px solid #ef4444;
    }
    .reviewer .agent-avatar {
      background: #fef2f2;
      border-color: #fca5a5;
    }
    .tester {
      border-left: 4px solid #f59e0b;
    }
    .tester .agent-avatar {
      background: #fffbeb;
      border-color: #fde68a;
    }
    .documenter {
      border-left: 4px solid #8b5cf6;
    }
    .documenter .agent-avatar {
      background: #f5f3ff;
      border-color: #ddd6fe;
    }
    .system {
      background: #f8fafc;
      border: 1px dashed #cbd5e1;
      font-style: italic;
    }
    .system .agent-avatar {
      background: #f1f5f9;
    }
  `]
})
export class ResponseCards {
  @Input() messages: MessageResponse[] = [];

  formatAgentName(source: string): string {
    if (!source) return 'Agent';
    return source
      .split('_')
      .map(word => word.charAt(0).toUpperCase() + word.slice(1))
      .join(' ');
  }

  getAgentClass(source: string): string {
    switch (source) {
      case 'manager_agent': return 'manager';
      case 'python_developer': return 'developer';
      case 'code_reviewer': return 'reviewer';
      case 'tester_agent': return 'tester';
      case 'documentation_agent': return 'documenter';
      case 'system': return 'system';
      default: return '';
    }
  }

  getAgentAvatar(source: string): string {
    switch (source) {
      case 'manager_agent': return '📋';
      case 'python_developer': return '💻';
      case 'code_reviewer': return '🔍';
      case 'tester_agent': return '🧪';
      case 'documentation_agent': return '📝';
      case 'system': return '⚙️';
      case 'user': return '👤';
      default: return '🤖';
    }
  }

  getReviewStatus(content: string): 'APPROVED' | 'CHANGES_REQUIRED' | null {
    if (!content) return null;
    if (content.includes('Review status: APPROVED')) return 'APPROVED';
    if (content.includes('Review status: CHANGES_REQUIRED')) return 'CHANGES_REQUIRED';
    return null;
  }

  getTestStatus(content: string): 'PASS' | 'FAIL' | null {
    if (!content) return null;
    if (content.includes('Test status: PASS')) return 'PASS';
    if (content.includes('Test status: FAIL')) return 'FAIL';
    return null;
  }

  getCleanContent(content: string): string {
    if (!content) return '';
    return content;
  }

  formatTimestamp(isoStr: string): string {
    try {
      const d = new Date(isoStr);
      if (isNaN(d.getTime())) return '';
      return d.toLocaleTimeString([], { hour: '2-digit', minute: '2-digit', second: '2-digit' });
    } catch {
      return '';
    }
  }
}
