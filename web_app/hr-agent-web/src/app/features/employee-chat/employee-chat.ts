import {
  AfterViewChecked,
  Component,
  DestroyRef,
  ElementRef,
  OnDestroy,
  OnInit,
  ViewChild,
  computed,
  inject,
  signal,
} from '@angular/core';
import { takeUntilDestroyed } from '@angular/core/rxjs-interop';
import { FormsModule } from '@angular/forms';
import {
  Archive,
  ArrowDown,
  ArrowLeft,
  ArrowRight,
  Download,
  FileImage,
  FileSpreadsheet,
  FileText,
  LucideAngularModule,
  MessageCircle,
  Paperclip,
  Presentation,
  Search,
  Send,
  X,
} from 'lucide-angular';

import { EmployeeChatService } from '../../core/services/employee-chat.service';
import { AuthService } from '../../core/services/auth.service';
import { I18nService } from '../../core/services/i18n.service';
import { ToastService } from '../../core/services/toast.service';
import {
  EmployeeChatAttachment,
  EmployeeChatPerson,
  EmployeeConversation,
  EmployeeMessage,
} from '../../core/models/employee-chat.model';

const MAX_ATTACHMENT_SIZE = 15 * 1024 * 1024;
const SUPPORTED_ATTACHMENT_MIMES: Record<string, string[]> = {
  jpg: ['image/jpeg'],
  jpeg: ['image/jpeg'],
  png: ['image/png'],
  gif: ['image/gif'],
  webp: ['image/webp'],
  pdf: ['application/pdf'],
  doc: ['application/msword', 'application/x-msword'],
  docx: ['application/vnd.openxmlformats-officedocument.wordprocessingml.document'],
  xls: ['application/vnd.ms-excel', 'application/x-msexcel'],
  xlsx: ['application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'],
  ppt: ['application/vnd.ms-powerpoint', 'application/mspowerpoint'],
  pptx: ['application/vnd.openxmlformats-officedocument.presentationml.presentation'],
  zip: ['application/zip', 'application/x-zip-compressed'],
  rar: ['application/vnd.rar', 'application/x-rar-compressed'],
  '7z': ['application/x-7z-compressed'],
};

@Component({
  selector: 'app-employee-chat',
  imports: [FormsModule, LucideAngularModule],
  templateUrl: './employee-chat.html',
  styleUrl: './employee-chat.css',
})
export class EmployeeChat implements OnInit, OnDestroy, AfterViewChecked {
  private readonly service = inject(EmployeeChatService);
  private readonly auth = inject(AuthService);
  private readonly destroyRef = inject(DestroyRef);
  private readonly toast = inject(ToastService);
  protected readonly i18n = inject(I18nService);

  protected readonly SearchIcon = Search;
  protected readonly MessageIcon = MessageCircle;
  protected readonly SendIcon = Send;
  protected readonly NewMessagesArrowIcon = ArrowDown;
  protected readonly PaperclipIcon = Paperclip;
  protected readonly DownloadIcon = Download;
  protected readonly RemoveIcon = X;
  protected readonly ImageFileIcon = FileImage;
  protected readonly TextFileIcon = FileText;
  protected readonly SpreadsheetIcon = FileSpreadsheet;
  protected readonly PresentationIcon = Presentation;
  protected readonly ArchiveIcon = Archive;
  protected readonly attachmentAccept = `.${Object.keys(SUPPORTED_ATTACHMENT_MIMES).join(',.')}`;
  protected readonly BackIcon = computed(() => this.i18n.lang() === 'ar' ? ArrowRight : ArrowLeft);
  protected readonly SendArrowIcon = computed(() => this.i18n.lang() === 'ar' ? ArrowLeft : ArrowRight);

  protected readonly employees = signal<EmployeeChatPerson[]>([]);
  protected readonly employeeSearch = signal('');
  protected readonly employeePage = signal(0);
  protected readonly employeeHasMore = signal(true);
  protected readonly isLoadingEmployees = signal(false);
  protected readonly startingEmployeeId = signal<string | null>(null);

  protected readonly conversations = signal<EmployeeConversation[]>([]);
  protected readonly totalUnread = signal(0);
  protected readonly recentPage = signal(0);
  protected readonly recentHasMore = signal(false);
  protected readonly isLoadingRecent = signal(false);

