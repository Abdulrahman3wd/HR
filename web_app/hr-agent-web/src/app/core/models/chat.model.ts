export interface AskRequest {
  question: string;
}

export interface AskResponse {
  answer: string;
  source_type: 'policy' | 'personal';
  sources: string[];
}

export interface ChatMessage {
  role: 'user' | 'agent';
  text: string;
  sources?: string[];
}