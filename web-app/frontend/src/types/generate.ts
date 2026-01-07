export interface Recipient {
  email: string;
  count: number;
}

export interface Email {
  message_id: string;
  subject: string;
  sender: string;
  receiver: string;
  sent_at: string;
}

export interface ThreadMessage {
  message_id: string;
  parent_message_id: string | null;
  references: string[];
  sender: string;
  receiver: string;
  subject: string;
  content: string;
  sent_at: string;
}

export interface GenerateInput {
  sender: string;
  receiver: string;
  content: string;
  custom_prompt: string;
  thread_messages: ThreadMessage[];
}
