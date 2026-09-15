import { Component, inject, signal, OnInit } from '@angular/core';
import { ActivatedRoute } from '@angular/router';
import { LucideAngularModule, CalendarClock, CheckCircle2, Video, MapPin } from 'lucide-angular';

import { InterviewService } from '../../core/services/interview.service';
import { I18nService } from '../../core/services/i18n.service';
import { ThemeToggle } from '../../shared/components/theme-toggle/theme-toggle';
import { LangToggle } from '../../shared/components/lang-toggle/lang-toggle';
import { PublicInterviewInfo } from '../../core/models/interview.model';

@Component({
  selector: 'app-book-interview',
  imports: [LucideAngularModule, ThemeToggle, LangToggle],
  templateUrl: './book-interview.html',
  styleUrl: './book-interview.css',
})
export class BookInterview implements OnInit {
  private readonly route = inject(ActivatedRoute);
  private readonly interviewService = inject(InterviewService);
  protected readonly i18n = inject(I18nService);

  protected readonly CalendarIcon = CalendarClock;
  protected readonly SuccessIcon = CheckCircle2;
  protected readonly OnlineIcon = Video;
  protected readonly OfflineIcon = MapPin;

  protected readonly info = signal<PublicInterviewInfo | null>(null);
  protected readonly isLoading = signal(true);
  protected readonly notFound = signal(false);

  protected readonly selectedSlot = signal<string | null>(null);
  protected readonly isBooking = signal(false);
  protected readonly errorMessage = signal<string | null>(null);
  protected readonly bookingSuccess = signal(false);
  protected readonly confirmedSlot = signal<string | null>(null);

  private scheduleId = 0;

  ngOnInit(): void {
    this.scheduleId = Number(this.route.snapshot.paramMap.get('scheduleId'));
    if (!this.scheduleId) {
      this.notFound.set(true);
      this.isLoading.set(false);
      return;
    }

    this.loadInfo();
  }

  private loadInfo(): void {
    this.interviewService.getPublicInterviewInfo(this.scheduleId).subscribe({
      next: (data) => {
        this.info.set(data);
        this.isLoading.set(false);
      },
      error: () => {
        this.notFound.set(true);
        this.isLoading.set(false);
      },
    });
  }

  protected selectSlot(slot: string): void {
    this.selectedSlot.set(slot);
    this.errorMessage.set(null);
  }

  protected confirmBooking(): void {
    const slot = this.selectedSlot();
    if (!slot) return;

    this.isBooking.set(true);
    this.errorMessage.set(null);

    this.interviewService.bookSlot(this.scheduleId, slot).subscribe({
      next: () => {
        this.isBooking.set(false);
        this.bookingSuccess.set(true);
        this.confirmedSlot.set(slot);
      },
      error: (err) => {
        this.isBooking.set(false);
        this.errorMessage.set(err.error?.detail || this.i18n.t('interview_sent_error'));
        this.loadInfo(); // refresh slots in case another candidate took one
      },
    });
  }

  protected typeLabel(type: string): string {
    return type === 'hr' ? this.i18n.t('interview_type_hr') : this.i18n.t('interview_type_technical');
  }
}