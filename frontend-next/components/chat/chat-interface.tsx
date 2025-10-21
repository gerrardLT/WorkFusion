'use client';

import * as React from 'react';
import { ScrollArea } from '@/lib/scroll-area';
import {
  MessageSquare,
  RefreshCw,
  Trash2,
  Download,
  Settings,
  ChevronDown,
  Star
} from 'lucide-react';

import { Button } from '@/components/ui/button';
import { Card } from '@/components/ui/card';
import { Badge } from '@/components/ui/badge';
import { MessageBubble } from './message-bubble';
import { InputArea } from './input-area';
import { cn, generateId } from '@/lib/utils';
import { useScenario } from '@/contexts/scenario-context';
import { Message, Chat } from '@/lib/types';

interface ChatInterfaceProps {
  chat?: Chat;
  messages: Message[];
  loading?: boolean;
  suggestions?: string[];
  onSendMessage: (message: string) => void;
  onRegenerateMessage?: (messageId: string) => void;
  onDeleteMessage?: (messageId: string) => void;
  onClearChat?: () => void;
  onExportChat?: () => void;
  onFeedback?: (messageId: string, type: 'like' | 'dislike') => void;
  showWelcome?: boolean;
  welcomeMessage?: React.ReactNode;
  className?: string;
}

export function ChatInterface({
  chat,
  messages = [],
  loading = false,
  suggestions = [],
  onSendMessage,
  onRegenerateMessage,
  onDeleteMessage,
  onClearChat,
  onExportChat,
  onFeedback,
  showWelcome = true,
  welcomeMessage,
  className,
}: ChatInterfaceProps) {
  const { getCurrentUI, state } = useScenario();
  const [autoScroll, setAutoScroll] = React.useState(true);
  const [showScrollToBottom, setShowScrollToBottom] = React.useState(false);
  const messagesEndRef = React.useRef<HTMLDivElement>(null);
  const messagesContainerRef = React.useRef<HTMLDivElement>(null);

  // Auto scroll to bottom when new messages arrive
  React.useEffect(() => {
    if (autoScroll && messagesEndRef.current) {
      messagesEndRef.current.scrollIntoView({ behavior: 'smooth' });
    }
  }, [messages, autoScroll]);

  // Handle scroll to check if user has scrolled up
  const handleScroll = React.useCallback(() => {
    if (!messagesContainerRef.current) return;

    const { scrollTop, scrollHeight, clientHeight } = messagesContainerRef.current;
    const isNearBottom = scrollHeight - scrollTop - clientHeight < 100;

    setAutoScroll(isNearBottom);
    setShowScrollToBottom(!isNearBottom && messages.length > 0);
  }, [messages.length]);

  const scrollToBottom = () => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
    setAutoScroll(true);
  };

  const handleSendMessage = (message: string) => {
    onSendMessage(message);
    setAutoScroll(true);
  };

  // 获取当前场景的UI配置
  const currentUI = getCurrentUI();
  const currentScenario = state.currentScenario;

  const defaultWelcomeMessage = (
    <div className="text-center py-12">
      <div className={cn(
        "inline-flex items-center justify-center w-16 h-16 rounded-full mb-6 shadow-lg",
        currentScenario?.theme.gradientFrom && currentScenario?.theme.gradientTo
          ? `bg-gradient-to-br ${currentScenario.theme.gradientFrom} ${currentScenario.theme.gradientTo}`
          : "bg-gradient-to-br from-blue-500 to-blue-600"
      )}>
        <MessageSquare className="h-8 w-8 text-white" />
      </div>
      <h2 className="text-2xl font-bold text-gray-800 mb-3">
        {currentUI?.welcomeTitle || '欢迎使用智能问答'}
      </h2>
      <p className="text-gray-600 max-w-md mx-auto mb-6">
        {currentUI?.welcomeMessage || '我是您的专业AI助手，为您提供深度分析和专业建议'}
      </p>
      <div className="space-y-2">
        <p className="text-sm text-gray-600">您可以尝试问我：</p>
        <div className="flex flex-wrap gap-2 justify-center">
          {(currentScenario?.presetQuestions || [
            "这是一个测试问题？",
            "请帮我分析相关内容",
            "有什么值得关注的要点？",
            "请提供专业建议",
          ]).slice(0, 6).map((example, index) => (
            <Button
              key={index}
              variant="outline"
              size="sm"
              onClick={() => onSendMessage(example)}
              className="text-xs bg-gray-700 text-gray-200 border-gray-600 hover:bg-gray-600 hover:border-blue-500 hover:text-blue-400 transition-all duration-200"
            >
              {example}
            </Button>
          ))}
        </div>
      </div>
    </div>
  );

  const hasMessages = messages.length > 0;

  return (
    <div className={cn('flex flex-col h-full bg-gray-800 text-gray-100 chat-interface', className)}>

      {/* Messages Area */}
      <div className="flex-1 relative">
        <div
          ref={messagesContainerRef}
          onScroll={handleScroll}
          className="absolute inset-0 overflow-y-auto"
        >
          <div className="min-h-full">
            {/* Welcome Message */}
            {!hasMessages && showWelcome && (
              <div className="h-full flex items-center justify-center px-4">
                {welcomeMessage || defaultWelcomeMessage}
              </div>
            )}

            {/* Messages */}
            {hasMessages && (
              <div className="max-w-4xl mx-auto space-y-1 px-4">
                {messages.map((message, index) => (
                  <MessageBubble
                    key={message.id}
                    message={message}
                    showTimestamp={true}
                    onRegenerate={
                      onRegenerateMessage
                        ? () => onRegenerateMessage(message.id)
                        : undefined
                    }
                    onFeedback={
                      onFeedback
                        ? (type) => onFeedback(message.id, type)
                        : undefined
                    }
                    className={cn(
                      index === 0 && 'mt-4',
                      index === messages.length - 1 && 'mb-4'
                    )}
                  />
                ))}

                {/* Loading indicator */}
                {loading && (
                  <MessageBubble
                    message={{
                      id: 'loading',
                      content: '正在思考中...',
                      role: 'assistant',
                      timestamp: new Date(),
                      status: 'sending',
                    }}
                    showTimestamp={false}
                    showActions={false}
                  />
                )}

                <div ref={messagesEndRef} />
              </div>
            )}
          </div>
        </div>

        {/* Scroll to bottom button */}
        {showScrollToBottom && (
          <div className="absolute bottom-4 left-1/2 transform -translate-x-1/2">
            <Button
              variant="outline"
              size="sm"
              onClick={scrollToBottom}
              className="shadow-lg bg-gray-700 backdrop-blur-sm border-gray-600 text-gray-200 hover:bg-gray-600 hover:text-blue-400"
            >
              <ChevronDown className="h-4 w-4 mr-1" />
              滚动到底部
            </Button>
          </div>
        )}
      </div>

      {/* Input Area - 固定在底部 */}
      <div className="bg-gray-800 backdrop-blur-sm p-4">
        <div className="max-w-4xl mx-auto">
          <InputArea
            onSend={handleSendMessage}
            loading={loading}
            suggestions={suggestions}
            placeholder="输入您的问题..."
            allowFileUpload={true}
            acceptedFileTypes={['.pdf', '.txt', '.md', '.doc', '.docx', '.xlsx', '.csv']}
            maxLength={4000}
          />
        </div>
      </div>
    </div>
  );
}
