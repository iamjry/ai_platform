/**
 * Chat Interface Component
 * Main chat UI with message list and input area
 */

'use client';

import * as React from 'react';
import { Box, Paper } from '@mui/material';
import { MessageList } from './MessageList';
import { InputArea } from './InputArea';
import { ModelSelector } from './ModelSelector';
import { agentApi, type ConversationMessage } from '@/lib/api';

export function ChatInterface() {
  const [messages, setMessages] = React.useState<ConversationMessage[]>([]);
  const [selectedModel, setSelectedModel] = React.useState<string>('claude-3-5-haiku-20241022');
  const [isLoading, setIsLoading] = React.useState(false);
  const [conversationId, setConversationId] = React.useState<string>('');

  const handleSendMessage = async (message: string) => {
    if (!message.trim() || isLoading) return;

    // Add user message
    const userMessage: ConversationMessage = {
      role: 'user',
      content: message,
      timestamp: new Date().toISOString(),
    };
    setMessages((prev) => [...prev, userMessage]);
    setIsLoading(true);

    try {
      // Execute agent task with streaming
      let assistantContent = '';
      const assistantMessage: ConversationMessage = {
        role: 'assistant',
        content: '',
        timestamp: new Date().toISOString(),
        model: selectedModel,
      };

      // Add empty assistant message that will be updated
      setMessages((prev) => [...prev, assistantMessage]);

      await agentApi.executeStream(
        {
          task: message,
          model: selectedModel,
          conversation_id: conversationId || undefined,
        },
        // onChunk
        (chunk) => {
          assistantContent += chunk;
          setMessages((prev) => {
            const newMessages = [...prev];
            newMessages[newMessages.length - 1] = {
              ...newMessages[newMessages.length - 1],
              content: assistantContent,
            };
            return newMessages;
          });
        },
        // onComplete
        (response) => {
          setConversationId(response.conversation_id);
          setMessages((prev) => {
            const newMessages = [...prev];
            newMessages[newMessages.length - 1] = {
              ...newMessages[newMessages.length - 1],
              content: response.response,
              model: response.model_used,
              tokens: response.total_tokens,
            };
            return newMessages;
          });
          setIsLoading(false);
        },
        // onError
        (error) => {
          console.error('Error executing agent:', error);
          setMessages((prev) => {
            const newMessages = [...prev];
            newMessages[newMessages.length - 1] = {
              ...newMessages[newMessages.length - 1],
              content: `錯誤: ${error.message}`,
            };
            return newMessages;
          });
          setIsLoading(false);
        }
      );
    } catch (error) {
      console.error('Error sending message:', error);
      setIsLoading(false);
    }
  };

  const handleClearChat = () => {
    setMessages([]);
    setConversationId('');
  };

  return (
    <Box
      sx={{
        height: 'calc(100vh - 64px)',
        display: 'flex',
        flexDirection: 'column',
        p: 2,
      }}
    >
      {/* Model Selector */}
      <Box sx={{ mb: 2 }}>
        <ModelSelector
          selectedModel={selectedModel}
          onModelChange={setSelectedModel}
          onClearChat={handleClearChat}
        />
      </Box>

      {/* Chat Area */}
      <Paper
        elevation={1}
        sx={{
          flexGrow: 1,
          display: 'flex',
          flexDirection: 'column',
          overflow: 'hidden',
        }}
      >
        {/* Message List */}
        <MessageList messages={messages} isLoading={isLoading} />

        {/* Input Area */}
        <InputArea onSendMessage={handleSendMessage} disabled={isLoading} />
      </Paper>
    </Box>
  );
}
