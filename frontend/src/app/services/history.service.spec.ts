import { TestBed } from '@angular/core/testing';
import { provideHttpClientTesting, HttpTestingController } from '@angular/common/http/testing';
import { provideHttpClient } from '@angular/common/http';
import { HistoryService } from './history.service';
import { environment } from '../../environments/environment';
import { WorkflowListResponse, WorkflowDetail, WorkflowStats } from '../models/chat.models';
import { describe, beforeEach, afterEach, it, expect } from 'vitest';

describe('HistoryService', () => {
  let service: HistoryService;
  let httpMock: HttpTestingController;

  beforeEach(() => {
    TestBed.configureTestingModule({
      providers: [
        HistoryService,
        provideHttpClient(),
        provideHttpClientTesting(),
      ],
    });
    service = TestBed.inject(HistoryService);
    httpMock = TestBed.inject(HttpTestingController);
  });

  afterEach(() => {
    httpMock.verify();
  });

  it('should be created', () => {
    expect(service).toBeTruthy();
  });

  it('should list workflows with query parameters', () => {
    const dummyResponse: WorkflowListResponse = {
      items: [
        {
          id: 'wf-1',
          prompt: 'Test prompt',
          status: 'COMPLETE',
          total_iterations: 1,
          generated_file_count: 1,
          created_at: '2026-07-28T00:00:00Z',
          completed_at: '2026-07-28T00:01:00Z',
        },
      ],
      total: 1,
      limit: 10,
      offset: 0,
    };

    service.listWorkflows({ limit: 10, offset: 0, search: 'test', status: 'COMPLETE' }).subscribe((res) => {
      expect(res).toEqual(dummyResponse);
    });

    const req = httpMock.expectOne(
      (request) =>
        request.url === `${environment.apiUrl}/api/workflows` &&
        request.params.get('limit') === '10' &&
        request.params.get('offset') === '0' &&
        request.params.get('search') === 'test' &&
        request.params.get('status') === 'COMPLETE'
    );
    expect(req.request.method).toBe('GET');
    req.flush(dummyResponse);
  });

  it('should get workflow detail', () => {
    const dummyDetail: WorkflowDetail = {
      id: 'wf-1',
      prompt: 'Test prompt',
      status: 'COMPLETE',
      final_summary: 'Success',
      total_iterations: 1,
      generated_file_count: 1,
      created_at: '2026-07-28T00:00:00Z',
      completed_at: '2026-07-28T00:01:00Z',
      iterations: [],
      messages: [],
      generated_files: [],
    };

    service.getWorkflow('wf-1').subscribe((res) => {
      expect(res).toEqual(dummyDetail);
    });

    const req = httpMock.expectOne(`${environment.apiUrl}/api/workflows/wf-1`);
    expect(req.request.method).toBe('GET');
    req.flush(dummyDetail);
  });

  it('should delete workflow', () => {
    service.deleteWorkflow('wf-1').subscribe((res) => {
      expect(res.status).toBe('deleted');
    });

    const req = httpMock.expectOne(`${environment.apiUrl}/api/workflows/wf-1`);
    expect(req.request.method).toBe('DELETE');
    req.flush({ status: 'deleted', workflow_id: 'wf-1' });
  });

  it('should get stats', () => {
    const dummyStats: WorkflowStats = {
      total_workflows: 5,
      completed_workflows: 3,
      failed_workflows: 1,
      needs_attention_workflows: 1,
      running_workflows: 0,
      average_iterations: 1.5,
    };

    service.getStats().subscribe((res) => {
      expect(res).toEqual(dummyStats);
    });

    const req = httpMock.expectOne(`${environment.apiUrl}/api/workflows/stats`);
    expect(req.request.method).toBe('GET');
    req.flush(dummyStats);
  });
});
