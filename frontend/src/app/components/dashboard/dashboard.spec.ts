import { ComponentFixture, TestBed } from '@angular/core/testing';
import { DashboardComponent } from './dashboard';
import { ApiService } from '../../services/api.service';
import { of } from 'rxjs';
import { QualityGateResult, WorkflowState } from '../../models/chat.models';

describe('Dashboard Component - Quality Gate & Run Readiness', () => {
  let component: DashboardComponent;
  let fixture: ComponentFixture<DashboardComponent>;
  let mockApiService: any;

  beforeEach(async () => {
    mockApiService = {
      getHealth: () => of({ status: 'healthy' }),
      executeTaskStream: () => of({}),
    };

    await TestBed.configureTestingModule({
      imports: [DashboardComponent],
      providers: [{ provide: ApiService, useValue: mockApiService }],
    }).compileComponents();

    fixture = TestBed.createComponent(DashboardComponent);
    component = fixture.componentInstance;
    fixture.detectChanges();
  });

  it('should create the dashboard component', () => {
    expect(component).toBeTruthy();
  });

  it('should compute workflow status text correctly for COMPLETE and NEEDS_ATTENTION', () => {
    expect(component.workflowStatusText()).toBe('Ready');

    // Simulate COMPLETE workflow state
    const completeState: WorkflowState = {
      workflow_id: 'w1',
      current_agent: null,
      current_iteration: 1,
      max_iterations: 3,
      status: 'COMPLETE',
      reviewer_status: 'APPROVED',
      tester_status: 'PASS',
      messages: [],
      generated_files: [],
      iteration_history: [],
      started_at: null,
      completed_at: null,
      error: null,
      quality_gate_result: {
        overall_status: 'PASS',
        run_readiness: 'RUNNABLE',
        requirements: [],
        framework_mismatches: [],
        missing_deliverables: [],
        unsupported_claims: [],
        security_issues: [],
        recommended_fixes: [],
        production_ready_eligible: true,
      },
    };
    component.workflowState.set(completeState);
    component.workflowStatus.set('completed');
    expect(component.workflowStatus()).toBe('completed');
    expect(component.workflowStatusText()).toBe('✓ Complete');

    // Simulate NEEDS_ATTENTION state
    component.workflowStatus.set('needs_attention');
    expect(component.workflowStatus()).toBe('needs_attention');
    expect(component.workflowStatusText()).toBe('⚠️ Needs Attention');
  });
});
