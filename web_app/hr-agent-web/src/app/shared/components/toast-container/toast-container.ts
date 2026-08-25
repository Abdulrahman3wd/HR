import { Component, inject } from '@angular/core';
import { LucideAngularModule, CheckCircle2, XCircle, Info, X } from 'lucide-angular';
import { ToastService } from '../../../core/services/toast.service';

@Component({
  selector: 'app-toast-container',
  imports: [LucideAngularModule],
  templateUrl: './toast-container.html',
  styleUrl: './toast-container.css',
})
export class ToastContainer {
  protected readonly toastService = inject(ToastService);

  protected readonly SuccessIcon = CheckCircle2;
  protected readonly ErrorIcon = XCircle;
  protected readonly InfoIcon = Info;
  protected readonly CloseIcon = X;

  protected iconFor(type: string) {
    if (type === 'success') return this.SuccessIcon;
    if (type === 'error') return this.ErrorIcon;
    return this.InfoIcon;
  }
}