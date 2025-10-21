/**
 * 应用设置状态管理 - Zustand Store
 * 管理主题、用户偏好、系统配置等
 */

import { create } from 'zustand';
import { devtools, persist } from 'zustand/middleware';

export type Theme = 'light' | 'dark' | 'system';
export type Language = 'zh-CN' | 'en-US';
export type MessageDisplayMode = 'bubble' | 'list' | 'compact';

export interface UserPreferences {
  // 界面设置
  theme: Theme;
  language: Language;
  messageDisplayMode: MessageDisplayMode;
  showTimestamps: boolean;
  showSourceLinks: boolean;
  autoScroll: boolean;

  // 聊天设置
  enableTypingIndicator: boolean;
  showConfidenceScore: boolean;
  enableNotifications: boolean;
  soundEnabled: boolean;

  // 性能设置
  enableAnimations: boolean;
  reduceMotion: boolean;
  lazyLoadImages: boolean;

  // 高级设置
  enableDevMode: boolean;
  showDebugInfo: boolean;
  cacheSize: number; // MB
}

export interface SystemInfo {
  version: string;
  buildTime: string;
  apiEndpoint: string;
  supportedFormats: string[];
  maxFileSize: number;
}

export interface APISettings {
  baseUrl: string;
  timeout: number;
  retryAttempts: number;
  enableCache: boolean;
  cacheExpiration: number; // minutes
}

interface SettingsState {
  // 用户偏好
  preferences: UserPreferences;
  // API设置
  apiSettings: APISettings;
  // 系统信息
  systemInfo: SystemInfo;
  // 是否首次使用
  isFirstTime: boolean;
  // 应用状态
  isOnline: boolean;
  lastSyncTime: Date | null;
  // 错误状态
  error: string | null;
}

interface SettingsActions {
  // 偏好设置
  updatePreferences: (preferences: Partial<UserPreferences>) => void;
  resetPreferences: () => void;

  // 主题相关
  setTheme: (theme: Theme) => void;
  toggleTheme: () => void;

  // API设置
  updateApiSettings: (settings: Partial<APISettings>) => void;
  testApiConnection: () => Promise<boolean>;

  // 系统状态
  setOnlineStatus: (online: boolean) => void;
  updateLastSyncTime: () => void;
  setFirstTimeComplete: () => void;

  // 缓存管理
  clearCache: () => void;
  getCacheSize: () => number;

  // 导入导出设置
  exportSettings: () => string;
  importSettings: (settingsJson: string) => boolean;

  // 错误处理
  setError: (error: string | null) => void;

  // 重置
  reset: () => void;
}

const defaultPreferences: UserPreferences = {
  // 界面设置
  theme: 'system',
  language: 'zh-CN',
  messageDisplayMode: 'bubble',
  showTimestamps: true,
  showSourceLinks: true,
  autoScroll: true,

  // 聊天设置
  enableTypingIndicator: true,
  showConfidenceScore: true,
  enableNotifications: true,
  soundEnabled: false,

  // 性能设置
  enableAnimations: true,
  reduceMotion: false,
  lazyLoadImages: true,

  // 高级设置
  enableDevMode: false,
  showDebugInfo: false,
  cacheSize: 100, // 100MB
};

const defaultApiSettings: APISettings = {
  baseUrl: 'http://localhost:8000',
  timeout: 30000, // 30 seconds
  retryAttempts: 3,
  enableCache: true,
  cacheExpiration: 30, // 30 minutes
};

const defaultSystemInfo: SystemInfo = {
  version: '1.0.0',
  buildTime: new Date().toISOString(),
  apiEndpoint: 'http://localhost:8000',
  supportedFormats: ['pdf', 'docx', 'txt', 'md'],
  maxFileSize: 50 * 1024 * 1024, // 50MB
};

const initialState: SettingsState = {
  preferences: defaultPreferences,
  apiSettings: defaultApiSettings,
  systemInfo: defaultSystemInfo,
  isFirstTime: true,
  isOnline: true,
  lastSyncTime: null,
  error: null,
};