  protected readonly selectedConversation = signal<EmployeeConversation | null>(null);
  protected readonly messages = signal<EmployeeMessage[]>([]);
  protected readonly hasOlderMessages = signal(false);
  protected readonly isLoadingMessages = signal(false);
  protected readonly isLoadingOlder = signal(false);
  protected readonly isSending = signal(false);
  protected readonly messageText = signal('');
  protected readonly isOtherTyping = signal(false);
  protected readonly newMessageCount = signal(0);
  protected readonly selectedFile = signal<File | null>(null);
  protected readonly imagePreviewUrls = signal<Record<number, string>>({});

  @ViewChild('messageViewport') private messageViewport?: ElementRef<HTMLDivElement>;
  private nextBeforeId: number | null = null;
  private pendingScroll: 'bottom' | 'preserve' | null = null;
  private previousScrollHeight = 0;
  private followLatest = true;
  private scrollBottomAfterOlderLoad = false;
  private searchTimer: ReturnType<typeof setTimeout> | undefined;
  private pollTimer: ReturnType<typeof setInterval> | undefined;
  private reconnectTimer: ReturnType<typeof setTimeout> | undefined;
  private typingIdleTimer: ReturnType<typeof setTimeout> | undefined;
  private typingHeartbeatTimer: ReturnType<typeof setInterval> | undefined;
  private remoteTypingTimer: ReturnType<typeof setTimeout> | undefined;
  private typingSoundTimer: ReturnType<typeof setInterval> | undefined;
  private localTypingConversationId: number | null = null;
  private realtimeSocket: WebSocket | undefined;
  private audioContext: AudioContext | undefined;
  private reconnectDelay = 1000;
  private isDestroying = false;
  private employeeSearchSequence = 0;
  private recentRefreshInFlight = false;
  private readonly markingRead = new Set<number>();
  private readonly loadingPreviewIds = new Set<number>();

  ngOnInit(): void {
    this.loadEmployees(true);
    this.loadRecentChats(true);
    this.connectRealtime();
    this.pollTimer = setInterval(() => {
      this.refreshRecentChats();
      this.refreshSelectedMessages();
    }, 6000);
  }

  protected currentEmployeeId(): string {
    return this.auth.currentUser()?.employee_id ?? '';
  }

  protected onEmployeeSearch(event: Event): void {
    const value = (event.target as HTMLInputElement).value;
    this.employeeSearch.set(value);
    this.employeeSearchSequence += 1;
    const sequence = this.employeeSearchSequence;
    if (this.searchTimer !== undefined) clearTimeout(this.searchTimer);
    this.employees.set([]);
    this.employeePage.set(0);
    this.employeeHasMore.set(false);
    this.isLoadingEmployees.set(false);
    this.searchTimer = setTimeout(() => this.loadEmployees(true, sequence), 250);
  }

  protected loadMoreEmployees(): void {
    this.loadEmployees(false);
  }

  private loadEmployees(reset: boolean, sequence = this.employeeSearchSequence): void {
    if (this.isLoadingEmployees() || (!reset && !this.employeeHasMore())) return;
    const page = reset ? 1 : this.employeePage() + 1;
    this.isLoadingEmployees.set(true);
    this.service.listEmployees(page, 20, this.employeeSearch()).pipe(
      takeUntilDestroyed(this.destroyRef),
    ).subscribe({
      next: (result) => {
        if (sequence !== this.employeeSearchSequence) return;
        this.employees.update((current) => reset ? result.employees : [...current, ...result.employees]);
        this.employeePage.set(result.page);
        this.employeeHasMore.set(result.has_more);
        this.isLoadingEmployees.set(false);
      },
      error: () => {
        if (sequence !== this.employeeSearchSequence) return;
        this.isLoadingEmployees.set(false);
        this.toast.error(this.i18n.t('employee_chat_error'));
      },
    });
  }

  protected loadMoreRecentChats(): void {
    this.loadRecentChats(false);
  }

