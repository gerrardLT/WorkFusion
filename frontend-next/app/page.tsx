'use client';

/**
 * 首页 - 基于Figma设计图的精确还原
 * 设计图: https://www.figma.com/design/rvcno018uktGPovdhJ7tJw/AI多场景智能顾问?node-id=8-217
 *
 * 核心设计规范:
 * - 容器: 1200px × 644px, background: #0B1020
 * - 布局: flex-direction: column
 * - 左侧边栏: 带搜索框和会话列表
 * - 主聊天区: 显示实际对话内容（含示例）
 * - 预设问题: 底部显示3个快捷问题
 */

import * as React from 'react';
import { useState, useEffect, useRef } from 'react';
import { useRouter } from 'next/navigation';
import NextImage from 'next/image';
import ReactMarkdown from 'react-markdown';
import remarkGfm from 'remark-gfm';
import rehypeHighlight from 'rehype-highlight';
import 'highlight.js/styles/github-dark.css';

import { cn, generateId } from '@/lib/utils';
import { ScenarioProvider, useScenario } from '@/contexts/scenario-context';
import { DynamicThemeProvider } from '@/components/theme/dynamic-theme-provider';
import { UserSettingsModal } from '@/components/user-settings-modal';
import {
  askQuestion,
  getSessions,
  createSession,
  deleteSession as deleteSessionAPI,
  getSession,
  uploadFile,
  getScenarios,
  getPresetQuestions,
  updateSession,
  getCurrentUser
} from '@/lib/api-v2';

