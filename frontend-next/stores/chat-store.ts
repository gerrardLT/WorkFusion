/**
 * 聊天状态管理 - Zustand Store
 * 管理对话历史、当前消息、加载状态等
 */

import { create } from 'zustand';
import { devtools, persist } from 'zustand/middleware';

export interface Message {
  id: string;
  content: string;
  role: 'user' | 'assistant';
  timestamp: Date;
  status: 'sending' | 'sent' | 'delivered' | 'error';
  sources?: Source[];
  confidence?: number;
  isLoading?: boolean;
}

export interface Source {
  title: string;
  content: string;
  page?: number;
  relevance_score?: number;
}

export interface ChatSession {
  id: string;
  title: string;
  messages: Message[];
  created_at: Date;
  updated_at: Date;
}

interface ChatState {
  // 当前会话
  currentSession: ChatSession | null;
  // 所有会话历史
  sessions: ChatSession[];
  // 当前正在输入的消息
  currentMessage: string;
  // 是否正在发送消息
  isLoading: boolean;
  // 是否正在输入
  isTyping: boolean;
  // 错误信息
  error: string | null;
}

interface ChatActions {
  // 会话管理
  createSession: (title?: string) => ChatSession;
  switchSession: (sessionId: string) => void;
  deleteSession: (sessionId: string) => void;
  updateSessionTitle: (sessionId: string, title: string) => void;

  // 消息管理
  addMessage: (message: Omit<Message, 'id' | 'timestamp'>) => void;
  updateMessage: (messageId: string, updates: Partial<Message>) => void;
  deleteMessage: (messageId: string) => void;
  clearMessages: () => void;

  // 输入状态
  setCurrentMessage: (message: string) => void;
  setIsLoading: (loading: boolean) => void;
  setIsTyping: (typing: boolean) => void;
  setError: (error: string | null) => void;

  // 重置状态
  reset: () => void;
}

const generateId = () => Math.random().toString(36).substr(2, 9);

const createDefaultSession = (): ChatSession => ({
  id: generateId(),
  title: '新对话',
  messages: [],
  created_at: new Date(),
  updated_at: new Date(),
});

const initialState: ChatState = {
  currentSession: null,
  sessions: [],
  currentMessage: '',
  isLoading: false,
  isTyping: false,
  error: null,
};

