/**
 * 状态管理统一导出
 * 集中管理所有Zustand stores
 */

// 聊天状态
export {
  useChatStore,
  useChatActions,
  useChatState,
} from './chat-store';

// 文件上传状态
export {
  useUploadStore,
  useUploadActions,
  useUploadState,
} from './upload-store';

// 应用设置状态
export {
  useSettingsStore,
  useSettingsActions,
  useSettingsState,
} from './settings-store';

// 导入hooks供内部使用
import {
  useChatState,
  useChatActions
} from './chat-store';
import {
  useUploadState,
  useUploadActions
} from './upload-store';
import {
  useSettingsState,
  useSettingsActions
} from './settings-store';

// 组合hooks - 多个store的组合使用
export const useAppState = () => {
  const chatState = useChatState();
  const uploadState = useUploadState();
  const settingsState = useSettingsState();

  return {
    chat: chatState,
    upload: uploadState,
    settings: settingsState,
    // 衍生状态
    hasActivities: chatState.sessions.length > 0 || uploadState.uploadHistory.length > 0,
    isSystemBusy: chatState.isLoading || uploadState.isUploading,
  };
};

export const useAppActions = () => {
  const chatActions = useChatActions();
  const uploadActions = useUploadActions();
  const settingsActions = useSettingsActions();

  return {
    chat: chatActions,
    upload: uploadActions,
    settings: settingsActions,
    // 组合操作
    resetAll: () => {
      chatActions.reset();
      uploadActions.reset();
      settingsActions.reset();
    },
  };
};
