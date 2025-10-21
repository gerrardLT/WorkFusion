'use client';

import * as React from 'react';
import { useDropzone } from '@/lib/dropzone';
import {
  Upload,
  File as FileIcon,
  Image,
  X,
  AlertCircle,
  CheckCircle,
  Loader2,
  Plus
} from 'lucide-react';

import { Button } from '@/components/ui/button';
import { Card } from '@/components/ui/card';
import { Badge } from '@/components/ui/badge';
import { cn, formatFileSize, isSupportedFileType } from '@/lib/utils';

export interface FileUploadProps {
  accept?: string[];
  maxSize?: number;
  maxFiles?: number;
  onUpload: (files: File[]) => void;
  onProgress?: (progress: number) => void;
  onError?: (error: string) => void;
  allowMultiple?: boolean;
  dragAndDrop?: boolean;
  preview?: boolean;
  disabled?: boolean;
  className?: string;
}

interface UploadingFileState {
  file: File;
  id: string;
  progress: number;
  status: 'uploading' | 'success' | 'error';
  error?: string;
}

export function FileUpload({
  accept = ['.pdf', '.txt', '.md', '.doc', '.docx', '.xlsx', '.csv'],
  maxSize = 10 * 1024 * 1024, // 10MB
  maxFiles = 10,
  onUpload,
  onProgress,
  onError,
  allowMultiple = true,
  dragAndDrop = true,
  preview = true,
  disabled = false,
  className,
}: FileUploadProps) {
  const [uploadingFiles, setUploadingFiles] = React.useState<UploadingFileState[]>([]);
  const fileInputRef = React.useRef<HTMLInputElement>(null);

  // Dropzone configuration
  const { getRootProps, getInputProps, isDragActive, isDragReject } = useDropzone({
    onDrop: (acceptedFiles, rejectedFiles) => {
      // Handle rejected files
      if (rejectedFiles.length > 0) {
        const errors = rejectedFiles.map(({ file, errors }) =>
          `${file.name}: ${errors.map((e: any) => e.message).join(', ')}`
        );
        onError?.(errors.join('\n'));
      }

      // Process accepted files
      if (acceptedFiles.length > 0) {
        handleFilesSelected(acceptedFiles);
      }
    },
    accept: accept.reduce((acc, type) => {
      if (type.startsWith('.')) {
        acc[`application/*`] = [type];
      } else {
        acc[type] = [];
      }
      return acc;
    }, {} as Record<string, string[]>),
    maxSize,
    maxFiles: maxFiles - uploadingFiles.length,
    multiple: allowMultiple,
    disabled: disabled || !dragAndDrop,
  });

  const handleFilesSelected = (files: File[]) => {
    // Validate files
    const validFiles = files.filter(file => {
      const isValidType = isSupportedFileType(file, accept);
      const isValidSize = file.size <= maxSize;

      if (!isValidType) {
        onError?.(`不支持的文件类型: ${file.name}`);
        return false;
      }

      if (!isValidSize) {
        onError?.(`文件过大: ${file.name} (最大 ${formatFileSize(maxSize)})`);
        return false;
      }

      return true;
    });

    if (validFiles.length === 0) return;

    // Check total file count
    const totalFiles = uploadingFiles.length + validFiles.length;
    if (totalFiles > maxFiles) {
      onError?.(`最多只能上传 ${maxFiles} 个文件`);
      return;
    }

    // Start upload simulation for each file
    const newUploadingFiles: UploadingFileState[] = validFiles.map(file => ({
      file,
      id: Math.random().toString(36).substr(2, 9),
      progress: 0,
      status: 'uploading',
    }));

    setUploadingFiles(prev => [...prev, ...newUploadingFiles]);

    // Simulate upload progress for each file
    newUploadingFiles.forEach(uploadFile => {
      simulateUpload(uploadFile);
    });

    // Call onUpload callback
    onUpload(validFiles);
  };

  const simulateUpload = (uploadFile: UploadingFileState) => {
    let progress = 0;
    const interval = setInterval(() => {
      progress += Math.random() * 15;

      if (progress >= 100) {
        progress = 100;
        clearInterval(interval);

        // Simulate success/error
        const isSuccess = Math.random() > 0.1; // 90% success rate

        setUploadingFiles(prev =>
          prev.map(f =>
            f.id === uploadFile.id
              ? {
                  ...f,
                  progress: 100,
                  status: isSuccess ? 'success' : 'error',
                  error: isSuccess ? undefined : '上传失败，请重试'
                }
              : f
          )
        );

        if (!isSuccess) {
          onError?.(`上传失败: ${uploadFile.file.name}`);
        }
      } else {
        setUploadingFiles(prev =>
          prev.map(f =>
            f.id === uploadFile.id ? { ...f, progress } : f
          )
        );

        onProgress?.(progress);
      }
    }, 200);
  };

  const removeFile = (id: string) => {
    setUploadingFiles(prev => prev.filter(f => f.id !== id));
  };

  const retryUpload = (id: string) => {
    const file = uploadingFiles.find(f => f.id === id);
    if (file) {
      const updatedFile = { ...file, progress: 0, status: 'uploading' as const, error: undefined };
      setUploadingFiles(prev =>
        prev.map(f => f.id === id ? updatedFile : f)
      );
      simulateUpload(updatedFile);
    }
  };

  const getFileIcon = (file: File) => {
    if (file.type.startsWith('image/')) {
      return <Image className="h-8 w-8 text-blue-500" />;
    }
    return <FileIcon className="h-8 w-8 text-gray-500" />;
  };

  const getStatusIcon = (status: UploadingFileState['status']) => {
    switch (status) {
      case 'uploading':
        return <Loader2 className="h-4 w-4 animate-spin text-blue-500" />;
      case 'success':
        return <CheckCircle className="h-4 w-4 text-success-500" />;
      case 'error':
        return <AlertCircle className="h-4 w-4 text-error-500" />;
    }
  };

  const canAddMore = uploadingFiles.length < maxFiles;

  return (
    <div className={cn('space-y-4', className)}>
      {/* Upload Area */}
      {canAddMore && (
        <div
          {...(dragAndDrop ? getRootProps() : {})}
          className={cn(
            'border-2 border-dashed rounded-lg transition-colors cursor-pointer',
            isDragActive && !isDragReject && 'border-brand-500 bg-brand-50 dark:bg-brand-950',
            isDragReject && 'border-error-500 bg-error-50 dark:bg-error-950',
            !isDragActive && 'border-muted-foreground/25 hover:border-brand-500',
            disabled && 'opacity-50 cursor-not-allowed'
          )}
        >
          {dragAndDrop && <input {...getInputProps()} />}
          <input
            ref={fileInputRef}
            type="file"
            multiple={allowMultiple}
            accept={accept.join(',')}
            onChange={(e) => {
              if (e.target.files) {
                handleFilesSelected(Array.from(e.target.files));
              }
            }}
            className="hidden"
            disabled={disabled}
          />

          <div className="p-8 text-center">
            <div className="mb-4">
              {isDragActive ? (
                isDragReject ? (
                  <AlertCircle className="h-12 w-12 mx-auto text-error-500" />
                ) : (
                  <Upload className="h-12 w-12 mx-auto text-brand-500" />
                )
              ) : (
                <Upload className="h-12 w-12 mx-auto text-muted-foreground" />
              )}
            </div>

            <div className="space-y-2">
              <h3 className="text-lg font-medium text-foreground">
                {isDragActive
                  ? isDragReject
                    ? '不支持的文件类型'
                    : '释放文件以上传'
                  : '上传文件'
                }
              </h3>

              {!isDragActive && (
                <div className="space-y-1">
                  <p className="text-sm text-muted-foreground">
                    {dragAndDrop ? '拖拽文件到此处' : '点击选择文件'}
                    {dragAndDrop && (
                      <>
                        或{' '}
                        <button
                          onClick={() => fileInputRef.current?.click()}
                          className="text-brand-600 hover:text-brand-700 font-medium"
                        >
                          浏览文件
                        </button>
                      </>
                    )}
                  </p>

                  <div className="flex items-center justify-center gap-4 text-xs text-muted-foreground">
                    <span>支持: {accept.join(', ')}</span>
                    <span>最大: {formatFileSize(maxSize)}</span>
                    <span>限制: {maxFiles} 个文件</span>
                  </div>
                </div>
              )}
            </div>

            {!dragAndDrop && (
              <Button
                onClick={() => fileInputRef.current?.click()}
                disabled={disabled}
                className="mt-4"
              >
                <Plus className="h-4 w-4 mr-2" />
                选择文件
              </Button>
            )}
          </div>
        </div>
      )}

      {/* Uploading Files List */}
      {uploadingFiles.length > 0 && (
        <div className="space-y-2">
          <h4 className="text-sm font-medium text-foreground">
            上传进度 ({uploadingFiles.length}/{maxFiles})
          </h4>

          <div className="space-y-2">
            {uploadingFiles.map((uploadFile) => (
              <Card key={uploadFile.id} className="p-4">
                <div className="flex items-center gap-4">
                  {/* File Icon */}
                  <div className="flex-shrink-0">
                    {preview && uploadFile.file.type.startsWith('image/') ? (
                      <div className="w-12 h-12 rounded border bg-muted flex items-center justify-center">
                        <Image className="h-6 w-6 text-muted-foreground" />
                      </div>
                    ) : (
                      getFileIcon(uploadFile.file)
                    )}
                  </div>

                  {/* File Info */}
                  <div className="flex-1 min-w-0">
                    <div className="flex items-center justify-between mb-1">
                      <p className="text-sm font-medium text-foreground truncate">
                        {uploadFile.file.name}
                      </p>
                      <div className="flex items-center gap-2">
                        {getStatusIcon(uploadFile.status)}
                        <span className="text-xs text-muted-foreground">
                          {formatFileSize(uploadFile.file.size)}
                        </span>
                      </div>
                    </div>

                    {/* Progress Bar */}
                    {uploadFile.status === 'uploading' && (
                      <div className="w-full bg-muted rounded-full h-1.5">
                        <div
                          className="bg-brand-500 h-1.5 rounded-full transition-all duration-300"
                          style={{ width: `${uploadFile.progress}%` }}
                        />
                      </div>
                    )}

                    {/* Status Messages */}
                    {uploadFile.status === 'success' && (
                      <p className="text-xs text-success-600">上传成功</p>
                    )}

                    {uploadFile.status === 'error' && (
                      <div className="flex items-center justify-between">
                        <p className="text-xs text-error-600">{uploadFile.error}</p>
                        <Button
                          variant="outline"
                          size="sm"
                          onClick={() => retryUpload(uploadFile.id)}
                          className="h-6 px-2 text-xs"
                        >
                          重试
                        </Button>
                      </div>
                    )}
                  </div>

                  {/* Remove Button */}
                  <Button
                    variant="ghost"
                    size="sm"
                    onClick={() => removeFile(uploadFile.id)}
                    className="h-8 w-8 p-0 hover:bg-error-100 hover:text-error-600"
                  >
                    <X className="h-4 w-4" />
                  </Button>
                </div>
              </Card>
            ))}
          </div>
        </div>
      )}
    </div>
  );
}