  private loadRecentChats(reset: boolean): void {
    if (this.isLoadingRecent()) return;
    const page = reset ? 1 : this.recentPage() + 1;
    if (!reset && !this.recentHasMore()) return;
    this.isLoadingRecent.set(true);
    this.service.listConversations(page, 20).pipe(
      takeUntilDestroyed(this.destroyRef),
    ).subscribe({
      next: (result) => {
        const current = reset ? [] : this.conversations();
        const byId = new Map(current.map((conversation) => [conversation.id, conversation]));
        for (const conversation of result.conversations) byId.set(conversation.id, conversation);
        this.conversations.set(this.sortConversations([...byId.values()]));
        this.recentPage.set(result.page);
        this.recentHasMore.set(result.has_more);
        this.totalUnread.set(result.total_unread);
        this.isLoadingRecent.set(false);
      },
      error: () => {
        this.isLoadingRecent.set(false);
        this.toast.error(this.i18n.t('employee_chat_error'));
      },
    });
  }

  private refreshRecentChats(): void {
    if (this.isLoadingRecent() || this.recentRefreshInFlight) return;
    this.recentRefreshInFlight = true;
    this.service.listConversations(1, 20).pipe(
      takeUntilDestroyed(this.destroyRef),
    ).subscribe({
      next: (result) => {
        const firstPageIds = new Set(result.conversations.map((conversation) => conversation.id));
        const loadedOlder = this.conversations().filter((conversation) => !firstPageIds.has(conversation.id));
        this.conversations.set(this.sortConversations([...result.conversations, ...loadedOlder]));
        this.recentHasMore.set(result.has_more || loadedOlder.length > 0);
        this.totalUnread.set(result.total_unread);
        this.recentRefreshInFlight = false;
      },
      error: () => {
        this.recentRefreshInFlight = false;
      },
    });
  }

  protected startConversation(employee: EmployeeChatPerson): void {
    if (this.startingEmployeeId()) return;
    this.startingEmployeeId.set(employee.employee_id);
    this.service.startConversation(employee.employee_id).pipe(
      takeUntilDestroyed(this.destroyRef),
    ).subscribe({
      next: (conversation) => {
        this.startingEmployeeId.set(null);
        this.upsertConversation(conversation);
        this.selectConversation(conversation);
      },
      error: () => {
        this.startingEmployeeId.set(null);
        this.toast.error(this.i18n.t('employee_chat_error'));
      },
    });
  }

  protected selectConversation(conversation: EmployeeConversation): void {
    if (this.selectedConversation()?.id === conversation.id) return;
    this.stopTyping();
    this.clearRemoteTyping();
    this.clearImagePreviews();
    this.selectedFile.set(null);
    this.followLatest = true;
    this.newMessageCount.set(0);
    this.pendingScroll = null;
    this.selectedConversation.set(conversation);
    this.messages.set([]);
    this.hasOlderMessages.set(false);
    this.isLoadingOlder.set(false);
    this.scrollBottomAfterOlderLoad = false;
    this.isLoadingMessages.set(true);
    this.nextBeforeId = null;
    this.markConversationRead(conversation.id);
    this.service.listMessages(conversation.id, 50).pipe(
      takeUntilDestroyed(this.destroyRef),
    ).subscribe({
      next: (result) => {
        if (this.selectedConversation()?.id !== conversation.id) return;
        const currentMessages = new Map(this.messages().map((message) => [message.id, message]));
        for (const message of result.messages) currentMessages.set(message.id, message);
        this.messages.set([...currentMessages.values()].sort((left, right) => left.id - right.id));
        this.loadImagePreviews(result.messages);
        this.hasOlderMessages.set(result.has_more);
        this.nextBeforeId = result.next_before_id;
        this.isLoadingMessages.set(false);
        this.pendingScroll = 'bottom';
      },
      error: () => {
        if (this.selectedConversation()?.id !== conversation.id) return;
        this.isLoadingMessages.set(false);
        this.toast.error(this.i18n.t('employee_chat_error'));
      },
    });
  }

  protected backToConversations(): void {
    this.stopTyping();
    this.clearRemoteTyping();
    this.clearImagePreviews();
    this.selectedFile.set(null);
    this.selectedConversation.set(null);
    this.messages.set([]);
    this.newMessageCount.set(0);
  }

