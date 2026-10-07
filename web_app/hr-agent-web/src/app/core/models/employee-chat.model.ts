export interface EmployeeChatPerson {
  employee_id: string;
  full_name: string;
  avatar_url: string | null;
}

export interface EmployeeDirectoryPage {
  employees: EmployeeChatPerson[];
  page: number;
  page_size: number;
  has_more: boolean;
}

export interface EmployeeConversation {
  id: number;
  employee: EmployeeChatPerson;
  last_message: string | null;
  last_activity_at: string;
  unread_count: number;
}

export interface EmployeeConversationPage {
  conversations: EmployeeConversation[];
  page: number;
  page_size: number;
  has_more: boolean;
  total_unread: number;
}

export interface EmployeeMessage {
  id: number;
  conversation_id: number;
  sender_id: string;
  recipient_id: string;
  body: string;
  created_at: string;
  attachment?: EmployeeChatAttachment | null;
}

export interface EmployeeChatAttachment {
  id: number;
  file_name: string;
  content_type: string;
  file_size: number;
  is_image: boolean;
}

export interface EmployeeMessagePage {
  messages: EmployeeMessage[];
  has_more: boolean;
  next_before_id: number | null;
}