export const useSettingsStore = create<SettingsState & SettingsActions>()(
  devtools(
    persist(
      (set, get) => ({
        ...initialState,

        // 偏好设置
        updatePreferences: (newPreferences: Partial<UserPreferences>) => {
          set((state) => ({
            preferences: { ...state.preferences, ...newPreferences },
          }));
        },

        resetPreferences: () => {
          set({ preferences: defaultPreferences });
        },

        // 主题相关
        setTheme: (theme: Theme) => {
          set((state) => ({
            preferences: { ...state.preferences, theme },
          }));
        },

        toggleTheme: () => {
          set((state) => {
            const currentTheme = state.preferences.theme;
            let newTheme: Theme;

            if (currentTheme === 'light') {
              newTheme = 'dark';
            } else if (currentTheme === 'dark') {
              newTheme = 'system';
            } else {
              newTheme = 'light';
            }

            return {
              preferences: { ...state.preferences, theme: newTheme },
            };
          });
        },

        // API设置
        updateApiSettings: (newSettings: Partial<APISettings>) => {
          set((state) => ({
            apiSettings: { ...state.apiSettings, ...newSettings },
          }));
        },

        testApiConnection: async () => {
          try {
            const { apiSettings } = get();
            const response = await fetch(`${apiSettings.baseUrl}/health`, {
              method: 'GET',
              signal: AbortSignal.timeout(apiSettings.timeout),
            });

            const isConnected = response.ok;
            set({ isOnline: isConnected, error: null });
            return isConnected;
          } catch (error) {
            const errorMessage = error instanceof Error ? error.message : 'Connection failed';
            set({ isOnline: false, error: errorMessage });
            return false;
          }
        },

        // 系统状态
        setOnlineStatus: (online: boolean) => {
          set({ isOnline: online });
        },

        updateLastSyncTime: () => {
          set({ lastSyncTime: new Date() });
        },

        setFirstTimeComplete: () => {
          set({ isFirstTime: false });
        },

        // 缓存管理
        clearCache: () => {
          // 清理各种缓存
          if (typeof window !== 'undefined') {
            // 清理 localStorage 中的缓存数据（保留设置）
            const keysToKeep = ['settings-store'];
            const allKeys = Object.keys(localStorage);
            allKeys.forEach(key => {
              if (!keysToKeep.some(keepKey => key.includes(keepKey))) {
                localStorage.removeItem(key);
              }
            });

            // 清理 sessionStorage
            sessionStorage.clear();
          }

          set({ lastSyncTime: null });
        },

        getCacheSize: () => {
          if (typeof window === 'undefined') return 0;

          let totalSize = 0;
          const keys = Object.keys(localStorage);

          keys.forEach(key => {
            const item = localStorage.getItem(key);
            if (item) {
              totalSize += new Blob([item]).size;
            }
          });

          return Math.round(totalSize / 1024 / 1024 * 100) / 100; // MB
        },

        // 导入导出设置
        exportSettings: () => {
          const state = get();
          const exportData = {
            preferences: state.preferences,
            apiSettings: state.apiSettings,
            exportTime: new Date().toISOString(),
            version: state.systemInfo.version,
          };

          return JSON.stringify(exportData, null, 2);
        },

        importSettings: (settingsJson: string) => {
          try {
            const importData = JSON.parse(settingsJson);

            // 验证数据结构
            if (!importData.preferences || !importData.apiSettings) {
              throw new Error('Invalid settings format');
            }

            // 合并设置（保留当前有效的字段）
            set((state) => ({
              preferences: { ...state.preferences, ...importData.preferences },
              apiSettings: { ...state.apiSettings, ...importData.apiSettings },
            }));

            return true;
          } catch (error) {
            const errorMessage = error instanceof Error ? error.message : 'Import failed';
            set({ error: errorMessage });
            return false;
          }
        },

        // 错误处理
        setError: (error: string | null) => {
          set({ error });
        },

        // 重置
        reset: () => {
          set(initialState);
        },
      }),
      {
        name: 'settings-store',
        partialize: (state) => ({
          preferences: state.preferences,
          apiSettings: state.apiSettings,
          isFirstTime: state.isFirstTime,
          lastSyncTime: state.lastSyncTime,
        }),
      }
    ),
    { name: 'SettingsStore' }
  )
);

// 便捷的选择器函数
export const useSettingsActions = () => useSettingsStore((state) => ({
  updatePreferences: state.updatePreferences,
  resetPreferences: state.resetPreferences,
  setTheme: state.setTheme,
  toggleTheme: state.toggleTheme,
  updateApiSettings: state.updateApiSettings,
  testApiConnection: state.testApiConnection,
  setOnlineStatus: state.setOnlineStatus,
  updateLastSyncTime: state.updateLastSyncTime,
  setFirstTimeComplete: state.setFirstTimeComplete,
  clearCache: state.clearCache,
  getCacheSize: state.getCacheSize,
  exportSettings: state.exportSettings,
  importSettings: state.importSettings,
  setError: state.setError,
  reset: state.reset,
}));

export const useSettingsState = () => useSettingsStore((state) => ({
  preferences: state.preferences,
  apiSettings: state.apiSettings,
  systemInfo: state.systemInfo,
  isFirstTime: state.isFirstTime,
  isOnline: state.isOnline,
  lastSyncTime: state.lastSyncTime,
  error: state.error,
}));

// 主题相关的便捷hooks
export const useTheme = () => useSettingsStore((state) => state.preferences.theme);
export const useIsOnline = () => useSettingsStore((state) => state.isOnline);
