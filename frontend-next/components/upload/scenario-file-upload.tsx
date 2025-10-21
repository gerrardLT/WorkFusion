'use client';

import * as React from 'react';
import { useState } from 'react';
import { useDropzone } from '@/lib/dropzone';
import {
  Upload,
  File as FileIcon,
  X,
  AlertCircle,
  CheckCircle,
  Loader2,
  FileText,
  Image as ImageIcon
} from 'lucide-react';

import { Button } from '@/components/ui/button';
import { Card } from '@/components/ui/card';
import { Badge } from '@/components/ui/badge';
import { cn, formatFileSize } from '@/lib/utils';
import { uploadFile } from '@/lib/api-v2';
import { useScenario } from '@/contexts/scenario-context';

export interface ScenarioFileUploadProps {
  onUploadComplete?: (result: any) => void;
  onError?: (error: string) => void;
  disabled?: boolean;
  className?: string;
}

interface UploadState {
  file: File | null;
  uploading: boolean;
  progress: number;
  status: 'idle' | 'uploading' | 'processing' | 'success' | 'error';
  result?: any;
  error?: string;
}

export function ScenarioFileUpload({
  onUploadComplete,
  onError,
  disabled = false,
  className
}: ScenarioFileUploadProps) {
  const { state: scenarioState } = useScenario();
  const [uploadState, setUploadState] = useState<UploadState>({
    file: null,
    uploading: false,
    progress: 0,
    status: 'idle'
  });

  // 支持的文件类型
  const acceptedTypes = ['.pdf', '.txt', '.docx', '.doc'];
  const maxSize = 50 * 1024 * 1024; // 50MB

  const { getRootProps, getInputProps, isDragActive } = useDropzone({
    accept: {
      'application/pdf': ['.pdf'],
      'text/plain': ['.txt'],
      'application/vnd.openxmlformats-officedocument.wordprocessingml.document': ['.docx'],
      'application/msword': ['.doc']
    },
    maxSize,
    multiple: false,
    disabled: disabled || uploadState.uploading,
    onDrop: async (acceptedFiles) => {
      if (acceptedFiles.length > 0) {
        await handleFileUpload(acceptedFiles[0]);
      }
    },
    onDropRejected: (fileRejections) => {
      const error = fileRejections[0]?.errors[0];
      if (error?.code === 'file-too-large') {
        onError?.('文件过大，最大支持50MB');
      } else if (error?.code === 'file-invalid-type') {
        onError?.(`不支持的文件类型，支持的类型: ${acceptedTypes.join(', ')}`);
      } else {
        onError?.(error?.message || '文件选择失败');
      }
    }
  });

  const handleFileUpload = async (file: File) => {
    if (!scenarioState.currentScenario) {
      onError?.('请先选择场景');
      return;
    }

    setUploadState({
      file,
      uploading: true,
      progress: 0,
      status: 'uploading'
    });

    try {
      // 模拟上传进度
      const progressInterval = setInterval(() => {
        setUploadState(prev => ({
          ...prev,
          progress: Math.min(prev.progress + Math.random() * 20, 90)
        }));
      }, 500);

      // 调用API上传
      const result = await uploadFile(file, scenarioState.currentScenario.id);

      clearInterval(progressInterval);

      setUploadState({
        file,
        uploading: false,
        progress: 100,
        status: 'success',
        result
      });

      onUploadComplete?.(result);

    } catch (error: any) {
      setUploadState({
        file,
        uploading: false,
        progress: 0,
        status: 'error',
        error: error.message || '上传失败'
      });

      onError?.(error.message || '上传失败');
    }
  };

  const resetUpload = () => {
    setUploadState({
      file: null,
      uploading: false,
      progress: 0,
      status: 'idle'
    });
  };

  const getFileIcon = (filename: string) => {
    const ext = filename.toLowerCase().split('.').pop();
    if (ext === 'pdf') return <FileText className="h-8 w-8 text-red-500" />;
    if (ext === 'docx' || ext === 'doc') return <FileText className="h-8 w-8 text-blue-500" />;
    if (ext === 'txt') return <FileText className="h-8 w-8 text-gray-500" />;
    return <FileIcon className="h-8 w-8 text-gray-500" />;
  };

  const getStatusMessage = () => {
    switch (uploadState.status) {
      case 'uploading':
        return '正在上传文件...';
      case 'processing':
        return '正在处理文档...';
      case 'success':
        return '文档处理完成！';
      case 'error':
        return uploadState.error || '处理失败';
      default:
        return '';
    }
  };

  const getStatusColor = () => {
    switch (uploadState.status) {
      case 'uploading':
      case 'processing':
        return 'text-blue-600';
      case 'success':
        return 'text-green-600';
      case 'error':
        return 'text-red-600';
      default:
        return 'text-gray-600';
    }
  };

  if (uploadState.file) {
    return (
      <Card className={cn('p-6', className)}>
        <div className="space-y-4">
          {/* 文件信息 */}
          <div className="flex items-center space-x-3">
            {getFileIcon(uploadState.file.name)}
            <div className="flex-1 min-w-0">
              <p className="text-sm font-medium text-gray-900 truncate">
                {uploadState.file.name}
              </p>
              <p className="text-xs text-gray-500">
                {formatFileSize(uploadState.file.size)}
              </p>
            </div>
            <div className="flex items-center space-x-2">
              {uploadState.status === 'success' && (
                <CheckCircle className="h-5 w-5 text-green-500" />
              )}
              {uploadState.status === 'error' && (
                <AlertCircle className="h-5 w-5 text-red-500" />
              )}
              {(uploadState.status === 'uploading' || uploadState.status === 'processing') && (
                <Loader2 className="h-5 w-5 animate-spin text-blue-500" />
              )}
            </div>
          </div>

          {/* 进度条 */}
          {(uploadState.status === 'uploading' || uploadState.status === 'processing') && (
            <div className="space-y-2">
              <div className="w-full bg-gray-200 rounded-full h-2">
                <div
                  className="bg-blue-600 h-2 rounded-full transition-all duration-300"
                  style={{ width: `${uploadState.progress}%` }}
                />
              </div>
              <p className={cn('text-sm', getStatusColor())}>
                {getStatusMessage()}
              </p>
            </div>
          )}

          {/* 成功信息 */}
          {uploadState.status === 'success' && uploadState.result && (
            <div className="bg-green-50 border border-green-200 rounded-lg p-3 space-y-2">
              <p className="text-sm text-green-800 font-medium">
                {uploadState.result.message}
              </p>
              {uploadState.result.processing_stats && (
                <div className="text-xs text-green-700 space-y-1">
                  <p>📄 创建文档块: {uploadState.result.processing_stats.chunks_created}</p>
                  <p>🔍 生成向量: {uploadState.result.processing_stats.vectors_created}</p>
                  <p>📊 文件大小: {uploadState.result.file_size_mb}MB</p>
                  {uploadState.result.processing_stats.pipeline_ready && (
                    <Badge variant="secondary" className="text-xs">
                      RAG系统已就绪
                    </Badge>
                  )}
                </div>
              )}
            </div>
          )}

          {/* 错误信息 */}
          {uploadState.status === 'error' && (
            <div className="bg-red-50 border border-red-200 rounded-lg p-3">
              <p className="text-sm text-red-800">
                {uploadState.error}
              </p>
            </div>
          )}

          {/* 操作按钮 */}
          <div className="flex justify-end space-x-2">
            <Button
              variant="outline"
              size="sm"
              onClick={resetUpload}
              disabled={uploadState.uploading}
            >
              {uploadState.status === 'success' ? '上传新文档' : '重新选择'}
            </Button>
          </div>
        </div>
      </Card>
    );
  }

  return (
    <div
      {...getRootProps()}
      className={cn(
        'border-2 border-dashed rounded-lg p-6 text-center cursor-pointer transition-colors',
        isDragActive
          ? 'border-blue-500 bg-blue-50'
          : 'border-gray-300 hover:border-gray-400',
        disabled && 'opacity-50 cursor-not-allowed',
        className
      )}
    >
      <input {...getInputProps()} />

      <div className="space-y-4">
        <div className="mx-auto w-12 h-12 flex items-center justify-center rounded-full bg-gray-100">
          <Upload className="h-6 w-6 text-gray-600" />
        </div>

        <div className="space-y-2">
          <p className="text-sm font-medium text-gray-900">
            {isDragActive ? '松开以上传文件' : '点击或拖拽文件到此处'}
          </p>
          <p className="text-xs text-gray-500">
            支持 PDF、Word、文本文件，最大 50MB
          </p>
          {scenarioState.currentScenario && (
            <Badge variant="secondary" className="text-xs">
              {scenarioState.currentScenario.name} 场景
            </Badge>
          )}
        </div>

        <Button variant="secondary" size="sm" disabled={disabled}>
          选择文件
        </Button>
      </div>
    </div>
  );
}
