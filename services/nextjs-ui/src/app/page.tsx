/**
 * Home Page
 * Main chat interface for the AI platform
 */

'use client';

import { MainLayout } from '@/components/layout';
import { ChatInterface } from '@/components/chat';

export default function HomePage() {
  return (
    <MainLayout>
      <ChatInterface />
    </MainLayout>
  );
}