  protected onMessageScroll(event: Event): void {
    const viewport = event.currentTarget as HTMLDivElement;
    this.followLatest = viewport.scrollHeight - viewport.clientHeight - viewport.scrollTop < 80;
    if (this.followLatest && this.newMessageCount() > 0) this.newMessageCount.set(0);
    if (viewport.scrollTop <= 48 && this.hasOlderMessages() && !this.isLoadingOlder()) {
      this.loadOlderMessages(viewport);
    }
  }

  protected scrollToNewMessages(): void {
    if (this.isLoadingOlder()) {
      this.scrollBottomAfterOlderLoad = true;
      return;
    }
    this.followLatest = true;
    this.pendingScroll = 'bottom';
  }

  protected onPreviewImageLoaded(): void {
    if (this.followLatest) this.scrollToLatest();
  }

  private loadOlderMessages(viewport: HTMLDivElement): void {
    const conversation = this.selectedConversation();
    if (!conversation || this.nextBeforeId === null) return;
    const beforeId = this.nextBeforeId;
    this.previousScrollHeight = viewport.scrollHeight;
    this.scrollBottomAfterOlderLoad = false;
    this.isLoadingOlder.set(true);
    this.service.listMessages(conversation.id, 50, beforeId).pipe(
      takeUntilDestroyed(this.destroyRef),
    ).subscribe({
      next: (result) => {
        if (this.selectedConversation()?.id !== conversation.id) return;
        this.messages.update((current) => [...result.messages, ...current]);
        this.loadImagePreviews(result.messages);
        this.hasOlderMessages.set(result.has_more);
        this.nextBeforeId = result.next_before_id;
        this.isLoadingOlder.set(false);
        const scrollToBottom = this.scrollBottomAfterOlderLoad;
        this.scrollBottomAfterOlderLoad = false;
        this.pendingScroll = scrollToBottom ? 'bottom' : 'preserve';
      },
      error: () => {
        this.isLoadingOlder.set(false);
        if (this.scrollBottomAfterOlderLoad) this.pendingScroll = 'bottom';
        this.scrollBottomAfterOlderLoad = false;
        this.toast.error(this.i18n.t('employee_chat_error'));
      },
    });
  }

  protected sendMessage(): void {
    const conversation = this.selectedConversation();
    const body = this.messageText().trim();
    const file = this.selectedFile();
    if (!conversation || (!body && !file) || this.isSending()) return;

    this.stopTyping();
    this.isSending.set(true);
    const request = file
      ? this.service.sendAttachment(conversation.id, body, file)
      : this.service.sendMessage(conversation.id, body);
    request.pipe(
      takeUntilDestroyed(this.destroyRef),
    ).subscribe({
      next: (message) => {
        this.isSending.set(false);
        if (this.selectedConversation()?.id !== conversation.id) return;
        this.messageText.set('');
        this.selectedFile.set(null);
        this.appendMessage(message);
        this.loadImagePreviews([message]);
        this.upsertConversation({
          ...conversation,
          last_message: message.body || message.attachment?.file_name || '',
          last_activity_at: message.created_at,
        });
        this.pendingScroll = 'bottom';
      },
      error: () => {
        this.isSending.set(false);
        this.toast.error(this.i18n.t('employee_chat_error'));
      },
    });
  }

  protected onComposerKeydown(event: KeyboardEvent): void {
    if (event.key === 'Enter' && !event.shiftKey) {
      event.preventDefault();
      this.sendMessage();
    }
  }

  protected onComposerInput(event: Event): void {
    const conversation = this.selectedConversation();
    const hasContent = (event.target as HTMLTextAreaElement).value.trim().length > 0;
    if (!conversation || !hasContent) {
      this.stopTyping();
      return;
    }

    if (this.localTypingConversationId !== conversation.id) {
      this.stopTyping();
      this.localTypingConversationId = conversation.id;
      this.sendTypingEvent(conversation.id, true);
      this.typingHeartbeatTimer = setInterval(
        () => this.sendTypingEvent(conversation.id, true),
        1800,
      );
    }

    if (this.typingIdleTimer !== undefined) clearTimeout(this.typingIdleTimer);
    this.typingIdleTimer = setTimeout(() => this.stopTyping(), 850);
  }

