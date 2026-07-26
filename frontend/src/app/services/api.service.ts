import { inject, Injectable } from '@angular/core';
import { HttpClient } from '@angular/common/http';
import { Observable } from 'rxjs';
import { environment } from '../../environments/environment';
import { HealthResponse, MessageResponse, TaskRequest, TaskResponse } from '../models/chat.models';

@Injectable({
  providedIn: 'root',
})
export class ApiService {
  private readonly http = inject(HttpClient);
  private readonly apiUrl = environment.apiUrl;

  getHealth(): Observable<HealthResponse> {
    return this.http.get<HealthResponse>(`${this.apiUrl}/health`);
  }

  executeChat(task: string): Observable<TaskResponse> {
    return this.http.post<TaskResponse>(`${this.apiUrl}/api/chat`, { task } as TaskRequest);
  }

  executeChatStream(task: string): Observable<MessageResponse> {
    return new Observable<MessageResponse>((observer) => {
      const controller = new AbortController();

      fetch(`${this.apiUrl}/api/chat/stream`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({ task }),
        signal: controller.signal,
      })
      .then(async (response) => {
        if (!response.ok) {
          throw new Error(`HTTP error! status: ${response.status}`);
        }

        const reader = response.body?.getReader();
        if (!reader) {
          throw new Error('Readable stream not supported on this browser');
        }

        const decoder = new TextDecoder('utf-8');
        let buffer = '';

        try {
          while (true) {
            const { done, value } = await reader.read();
            if (done) break;

            buffer += decoder.decode(value, { stream: true });
            const lines = buffer.split('\n');
            buffer = lines.pop() || ''; // Keep incomplete line in the buffer

            for (const line of lines) {
              const trimmed = line.trim();
              if (trimmed.startsWith('data: ')) {
                const jsonStr = trimmed.slice(6);
                try {
                  const data = JSON.parse(jsonStr) as MessageResponse;
                  observer.next(data);
                } catch (e) {
                  console.error('Failed to parse event JSON:', e);
                }
              }
            }
          }
          observer.complete();
        } catch (err) {
          observer.error(err);
        }
      })
      .catch((err) => {
        // Skip errors if request was aborted
        if (err.name !== 'AbortError') {
          observer.error(err);
        }
      });

      return () => {
        controller.abort();
      };
    });
  }
}
