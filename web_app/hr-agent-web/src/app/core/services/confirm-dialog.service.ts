import { Injectable, signal } from '@angular/core';

interface ConfirmRequest {
  message: string;
  resolve: (confirmed: boolean) => void;
}

@Injectable({ providedIn: 'root' })
export class ConfirmDialogService {
  readonly currentRequest = signal<ConfirmRequest | null>(null);

  confirm(message: string): Promise<boolean> {
    return new Promise((resolve) => {
      this.currentRequest.set({ message, resolve });
    });
  }

  respond(confirmed: boolean): void {
    const request = this.currentRequest();
    if (request) {
      request.resolve(confirmed);
      this.currentRequest.set(null);
    }
  }
}