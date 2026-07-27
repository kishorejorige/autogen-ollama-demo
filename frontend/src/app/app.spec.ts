import { TestBed } from '@angular/core/testing';
import { provideHttpClient } from '@angular/common/http';
import { provideHttpClientTesting } from '@angular/common/http/testing';
import { App } from './app';
import { DashboardComponent } from './components/dashboard/dashboard';
import { of } from 'rxjs';
import { ApiService } from './services/api.service';
import { vi } from 'vitest';

describe('App', () => {
  beforeEach(async () => {
    await TestBed.configureTestingModule({
      imports: [App, DashboardComponent],
      providers: [
        provideHttpClient(),
        provideHttpClientTesting(),
      ],
    }).compileComponents();
  });

  it('should create the app', () => {
    const fixture = TestBed.createComponent(App);
    const app = fixture.componentInstance;
    expect(app).toBeTruthy();
  });

  it('should render the dashboard', () => {
    const fixture = TestBed.createComponent(App);
    fixture.detectChanges();
    const compiled = fixture.nativeElement as HTMLElement;
    expect(compiled.querySelector('app-dashboard')).toBeTruthy();
  });
});

describe('DashboardComponent - Additional Tests', () => {
  let component: DashboardComponent;
  let apiService: ApiService;

  beforeEach(() => {
    TestBed.configureTestingModule({
      imports: [DashboardComponent],
      providers: [
        provideHttpClient(),
        provideHttpClientTesting(),
      ]
    });
    const fixture = TestBed.createComponent(DashboardComponent);
    component = fixture.componentInstance;
    apiService = TestBed.inject(ApiService);
  });

  it('should handle clipboard copy failure gracefully', async () => {
    const mockClipboard = {
      writeText: vi.fn().mockRejectedValue(new Error('Clipboard write permission denied'))
    };
    Object.defineProperty(navigator, 'clipboard', {
      value: mockClipboard,
      writable: true,
      configurable: true
    });

    const file = { filename: 'test.py', content: 'print(1)', iteration: 1, is_final: true };
    component.copyCode(file);

    await Promise.resolve();

    expect(component.copyConfirmation()).toBeNull();
  });

  it('should trigger browser download behavior correctly', () => {
    const mockRevoke = vi.fn();
    const mockCreate = vi.fn().mockReturnValue('blob:http://localhost/test');

    Object.defineProperty(window.URL, 'createObjectURL', { value: mockCreate, configurable: true });
    Object.defineProperty(window.URL, 'revokeObjectURL', { value: mockRevoke, configurable: true });

    const mockAnchor = {
      href: '',
      download: '',
      click: vi.fn()
    };
    const spyCreateElement = vi.spyOn(document, 'createElement').mockReturnValue(mockAnchor as any);

    const file = { filename: 'test.py', content: 'print(1)', iteration: 1, is_final: true };
    component.downloadFile(file);

    expect(spyCreateElement).toHaveBeenCalledWith('a');
    expect(mockAnchor.download).toBe('test.py');
    expect(mockAnchor.click).toHaveBeenCalled();
    expect(mockRevoke).toHaveBeenCalledWith('blob:http://localhost/test');

    spyCreateElement.mockRestore();
  });

  it('should terminate the loading spinner on workflow completion', () => {
    const mockResponse = {
      id: 'result',
      source: 'system',
      type: 'TaskResult',
      content: 'Workflow finished successfully.',
      created_at: '',
      metadata: {},
      workflow_state: {
        workflow_id: '123',
        status: 'COMPLETE' as const,
        current_iteration: 1,
        max_iterations: 3,
        generated_files: [],
        messages: [],
        iteration_history: [],
        started_at: '',
        completed_at: '',
        error: null,
        current_agent: null,
        reviewer_status: null,
        tester_status: null
      }
    };

    vi.spyOn(apiService, 'executeChatStream').mockReturnValue(of(mockResponse));

    component.loading.set(true);
    component.onExecuteTask('some task');

    expect(component.loading()).toBe(false);
    expect(component.workflowStatus()).toBe('completed');
  });

  it('should terminate the loading spinner on workflow error event', () => {
    const mockErrorResponse = {
      id: 'error',
      source: 'error',
      type: 'Error',
      content: 'An error occurred.',
      created_at: '',
      metadata: {},
      workflow_state: undefined
    };

    vi.spyOn(apiService, 'executeChatStream').mockReturnValue(of(mockErrorResponse));

    component.loading.set(true);
    component.onExecuteTask('some task');

    expect(component.loading()).toBe(false);
    expect(component.workflowStatus()).toBe('failed');
    expect(component.error()).toBe('An error occurred.');
  });
});
