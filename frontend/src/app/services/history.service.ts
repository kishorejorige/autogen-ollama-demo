import { inject, Injectable } from '@angular/core';
import { HttpClient, HttpParams } from '@angular/common/http';
import { Observable } from 'rxjs';
import { environment } from '../../environments/environment';
import {
  WorkflowDetail,
  WorkflowListResponse,
  WorkflowStats,
} from '../models/chat.models';

export interface ListWorkflowsParams {
  limit?: number;
  offset?: number;
  search?: string;
  status?: string;
  date_range?: string;
}

@Injectable({
  providedIn: 'root',
})
export class HistoryService {
  private readonly http = inject(HttpClient);
  private readonly apiUrl = environment.apiUrl;

  listWorkflows(params: ListWorkflowsParams = {}): Observable<WorkflowListResponse> {
    let httpParams = new HttpParams();

    if (params.limit !== undefined && params.limit !== null) {
      httpParams = httpParams.set('limit', params.limit.toString());
    }
    if (params.offset !== undefined && params.offset !== null) {
      httpParams = httpParams.set('offset', params.offset.toString());
    }
    if (params.search && params.search.trim()) {
      httpParams = httpParams.set('search', params.search.trim());
    }
    if (params.status && params.status.trim()) {
      httpParams = httpParams.set('status', params.status.trim());
    }
    if (params.date_range && params.date_range.trim()) {
      httpParams = httpParams.set('date_range', params.date_range.trim());
    }

    return this.http.get<WorkflowListResponse>(`${this.apiUrl}/api/workflows`, {
      params: httpParams,
    });
  }

  getWorkflow(workflowId: string): Observable<WorkflowDetail> {
    return this.http.get<WorkflowDetail>(`${this.apiUrl}/api/workflows/${workflowId}`);
  }

  markFavorite(workflowId: string): Observable<WorkflowDetail> {
    return this.http.post<WorkflowDetail>(`${this.apiUrl}/api/workflows/${workflowId}/favorite`, {});
  }

  removeFavorite(workflowId: string): Observable<WorkflowDetail> {
    return this.http.delete<WorkflowDetail>(`${this.apiUrl}/api/workflows/${workflowId}/favorite`);
  }

  exportJson(workflowId: string): Observable<any> {
    return this.http.get<any>(`${this.apiUrl}/api/workflows/${workflowId}/export/json`);
  }

  downloadZip(workflowId: string): Observable<Blob> {
    return this.http.get(`${this.apiUrl}/api/workflows/${workflowId}/export/zip`, {
      responseType: 'blob',
    });
  }

  deleteWorkflow(workflowId: string): Observable<{ status: string; workflow_id: string }> {
    return this.http.delete<{ status: string; workflow_id: string }>(
      `${this.apiUrl}/api/workflows/${workflowId}`
    );
  }

  getStats(): Observable<WorkflowStats> {
    return this.http.get<WorkflowStats>(`${this.apiUrl}/api/workflows/stats`);
  }
}
