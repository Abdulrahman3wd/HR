import { Component, inject } from '@angular/core';
import { LucideAngularModule, AlertTriangle } from 'lucide-angular';
import { ConfirmDialogService } from '../../../core/services/confirm-dialog.service';
import { I18nService } from '../../../core/services/i18n.service';

@Component({
  selector: 'app-confirm-dialog',
  imports: [LucideAngularModule],
  templateUrl: './confirm-dialog.html',
  styleUrl: './confirm-dialog.css',
})
export class ConfirmDialog {
  protected readonly dialogService = inject(ConfirmDialogService);
  protected readonly i18n = inject(I18nService);

  protected readonly WarningIcon = AlertTriangle;

  protected confirm(): void {
    this.dialogService.respond(true);
  }

  protected cancel(): void {
    this.dialogService.respond(false);
  }
}