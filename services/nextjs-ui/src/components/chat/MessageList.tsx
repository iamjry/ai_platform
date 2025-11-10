/**
 * Message List Component
 * Displays chat messages with auto-scroll
 */

'use client';

import * as React from 'react';
import { Box, CircularProgress } from '@mui/material';
import { MessageBubble } from './MessageBubble';
import type { ConversationMessage } from '@/lib/api';

interface MessageListProps {
  messages: ConversationMessage[];
  isLoading: boolean;
}

export function MessageList({ messages, isLoading }: MessageListProps) {
  const messagesEndRef = React.useRef<HTMLDivElement>(null);

  // Auto-scroll to bottom when new messages arrive
  React.useEffect(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  }, [messages]);

  return (
    <Box
      sx={{
        flexGrow: 1,
        overflow: 'auto',
        p: 2,
        display: 'flex',
        flexDirection: 'column',
        gap: 2,
      }}
    >
      {messages.length === 0 && (
        <Box
          sx={{
            display: 'flex',
            justifyContent: 'center',
            alignItems: 'center',
            height: '100%',
            color: 'text.secondary',
          }}
        >
          開始對話...
        </Box>
      )}

      {messages.map((message, index) => (
        <MessageBubble key={index} message={message} />
      ))}

      {isLoading && messages[messages.length - 1]?.role === 'user' && (
        <Box sx={{ display: 'flex', alignItems: 'center', gap: 2, ml: 2 }}>
          <CircularProgress size={20} />
          <span>思考中...</span>
        </Box>
      )}

      <div ref={messagesEndRef} />
    </Box>
  );
}
