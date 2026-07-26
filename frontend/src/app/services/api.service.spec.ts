import { TestBed } from '@angular/core/testing';
import { provideHttpClient } from '@angular/common/http';
import { provideHttpClientTesting, HttpTestingController } from '@angular/common/http/testing';
import { ApiService } from './api.service';
import { HealthResponse, TaskResponse } from '../models/chat.models';
import { environment } from '../../environments/environment';

describe('ApiService', () => {
  let service: ApiService;
  let httpMock: HttpTestingController;

  beforeEach(() => {
    TestBed.configureTestingModule({
      providers: [
        ApiService,
        provideHttpClient(),
        provideHttpClientTesting(),
      ],
    });
    service = TestBed.inject(ApiService);
    httpMock = TestBed.inject(HttpTestingController);
  });

  afterEach(() => {
    httpMock.verify();
  });

  it('should get backend health status', () => {
    const dummyHealth: HealthResponse = { status: 'healthy' };

    service.getHealth().subscribe((res) => {
      expect(res.status).toBe('healthy');
    });

    const req = httpMock.expectOne(`${environment.apiUrl}/health`);
    expect(req.request.method).toBe('GET');
    req.flush(dummyHealth);
  });

  it('should execute chat workflow', () => {
    const dummyResponse: TaskResponse = {
      messages: [
        { id: '1', source: 'manager_agent', type: 'TextMessage', content: 'Delegate', created_at: '', metadata: {} },
      ],
      stop_reason: 'Complete',
    };

    service.executeChat('test task').subscribe((res) => {
      expect(res.messages.length).toBe(1);
      expect(res.messages[0].source).toBe('manager_agent');
      expect(res.stop_reason).toBe('Complete');
    });

    const req = httpMock.expectOne(`${environment.apiUrl}/api/chat`);
    expect(req.request.method).toBe('POST');
    expect(req.request.body).toEqual({ task: 'test task' });
    req.flush(dummyResponse);
  });
});