function HomeContent() {
  const router = useRouter();
  const { state: scenarioState, switchScenario } = useScenario();

  // 状态管理
  const [apiSessions, setApiSessions] = useState<any[]>([]);
  const [currentApiSession, setCurrentApiSession] = useState<any>(null);
  const [apiLoading, setApiLoading] = useState(false);
  const [messages, setMessages] = useState<any[]>([]);
  const [inputValue, setInputValue] = useState('');
  const [uploadNotifications, setUploadNotifications] = useState<any[]>([]);
  const [showScenarioDropdown, setShowScenarioDropdown] = useState(false);
  const fileInputRef = useRef<HTMLInputElement>(null);
  const messagesEndRef = useRef<HTMLDivElement>(null);

  // 新增状态
  const [searchQuery, setSearchQuery] = useState('');
  const [showSearch, setShowSearch] = useState(false);
  const [uploadProgress, setUploadProgress] = useState<{[key: string]: {
    progress: number;
    fileName: string;
    fileSize: number;
  }}>({});
  const [editingSessionId, setEditingSessionId] = useState<string | null>(null);
  const [editingSessionTitle, setEditingSessionTitle] = useState('');
  const [hoveredMessageId, setHoveredMessageId] = useState<string | null>(null);
  const [availableScenarios, setAvailableScenarios] = useState<any[]>([]);
  const [presetQuestions, setPresetQuestions] = useState<Array<string | {text: string}>>([]);
  const [showUserSettings, setShowUserSettings] = useState(false);
  const [currentUser, setCurrentUser] = useState<any>(null);

  // 获取当前场景
  const currentScenario = scenarioState.currentScenario;

  // 计算用户头像URL - 使用安全的默认值
  const userAvatarUrl = React.useMemo(() => {
    // 如果没有用户或没有头像，返回默认头像
    if (!currentUser?.avatar_url) {
      return "/images/alex-avatar-56586a.png";
    }

    // 如果是完整的HTTP URL，直接返回
    if (currentUser.avatar_url.startsWith('http://') || currentUser.avatar_url.startsWith('https://')) {
      return currentUser.avatar_url;
    }

    // 如果是相对路径，拼接完整URL
    return `http://localhost:8000${currentUser.avatar_url}`;
  }, [currentUser]);

  // 场景二级导航配置
  const scenarioNavConfig: { [key: string]: Array<{ label: string; path: string }> } = {
    'tender': [
      { label: '企业画像', path: '/company' },
      { label: '任务清单', path: '/tasks' },
      { label: '评估报告', path: '/evaluations' },
      { label: '项目推荐', path: '/projects' }
    ],
    '招投标': [
      { label: '企业画像', path: '/company' },
      { label: '任务清单', path: '/tasks' },
      { label: '评估报告', path: '/evaluations' },
      { label: '项目推荐', path: '/projects' }
    ],
    'admin': [],
    '行政': [],
    'finance': [],
    '财务': [],
    'procurement': [],
    '采购': [],
    'engineering': [],
    '工程': []
  };

  // 获取当前场景的二级导航
  const currentNavItems = scenarioNavConfig[currentScenario?.id || ''] ||
                          scenarioNavConfig[currentScenario?.name || ''] ||
                          [];

  // 示例消息（匹配设计图）
  const hasMessages = messages.length > 0;
  const showExampleChat = !hasMessages; // 无真实消息时显示示例

  // 自动滚动
  const scrollToBottom = () => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  };

  useEffect(() => {
    scrollToBottom();
  }, [messages]);

  // 从API加载会话（根据当前场景过滤）
  const loadSessions = async () => {
    try {
      // 如果有当前场景，只加载该场景的会话
      const scenarioId = currentScenario?.id;
      const response = await getSessions(scenarioId, 50);
      setApiSessions(response.sessions || []);
    } catch (error) {
      console.error('加载会话失败:', error);
    }
  };

  // 加载会话消息
  const loadSessionMessages = async (sessionId: string) => {
    try {
      const session = await getSession(sessionId);
      const msgs = (session.messages || []).map(msg => ({
        ...msg,
        timestamp: typeof msg.timestamp === 'string' ? new Date(msg.timestamp) : msg.timestamp,
      }));
      setMessages(msgs);
    } catch (error) {
      console.error('加载会话消息失败:', error);
      setMessages([]);
    }
  };

  useEffect(() => {
    loadSessions();
    loadScenarios();
    loadUserInfo();
  }, []);

  // 加载用户信息
  const loadUserInfo = async () => {
    try {
      const response = await getCurrentUser();
      console.log('Loaded current user:', response);
      setCurrentUser(response.data || response);
    } catch (error) {
      console.error('Failed to load user info:', error);
    }
  };

  useEffect(() => {
    if (currentApiSession) {
      loadSessionMessages(currentApiSession.id);
    }
  }, [currentApiSession]);

  // 加载场景列表
  const loadScenarios = async () => {
    try {
      const response = await getScenarios();
      setAvailableScenarios(response.scenarios || []);
    } catch (error) {
      console.error('加载场景失败:', error);
    }
  };

  // 加载预设问题
  useEffect(() => {
    const loadPresetQuestions = async () => {
      if (!currentScenario) return;
      try {
        const response = await getPresetQuestions(currentScenario.id);
        // 从响应中提取preset_questions数组
        if (response && response.preset_questions) {
          setPresetQuestions(response.preset_questions);
        } else {
          setPresetQuestions([
            '这份文档主要讲什么？',
            '列出关键要点',
            '有哪些风险或空白？'
          ]);
        }
      } catch (error) {
        console.error('加载预设问题失败:', error);
        // 使用默认问题
        setPresetQuestions([
          '这份文档主要讲什么？',
          '列出关键要点',
          '有哪些风险或空白？'
        ]);
      }
    };
    loadPresetQuestions();
  }, [currentScenario]);

  // 当场景切换时重新加载会话
  useEffect(() => {
    if (currentScenario) {
      loadSessions();
    }
  }, [currentScenario]);

  // 创建新聊天
  const createNewChat = async () => {
    try {
      if (!currentScenario) return;
      const newSession = await createSession({
        title: '新对话',
        scenario_id: currentScenario.id
      });
      setCurrentApiSession(newSession);
      setMessages([]);
      await loadSessions();
    } catch (error) {
      console.error('创建会话失败:', error);
    }
  };

  // 选择聊天
  const selectChat = (session: any) => {
    setCurrentApiSession(session);
  };

  // 删除会话
  const deleteChat = async (e: React.MouseEvent, sessionId: string) => {
    e.stopPropagation();
    if (window.confirm('确定要删除这个对话吗？')) {
      try {
        await deleteSessionAPI(sessionId);
        if (currentApiSession?.id === sessionId) {
          setCurrentApiSession(null);
          setMessages([]);
        }
        await loadSessions();
      } catch (error) {
        console.error('删除会话失败:', error);
      }
    }
  };

  // 文件上传
  const handleFileUpload = async (files: FileList | null) => {
    if (!files || !currentScenario) return;

    for (const file of Array.from(files)) {
      try {
        const uploadId = generateId();
        setUploadNotifications(prev => [...prev, {
          id: uploadId,
          type: 'loading',
          message: `正在上传: ${file.name}...`
        }]);

        await uploadFile(file, currentScenario.id);

        setUploadNotifications(prev => prev.map(n =>
          n.id === uploadId
            ? { ...n, type: 'success', message: `${file.name} 上传成功` }
            : n
        ));

        setTimeout(() => {
          setUploadNotifications(prev => prev.filter(n => n.id !== uploadId));
        }, 3000);
      } catch (error) {
        // Error handling
      }
    }
  };

  // 发送消息
  const handleSendMessage = async (content: string) => {
    if (!content.trim() || apiLoading) return;
    setApiLoading(true);

    try {
      let sessionToUse = currentApiSession;
      if (!sessionToUse && currentScenario) {
        sessionToUse = await createSession({
          title: content.slice(0, 30),
          scenario_id: currentScenario.id
        });
        setCurrentApiSession(sessionToUse);
        await loadSessions();
      }

      const userMessage = {
        id: generateId(),
        session_id: sessionToUse.id,
        content: content.trim(),
        role: 'user',
        timestamp: new Date(),
      };

      setMessages(prev => [...prev, userMessage]);

      if (!currentScenario) throw new Error('未选择场景');

      const response = await askQuestion({
        question: content.trim(),
        scenario_id: currentScenario.id,
        session_id: sessionToUse.id
      });

      const assistantMessage = {
        id: generateId(),
        session_id: sessionToUse.id,
        content: response.answer,
        role: 'assistant',
        timestamp: new Date(),
        metadata: {
          confidence: response.confidence,
          sources: response.sources || [],
          processingTime: response.processing_time,
        },
      };

      setMessages(prev => [...prev, assistantMessage]);
      await loadSessions();
    } catch (error) {
      console.error('处理请求失败:', error);
    } finally {
      setApiLoading(false);
    }
  };

  // 提交
  const handleSubmit = () => {
    if (inputValue.trim()) {
      handleSendMessage(inputValue);
      setInputValue('');
    }
  };

  // 过滤会话列表
  const filteredSessions = apiSessions.filter(session => {
    if (!searchQuery.trim()) return true;
    const title = (session.title || '').toLowerCase();
    const query = searchQuery.toLowerCase();
    return title.includes(query);
  });

  // 预设问题点击
  const handlePresetQuestion = (question: string) => {
    handleSendMessage(question);
  };

  // 复制消息内容
  const copyMessage = async (content: string) => {
    try {
      await navigator.clipboard.writeText(content);
      alert('已复制到剪贴板');
    } catch (error) {
      console.error('复制失败:', error);
    }
  };

  // 重新生成消息
  const regenerateMessage = async (messageId: string) => {
    const messageIndex = messages.findIndex(m => m.id === messageId);
    if (messageIndex === -1) return;

    // 找到上一条用户消息
    const userMessage = messages[messageIndex - 1];
    if (!userMessage || userMessage.role !== 'user') return;

    // 删除当前AI回复
    setMessages(prev => prev.filter(m => m.id !== messageId));

    // 重新发送问题
    await handleSendMessage(userMessage.content);
  };

  // 删除消息（标记为待实现）
  const deleteMessage = async (messageId: string) => {
    if (confirm('确定删除这条消息吗？')) {
      setMessages(prev => prev.filter(m => m.id !== messageId));
    }
  };

  // 编辑消息（标记为待实现）
  const editMessage = async (messageId: string, newContent: string) => {
    setMessages(prev => prev.map(m =>
      m.id === messageId ? { ...m, content: newContent } : m
    ));
  };

  // 场景切换
  const handleScenarioChange = async (scenarioId: string) => {
    switchScenario(scenarioId);
    setShowScenarioDropdown(false);
    setCurrentApiSession(null);
    setMessages([]);
    await loadSessions();
  };

  return (
    <div className="w-screen h-screen overflow-hidden" style={{ background: '#0B1020' }}>
      {/* 主容器 - 占满全屏 */}
      <div
        className="flex flex-col items-start p-0 relative w-full h-full"
        style={{
          background: '#0B1020'
        }}
      >
        {/* 顶部导航栏 */}
        <div
          className="flex flex-row justify-between items-center w-full"
          style={{
            height: '64px',
            padding: '1px 21px',
            background: 'rgba(255, 255, 255, 0.04)',
            border: '1px solid #2A2F3A',
            boxShadow: '0px 10px 30px rgba(0, 0, 0, 0.25)',
            borderRadius: '24px',
            order: 0,
            flexGrow: 0,
            zIndex: 10
          }}
        >
          {/* 左侧 - 知识问答 + 场景 */}
          <div className="flex items-center gap-3">
            <div className="flex items-center gap-[10px]">
              <NextImage
                src="/icons/knowledge-qa-icon.svg"
                alt="知识问答"
                width={20}
                height={20}
              />
              <span style={{
                fontFamily: 'WenQuanYi Zen Hei, sans-serif',
                fontWeight: 600,
                fontSize: '16px',
                color: '#DDE9FF'
              }}>
                知识问答
              </span>
            </div>

            {/* 场景选择器 */}
            <div className="relative">
              <button
                onClick={() => setShowScenarioDropdown(!showScenarioDropdown)}
                className="flex items-center gap-2 px-3 py-2 bg-[#0D1B2A] rounded-[48px] hover:bg-[#111827] transition-colors"
                style={{ height: '35px' }}
              >
                <NextImage
                  src="/icons/scenario-icon.svg"
                  alt="场景"
                  width={18}
                  height={18}
                />
                <span style={{
                  fontFamily: 'WenQuanYi Zen Hei, sans-serif',
                  fontWeight: 500,
                  fontSize: '14px',
                  color: '#CFE8FF'
                }}>
                  场景：{currentScenario?.name || '招投标'}
                </span>
                <svg width="16" height="16" viewBox="0 0 16 16" fill="none">
                  <path d="M4 6L8 10L12 6" stroke="#CFE8FF" strokeWidth="1.33"/>
                </svg>
              </button>

              {showScenarioDropdown && (
                <div className="absolute top-full mt-2 right-0 bg-[#0D1B2A] border border-[#2A2F3A] rounded-xl min-w-[150px]" style={{ boxShadow: '0px 10px 30px rgba(0, 0, 0, 0.25)', zIndex: 9999 }}>
                  {/* 固定5个场景选项 */}
                  {['招投标', '行政', '财务', '采购', '工程'].map((scenarioName, idx) => {
                    const scenarioId = ['tender', 'admin', 'finance', 'procurement', 'engineering'][idx];
                    const isActive = currentScenario?.id === scenarioId || currentScenario?.name === scenarioName;

                    return (
                      <button
                        key={scenarioId}
                        onClick={async () => {
                          // 切换场景
                          if (currentScenario?.name !== scenarioName && currentScenario?.id !== scenarioId) {
                            // 更新场景ID到localStorage
                            localStorage.setItem('currentScenarioId', scenarioId);

                            // 切换场景
                            switchScenario(scenarioId);

                            setShowScenarioDropdown(false);
                            setCurrentApiSession(null);
                            setMessages([]);
                            await loadSessions();

                            // 强制重新渲染以应用新场景
                            window.location.reload();
                          } else {
                            setShowScenarioDropdown(false);
                          }
                        }}
                        className={cn(
                          "w-full px-4 py-2 text-left text-sm transition-colors first:rounded-t-xl last:rounded-b-xl",
                          isActive ? "bg-[#6D28D9] text-white" : "text-[#CFE8FF] hover:bg-[#111827]"
                        )}
                        style={{ fontFamily: 'WenQuanYi Zen Hei, sans-serif' }}
                      >
                        {scenarioName}
                      </button>
                    );
                  })}
                </div>
              )}
            </div>
          </div>

          {/* 中间 - 功能按钮（动态二级导航） */}
          {currentNavItems.length > 0 && (
            <div className="flex items-center gap-2 px-[10px] py-[6px] bg-[#0D1B2A] rounded-[48px]">
              {currentNavItems.map((item, idx) => (
                <button
                  key={item.path}
                  className={cn(
                    "px-[10px] py-[6px] h-[30px] rounded-[48px] text-[13px] font-medium transition-colors",
                    idx === 0 ? "bg-[#6D28D9] text-white" : "bg-[#111827] text-[#9CA3AF] hover:bg-[#1F2937]"
                  )}
                  style={{ fontFamily: 'WenQuanYi Zen Hei, sans-serif' }}
                  onClick={() => router.push(item.path)}
                >
                  {item.label}
                </button>
              ))}
            </div>
          )}

          {/* 右侧 - 知识库 + 用户 */}
          <div className="flex items-center gap-3">
            <button
              onClick={() => router.push('/knowledge')}
              className="flex items-center gap-2 px-3 py-2 bg-[#0D1B2A] hover:bg-[#111827] rounded-[48px] transition-colors"
              style={{ height: '35px' }}
            >
              <NextImage
                src="/icons/knowledge-base-icon.svg"
                alt="知识库"
                width={18}
                height={18}
              />
              <span style={{
                fontFamily: 'WenQuanYi Zen Hei, sans-serif',
                fontWeight: 500,
                fontSize: '14px',
                color: '#CFE8FF'
              }}>
                知识库
              </span>
            </button>

            <button
              onClick={() => setShowUserSettings(true)}
              className="flex items-center gap-2 px-[10px] py-[6px] bg-[#0D1B2A] rounded-[48px] hover:bg-[#111827] transition-colors cursor-pointer"
            >
              <NextImage
                src={userAvatarUrl}
                alt={currentUser?.username || "User"}
                width={32}
                height={32}
                className="rounded-full"
                unoptimized
                priority
              />
              <span style={{
                fontFamily: 'Inter, sans-serif',
                fontWeight: 500,
                fontSize: '14px',
                color: '#CFE8FF'
              }}>
                {currentUser?.username || 'Alex'}
              </span>
              <svg width="16" height="16" viewBox="0 0 16 16" fill="none">
                <path d="M4 6L8 10L12 6" stroke="#CFE8FF" strokeWidth="1.33"/>
              </svg>
            </button>
          </div>
        </div>

        {/* 主内容区 */}
        <div
          className="flex flex-row items-start w-full"
          style={{
            flex: 1,
            padding: '16px',
            gap: '16px',
            background: '#0B1020',
            order: 1,
            overflow: 'hidden',
            zIndex: 1
          }}
        >
          {/* 左侧边栏 */}
          <div
            className="flex flex-col items-start h-full"
            style={{
              padding: '13px',
              width: '280px',
              background: 'rgba(255, 255, 255, 0.04)',
              border: '1px solid #2A2F3A',
              boxShadow: '0px 10px 30px rgba(0, 0, 0, 0.25)',
              borderRadius: '24px',
              order: 0,
              flexGrow: 0,
              overflow: 'hidden'
            }}
          >
            {/* 会话标题 + 搜索 + 新建 */}
            <div className="w-full mb-2">
              <div className="flex items-center justify-between mb-3">
                <span style={{
                  fontFamily: 'WenQuanYi Zen Hei, sans-serif',
                  fontWeight: 600,
                  fontSize: '14px',
                  color: '#DDE9FF'
                }}>
                  会话
                </span>
                <div className="flex items-center gap-2">
                  {/* 搜索按钮 */}
                  <button
                    onClick={() => setShowSearch(!showSearch)}
                    className="p-1.5 hover:bg-[#111827] rounded-lg transition-colors"
                  >
                    <svg width="16" height="16" viewBox="0 0 16 16" fill="none">
                      <circle cx="7" cy="7" r="5" stroke="#9CA3AF" strokeWidth="1.33"/>
                      <path d="M11 11L14 14" stroke="#9CA3AF" strokeWidth="1.33" strokeLinecap="round"/>
                    </svg>
                  </button>
                  {/* 新建按钮 */}
                  <button
                    onClick={createNewChat}
                    className="hover:bg-[#111827] rounded-lg transition-colors"
                  >
                    <NextImage
                      src="/icons/add-icon.svg"
                      alt="New chat"
                      width={32}
                      height={32}
                    />
                  </button>
                </div>
              </div>

              {/* 搜索输入框 */}
              {showSearch && (
                <div className="mt-2 mb-3">
                  <input
                    type="text"
                    placeholder="搜索对话..."
                    value={searchQuery}
                    onChange={(e) => setSearchQuery(e.target.value)}
                    className="w-full px-3 py-2 bg-[#0F1724] border border-[#2A2F3A] rounded-lg text-[#E6EEF8] placeholder-[#64748B] focus:outline-none focus:border-[#6366F1]"
                    style={{
                      fontFamily: 'WenQuanYi Zen Hei, sans-serif',
                      fontSize: '14px'
                    }}
                    autoFocus
                  />
                </div>
              )}
            </div>

            {/* 会话列表 */}
            <div className="flex-1 w-full space-y-2 overflow-y-auto">
              {/* 真实会话列表 */}
              {filteredSessions.length === 0 ? (
                <div className="text-center py-8 text-gray-500">
                  <p style={{
                    fontFamily: 'WenQuanYi Zen Hei, sans-serif',
                    fontSize: '14px'
                  }}>
                    {searchQuery ? '未找到匹配的对话' : '暂无对话'}
                  </p>
                </div>
              ) : (
                filteredSessions.map((session, idx) => {
                  const isActive = currentApiSession?.id === session.id;
                  const isEditing = editingSessionId === session.id;

                  return (
                    <div
                      key={session.id}
                      onClick={() => !isEditing && setCurrentApiSession(session)}
                      className="group relative px-3 py-2.5 rounded-xl cursor-pointer transition-all"
                      style={{
                        background: isActive ? 'rgba(99, 102, 241, 0.16)' : '#0D1B2A'
                      }}
                      onMouseEnter={(e) => {
                        if (!isActive) {
                          e.currentTarget.style.background = '#111827';
                        }
                      }}
                      onMouseLeave={(e) => {
                        if (!isActive) {
                          e.currentTarget.style.background = '#0D1B2A';
                        }
                      }}
                    >
                      <div className="flex items-center gap-2">
                        <div className="flex-1 min-w-0">
                          {isEditing ? (
                            <input
                              type="text"
                              value={editingSessionTitle}
                              onChange={(e) => setEditingSessionTitle(e.target.value)}
                              onBlur={() => {
                                if (editingSessionTitle.trim() && editingSessionTitle !== session.title) {
                                  updateSession(session.id, { title: editingSessionTitle }).then(() => {
                                    loadSessions();
                                  });
                                }
                                setEditingSessionId(null);
                              }}
                              onKeyDown={(e) => {
                                if (e.key === 'Enter') {
                                  e.currentTarget.blur();
                                } else if (e.key === 'Escape') {
                                  setEditingSessionId(null);
                                  setEditingSessionTitle(session.title || '');
                                }
                              }}
                              className="w-full bg-[#0F1724] border border-[#6366F1] rounded px-2 py-1 text-[#E6EEF8] focus:outline-none"
                              style={{
                                fontFamily: 'WenQuanYi Zen Hei, sans-serif',
                                fontSize: '14px'
                              }}
                              autoFocus
                              onClick={(e) => e.stopPropagation()}
                            />
                          ) : (
                            <div className="flex items-center justify-between">
                              <p
                                onDoubleClick={(e) => {
                                  e.stopPropagation();
                                  setEditingSessionId(session.id);
                                  setEditingSessionTitle(session.title || '');
                                }}
                                style={{
                                  fontFamily: 'WenQuanYi Zen Hei, sans-serif',
                                  fontSize: '14px',
                                  fontWeight: isActive ? 600 : 500,
                                  color: isActive ? '#EEF2FF' : '#E6EEF8',
                                  whiteSpace: 'nowrap',
                                  overflow: 'hidden',
                                  textOverflow: 'ellipsis'
                                }}
                              >
                                {session.title || '新对话'}
                              </p>
                              <div className="flex items-center gap-1 opacity-0 group-hover:opacity-100 transition-opacity">
                                <button
                                  onClick={(e) => {
                                    e.stopPropagation();
                                    setEditingSessionId(session.id);
                                    setEditingSessionTitle(session.title || '');
                                  }}
                                  className="p-1 hover:bg-[#2A2F3A] rounded"
                                  title="重命名"
                                >
                                  <svg width="14" height="14" viewBox="0 0 14 14" fill="none">
                                    <path d="M10 2L12 4L5 11H3V9L10 2Z" stroke="#9CA3AF" strokeWidth="1.2" strokeLinecap="round" strokeLinejoin="round"/>
                                  </svg>
                                </button>
                                <button
                                  onClick={(e) => deleteChat(e, session.id)}
                                  className="p-1 hover:bg-[#EF4444] hover:bg-opacity-20 rounded"
                                  title="删除"
                                >
                                  <svg width="14" height="14" viewBox="0 0 14 14" fill="none">
                                    <path d="M2 4H12M5 4V2H9V4M3 4L4 12H10L11 4" stroke="#EF4444" strokeWidth="1.2" strokeLinecap="round" strokeLinejoin="round"/>
                                  </svg>
                                </button>
                              </div>
                            </div>
                          )}
                        </div>
                      </div>
                    </div>
                  );
                })
              )}
            </div>
          </div>

          {/* 主聊天区 */}
          <div
            className="flex flex-col items-start h-full"
            style={{
              padding: '1px',
              flex: 1,
              background: 'rgba(255, 255, 255, 0.04)',
              border: '1px solid #2A2F3A',
              boxShadow: '0px 10px 30px rgba(0, 0, 0, 0.25)',
              borderRadius: '24px',
              order: 1,
              overflow: 'hidden'
            }}
          >
            {/* 标题栏 */}
            <div
              className="flex flex-row justify-between items-center w-full"
              style={{
                padding: '16px',
                height: '57px',
                borderBottom: '1px solid #2A2F3A'
              }}
            >
              <span style={{
                fontFamily: 'WenQuanYi Zen Hei, sans-serif',
                fontWeight: 600,
                fontSize: '18px',
                color: '#E6EEF8'
              }}>
                {currentApiSession?.title || '新对话'}
              </span>
              {apiLoading && (
                <div className="flex items-center gap-2">
                  <svg className="animate-spin" width="18" height="18" viewBox="0 0 18 18" fill="none">
                    <circle cx="9" cy="9" r="7" stroke="#9CA3AF" strokeWidth="1.5" strokeDasharray="32"/>
                  </svg>
                  <span style={{
                    fontFamily: 'Inter, sans-serif',
                    fontSize: '12px',
                    color: '#9CA3AF'
                  }}>
                    AI 思考中…
                  </span>
                </div>
              )}
            </div>

            {/* 消息区域 */}
            <div className="flex-1 w-full px-4 py-4 overflow-y-auto">
              {showExampleChat ? (
                /* 空状态 - 显示欢迎消息 */
                <div className="flex flex-col items-center justify-center h-full text-center px-4">
                  <div className="mb-6">
                    <svg width="64" height="64" viewBox="0 0 64 64" fill="none" className="mx-auto">
                      <rect x="8" y="8" width="48" height="48" rx="12" stroke="#6366F1" strokeWidth="2"/>
                      <path d="M20 28L28 36L44 20" stroke="#6366F1" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"/>
                    </svg>
                  </div>
                  <h3 style={{
                    fontFamily: 'WenQuanYi Zen Hei, sans-serif',
                    fontSize: '20px',
                    fontWeight: 600,
                    color: '#E6EEF8',
                    marginBottom: '12px'
                  }}>
                    {currentScenario?.ui?.welcomeTitle || '开始新对话'}
                  </h3>
                  <p style={{
                    fontFamily: 'WenQuanYi Zen Hei, sans-serif',
                    fontSize: '14px',
                    color: '#9CA3AF',
                    maxWidth: '480px',
                    lineHeight: '1.6'
                  }}>
                    {currentScenario?.ui?.welcomeMessage || '您好！我是您的AI助手，请输入您的问题，我会尽力帮您解答。'}
                  </p>
                </div>
              ) : (
                /* 真实消息 */
                <div className="space-y-4">
                  {messages.map((msg) => (
                    <div
                      key={msg.id}
                      className="group flex gap-3"
                      onMouseEnter={() => setHoveredMessageId(msg.id)}
                      onMouseLeave={() => setHoveredMessageId(null)}
                    >
                      <NextImage
                        src={msg.role === 'user' ? "/images/user-message-avatar-56586a.png" : "/images/assistant-avatar-56586a.png"}
                        alt={msg.role === 'user' ? "User" : "Assistant"}
                        width={32}
                        height={32}
                        className="rounded-full flex-shrink-0"
                      />
                      <div className="flex-1 max-w-[794px]">
                        <div className={cn(
                          "relative p-[13px] border border-[#2A2F3A] rounded-[24px]",
                          msg.role === 'user' ? "bg-white/[0.04]" : "bg-[#0D1B2A]"
                        )}>
                          {msg.role === 'assistant' ? (
                            <div
                              className="markdown-content"
                              style={{
                                fontFamily: 'WenQuanYi Zen Hei, sans-serif',
                                fontSize: '16px',
                                lineHeight: '20px',
                                color: '#CFE8FF'
                              }}
                            >
                              <ReactMarkdown
                                remarkPlugins={[remarkGfm]}
                                rehypePlugins={[rehypeHighlight]}
                                components={{
                                  code({node, className, children, ...props}: any) {
                                    const inline = !(props as any).inline !== false;
                                    return inline ? (
                                      <code
                                        className="bg-[#1E293B] px-1 py-0.5 rounded text-[#E879F9]"
                                        {...props}
                                      >
                                        {children}
                                      </code>
                                    ) : (
                                      <code
                                        className={`${className || ''} block bg-[#1E293B] p-3 rounded-lg overflow-x-auto`}
                                        {...props}
                                      >
                                        {children}
                                      </code>
                                    );
                                  },
                                  p: ({children}) => <p className="mb-2 last:mb-0">{children}</p>,
                                  ul: ({children}) => <ul className="list-disc list-inside mb-2">{children}</ul>,
                                  ol: ({children}) => <ol className="list-decimal list-inside mb-2">{children}</ol>,
                                  li: ({children}) => <li className="mb-1">{children}</li>,
                                  h1: ({children}) => <h1 className="text-xl font-bold mb-2">{children}</h1>,
                                  h2: ({children}) => <h2 className="text-lg font-bold mb-2">{children}</h2>,
                                  h3: ({children}) => <h3 className="text-base font-bold mb-1">{children}</h3>,
                                  a: ({children, href}) => <a href={href} className="text-[#60A5FA] hover:underline" target="_blank" rel="noopener noreferrer">{children}</a>,
                                  blockquote: ({children}) => <blockquote className="border-l-4 border-[#2A2F3A] pl-3 italic my-2">{children}</blockquote>,
                                }}
                              >
                                {msg.content}
                              </ReactMarkdown>
                            </div>
                          ) : (
                            <p style={{
                              fontFamily: 'WenQuanYi Zen Hei, sans-serif',
                              fontSize: '16px',
                              lineHeight: '20px',
                              color: '#E6EEF8'
                            }}>
                              {msg.content}
                            </p>
                          )}

                          {/* 消息操作按钮 */}
                          {msg.role === 'assistant' && hoveredMessageId === msg.id && (
                            <div className="absolute -bottom-8 right-2 flex items-center gap-1 bg-[#0D1B2A] border border-[#2A2F3A] rounded-lg p-1 shadow-lg">
                              <button
                                onClick={() => copyMessage(msg.content)}
                                className="p-1.5 hover:bg-[#111827] rounded transition-colors"
                                title="复制"
                              >
                                <svg width="16" height="16" viewBox="0 0 16 16" fill="none">
                                  <rect x="5" y="5" width="8" height="8" rx="1" stroke="#9CA3AF" strokeWidth="1.2"/>
                                  <path d="M3 3H9V4H4V9H3V3Z" fill="#9CA3AF"/>
                                </svg>
                              </button>
                              <button
                                onClick={() => regenerateMessage(msg.id)}
                                className="p-1.5 hover:bg-[#111827] rounded transition-colors"
                                title="重新生成"
                              >
                                <svg width="16" height="16" viewBox="0 0 16 16" fill="none">
                                  <path d="M13 8C13 10.7614 10.7614 13 8 13C5.23858 13 3 10.7614 3 8C3 5.23858 5.23858 3 8 3C9.12622 3 10.1644 3.37147 11 3.99963M11 2V4H13" stroke="#9CA3AF" strokeWidth="1.2" strokeLinecap="round"/>
                                </svg>
                              </button>
                            </div>
                          )}
                        </div>
                      </div>
                    </div>
                  ))}
                </div>
              )}
              <div ref={messagesEndRef} />
            </div>

            {/* 预设问题 + 输入区 */}
            <div className="w-full border-t border-[#2A2F3A]">
              {/* 输入框 */}
              <div className="px-[13px] pb-[13px]">
                {/* 快捷提示文字 */}
                <div
                  style={{
                    display: 'flex',
                    flexDirection: 'row',
                    alignItems: 'center',
                    padding: '0px',
                    gap: '8px',
                    width: '846px',
                    height: '19px',
                    flex: 'none',
                    order: 0,
                    alignSelf: 'stretch',
                    flexGrow: 0,
                    margin: '0 auto 12px auto'
                  }}
                >
                  {presetQuestions.map((q, idx) => (
                    <span
                      key={idx}
                      onClick={() => handlePresetQuestion(typeof q === 'string' ? q : q.text)}
                      style={{
                        fontFamily: 'WenQuanYi Zen Hei, sans-serif',
                        fontSize: '14px',
                        fontWeight: 400,
                        color: '#9CA3AF',
                        cursor: 'pointer',
                        transition: 'color 0.2s'
                      }}
                      onMouseEnter={(e) => e.currentTarget.style.color = '#CFE8FF'}
                      onMouseLeave={(e) => e.currentTarget.style.color = '#9CA3AF'}
                    >
                      {typeof q === 'string' ? q : q.text}
                    </span>
                  ))}
                </div>

                <div className="flex items-center gap-2 px-[11px] py-[9px] bg-[#0F1724] border border-[#2A2F3A] rounded-[48px]">
                  <input
                    ref={fileInputRef}
                    type="file"
                    multiple
                    accept=".pdf,.doc,.docx,.txt"
                    onChange={(e) => handleFileUpload(e.target.files)}
                    className="hidden"
                  />
                  <button
                    onClick={() => fileInputRef.current?.click()}
                    className="flex items-center justify-center hover:bg-[#111827] rounded-lg transition-colors flex-shrink-0"
                  >
                    <NextImage
                      src="/icons/attach-icon.svg"
                      alt="Attach"
                      width={36}
                      height={36}
                    />
                  </button>
                  <input
                    type="text"
                    value={inputValue}
                    onChange={(e) => setInputValue(e.target.value)}
                    onKeyDown={(e) => {
                      if (e.key === 'Enter' && !e.shiftKey) {
                        e.preventDefault();
                        handleSubmit();
                      }
                    }}
                    placeholder="输入你的消息…"
                    className="flex-1 bg-transparent text-[#E6EEF8] placeholder-[#E6EEF8]/60 text-sm outline-none"
                    style={{ fontFamily: 'WenQuanYi Zen Hei, sans-serif' }}
                  />
                  <button
                    onClick={handleSubmit}
                    disabled={!inputValue.trim() || apiLoading}
                    className="flex items-center justify-center disabled:opacity-50 disabled:cursor-not-allowed transition-colors flex-shrink-0"
                  >
                    <NextImage
                      src="/icons/send-icon.svg"
                      alt="Send"
                      width={36}
                      height={36}
                    />
                  </button>
                </div>
                <p className="text-center mt-2 text-xs text-[#9CA3AF]" style={{ fontFamily: 'Inter, sans-serif' }}>
                  回车发送 • Shift+Enter 换行 • 使用回形针上传文档（不再弹出上传成功提示）
                </p>
              </div>
            </div>
          </div>
        </div>
      </div>

      {/* 上传通知 */}
      {uploadNotifications.length > 0 && (
        <div className="fixed bottom-5 right-5 space-y-2 z-50">
          {uploadNotifications.map((n) => (
            <div
              key={n.id}
              className={cn(
                "rounded-xl px-3 py-3 border border-[#2A2F3A] min-w-[220px]",
                n.type === 'error' ? "bg-[#EF4444]" : "bg-[#0D1B2A]"
              )}
              style={{ boxShadow: '0px 10px 30px rgba(0, 0, 0, 0.25)' }}
            >
              <p style={{
                fontFamily: n.type === 'error' ? 'Inter, sans-serif' : 'WenQuanYi Zen Hei, sans-serif',
                fontSize: '16px',
                color: n.type === 'error' ? '#FFFFFF' : '#CFE8FF'
              }}>
                {n.message}
              </p>
            </div>
          ))}
        </div>
      )}

      {/* 用户设置模态框 */}
      <UserSettingsModal
        isOpen={showUserSettings}
        onClose={() => setShowUserSettings(false)}
      />
    </div>
  );
}

export default function HomePage() {
  return (
    <ScenarioProvider>
      <DynamicThemeProvider>
        <HomeContent />
      </DynamicThemeProvider>
    </ScenarioProvider>
  );
}
