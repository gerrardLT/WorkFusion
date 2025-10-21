'use client';

import * as React from 'react';
import { format, zhCN } from '@/lib/date';
import {
  User,
  Bot,
  Copy,
  ThumbsUp,
  ThumbsDown,
  RefreshCw,
  Clock,
  CheckCircle2,
  XCircle,
  Loader2
} from 'lucide-react';
import ReactMarkdown from '@/lib/markdown';

import { Button } from '@/components/ui/button';
import { Card } from '@/components/ui/card';
import { Badge, ConfidenceBadge } from '@/components/ui/badge';
import { cn, copyToClipboard, formatDuration } from '@/lib/utils';
import { Message } from '@/lib/types';

interface MessageBubbleProps {
  message: Message;
  showTimestamp?: boolean;
  showActions?: boolean;
  onRegenerate?: () => void;
  onCopy?: () => void;
  onFeedback?: (type: 'like' | 'dislike') => void;
  className?: string;
}

export function MessageBubble({
  message,
  showTimestamp = false,
  showActions = true,
  onRegenerate,
  onCopy,
  onFeedback,
  className,
}: MessageBubbleProps) {
  const [copied, setCopied] = React.useState(false);
  const [expanded, setExpanded] = React.useState(false);

  const isUser = message.role === 'user';
  const isAssistant = message.role === 'assistant';
  const isSystem = message.role === 'system';

  const handleCopy = async () => {
    const success = await copyToClipboard(message.content);
    if (success) {
      setCopied(true);
      onCopy?.();
      setTimeout(() => setCopied(false), 2000);
    }
  };

  const getStatusIcon = () => {
    switch (message.status) {
      case 'sending':
        return <Loader2 className="h-3 w-3 animate-spin text-muted-foreground" />;
      case 'sent':
      case 'delivered':
        return <CheckCircle2 className="h-3 w-3 text-success-500" />;
      case 'error':
        return <XCircle className="h-3 w-3 text-error-500" />;
      default:
        return null;
    }
  };

  const getAvatarIcon = () => {
    if (isUser) return <User className="h-4 w-4" />;
    if (isSystem) return <Bot className="h-4 w-4 text-cyan-500" />;
    return <Bot className="h-4 w-4 text-brand-500" />;
  };

  const getMessageContainerClass = () => {
    if (isUser) {
      return 'ml-12 flex-row-reverse';
    }
    return 'mr-12';
  };

  const getBubbleClass = () => {
    if (isUser) {
      return 'bg-gradient-to-br from-blue-500 to-purple-600 text-white ml-auto shadow-lg';
    }
    if (isSystem) {
      return 'bg-gradient-to-br from-cyan-50 to-blue-50 border border-cyan-200/50 shadow-sm';
    }
    return 'bg-gray-800 backdrop-blur-sm border border-gray-700 shadow-sm hover:shadow-md transition-all duration-200';
  };

  return (
    <div className={cn('group flex gap-3 p-4', getMessageContainerClass(), className)}>
      {/* Avatar */}
      <div className={cn(
        'flex-shrink-0 w-10 h-10 rounded-full flex items-center justify-center shadow-sm',
        isUser
          ? 'bg-gradient-to-br from-blue-500 to-purple-600 text-white'
          : isSystem
          ? 'bg-gradient-to-br from-cyan-500 to-blue-500 text-white'
          : 'bg-gradient-to-br from-gray-600 to-gray-700 text-gray-200'
      )}>
        {getAvatarIcon()}
      </div>

      {/* Message Content */}
      <div className={cn('flex-1 min-w-0', isUser && 'flex flex-col items-end')}>
        {/* Message Header */}
        {showTimestamp && (
          <div className={cn(
            'flex items-center gap-2 mb-1 text-xs text-gray-400',
            isUser && 'flex-row-reverse'
          )}>
            <span className="font-medium text-gray-300">
              {isUser ? '您' : isSystem ? '系统' : 'AI助手'}
            </span>
            <span>{format(message.timestamp, 'HH:mm', { locale: zhCN })}</span>
            {getStatusIcon()}
          </div>
        )}

        {/* Message Bubble */}
        <Card className={cn(
          'relative max-w-4xl p-5 rounded-3xl',
          getBubbleClass(),
          message.status === 'sending' && 'opacity-70'
        )}>
          {/* Message Content */}
          <div className="prose prose-sm max-w-none prose-invert prose-headings:text-gray-100 prose-p:text-gray-100 prose-strong:text-gray-100 prose-code:text-gray-100 prose-pre:bg-gray-800 prose-pre:text-gray-100">
            {isUser ? (
              <p className="text-white m-0">{message.content}</p>
            ) : (
              <ReactMarkdown className="m-0 text-gray-100 [&>*]:text-gray-100 [&_p]:text-gray-100 [&_li]:text-gray-100 [&_strong]:text-gray-100 [&_em]:text-gray-100 [&_code]:text-gray-100 [&_a]:text-blue-400">
                {message.content}
              </ReactMarkdown>
            )}
          </div>

          {/* Metadata for Assistant Messages */}
          {isAssistant && message.metadata && (
            <div className="mt-4 space-y-3">
              {/* Confidence and Processing Time */}
              <div className="flex items-center gap-2 flex-wrap">
                {message.metadata.confidence && (
                  <ConfidenceBadge
                    confidence={message.metadata.confidence}
                    className="text-xs"
                  />
                )}

                {message.metadata.processingTime && (
                  <Badge variant="secondary" size="sm" icon={<Clock className="h-3 w-3" />}>
                    {formatDuration(message.metadata.processingTime)}
                  </Badge>
                )}

                {message.metadata.tokens && (
                  <Badge variant="outline" size="sm">
                    {message.metadata.tokens.total} tokens
                  </Badge>
                )}
              </div>

              {/* Sources */}
              {message.metadata.sources && message.metadata.sources.length > 0 && (
                <div className="border-t border-gray-600 pt-3">
                  <div className="flex items-center justify-between mb-2">
                    <span className="text-xs font-medium text-gray-300">
                      参考来源 ({message.metadata.sources.length})
                    </span>
                    <Button
                      variant="ghost"
                      size="sm"
                      onClick={() => setExpanded(!expanded)}
                      className="h-6 px-2 text-xs text-gray-300 hover:text-blue-400 hover:bg-gray-600"
                    >
                      {expanded ? '收起' : '展开'}
                    </Button>
                  </div>

                  {expanded && (
                    <div className="space-y-2">
                      {message.metadata.sources.map((source, index) => (
                        <div
                          key={index}
                          className="text-xs p-3 rounded-lg bg-gray-600/50 border border-gray-500"
                        >
                          <div className="flex items-center justify-between mb-1">
                            <span className="font-medium text-gray-200">第{source.page}页</span>
                            <Badge className="bg-blue-500/20 text-blue-300 border-blue-400" size="sm">
                              相关度: {Math.round(source.relevance_score * 100)}%
                            </Badge>
                          </div>
                          <p className="text-gray-300 line-clamp-2">
                            {source.content}
                          </p>
                        </div>
                      ))}
                    </div>
                  )}
                </div>
              )}

              {/* Reasoning (for debugging or transparency) */}
              {message.metadata.reasoning && expanded && (
                <div className="border-t border-gray-600 pt-3">
                  <span className="text-xs font-medium text-gray-300 mb-2 block">
                    推理过程
                  </span>
                  <div className="text-xs text-gray-300 bg-gray-600/50 p-3 rounded-lg border border-gray-500">
                    {message.metadata.reasoning}
                  </div>
                </div>
              )}
            </div>
          )}

          {/* File Attachments */}
          {message.attachments && message.attachments.length > 0 && (
            <div className="mt-3 space-y-2">
              {message.attachments.map((file, index) => (
                <div
                  key={index}
                  className="flex items-center gap-2 p-3 bg-gray-600/50 rounded-lg border border-gray-500 text-sm"
                >
                  <div className="w-8 h-8 bg-gray-500 rounded flex items-center justify-center">
                    📎
                  </div>
                  <div className="flex-1 min-w-0">
                    <p className="font-medium text-gray-200 truncate">{file.name}</p>
                    <p className="text-xs text-gray-400">
                      {(file.size / 1024).toFixed(1)} KB
                    </p>
                  </div>
                  <div className="text-xs text-gray-400">
                    {file.status === 'uploading' && '上传中...'}
                    {file.status === 'uploaded' && '✓'}
                    {file.status === 'error' && '❌'}
                  </div>
                </div>
              ))}
            </div>
          )}
        </Card>

        {/* Action Buttons */}
        {showActions && !isUser && isAssistant && (
          <div className="flex items-center gap-2 mt-3 opacity-0 group-hover:opacity-100 transition-all duration-200">
            <Button
              variant="ghost"
              size="sm"
              onClick={handleCopy}
              className="h-8 px-3 text-xs bg-gray-700 backdrop-blur-sm border border-gray-600 text-gray-300 hover:bg-gray-600 hover:border-blue-500 hover:text-blue-400 transition-all duration-200"
            >
              <Copy className="h-3 w-3 mr-1" />
              {copied ? '已复制' : '复制'}
            </Button>

            {onRegenerate && (
              <Button
                variant="ghost"
                size="sm"
                onClick={onRegenerate}
                className="h-8 px-3 text-xs bg-gray-700 backdrop-blur-sm border border-gray-600 text-gray-300 hover:bg-gray-600 hover:border-purple-500 hover:text-purple-400 transition-all duration-200"
                disabled={message.status === 'sending'}
              >
                <RefreshCw className="h-3 w-3 mr-1" />
                重新生成
              </Button>
            )}

            {onFeedback && (
              <>
                <Button
                  variant="ghost"
                  size="sm"
                  onClick={() => onFeedback('like')}
                  className="h-8 w-8 p-0 bg-gray-700 backdrop-blur-sm border border-gray-600 text-gray-300 hover:bg-gray-600 hover:border-green-500 hover:text-green-400 transition-all duration-200"
                >
                  <ThumbsUp className="h-3 w-3" />
                </Button>
                <Button
                  variant="ghost"
                  size="sm"
                  onClick={() => onFeedback('dislike')}
                  className="h-8 w-8 p-0 bg-gray-700 backdrop-blur-sm border border-gray-600 text-gray-300 hover:bg-gray-600 hover:border-red-500 hover:text-red-400 transition-all duration-200"
                >
                  <ThumbsDown className="h-3 w-3" />
                </Button>
              </>
            )}
          </div>
        )}
      </div>
    </div>
  );
}