  protected onAttachmentSelected(event: Event): void {
    const input = event.target as HTMLInputElement;
    const file = input.files?.[0];
    input.value = '';
    if (!file) return;

    const extension = file.name.split('.').at(-1)?.toLowerCase() ?? '';
    const allowedMimes = SUPPORTED_ATTACHMENT_MIMES[extension];
    if (!allowedMimes || (file.type && file.type !== 'application/octet-stream' && !allowedMimes.includes(file.type))) {
      this.toast.error(this.i18n.t('employee_chat_attachment_invalid'));
      return;
    }
    if (file.size === 0 || file.size > MAX_ATTACHMENT_SIZE) {
      this.toast.error(this.i18n.t('employee_chat_attachment_size'));
      return;
    }
    this.selectedFile.set(file);
  }

  protected removeSelectedFile(): void {
    this.selectedFile.set(null);
  }

  protected attachmentIcon(attachment: EmployeeChatAttachment) {
    const extension = attachment.file_name.split('.').at(-1)?.toLowerCase();
    if (attachment.is_image) return this.ImageFileIcon;
    if (extension === 'xls' || extension === 'xlsx') return this.SpreadsheetIcon;
    if (extension === 'ppt' || extension === 'pptx') return this.PresentationIcon;
    if (extension === 'zip' || extension === 'rar' || extension === '7z') return this.ArchiveIcon;
    return this.TextFileIcon;
  }

  protected formatFileSize(bytes: number): string {
    const unit = bytes < 1024 * 1024 ? 'KB' : 'MB';
    const size = unit === 'KB' ? bytes / 1024 : bytes / (1024 * 1024);
    return `${new Intl.NumberFormat(this.i18n.lang(), { maximumFractionDigits: 1 }).format(size)} ${unit}`;
  }

  protected imagePreviewUrl(message: EmployeeMessage): string | null {
    return this.imagePreviewUrls()[message.id] ?? null;
  }

  protected downloadAttachment(message: EmployeeMessage): void {
    if (!message.attachment) return;
    this.service.fetchAttachment(message.conversation_id, message.id).pipe(
      takeUntilDestroyed(this.destroyRef),
    ).subscribe({
      next: (file) => this.triggerDownload(file, message.attachment!.file_name),
      error: () => this.toast.error(this.i18n.t('employee_chat_attachment_download_error')),
    });
  }

  private loadImagePreviews(messages: EmployeeMessage[]): void {
    const conversationId = this.selectedConversation()?.id;
    if (!conversationId) return;
    for (const message of messages) {
      if (!message.attachment?.is_image || this.imagePreviewUrls()[message.id] || this.loadingPreviewIds.has(message.id)) {
        continue;
      }
      this.loadingPreviewIds.add(message.id);
      this.service.fetchAttachment(conversationId, message.id, true).pipe(
        takeUntilDestroyed(this.destroyRef),
      ).subscribe({
        next: (blob) => {
          if (this.selectedConversation()?.id !== conversationId) return;
          const url = URL.createObjectURL(blob);
          this.imagePreviewUrls.update((urls) => ({ ...urls, [message.id]: url }));
        },
        error: () => undefined,
        complete: () => this.loadingPreviewIds.delete(message.id),
      });
    }
  }

  private clearImagePreviews(): void {
    for (const url of Object.values(this.imagePreviewUrls())) URL.revokeObjectURL(url);
    this.imagePreviewUrls.set({});
    this.loadingPreviewIds.clear();
  }

  private triggerDownload(file: Blob, fileName: string): void {
    const url = URL.createObjectURL(file);
    const anchor = document.createElement('a');
    anchor.href = url;
    anchor.download = fileName;
    anchor.click();
    setTimeout(() => URL.revokeObjectURL(url), 0);
  }

  protected formatMessageTime(value: string): string {
    return new Intl.DateTimeFormat(this.i18n.lang(), {
      hour: 'numeric',
      minute: '2-digit',
    }).format(new Date(value));
  }

  protected employeeInitial(person: EmployeeChatPerson): string {
    return person.full_name.trim().charAt(0).toLocaleUpperCase(this.i18n.lang());
  }

