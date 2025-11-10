/**
 * Message Bubble Component
 * Individual message display with Material Design 3 styling
 */

'use client';

import * as React from 'react';
import { Box, Paper, Typography, Chip } from '@mui/material';
import PersonIcon from '@mui/icons-material/Person';
import SmartToyIcon from '@mui/icons-material/SmartToy';
import type { ConversationMessage } from '@/lib/api';

interface MessageBubbleProps {
  message: ConversationMessage;
}

export function MessageBubble({ message }: MessageBubbleProps) {
  const isUser = message.role === 'user';

  return (
    <Box
      sx={{
        display: 'flex',
        justifyContent: isUser ? 'flex-end' : 'flex-start',
        mb: 1,
      }}
    >
      <Paper
        elevation={0}
        sx={{
          maxWidth: '70%',
          p: 2,
          backgroundColor: isUser ? 'primary.main' : 'surfaceVariant',
          color: isUser ? 'primary.contrastText' : 'text.primary',
          borderRadius: 3,
        }}
      >
        {/* Header with icon and model */}
        <Box sx={{ display: 'flex', alignItems: 'center', gap: 1, mb: 1 }}>
          {isUser ? (
            <PersonIcon fontSize="small" />
          ) : (
            <SmartToyIcon fontSize="small" />
          )}
          <Typography variant="caption" sx={{ fontWeight: 500 }}>
            {isUser ? '你' : 'AI 助理'}
          </Typography>
          {!isUser && message.model && (
            <Chip
              label={message.model.split('/').pop()}
              size="small"
              sx={{ height: 20, fontSize: '0.65rem' }}
            />
          )}
        </Box>

        {/* Message content */}
        <Typography
          variant="body1"
          sx={{
            whiteSpace: 'pre-wrap',
            wordBreak: 'break-word',
          }}
        >
          {message.content}
        </Typography>

        {/* Footer with timestamp and tokens */}
        <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', mt: 1 }}>
          <Typography variant="caption" sx={{ opacity: 0.7 }}>
            {new Date(message.timestamp).toLocaleTimeString('zh-TW', {
              hour: '2-digit',
              minute: '2-digit',
            })}
          </Typography>
          {message.tokens && (
            <Typography variant="caption" sx={{ opacity: 0.7 }}>
              {message.tokens.toLocaleString()} tokens
            </Typography>
          )}
        </Box>
      </Paper>
    </Box>
  );
}
