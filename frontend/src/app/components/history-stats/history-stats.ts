import { Component, Input } from '@angular/core';
import { CommonModule } from '@angular/common';
import { WorkflowStats } from '../../models/chat.models';

@Component({
  selector: 'app-history-stats',
  standalone: true,
  imports: [CommonModule],
  template: `
    <div class="stats-grid animate-fade-in" *ngIf="stats">
      <div class="stat-card total">
        <div class="stat-icon">📊</div>
        <div class="stat-details">
          <span class="stat-label">Total Workflows</span>
          <span class="stat-value">{{ stats.total_workflows }}</span>
        </div>
      </div>

      <div class="stat-card completed">
        <div class="stat-icon">✓</div>
        <div class="stat-details">
          <span class="stat-label">Completed</span>
          <span class="stat-value">{{ stats.completed_workflows }}</span>
        </div>
      </div>

      <div class="stat-card failed">
        <div class="stat-icon">✗</div>
        <div class="stat-details">
          <span class="stat-label">Failed</span>
          <span class="stat-value">{{ stats.failed_workflows }}</span>
        </div>
      </div>

      <div class="stat-card needs-attention">
        <div class="stat-icon">⚠️</div>
        <div class="stat-details">
          <span class="stat-label">Needs Attention</span>
          <span class="stat-value">{{ stats.needs_attention_workflows }}</span>
        </div>
      </div>

      <div class="stat-card favorites">
        <div class="stat-icon">⭐</div>
        <div class="stat-details">
          <span class="stat-label">Favorites</span>
          <span class="stat-value">{{ stats.favorite_count || 0 }}</span>
        </div>
      </div>

      <div class="stat-card avg-iterations">
        <div class="stat-icon">🔄</div>
        <div class="stat-details">
          <span class="stat-label">Avg Iterations</span>
          <span class="stat-value">{{ stats.average_iterations || 0 }}</span>
        </div>
      </div>
    </div>
  `,
  styles: [`
    .stats-grid {
      display: grid;
      grid-template-columns: repeat(auto-fit, minmax(160px, 1fr));
      gap: 1rem;
      margin-bottom: 1.5rem;
    }
    .stat-card {
      background: #ffffff;
      border: 1px solid #e2e8f0;
      border-radius: 12px;
      padding: 1rem;
      display: flex;
      align-items: center;
      gap: 1rem;
      box-shadow: 0 1px 3px rgba(0, 0, 0, 0.02);
      transition: transform 0.2s ease, box-shadow 0.2s ease;
    }
    .stat-card:hover {
      transform: translateY(-2px);
      box-shadow: 0 4px 12px rgba(0, 0, 0, 0.05);
    }
    .stat-icon {
      font-size: 1.5rem;
      width: 42px;
      height: 42px;
      border-radius: 10px;
      display: flex;
      align-items: center;
      justify-content: center;
      background: #f1f5f9;
    }
    .total .stat-icon { background: #eff6ff; color: #2563eb; }
    .completed .stat-icon { background: #ecfdf5; color: #059669; }
    .failed .stat-icon { background: #fef2f2; color: #dc2626; }
    .needs-attention .stat-icon { background: #fffbeb; color: #d97706; }
    .favorites .stat-icon { background: #fef9c3; color: #ca8a04; }
    .avg-iterations .stat-icon { background: #f3e8ff; color: #9333ea; }

    .stat-details {
      display: flex;
      flex-direction: column;
    }
    .stat-label {
      font-size: 0.75rem;
      font-weight: 600;
      color: #64748b;
      text-transform: uppercase;
      letter-spacing: 0.04em;
    }
    .stat-value {
      font-size: 1.4rem;
      font-weight: 700;
      color: #0f172a;
    }
    .animate-fade-in {
      animation: fadeIn 0.3s ease forwards;
    }
    @keyframes fadeIn {
      from { opacity: 0; transform: translateY(4px); }
      to { opacity: 1; transform: translateY(0); }
    }
  `]
})
export class HistoryStatsComponent {
  @Input() stats: WorkflowStats | null = null;
}