export const useChatStore = create<ChatState & ChatActions>()(
  devtools(
    persist(
      (set, get) => ({
        ...initialState,

        // 会话管理
        createSession: (title = '新对话') => {
          const newSession = {
            ...createDefaultSession(),
            title,
          };

          set((state) => ({
            sessions: [newSession, ...state.sessions],
            currentSession: newSession,
          }));

          return newSession;
        },

        switchSession: (sessionId: string) => {
          const session = get().sessions.find(s => s.id === sessionId);
          if (session) {
            set({ currentSession: session });
          }
        },

        deleteSession: (sessionId: string) => {
          set((state) => {
            const newSessions = state.sessions.filter(s => s.id !== sessionId);
            const currentSession = state.currentSession?.id === sessionId
              ? (newSessions[0] || null)
              : state.currentSession;

            return {
              sessions: newSessions,
              currentSession,
            };
          });
        },

        updateSessionTitle: (sessionId: string, title: string) => {
          set((state) => ({
            sessions: state.sessions.map(session =>
              session.id === sessionId
                ? { ...session, title, updatedAt: new Date() }
                : session
            ),
            currentSession: state.currentSession?.id === sessionId
              ? { ...state.currentSession, title, updatedAt: new Date() }
              : state.currentSession,
          }));
        },

        // 消息管理
        addMessage: (message) => {
          const newMessage: Message = {
            ...message,
            id: generateId(),
            timestamp: new Date(),
            status: message.status || 'sent',
          };

          set((state) => {
            if (!state.currentSession) {
              // 如果没有当前会话，创建新会话
              const newSession = createDefaultSession();
              newSession.messages = [newMessage];
              newSession.title = message.content.slice(0, 30) + (message.content.length > 30 ? '...' : '');

              return {
                sessions: [newSession, ...state.sessions],
                currentSession: newSession,
              };
            }

            // 更新当前会话
            const updatedSession = {
              ...state.currentSession,
              messages: [...state.currentSession.messages, newMessage],
              updatedAt: new Date(),
            };

            return {
              sessions: state.sessions.map(session =>
                session.id === state.currentSession!.id ? updatedSession : session
              ),
              currentSession: updatedSession,
            };
          });
        },

        updateMessage: (messageId: string, updates: Partial<Message>) => {
          set((state) => {
            if (!state.currentSession) return state;

            const updatedSession = {
              ...state.currentSession,
              messages: state.currentSession.messages.map(msg =>
                msg.id === messageId ? { ...msg, ...updates } : msg
              ),
              updatedAt: new Date(),
            };

            return {
              sessions: state.sessions.map(session =>
                session.id === state.currentSession!.id ? updatedSession : session
              ),
              currentSession: updatedSession,
            };
          });
        },

        deleteMessage: (messageId: string) => {
          set((state) => {
            if (!state.currentSession) return state;

            const updatedSession = {
              ...state.currentSession,
              messages: state.currentSession.messages.filter(msg => msg.id !== messageId),
              updatedAt: new Date(),
            };

            return {
              sessions: state.sessions.map(session =>
                session.id === state.currentSession!.id ? updatedSession : session
              ),
              currentSession: updatedSession,
            };
          });
        },

        clearMessages: () => {
          set((state) => {
            if (!state.currentSession) return state;

            const updatedSession = {
              ...state.currentSession,
              messages: [],
              updatedAt: new Date(),
            };

            return {
              sessions: state.sessions.map(session =>
                session.id === state.currentSession!.id ? updatedSession : session
              ),
              currentSession: updatedSession,
            };
          });
        },

        // 输入状态
        setCurrentMessage: (message: string) => set({ currentMessage: message }),
        setIsLoading: (loading: boolean) => set({ isLoading: loading }),
        setIsTyping: (typing: boolean) => set({ isTyping: typing }),
        setError: (error: string | null) => set({ error }),

        // 重置状态
        reset: () => set(initialState),
      }),
      {
        name: 'chat-store',
        partialize: (state) => ({
          sessions: state.sessions,
          currentSession: state.currentSession,
        }),
        storage: {
          getItem: (name) => {
            const str = localStorage.getItem(name);
            if (!str) return null;

            const parsed = JSON.parse(str);

            // 转换日期字符串回 Date 对象
            if (parsed.state) {
              if (parsed.state.sessions) {
                parsed.state.sessions = parsed.state.sessions.map((session: any) => ({
                  ...session,
                  created_at: new Date(session.created_at),
                  updated_at: new Date(session.updated_at),
                  messages: session.messages.map((message: any) => ({
                    ...message,
                    timestamp: new Date(message.timestamp),
                  })),
                }));
              }

              if (parsed.state.currentSession) {
                parsed.state.currentSession = {
                  ...parsed.state.currentSession,
                  created_at: new Date(parsed.state.currentSession.created_at),
                  updated_at: new Date(parsed.state.currentSession.updated_at),
                  messages: parsed.state.currentSession.messages.map((message: any) => ({
                    ...message,
                    timestamp: new Date(message.timestamp),
                  })),
                };
              }
            }

            return parsed;
          },
          setItem: (name, value) => {
            localStorage.setItem(name, JSON.stringify(value));
          },
          removeItem: (name) => {
            localStorage.removeItem(name);
          },
        },
      }
    ),
    { name: 'ChatStore' }
  )
);

// 便捷的选择器函数
export const useChatActions = () => useChatStore((state) => ({
  createSession: state.createSession,
  switchSession: state.switchSession,
  deleteSession: state.deleteSession,
  updateSessionTitle: state.updateSessionTitle,
  addMessage: state.addMessage,
  updateMessage: state.updateMessage,
  deleteMessage: state.deleteMessage,
  clearMessages: state.clearMessages,
  setCurrentMessage: state.setCurrentMessage,
  setIsLoading: state.setIsLoading,
  setIsTyping: state.setIsTyping,
  setError: state.setError,
  reset: state.reset,
}));

export const useChatState = () => useChatStore((state) => ({
  currentSession: state.currentSession,
  sessions: state.sessions,
  currentMessage: state.currentMessage,
  isLoading: state.isLoading,
  isTyping: state.isTyping,
  error: state.error,
}));