  ngAfterViewChecked(): void {
    const viewport = this.messageViewport?.nativeElement;
    if (!viewport || !this.pendingScroll) return;
    if (this.pendingScroll === 'bottom') {
      this.followLatest = true;
      this.newMessageCount.set(0);
      this.scrollToLatest();
    } else {
      viewport.scrollTop = viewport.scrollHeight - this.previousScrollHeight;
    }
    this.pendingScroll = null;
  }

  private scrollToLatest(): void {
    const viewport = this.messageViewport?.nativeElement;
    if (!viewport) return;
    viewport.scrollTop = viewport.scrollHeight;
    requestAnimationFrame(() => {
      if (this.followLatest && this.messageViewport?.nativeElement === viewport) {
        viewport.scrollTop = viewport.scrollHeight;
      }
    });
  }

  private scrollForTypingIndicator(conversationId: number): void {
    requestAnimationFrame(() => {
      requestAnimationFrame(() => {
        if (
          this.selectedConversation()?.id !== conversationId ||
          !this.isOtherTyping() ||
          !this.followLatest
        ) {
          return;
        }
        this.scrollToLatest();
      });
    });
  }

  ngOnDestroy(): void {
    this.stopTyping();
    this.isDestroying = true;
    if (this.searchTimer !== undefined) clearTimeout(this.searchTimer);
    if (this.pollTimer !== undefined) clearInterval(this.pollTimer);
    if (this.reconnectTimer !== undefined) clearTimeout(this.reconnectTimer);
    this.clearRemoteTyping();
    this.realtimeSocket?.close();
    void this.audioContext?.close();
    this.clearImagePreviews();
  }

  private connectRealtime(): void {
    if (this.isDestroying) return;
    const token = this.auth.token();
    if (!token) return;

    const socket = this.service.connectRealtime(token);
    this.realtimeSocket = socket;
    socket.onopen = () => {
      this.reconnectDelay = 1000;
      if (this.localTypingConversationId !== null) {
        this.sendTypingEvent(this.localTypingConversationId, true);
      }
    };
    socket.onmessage = (event) => this.handleRealtimeEvent(event.data);
    socket.onerror = () => socket.close();
    socket.onclose = () => {
      if (this.isDestroying || this.realtimeSocket !== socket) return;
      this.realtimeSocket = undefined;
      this.reconnectTimer = setTimeout(() => this.connectRealtime(), this.reconnectDelay);
      this.reconnectDelay = Math.min(this.reconnectDelay * 2, 30000);
    };
  }

  private handleRealtimeEvent(data: unknown): void {
    let event: {
      type?: string;
      message?: EmployeeMessage;
      conversation_id?: number;
      total_unread?: number;
      employee_id?: string;
      is_typing?: boolean;
    };
    try {
      event = JSON.parse(String(data));
    } catch {
      return;
    }

    if (event.type === 'typing') {
      const typingConversationId = event.conversation_id;
      if (
        typeof typingConversationId === 'number' &&
        typingConversationId === this.selectedConversation()?.id &&
        event.employee_id !== this.currentEmployeeId()
      ) {
        if (event.is_typing) {
          const indicatorWasVisible = this.isOtherTyping();
          this.isOtherTyping.set(true);
          if (this.remoteTypingTimer !== undefined) clearTimeout(this.remoteTypingTimer);
          this.remoteTypingTimer = setTimeout(() => this.clearRemoteTyping(), 2800);
          if (!indicatorWasVisible) {
            if (this.followLatest) this.scrollForTypingIndicator(typingConversationId);
            this.startTypingSound();
          }
        } else {
          this.clearRemoteTyping();
        }
      }
      return;
    }

    if (event.type === 'read' && typeof event.total_unread === 'number') {
      this.totalUnread.set(event.total_unread);
      if (typeof event.conversation_id === 'number') {
        const conversationId = event.conversation_id;
        this.conversations.update((items) => items.map((item) =>
          item.id === conversationId ? { ...item, unread_count: 0 } : item,
        ));
        this.selectedConversation.update((item) => item?.id === conversationId
          ? { ...item, unread_count: 0 }
          : item,
        );
      }
      return;
    }
    if (event.type !== 'message' || !event.message) return;

    const message = event.message;
    const isReceived = message.recipient_id === this.currentEmployeeId();
    const conversation = this.conversations().find((item) => item.id === message.conversation_id);
    const selected = this.selectedConversation();

    if (isReceived) this.playNotificationSound();
    if (selected?.id === message.conversation_id) {
      const viewport = this.messageViewport?.nativeElement;
      const wasAtBottom = !viewport || viewport.scrollHeight - viewport.clientHeight - viewport.scrollTop < 80;
      this.appendMessage(message);
      this.loadImagePreviews([message]);
      const updatedConversation = {
        ...selected,
        last_message: message.body || message.attachment?.file_name || '',
        last_activity_at: message.created_at,
        unread_count: isReceived ? 0 : selected.unread_count,
      };
      this.selectedConversation.set(updatedConversation);
      this.upsertConversation(updatedConversation);
      if (isReceived) this.markConversationRead(message.conversation_id);
      if (isReceived) {
        if (wasAtBottom) {
          this.newMessageCount.set(0);
          if (this.isLoadingOlder()) {
            this.scrollBottomAfterOlderLoad = true;
          } else {
            this.followLatest = true;
            this.pendingScroll = 'bottom';
          }
        } else {
          this.newMessageCount.update((count) => count + 1);
        }
      } else if (wasAtBottom) {
        this.pendingScroll = 'bottom';
      }
    } else if (isReceived) {
      this.totalUnread.update((count) => count + 1);
      if (conversation) {
        this.upsertConversation({
          ...conversation,
          last_message: message.body || message.attachment?.file_name || '',
          last_activity_at: message.created_at,
          unread_count: conversation.unread_count + 1,
        });
      }
    }
    this.refreshRecentChats();
  }

