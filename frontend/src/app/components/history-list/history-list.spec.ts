import { ComponentFixture, TestBed } from '@angular/core/testing';
import { HistoryListComponent } from './history-list';
import { HistoryService } from '../../services/history.service';
import { of, throwError } from 'rxjs';
import { WorkflowListResponse, WorkflowStats } from '../../models/chat.models';
import { describe, beforeEach, it, expect, vi } from 'vitest';

describe('HistoryListComponent', () => {
  let component: HistoryListComponent;
  let fixture: ComponentFixture<HistoryListComponent>;
  let mockHistoryService: any;

  const dummyWorkflows: WorkflowListResponse = {
    items: [
      {
        id: 'wf-1',
        prompt: 'Build Python CLI',
        status: 'COMPLETE',
        total_iterations: 1,
        generated_file_count: 2,
        favorite: false,
        created_at: '2026-07-28T00:00:00Z',
        completed_at: '2026-07-28T00:01:00Z',
      },
      {
        id: 'wf-2',
        prompt: 'Build Web App',
        status: 'FAILED',
        total_iterations: 3,
        generated_file_count: 0,
        favorite: false,
        created_at: '2026-07-28T01:00:00Z',
        completed_at: null,
      },
    ],
    total: 2,
    limit: 10,
    offset: 0,
  };

  const dummyStats: WorkflowStats = {
    total_workflows: 2,
    completed_workflows: 1,
    failed_workflows: 1,
    needs_attention_workflows: 0,
    running_workflows: 0,
    favorite_count: 0,
    average_iterations: 2.0,
  };

  beforeEach(async () => {
    mockHistoryService = {
      listWorkflows: vi.fn().mockReturnValue(of(dummyWorkflows)),
      getStats: vi.fn().mockReturnValue(of(dummyStats)),
    };

    await TestBed.configureTestingModule({
      imports: [HistoryListComponent],
      providers: [{ provide: HistoryService, useValue: mockHistoryService }],
    }).compileComponents();

    fixture = TestBed.createComponent(HistoryListComponent);
    component = fixture.componentInstance;
  });

  it('should create and load data on init', () => {
    fixture.detectChanges();
    expect(component).toBeTruthy();
    expect(mockHistoryService.listWorkflows).toHaveBeenCalled();
    expect(mockHistoryService.getStats).toHaveBeenCalled();
    expect(component.workflows().length).toBe(2);
  });

  it('should handle search input', async () => {
    fixture.detectChanges();
    const event = { target: { value: 'CLI' } } as unknown as Event;
    component.onSearchInput(event);
    expect(component.searchQuery()).toBe('CLI');

    await new Promise((r) => setTimeout(r, 400));

    expect(mockHistoryService.listWorkflows).toHaveBeenCalledWith(
      expect.objectContaining({ search: 'CLI' })
    );
  });

  it('should filter by status', () => {
    fixture.detectChanges();
    const event = { target: { value: 'COMPLETE' } } as unknown as Event;
    component.onStatusFilterChange(event);
    expect(component.statusFilter()).toBe('COMPLETE');
    expect(mockHistoryService.listWorkflows).toHaveBeenCalledWith(
      expect.objectContaining({ status: 'COMPLETE' })
    );
  });

  it('should handle empty state', () => {
    mockHistoryService.listWorkflows.mockReturnValue(
      of({ items: [], total: 0, limit: 10, offset: 0 })
    );
    fixture.detectChanges();
    expect(component.workflows().length).toBe(0);
  });

  it('should handle error and retry', () => {
    mockHistoryService.listWorkflows.mockReturnValue(
      throwError(() => new Error('Server error'))
    );
    fixture.detectChanges();
    expect(component.error()).toContain('Server error');

    // Retry
    mockHistoryService.listWorkflows.mockReturnValue(of(dummyWorkflows));
    component.loadData();
    expect(component.error()).toBeNull();
    expect(component.workflows().length).toBe(2);
  });

  it('should filter by date range', () => {
    fixture.detectChanges();
    const event = { target: { value: 'today' } } as unknown as Event;
    component.onDateRangeFilterChange(event);
    expect(component.dateRangeFilter()).toBe('today');
    expect(mockHistoryService.listWorkflows).toHaveBeenCalledWith(
      expect.objectContaining({ date_range: 'today' })
    );
  });

  it('should toggle favorite status on card', () => {
    mockHistoryService.markFavorite = vi.fn().mockReturnValue(of({ id: 'wf-1', favorite: true }));
    fixture.detectChanges();

    const mockEvent = { stopPropagation: vi.fn() } as unknown as Event;
    const wf = { ...dummyWorkflows.items[0], favorite: false };

    component.toggleFavorite(mockEvent, wf);
    expect(mockEvent.stopPropagation).toHaveBeenCalled();
    expect(mockHistoryService.markFavorite).toHaveBeenCalledWith('wf-1');
  });

  it('should handle export JSON success and failure', () => {
    mockHistoryService.exportJson = vi.fn().mockReturnValue(of({ workflow: {} }));
    fixture.detectChanges();

    const mockEvent = { stopPropagation: vi.fn() } as unknown as Event;
    component.onExportJson(mockEvent, 'wf-1');
    expect(mockHistoryService.exportJson).toHaveBeenCalledWith('wf-1');

    // Error test
    const alertSpy = vi.spyOn(window, 'alert').mockImplementation(() => {});
    mockHistoryService.exportJson = vi.fn().mockReturnValue(throwError(() => new Error('Export error')));
    component.onExportJson(mockEvent, 'wf-1');
    expect(alertSpy).toHaveBeenCalledWith(expect.stringContaining('Export error'));
  });

  it('should handle ZIP download success and failure', () => {
    const dummyBlob = new Blob(['zipdata'], { type: 'application/zip' });
    mockHistoryService.downloadZip = vi.fn().mockReturnValue(of(dummyBlob));
    fixture.detectChanges();

    const mockEvent = { stopPropagation: vi.fn() } as unknown as Event;
    component.onDownloadZip(mockEvent, 'wf-1');
    expect(mockHistoryService.downloadZip).toHaveBeenCalledWith('wf-1');

    // Error test
    const alertSpy = vi.spyOn(window, 'alert').mockImplementation(() => {});
    mockHistoryService.downloadZip = vi.fn().mockReturnValue(throwError(() => new Error('ZIP error')));
    component.onDownloadZip(mockEvent, 'wf-1');
    expect(alertSpy).toHaveBeenCalledWith(expect.stringContaining('ZIP error'));
  });
});
