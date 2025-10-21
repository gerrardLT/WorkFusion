'use client';

import React, { createContext, useContext, useReducer, useEffect, ReactNode } from 'react';

// 场景配置类型定义
export interface ScenarioTheme {
  primaryColor: string;
  gradientFrom: string;
  gradientTo: string;
  iconColor: string;
}

export interface ScenarioUI {
  welcomeTitle: string;
  welcomeMessage: string;
  placeholderText: string;
  uploadAreaTitle: string;
  uploadAreaDescription: string;
}

export interface ScenarioConfig {
  id: string;
  name: string;
  description: string;
  status: string;
  theme: ScenarioTheme;
  ui: ScenarioUI;
  presetQuestions: string[];
  documentTypes: Array<{
    id: string;
    name: string;
    extensions: string[];
    maxSize: number;
  }>;
}

// 状态类型
export interface ScenarioState {
  currentScenario: ScenarioConfig | null;
  availableScenarios: ScenarioConfig[];
  loading: boolean;
  error: string | null;
}

// 动作类型
type ScenarioAction =
  | { type: 'SET_LOADING'; payload: boolean }
  | { type: 'SET_ERROR'; payload: string | null }
  | { type: 'SET_SCENARIOS'; payload: ScenarioConfig[] }
  | { type: 'SET_CURRENT_SCENARIO'; payload: ScenarioConfig }
  | { type: 'CLEAR_CURRENT_SCENARIO' };

// 默认状态
const initialState: ScenarioState = {
  currentScenario: null,
  availableScenarios: [],
  loading: true,
  error: null,
};