  private sendTypingEvent(conversationId: number, isTyping: boolean): void {
    if (this.realtimeSocket?.readyState !== WebSocket.OPEN) return;
    this.realtimeSocket.send(JSON.stringify({
      type: 'typing',
      conversation_id: conversationId,
      is_typing: isTyping,
    }));
  }

  private stopTyping(): void {
    if (this.typingIdleTimer !== undefined) clearTimeout(this.typingIdleTimer);
    if (this.typingHeartbeatTimer !== undefined) clearInterval(this.typingHeartbeatTimer);
    this.typingIdleTimer = undefined;
    this.typingHeartbeatTimer = undefined;

    if (this.localTypingConversationId !== null) {
      this.sendTypingEvent(this.localTypingConversationId, false);
      this.localTypingConversationId = null;
    }
  }

  private clearRemoteTyping(): void {
    if (this.remoteTypingTimer !== undefined) clearTimeout(this.remoteTypingTimer);
    this.remoteTypingTimer = undefined;
    this.isOtherTyping.set(false);
    this.stopTypingSound();
  }

  private startTypingSound(): void {
    if (this.typingSoundTimer !== undefined) return;
    this.playTypingTick();
    this.typingSoundTimer = setInterval(() => {
      if (!this.isOtherTyping()) {
        this.stopTypingSound();
        return;
      }
      this.playTypingTick();
    }, 1100);
  }

  private stopTypingSound(): void {
    if (this.typingSoundTimer !== undefined) clearInterval(this.typingSoundTimer);
    this.typingSoundTimer = undefined;
  }

  private playTypingTick(): void {
    try {
      const context = this.audioContext ?? new AudioContext();
      this.audioContext = context;
      if (context.state === 'suspended') void context.resume().catch(() => undefined);

      const oscillator = context.createOscillator();
      const volume = context.createGain();
      const now = context.currentTime;
      oscillator.type = 'sine';
      oscillator.frequency.setValueAtTime(720, now);
      oscillator.frequency.exponentialRampToValueAtTime(520, now + 0.035);
      volume.gain.setValueAtTime(0.0001, now);
      volume.gain.exponentialRampToValueAtTime(0.012, now + 0.004);
      volume.gain.exponentialRampToValueAtTime(0.0001, now + 0.045);
      oscillator.connect(volume);
      volume.connect(context.destination);
      oscillator.start(now);
      oscillator.stop(now + 0.05);
    } catch {
      return;
    }
  }

