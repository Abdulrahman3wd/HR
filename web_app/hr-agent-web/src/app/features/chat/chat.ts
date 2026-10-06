import { AfterViewChecked, Component, computed, DestroyRef, ElementRef, inject, OnDestroy, signal, ViewChild } from '@angular/core';
import { takeUntilDestroyed } from '@angular/core/rxjs-interop';
import { FormsModule } from '@angular/forms';
import { ArrowLeft, ArrowRight, LucideAngularModule, MessageCircle } from 'lucide-angular';

import { AuthService } from '../../core/services/auth.service';
import { ChatService } from '../../core/services/chat.service';
import { I18nService } from '../../core/services/i18n.service';
import { ChatMessage } from '../../core/models/chat.model';

@Component({
  selector: 'app-chat',
  imports: [FormsModule, LucideAngularModule],
  templateUrl: './chat.html',
  styleUrl: './chat.css',
})
export class Chat implements AfterViewChecked, OnDestroy {
  private readonly auth = inject(AuthService);
  private readonly chatService = inject(ChatService);
  private readonly destroyRef = inject(DestroyRef);
  protected readonly i18n = inject(I18nService);

  protected readonly MessageIcon = MessageCircle;
  protected readonly ArrowIcon = ArrowRight;
  protected readonly SendArrowIcon = computed(() =>
    this.i18n.lang() === 'ar' ? ArrowLeft : ArrowRight,
  );
  protected readonly suggestions = [
    'chat_suggestion_balance',
    'chat_suggestion_carryover',
    'chat_suggestion_hours',
  ] as const;

  protected readonly messages = signal<ChatMessage[]>([]);
  protected readonly questionText = signal('');
  protected readonly isThinking = signal(false);
  protected readonly isTyping = signal(false);
  protected readonly typingMessageIndex = signal<number | null>(null);
  protected readonly displayedAnswer = signal('');

  protected welcomeTitle(): string {
    const firstName = this.auth.currentUser()?.full_name.trim().split(/\s+/)[0];
    return firstName
      ? this.i18n.t('chat_empty_title', { name: firstName })
      : this.i18n.t('chat_empty_title_fallback');
  }

  @ViewChild('scrollAnchor') private scrollAnchor?: ElementRef<HTMLDivElement>;
  @ViewChild('questionInput') private questionInput?: ElementRef<HTMLTextAreaElement>;
  private shouldScroll = false;
  private typingTimeout: ReturnType<typeof setTimeout> | undefined;

  protected sendQuestion(): void {
    const question = this.questionText().trim();
    if (!question || this.isThinking() || this.isTyping()) return;

    this.messages.update((msgs) => [...msgs, { role: 'user', text: question }]);
    this.questionText.set('');
    this.resetQuestionInput();
    this.isThinking.set(true);
    this.shouldScroll = true;

    this.chatService.ask({ question }).pipe(takeUntilDestroyed(this.destroyRef)).subscribe({
      next: (response) => {
        const messageIndex = this.messages().length;
        this.messages.update((msgs) => [
          ...msgs,
          { role: 'agent', text: response.answer, sources: response.sources },
        ]);
        this.isThinking.set(false);
        this.startTyping(response.answer, messageIndex);
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

  private startTyping(answer: string, messageIndex: number): void {
    const characters = Array.from(answer);
    let characterIndex = 0;

    this.typingMessageIndex.set(messageIndex);
    this.displayedAnswer.set('');
    this.isTyping.set(true);
    this.shouldScroll = true;

    const typeNextCharacter = (): void => {
      if (characterIndex >= characters.length) {
        this.isTyping.set(false);
        this.typingMessageIndex.set(null);
        this.displayedAnswer.set('');
        this.typingTimeout = undefined;
        this.shouldScroll = true;
        return;
      }

      const character = characters[characterIndex++];
      this.displayedAnswer.update((text) => text + character);
      if (characterIndex % 6 === 0 || characterIndex === characters.length) {
        this.shouldScroll = true;
      }

      const delay = /[.!?؟。]/u.test(character) ? 190 : /[,،;:]/u.test(character) ? 95 : 24;
      this.typingTimeout = setTimeout(typeNextCharacter, delay);
    };

    typeNextCharacter();
  }

  protected askSuggestion(question: string): void {
    this.questionText.set(question);
    this.sendQuestion();
  }

  protected onKeydown(event: KeyboardEvent): void {
    if (event.key === 'Enter' && !event.shiftKey) {
      event.preventDefault();
      this.sendQuestion();
    }
  }

  protected resizeInput(event: Event): void {
    const textarea = event.target as HTMLTextAreaElement;
    textarea.style.height = 'auto';

    const maxHeight = Number.parseFloat(getComputedStyle(textarea).maxHeight);
    const targetHeight = Number.isFinite(maxHeight)
      ? Math.min(textarea.scrollHeight, maxHeight)
      : textarea.scrollHeight;

    textarea.style.height = `${targetHeight}px`;
    textarea.style.overflowY = textarea.scrollHeight > targetHeight ? 'auto' : 'hidden';
  }

  private resetQuestionInput(): void {
    const textarea = this.questionInput?.nativeElement;
    if (!textarea) return;

    textarea.value = '';
    textarea.style.height = '';
    textarea.style.overflowY = 'hidden';
  }

  ngAfterViewChecked(): void {
    if (this.shouldScroll && this.scrollAnchor) {
      this.scrollAnchor.nativeElement.scrollIntoView({ behavior: 'smooth' });
      this.shouldScroll = false;
    }
  }

  ngOnDestroy(): void {
    if (this.typingTimeout !== undefined) {
      clearTimeout(this.typingTimeout);
    }
  }
}