/**
 * 文件上传状态管理 - Zustand Store
 * 管理文件上传进度、历史、状态等
 */

import { create } from 'zustand';
import { devtools, persist } from 'zustand/middleware';

export interface UploadFile {
  id: string;
  file: File | null; // null for persisted files
  name: string;
  size: number;
  type: string;
  status: 'pending' | 'uploading' | 'processing' | 'completed' | 'error';
  progress: number;
  uploadedAt?: Date;
  processedAt?: Date;
  error?: string;
  url?: string;
  chunks?: number;
  processedChunks?: number;
}

export interface UploadStats {
  totalFiles: number;
  completedFiles: number;
  totalSize: number;
  uploadedSize: number;
  averageSpeed: number; // bytes per second
}

interface UploadState {
  // 当前上传队列
  uploadQueue: UploadFile[];
  // 上传历史
  uploadHistory: UploadFile[];
  // 是否正在上传
  isUploading: boolean;
  // 当前上传的文件ID
  currentUploadId: string | null;
  // 全局上传统计
  stats: UploadStats;
  // 上传配置
  config: {
    maxFileSize: number; // bytes
    allowedTypes: string[];
    maxConcurrentUploads: number;
    chunkSize: number;
  };
  // 错误信息
  error: string | null;
}

interface UploadActions {
  // 文件管理
  addFiles: (files: File[]) => void;
  removeFile: (fileId: string) => void;
  clearQueue: () => void;
  clearHistory: () => void;
  retryUpload: (fileId: string) => void;

  // 上传控制
  startUpload: (fileId?: string) => Promise<void>;
  pauseUpload: (fileId: string) => void;
  cancelUpload: (fileId: string) => void;

  // 状态更新
  updateFileStatus: (fileId: string, status: UploadFile['status']) => void;
  updateFileProgress: (fileId: string, progress: number) => void;
  updateFileError: (fileId: string, error: string) => void;

  // 配置
  updateConfig: (config: Partial<UploadState['config']>) => void;

  // 工具函数
  validateFile: (file: File) => { valid: boolean; error?: string };
  getFileById: (fileId: string) => UploadFile | undefined;

  // 重置
  reset: () => void;
}

const generateId = () => Math.random().toString(36).substr(2, 9);

const defaultConfig: UploadState['config'] = {
  maxFileSize: 50 * 1024 * 1024, // 50MB
  allowedTypes: [
    'application/pdf',
    'application/vnd.openxmlformats-officedocument.wordprocessingml.document',
    'application/msword',
    'text/plain',
    'text/markdown',
  ],
  maxConcurrentUploads: 3,
  chunkSize: 1024 * 1024, // 1MB chunks
};

const initialStats: UploadStats = {
  totalFiles: 0,
  completedFiles: 0,
  totalSize: 0,
  uploadedSize: 0,
  averageSpeed: 0,
};

const initialState: UploadState = {
  uploadQueue: [],
  uploadHistory: [],
  isUploading: false,
  currentUploadId: null,
  stats: initialStats,
  config: defaultConfig,
  error: null,
};

