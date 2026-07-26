import { Component, inject, OnInit, OnDestroy, signal } from '@angular/core';
import { CommonModule } from '@angular/common';
import { ApiService } from '../../services/api.service';
import { Subscription, interval } from 'rxjs';
import { startWith, switchMap } from 'rxjs/operators';

@Component({
  selector: 'app-health-status',
  standalone: true,
  imports: [CommonModule],
  template: `
    <div class="health-container" [ngClass]="status()">
      <span class="dot"></span>
      <span class="label">Backend: {{ statusText() }}</span>
    </div>
  `,
  styles: [`
    .health-container {
      display: inline-flex;
      align-items: center;
      gap: 0.5rem;
      padding: 0.4rem 0.85rem;
      border-radius: 9999px;
      font-size: 0.8rem;
      font-weight: 600;
      transition: all 0.3s ease;
      background: #f1f5f9;
      border: 1px solid #e2e8f0;
    }
    .dot {
      width: 8px;
      height: 8px;
      border-radius: 50%;
      background-color: #f59e0b;
      box-shadow: 0 0 6px #f59e0b;
      transition: all 0.3s ease;
    }
    .label {
      color: #64748b;
      letter-spacing: 0.02em;
    }
    .HEALTHY {
      border-color: #a7f3d0;
      background: #ecfdf5;
    }
    .HEALTHY .dot {
      background-color: #10b981;
      box-shadow: 0 0 8px #10b981;
    }
    .HEALTHY .label {
      color: #065f46;
    }
    .UNHEALTHY, .UNREACHABLE {
      border-color: #fca5a5;
      background: #fef2f2;
    }
    .UNHEALTHY .dot, .UNREACHABLE .dot {
      background-color: #ef4444;
      box-shadow: 0 0 8px #ef4444;
    }
    .UNHEALTHY .label, .UNREACHABLE .label {
      color: #991b1b;
    }
  `]
})
export class HealthStatus implements OnInit, OnDestroy {
  private readonly apiService = inject(ApiService);
  public readonly status = signal<'CONNECTING' | 'HEALTHY' | 'UNREACHABLE'>('CONNECTING');
  private pollSub?: Subscription;

  statusText(): string {
    switch (this.status()) {
      case 'HEALTHY': return 'Online';
      case 'UNREACHABLE': return 'Offline';
      default: return 'Connecting...';
    }
  }

  ngOnInit() {
    this.pollSub = interval(10000).pipe(
      startWith(0),
      switchMap(() => this.apiService.getHealth())
    ).subscribe({
      next: (res) => {
        this.status.set(res.status === 'healthy' ? 'HEALTHY' : 'UNREACHABLE');
      },
      error: () => {
        this.status.set('UNREACHABLE');
      }
    });
  }

  ngOnDestroy() {
    this.pollSub?.unsubscribe();
  }
}