// 默认场景配置
const defaultScenarios: ScenarioConfig[] = [
  {
    id: 'tender',
    name: '招投标',
    description: '招标文件分析和投标方案优化',
    status: 'active',
    theme: {
      primaryColor: 'green',
      gradientFrom: 'from-green-600',
      gradientTo: 'to-teal-600',
      iconColor: 'text-green-600',
    },
    ui: {
      welcomeTitle: '欢迎使用招投标智能助手',
      welcomeMessage: '我是您的专业招投标分析师，帮助您解读招标文件、分析投标要求',
      placeholderText: '请输入您的招投标相关问题...',
      uploadAreaTitle: '上传招投标文档',
      uploadAreaDescription: '支持上传招标文件、投标书、技术方案等文档',
    },
    presetQuestions: [
      '这个招标项目的主要技术要求是什么？',
      '投标截止时间和开标时间是什么时候？',
      '参与投标需要哪些资质证书？',
      '项目预算范围是多少？',
    ],
    documentTypes: [
      {
        id: 'tender_document',
        name: '招标文件',
        extensions: ['.pdf', '.doc', '.docx'],
        maxSize: 100 * 1024 * 1024,
      },
    ],
  },
  {
    id: 'enterprise',
    name: '企业管理',
    description: '企业制度、流程和管理规范',
    status: 'active',
    theme: {
      primaryColor: 'purple',
      gradientFrom: 'from-purple-600',
      gradientTo: 'to-indigo-600',
      iconColor: 'text-purple-600',
    },
    ui: {
      welcomeTitle: '欢迎使用企业管理智能助手',
      welcomeMessage: '我是您的专业企业管理顾问，帮助您理解制度流程、解读管理规范',
      placeholderText: '请输入您的企业管理相关问题...',
      uploadAreaTitle: '上传企业管理文档',
      uploadAreaDescription: '支持上传制度文档、流程手册、管理规范等文档',
    },
    presetQuestions: [
      '员工请假流程是怎样的？',
      '新员工入职需要准备哪些材料？',
      '公司的考勤制度是什么？',
      '项目管理流程包括哪些步骤？',
    ],
    documentTypes: [
      {
        id: 'management_document',
        name: '管理文档',
        extensions: ['.pdf', '.doc', '.docx'],
        maxSize: 50 * 1024 * 1024,
      },
    ],
  },
  {
    id: 'admin',
    name: '行政',
    description: '行政管理和办公事务',
    status: 'active',
    theme: {
      primaryColor: 'blue',
      gradientFrom: 'from-blue-600',
      gradientTo: 'to-cyan-600',
      iconColor: 'text-blue-600',
    },
    ui: {
      welcomeTitle: '欢迎使用行政智能助手',
      welcomeMessage: '我是您的专业行政管理顾问，帮助您处理行政事务',
      placeholderText: '请输入您的行政相关问题...',
      uploadAreaTitle: '上传行政文档',
      uploadAreaDescription: '支持上传行政文档、通知公告等文档',
    },
    presetQuestions: [],
    documentTypes: [
      {
        id: 'admin_document',
        name: '行政文档',
        extensions: ['.pdf', '.doc', '.docx'],
        maxSize: 50 * 1024 * 1024,
      },
    ],
  },
  {
    id: 'finance',
    name: '财务',
    description: '财务管理和报表分析',
    status: 'active',
    theme: {
      primaryColor: 'yellow',
      gradientFrom: 'from-yellow-600',
      gradientTo: 'to-orange-600',
      iconColor: 'text-yellow-600',
    },
    ui: {
      welcomeTitle: '欢迎使用财务智能助手',
      welcomeMessage: '我是您的专业财务顾问，帮助您处理财务问题',
      placeholderText: '请输入您的财务相关问题...',
      uploadAreaTitle: '上传财务文档',
      uploadAreaDescription: '支持上传财务报表、凭证等文档',
    },
    presetQuestions: [],
    documentTypes: [
      {
        id: 'finance_document',
        name: '财务文档',
        extensions: ['.pdf', '.doc', '.docx', '.xlsx'],
        maxSize: 50 * 1024 * 1024,
      },
    ],
  },
  {
    id: 'procurement',
    name: '采购',
    description: '采购管理和供应商管理',
    status: 'active',
    theme: {
      primaryColor: 'red',
      gradientFrom: 'from-red-600',
      gradientTo: 'to-pink-600',
      iconColor: 'text-red-600',
    },
    ui: {
      welcomeTitle: '欢迎使用采购智能助手',
      welcomeMessage: '我是您的专业采购顾问，帮助您处理采购事务',
      placeholderText: '请输入您的采购相关问题...',
      uploadAreaTitle: '上传采购文档',
      uploadAreaDescription: '支持上传采购合同、询价单等文档',
    },
    presetQuestions: [],
    documentTypes: [
      {
        id: 'procurement_document',
        name: '采购文档',
        extensions: ['.pdf', '.doc', '.docx'],
        maxSize: 50 * 1024 * 1024,
      },
    ],
  },
  {
    id: 'engineering',
    name: '工程',
    description: '工程项目管理和技术管理',
    status: 'active',
    theme: {
      primaryColor: 'gray',
      gradientFrom: 'from-gray-600',
      gradientTo: 'to-slate-600',
      iconColor: 'text-gray-600',
    },
    ui: {
      welcomeTitle: '欢迎使用工程智能助手',
      welcomeMessage: '我是您的专业工程顾问，帮助您处理工程项目',
      placeholderText: '请输入您的工程相关问题...',
      uploadAreaTitle: '上传工程文档',
      uploadAreaDescription: '支持上传工程图纸、技术文档等文档',
    },
    presetQuestions: [],
    documentTypes: [
      {
        id: 'engineering_document',
        name: '工程文档',
        extensions: ['.pdf', '.doc', '.docx', '.dwg'],
        maxSize: 100 * 1024 * 1024,
      },
    ],
  },
];