export const useUploadStore = create<UploadState & UploadActions>()(
  devtools(
    persist(
      (set, get) => ({
        ...initialState,

        // 文件管理
        addFiles: (files: File[]) => {
          const validFiles: UploadFile[] = [];
          const errors: string[] = [];

          files.forEach(file => {
            const validation = get().validateFile(file);
            if (validation.valid) {
              validFiles.push({
                id: generateId(),
                file,
                name: file.name,
                size: file.size,
                type: file.type,
                status: 'pending',
                progress: 0,
              });
            } else {
              errors.push(`${file.name}: ${validation.error}`);
            }
          });

          if (errors.length > 0) {
            set({ error: errors.join('; ') });
          } else {
            set({ error: null });
          }

          set((state) => ({
            uploadQueue: [...state.uploadQueue, ...validFiles],
          }));
        },

        removeFile: (fileId: string) => {
          set((state) => ({
            uploadQueue: state.uploadQueue.filter(f => f.id !== fileId),
            uploadHistory: state.uploadHistory.filter(f => f.id !== fileId),
          }));
        },

        clearQueue: () => set({ uploadQueue: [] }),

        clearHistory: () => set({ uploadHistory: [] }),

        retryUpload: (fileId: string) => {
          set((state) => {
            const fileInHistory = state.uploadHistory.find(f => f.id === fileId);
            if (fileInHistory && fileInHistory.status === 'error') {
              const retryFile = {
                ...fileInHistory,
                status: 'pending' as const,
                progress: 0,
                error: undefined,
              };

              return {
                uploadQueue: [...state.uploadQueue, retryFile],
                uploadHistory: state.uploadHistory.filter(f => f.id !== fileId),
              };
            }
            return state;
          });
        },

        // 上传控制 (真实API实现)
        startUpload: async (fileId?: string) => {
          const state = get();
          if (state.isUploading) return;

          const filesToUpload = fileId
            ? state.uploadQueue.filter(f => f.id === fileId)
            : state.uploadQueue.filter(f => f.status === 'pending');

          if (filesToUpload.length === 0) return;

          set({ isUploading: true, error: null });

          // 动态导入API客户端以避免循环依赖
          const { uploadFile } = await import('@/lib/api');

          for (const uploadFileData of filesToUpload.slice(0, state.config.maxConcurrentUploads)) {
            try {
              set({ currentUploadId: uploadFileData.id });
              get().updateFileStatus(uploadFileData.id, 'uploading');

              // 调用真实的上传API
              const response = await uploadFile(uploadFileData.file, (progress) => {
                get().updateFileProgress(uploadFileData.id, progress);
              });

              // 处理成功响应
              get().updateFileStatus(uploadFileData.id, 'processing');

              // 等待后端处理
              await new Promise(resolve => setTimeout(resolve, 2000));

              // 完成上传
              get().updateFileStatus(uploadFileData.id, 'completed');

              set((state) => {
                const completedFile = {
                  ...uploadFileData,
                  status: 'completed' as const,
                  progress: 100,
                  uploadedAt: new Date(),
                  processedAt: new Date(),
                  file: null, // Remove file object for persistence
                  fileId: response.file_id,
                  processingStatus: response.processing_status,
                };

                return {
                  uploadQueue: state.uploadQueue.filter(f => f.id !== uploadFileData.id),
                  uploadHistory: [completedFile, ...state.uploadHistory],
                };
              });

            } catch (error) {
              const errorMessage = error instanceof Error ? error.message : '上传失败';
              get().updateFileError(uploadFileData.id, errorMessage);

              set((state) => {
                const failedFile = {
                  ...uploadFileData,
                  status: 'error' as const,
                  error: errorMessage,
                  file: null,
                };

                return {
                  uploadQueue: state.uploadQueue.filter(f => f.id !== uploadFileData.id),
                  uploadHistory: [failedFile, ...state.uploadHistory],
                };
              });
            }
          }

          set({ isUploading: false, currentUploadId: null });
        },

        pauseUpload: (fileId: string) => {
          // 实际实现中会暂停上传
          console.log('Pausing upload for file:', fileId);
        },

        cancelUpload: (fileId: string) => {
          set((state) => ({
            uploadQueue: state.uploadQueue.filter(f => f.id !== fileId),
            currentUploadId: state.currentUploadId === fileId ? null : state.currentUploadId,
          }));
        },

        // 状态更新
        updateFileStatus: (fileId: string, status: UploadFile['status']) => {
          set((state) => ({
            uploadQueue: state.uploadQueue.map(f =>
              f.id === fileId ? { ...f, status } : f
            ),
          }));
        },

        updateFileProgress: (fileId: string, progress: number) => {
          set((state) => ({
            uploadQueue: state.uploadQueue.map(f =>
              f.id === fileId ? { ...f, progress } : f
            ),
          }));
        },

        updateFileError: (fileId: string, error: string) => {
          set((state) => ({
            uploadQueue: state.uploadQueue.map(f =>
              f.id === fileId ? { ...f, error, status: 'error' as const } : f
            ),
          }));
        },

        // 配置
        updateConfig: (newConfig: Partial<UploadState['config']>) => {
          set((state) => ({
            config: { ...state.config, ...newConfig },
          }));
        },

        // 工具函数
        validateFile: (file: File) => {
          const { config } = get();

          if (file.size > config.maxFileSize) {
            return {
              valid: false,
              error: `文件大小超过限制 (${Math.round(config.maxFileSize / 1024 / 1024)}MB)`,
            };
          }

          if (!config.allowedTypes.includes(file.type)) {
            return {
              valid: false,
              error: '不支持的文件类型',
            };
          }

          return { valid: true };
        },

        getFileById: (fileId: string) => {
          const state = get();
          return state.uploadQueue.find(f => f.id === fileId) ||
                 state.uploadHistory.find(f => f.id === fileId);
        },

        // 重置
        reset: () => set(initialState),
      }),
      {
        name: 'upload-store',
        partialize: (state) => ({
          uploadHistory: state.uploadHistory.map(file => ({
            ...file,
            file: null, // Don't persist File objects
          })),
          config: state.config,
        }),
      }
    ),
    { name: 'UploadStore' }
  )
);

// 便捷的选择器函数
export const useUploadActions = () => useUploadStore((state) => ({
  addFiles: state.addFiles,
  removeFile: state.removeFile,
  clearQueue: state.clearQueue,
  clearHistory: state.clearHistory,
  retryUpload: state.retryUpload,
  startUpload: state.startUpload,
  pauseUpload: state.pauseUpload,
  cancelUpload: state.cancelUpload,
  updateConfig: state.updateConfig,
  validateFile: state.validateFile,
  reset: state.reset,
}));

export const useUploadState = () => useUploadStore((state) => ({
  uploadQueue: state.uploadQueue,
  uploadHistory: state.uploadHistory,
  isUploading: state.isUploading,
  currentUploadId: state.currentUploadId,
  stats: state.stats,
  config: state.config,
  error: state.error,
}));
