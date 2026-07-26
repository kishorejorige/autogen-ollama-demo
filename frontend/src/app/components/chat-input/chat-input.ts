import { Component, EventEmitter, Input, Output, signal } from '@angular/core';
import { CommonModule } from '@angular/common';
import { FormsModule } from '@angular/forms';

@Component({
  selector: 'app-chat-input',
  standalone: true,
  imports: [CommonModule, FormsModule],
  template: `
    <div class="input-card">
      <div class="card-header">
        <h3>1. Describe Your Task</h3>
        <span class="char-counter" [ngClass]="{ 'limit-reached': text().length >= maxChars }">
          {{ text().length }} / {{ maxChars }} chars
        </span>
      </div>
      
      <div class="textarea-wrapper">
        <textarea
          [(ngModel)]="rawText"
          (ngModelChange)="onTextChange($event)"
          [disabled]="disabled"
          [maxLength]="maxChars"
          placeholder="Enter a prompt for the AI agent team (e.g. 'Write a Python script that fetches weather updates and outputs a clean JSON file...')"
          rows="4"
        ></textarea>
      </div>

      <div class="actions">
        <button
          class="btn btn-primary"
          (click)="onRun()"
          [disabled]="disabled || !text().trim()"
        >
          <span class="icon">🚀</span> Run Workflow
        </button>
        
        <button
          class="btn btn-secondary"
          (click)="onClear()"
          [disabled]="disabled || !text().trim()"
        >
          <span class="icon">🗑️</span> Clear Input
        </button>
      </div>
    </div>
  `,
  styles: [`
    .input-card {
      background: #ffffff;
      border: 1px solid #e2e8f0;
      border-radius: 16px;
      padding: 1.5rem;
      display: flex;
      flex-direction: column;
      gap: 1rem;
      box-shadow: 0 1px 3px rgba(0, 0, 0, 0.02), 0 4px 12px rgba(0, 0, 0, 0.03);
    }
    .card-header {
      display: flex;
      justify-content: space-between;
      align-items: center;
      border-bottom: 1px solid #f1f5f9;
      padding-bottom: 0.5rem;
    }
    .card-header h3 {
      font-size: 1rem;
      font-weight: 600;
      color: #0f172a;
      margin: 0;
    }
    .char-counter {
      font-size: 0.8rem;
      color: #64748b;
      font-weight: 500;
    }
    .char-counter.limit-reached {
      color: #ef4444;
    }
    .textarea-wrapper textarea {
      width: 100%;
      background: #f8fafc;
      border: 1px solid #cbd5e1;
      border-radius: 10px;
      color: #0f172a;
      padding: 1rem;
      font-family: inherit;
      font-size: 0.95rem;
      line-height: 1.5;
      resize: vertical;
      outline: none;
      box-sizing: border-box;
      transition: border-color 0.2s ease, box-shadow 0.2s ease;
    }
    .textarea-wrapper textarea:focus {
      border-color: #3b82f6;
      box-shadow: 0 0 0 3px rgba(59, 130, 246, 0.15);
      background: #ffffff;
    }
    .textarea-wrapper textarea::placeholder {
      color: #94a3b8;
    }
    .textarea-wrapper textarea:disabled {
      opacity: 0.6;
      cursor: not-allowed;
      background: #f1f5f9;
    }
    .actions {
      display: flex;
      gap: 0.75rem;
    }
    .btn {
      display: inline-flex;
      align-items: center;
      gap: 0.5rem;
      padding: 0.7rem 1.35rem;
      font-size: 0.9rem;
      font-weight: 600;
      border-radius: 8px;
      border: none;
      cursor: pointer;
      transition: all 0.2s ease;
    }
    .btn-primary {
      background: #2563eb;
      color: #ffffff;
      box-shadow: 0 2px 4px rgba(37, 99, 235, 0.15);
    }
    .btn-primary:hover:not(:disabled) {
      background: #1d4ed8;
      transform: translateY(-1px);
      box-shadow: 0 4px 8px rgba(37, 99, 235, 0.25);
    }
    .btn-secondary {
      background: #f1f5f9;
      color: #475569;
      border: 1px solid #cbd5e1;
    }
    .btn-secondary:hover:not(:disabled) {
      background: #e2e8f0;
      color: #0f172a;
      transform: translateY(-1px);
    }
    .btn:disabled {
      opacity: 0.5;
      cursor: not-allowed;
      transform: none !important;
      box-shadow: none !important;
    }
  `]
})
export class ChatInput {
  @Input() disabled: boolean = false;
  @Output() run = new EventEmitter<string>();
  @Output() clear = new EventEmitter<void>();

  protected readonly maxChars = 5000;
  protected rawText = '';
  public readonly text = signal('');

  onTextChange(val: string) {
    this.text.set(val || '');
  }

  onRun() {
    const task = this.text().trim();
    if (task) {
      this.run.emit(task);
    }
  }

  onClear() {
    this.rawText = '';
    this.text.set('');
    this.clear.emit();
  }
}