// Reducer函数
function scenarioReducer(state: ScenarioState, action: ScenarioAction): ScenarioState {
  switch (action.type) {
    case 'SET_LOADING':
      return { ...state, loading: action.payload };
    case 'SET_ERROR':
      return { ...state, error: action.payload, loading: false };
    case 'SET_SCENARIOS':
      return { ...state, availableScenarios: action.payload, loading: false, error: null };
    case 'SET_CURRENT_SCENARIO':
      return { ...state, currentScenario: action.payload };
    case 'CLEAR_CURRENT_SCENARIO':
      return { ...state, currentScenario: null };
    default:
      return state;
  }
}

// Context创建
const ScenarioContext = createContext<{
  state: ScenarioState;
  dispatch: React.Dispatch<ScenarioAction>;
  switchScenario: (scenarioId: string) => void;
  getCurrentTheme: () => ScenarioTheme | null;
  getCurrentUI: () => ScenarioUI | null;
  getPresetQuestions: () => string[];
  getDocumentTypes: () => Array<{ id: string; name: string; extensions: string[]; maxSize: number }>;
} | null>(null);

// Provider组件
interface ScenarioProviderProps {
  children: ReactNode;
}

export function ScenarioProvider({ children }: ScenarioProviderProps) {
  const [state, dispatch] = useReducer(scenarioReducer, initialState);

  // 初始化场景数据
  useEffect(() => {
    const initializeScenarios = async () => {
      try {
        dispatch({ type: 'SET_LOADING', payload: true });

        // 尝试从API获取场景列表
        try {
          const apiBaseUrl = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000';
          const response = await fetch(`${apiBaseUrl}/api/v2/scenarios/`);
          if (response.ok) {
            const data = await response.json();
            dispatch({ type: 'SET_SCENARIOS', payload: data.scenarios });
          } else {
            throw new Error('API请求失败');
          }
        } catch (error) {
          console.warn('无法从API获取场景，使用默认配置:', error);
          dispatch({ type: 'SET_SCENARIOS', payload: defaultScenarios });
        }

        // 设置默认场景 (招投标为默认)
        const savedScenarioId = localStorage.getItem('currentScenarioId');

        // 如果保存的场景是investment，重置为tender
        const defaultScenarioId = (savedScenarioId === 'investment' || !savedScenarioId) ? 'tender' : savedScenarioId;

        const defaultScenario = defaultScenarios.find(s => s.id === defaultScenarioId) || defaultScenarios[0];
        dispatch({ type: 'SET_CURRENT_SCENARIO', payload: defaultScenario });

      } catch (error) {
        dispatch({ type: 'SET_ERROR', payload: '初始化场景失败' });
        console.error('场景初始化失败:', error);
      }
    };

    initializeScenarios();
  }, []);

  // 切换场景
  const switchScenario = (scenarioId: string) => {
    const scenario = state.availableScenarios.find(s => s.id === scenarioId);
    if (scenario) {
      dispatch({ type: 'SET_CURRENT_SCENARIO', payload: scenario });
      localStorage.setItem('currentScenarioId', scenarioId);
    }
  };

  // 获取当前主题
  const getCurrentTheme = (): ScenarioTheme | null => {
    return state.currentScenario?.theme || null;
  };

  // 获取当前UI配置
  const getCurrentUI = (): ScenarioUI | null => {
    return state.currentScenario?.ui || null;
  };

  // 获取预设问题
  const getPresetQuestions = (): string[] => {
    return state.currentScenario?.presetQuestions || [];
  };

  // 获取文档类型
  const getDocumentTypes = () => {
    return state.currentScenario?.documentTypes || [];
  };

  const contextValue = {
    state,
    dispatch,
    switchScenario,
    getCurrentTheme,
    getCurrentUI,
    getPresetQuestions,
    getDocumentTypes,
  };

  return (
    <ScenarioContext.Provider value={contextValue}>
      {children}
    </ScenarioContext.Provider>
  );
}

// Hook
export function useScenario() {
  const context = useContext(ScenarioContext);
  if (!context) {
    throw new Error('useScenario必须在ScenarioProvider内使用');
  }
  return context;
}

// 导出类型
export type { ScenarioState, ScenarioAction };
