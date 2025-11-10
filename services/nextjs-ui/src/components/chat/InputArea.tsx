/**
 * Input Area Component
 * Message input with send button
 */

'use client';

import * as React from 'react';
import { Box, TextField, IconButton, Paper } from '@mui/material';
import SendIcon from '@mui/icons-material/Send';

interface InputAreaProps {
  onSendMessage: (message: string) => void;
  disabled?: boolean;
}

export function InputArea({ onSendMessage, disabled = false }: InputAreaProps) {
  const [input, setInput] = React.useState('');

  const handleSend = () => {
    if (input.trim() && !disabled) {
      onSendMessage(input);
      setInput('');
    }
  };

  const handleKeyPress = (event: React.KeyboardEvent) => {
    if (event.key === 'Enter' && !event.shiftKey) {
      event.preventDefault();
      handleSend();
    }
  };

  return (
    <Paper
      elevation={0}
      sx={{
        p: 2,
        borderTop: 1,
        borderColor: 'divider',
      }}
    >
      <Box sx={{ display: 'flex', gap: 1 }}>
        <TextField
          fullWidth
          multiline
          maxRows={4}
          value={input}
          onChange={(e) => setInput(e.target.value)}
          onKeyPress={handleKeyPress}
          placeholder="輸入訊息... (Enter 發送, Shift+Enter 換行)"
          disabled={disabled}
          variant="outlined"
          sx={{
            '& .MuiOutlinedInput-root': {
              borderRadius: 3,
            },
          }}
        />
        <IconButton
          color="primary"
          onClick={handleSend}
          disabled={disabled || !input.trim()}
          sx={{
            width: 48,
            height: 48,
            alignSelf: 'flex-end',
          }}
        >
          <SendIcon />
        </IconButton>
      </Box>
    </Paper>
  );
}
