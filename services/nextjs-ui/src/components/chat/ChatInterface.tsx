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
  const [selectedModel, setSelectedModel] = React.useState<string>('claude-3-haiku');
  const [isLoading, setIsLoading] = React.useState(false);
  const [conversationHistory, setConversationHistory] = React.useState<Array<{role: string, content: string}>>([]);

  const handleSendMessage = async (message: string) => {
    if (!message.trim() || isLoading) return;

    // Add user message
    const userMessage: ConversationMessage = {
      role: 'user',
      content: message,
      timestamp: new Date().toISOString(),
    };
    setMessages((prev) => [...prev, userMessage]);

    // Update conversation history
    const newHistory = [...conversationHistory, { role: 'user', content: message }];
    setConversationHistory(newHistory);

    setIsLoading(true);

    try {
      // Execute agent task (non-streaming)
      const response = await agentApi.execute({
        task: message,
        model: selectedModel,
        conversation_history: newHistory,
        temperature: 0.7,
        top_p: 0.9,
        top_k: 40,
      });

      // Update conversation history with assistant response
      setConversationHistory((prev) => [
        ...prev,
        { role: 'assistant', content: response.result }
      ]);

      // Add assistant message
      const assistantMessage: ConversationMessage = {
        role: 'assistant',
        content: response.result,
        timestamp: new Date().toISOString(),
        model: response.metadata?.model_used || selectedModel,
        tokens: response.metadata?.total_tokens,
      };
      setMessages((prev) => [...prev, assistantMessage]);

      setIsLoading(false);
    } catch (error: any) {
      console.error('Error sending message:', error);

      // Add error message
      const errorMessage: ConversationMessage = {
        role: 'assistant',
        content: `錯誤: ${error.message || 'Unknown error'}`,
        timestamp: new Date().toISOString(),
      };
      setMessages((prev) => [...prev, errorMessage]);

      setIsLoading(false);
    }
  };

  const handleClearChat = () => {
    setMessages([]);
    setConversationHistory([]);
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