  private markConversationRead(conversationId: number): void {
    if (this.markingRead.has(conversationId)) return;
    this.markingRead.add(conversationId);
    this.conversations.update((items) => items.map((item) =>
      item.id === conversationId ? { ...item, unread_count: 0 } : item,
    ));
    this.selectedConversation.update((item) => item?.id === conversationId
      ? { ...item, unread_count: 0 }
      : item,
    );

    this.service.markConversationRead(conversationId).pipe(
      takeUntilDestroyed(this.destroyRef),
    ).subscribe({
      next: (result) => this.totalUnread.set(result.total_unread),
      error: () => {
        this.markingRead.delete(conversationId);
        this.refreshRecentChats();
      },
      complete: () => this.markingRead.delete(conversationId),
    });
  }

  private playNotificationSound(): void {
    try {
      const context = this.audioContext ?? new AudioContext();
      this.audioContext = context;
      if (context.state === 'suspended') void context.resume().catch(() => undefined);

      const oscillator = context.createOscillator();
      const volume = context.createGain();
      const now = context.currentTime;
      oscillator.type = 'sine';
      oscillator.frequency.setValueAtTime(880, now);
      oscillator.frequency.exponentialRampToValueAtTime(660, now + 0.15);
      volume.gain.setValueAtTime(0.0001, now);
      volume.gain.exponentialRampToValueAtTime(0.08, now + 0.015);
      volume.gain.exponentialRampToValueAtTime(0.0001, now + 0.18);
      oscillator.connect(volume);
      volume.connect(context.destination);
      oscillator.start(now);
      oscillator.stop(now + 0.19);
    } catch {
      return;
    }
  }

  private refreshSelectedMessages(): void {
    const conversation = this.selectedConversation();
    if (!conversation || this.isLoadingMessages() || this.isLoadingOlder()) return;
    const conversationId = conversation.id;
    const viewport = this.messageViewport?.nativeElement;
    const wasAtBottom = !viewport || viewport.scrollHeight - viewport.clientHeight - viewport.scrollTop < 80;

    this.service.listMessages(conversationId, 50).pipe(
      takeUntilDestroyed(this.destroyRef),
    ).subscribe({
      next: (result) => {
        if (this.selectedConversation()?.id !== conversationId) return;
        const previousCount = this.messages().length;
        const knownMessageIds = new Set(this.messages().map((message) => message.id));
        const newReceivedMessages = result.messages.filter(
          (message) => !knownMessageIds.has(message.id) && message.recipient_id === this.currentEmployeeId(),
        );
        const byId = new Map(this.messages().map((message) => [message.id, message]));
        for (const message of result.messages) byId.set(message.id, message);
        const merged = [...byId.values()].sort((left, right) => left.id - right.id);
        this.messages.set(merged);
        this.loadImagePreviews(result.messages);
        if (newReceivedMessages.length > 0) {
          if (wasAtBottom) {
            this.newMessageCount.set(0);
            if (this.isLoadingOlder()) {
              this.scrollBottomAfterOlderLoad = true;
            } else {
              this.followLatest = true;
              this.pendingScroll = 'bottom';
            }
          } else {
            this.newMessageCount.update((count) => count + newReceivedMessages.length);
          }
        } else if (merged.length > previousCount && wasAtBottom) {
          this.pendingScroll = 'bottom';
        }
        const lastMessage = result.messages.at(-1);
        if (lastMessage) {
          this.upsertConversation({
            ...conversation,
            last_message: lastMessage.body || lastMessage.attachment?.file_name || '',
            last_activity_at: lastMessage.created_at,
          });
        }
      },
    });
  }

  private appendMessage(message: EmployeeMessage): void {
    this.messages.update((current) =>
      current.some((existing) => existing.id === message.id) ? current : [...current, message],
    );
  }

  private upsertConversation(conversation: EmployeeConversation): void {
    const conversations = new Map(this.conversations().map((item) => [item.id, item]));
    conversations.set(conversation.id, conversation);
    this.conversations.set(this.sortConversations([...conversations.values()]));
  }

  private sortConversations(conversations: EmployeeConversation[]): EmployeeConversation[] {
    return conversations.sort(
      (left, right) => Date.parse(right.last_activity_at) - Date.parse(left.last_activity_at),
    );
  }
}