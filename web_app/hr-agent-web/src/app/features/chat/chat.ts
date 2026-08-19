import { Component, inject, signal, ViewChild, ElementRef, AfterViewChecked } from '@angular/core';
import { FormsModule } from '@angular/forms';
import { LucideAngularModule, Send, Sparkles } from 'lucide-angular';

import { ChatService } from '../../core/services/chat.service';
import { I18nService } from '../../core/services/i18n.service';
import { ChatMessage } from '../../core/models/chat.model';

@Component({
  selector: 'app-chat',
  imports: [FormsModule, LucideAngularModule],
  templateUrl: './chat.html',
  styleUrl: './chat.css',
})
export class Chat implements AfterViewChecked {
  private readonly chatService = inject(ChatService);
  protected readonly i18n = inject(I18nService);

  protected readonly SendIcon = Send;
  protected readonly SparklesIcon = Sparkles;

  protected readonly messages = signal<ChatMessage[]>([]);
  protected readonly questionText = signal('');
  protected readonly isThinking = signal(false);

  @ViewChild('scrollAnchor') private scrollAnchor?: ElementRef<HTMLDivElement>;
  private shouldScroll = false;

  protected sendQuestion(): void {
    const question = this.questionText().trim();
    if (!question || this.isThinking()) return;

    this.messages.update((msgs) => [...msgs, { role: 'user', text: question }]);
    this.questionText.set('');
    this.isThinking.set(true);
    this.shouldScroll = true;

    this.chatService.ask({ question }).subscribe({
      next: (response) => {
        this.messages.update((msgs) => [
          ...msgs,
          { role: 'agent', text: response.answer, sources: response.sources },
        ]);
        this.isThinking.set(false);
        this.shouldScroll = true;
      },
      error: () => {
        this.messages.update((msgs) => [
          ...msgs,
          { role: 'agent', text: this.i18n.t('chat_error') },
        ]);
        this.isThinking.set(false);
        this.shouldScroll = true;
      },
    });
  }

  protected onKeydown(event: KeyboardEvent): void {
    if (event.key === 'Enter' && !event.shiftKey) {
      event.preventDefault();
      this.sendQuestion();
    }
  }

  ngAfterViewChecked(): void {
    if (this.shouldScroll && this.scrollAnchor) {
      this.scrollAnchor.nativeElement.scrollIntoView({ behavior: 'smooth' });
      this.shouldScroll = false;
    }
  }
}