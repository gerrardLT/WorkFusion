'use client';

import * as React from 'react';
import { useDropzone } from 'react-dropzone';
import {
  Send,
  X,
  Mic,
  MicOff,
  Image,
  FileText,
  AlertCircle,
  Sparkles,
  CheckCircle,
  RefreshCw,
  ArrowUp
} from 'lucide-react';

import { Button } from '@/components/ui/button';
import { Textarea } from '@/components/ui/input';
import { Badge } from '@/components/ui/badge';
import { Card } from '@/components/ui/card';
import { cn, formatFileSize, isSupportedFileType } from '@/lib/utils';
import { uploadFile, getUploadProgress } from '@/lib/api-v2';
import { useScenario } from '@/contexts/scenario-context';
import { ContentGenerationButtons } from './content-generation-buttons';

interface InputAreaProps {
  onSend: (message: string) => void;
  loading?: boolean;
  disabled?: boolean;
  suggestions?: string[];
  maxLength?: number;
  allowFileUpload?: boolean;
  acceptedFileTypes?: string[];
  maxFileSize?: number;
  maxFiles?: number;
  placeholder?: string;
  className?: string;
}

interface UploadingFile {
  file: File;
  progress: number;
  status: 'uploading' | 'processing' | 'completed' | 'error';
  error?: string;
  documentId?: string;
}

export function InputArea({
  onSend,
  loading = false,
  disabled = false,
  suggestions = [],
  maxLength = 4000,
  allowFileUpload = true,
  acceptedFileTypes = ['.pdf', '.txt', '.md', '.doc', '.docx'],
  maxFileSize = 10 * 1024 * 1024, // 10MB
  maxFiles = 5,
  placeholder = '输入您的问题...',
  className,
}: InputAreaProps) {
  const [message, setMessage] = React.useState('');
  const [files, setFiles] = React.useState<File[]>([]);
  const [uploadingFiles, setUploadingFiles] = React.useState<UploadingFile[]>([]);
  const [isRecording, setIsRecording] = React.useState(false);
  const [showSuggestions, setShowSuggestions] = React.useState(false);
  const textareaRef = React.useRef<HTMLTextAreaElement>(null);
  const fileInputRef = React.useRef<HTMLInputElement>(null);
  const { state: scenarioState } = useScenario();

  // Auto-resize textarea - 降低最大高度
  React.useEffect(() => {
    if (textareaRef.current) {
      textareaRef.current.style.height = 'auto';
      textareaRef.current.style.height = `${Math.min(textareaRef.current.scrollHeight, 120)}px`;
    }
  }, [message]);

  // 即时上传文件函数
  const uploadFileImmediately = async (file: File) => {
    if (!scenarioState.currentScenario) {
      console.error('没有选择场景');
      return;
    }

    // 创建上传中的文件记录
    const uploadingFile: UploadingFile = {
      file,
      progress: 0,
      status: 'uploading',
    };

    setUploadingFiles(prev => [...prev, uploadingFile]);

    try {
      console.log(`🚀 开始上传文件: ${file.name}`);

      const result = await uploadFile(
        file,
        scenarioState.currentScenario.id,
        file.name,
        (uploadProgress) => {
          // HTTP 上传进度占总进度的 5%（文件上传很快）
          const adjustedProgress = Math.min(5, Math.round(uploadProgress * 0.05));

          setUploadingFiles(prev =>
            prev.map(f =>
              f.file === file
                ? {
                    ...f,
                    progress: adjustedProgress,
                    status: 'uploading'
                  }
                : f
            )
          );
        }
      );

      console.log(`✅ 文件上传成功，开始处理: ${file.name}`, result);

      const documentId = result.document_id;

      // 开始轮询后端进度
      const pollInterval = setInterval(async () => {
        try {
          const progressResponse = await getUploadProgress(documentId);
          const progressData = progressResponse.data;

          console.log(`📊 进度更新:`, progressData);

          setUploadingFiles(prev =>
            prev.map(f => {
              if (f.file !== file) return f;

              // 根据后端返回的阶段更新状态
              let status: 'uploading' | 'processing' | 'completed' | 'error' = 'processing';
              if (progressData.stage === 'completed') {
                status = 'completed';
              } else if (progressData.stage === 'error') {
                status = 'error';
              } else if (progressData.stage === 'parsing' || progressData.stage === 'vectorizing') {
                status = 'processing';
              }

              // 构建详细消息
              let message = progressData.message;
              if (progressData.total_pages && progressData.current_page !== undefined) {
                message = `${progressData.message} (${progressData.current_page}/${progressData.total_pages} 页)`;
              }

              return {
                ...f,
                progress: progressData.progress,
                status,
                error: progressData.stage === 'error' ? progressData.message : undefined,
                documentId
              };
            })
          );

          // 如果完成或出错，停止轮询
          if (progressData.stage === 'completed' || progressData.stage === 'error') {
            clearInterval(pollInterval);

            // 如果完成，3秒后移除
            if (progressData.stage === 'completed') {
              setTimeout(() => {
                setUploadingFiles(prev => prev.filter(f => f.file !== file));
              }, 3000);
            }
          }

        } catch (error) {
          console.error(`❌ 获取进度失败:`, error);
          // 如果进度接口返回404，说明处理已完成或文档不存在
          if ((error as any)?.response?.status === 404) {
            clearInterval(pollInterval);
            setUploadingFiles(prev =>
              prev.map(f =>
                f.file === file
                  ? { ...f, progress: 100, status: 'completed', documentId }
                  : f
              )
            );
            setTimeout(() => {
              setUploadingFiles(prev => prev.filter(f => f.file !== file));
            }, 3000);
          }
        }
      }, 1000); // 每秒轮询一次

    } catch (error) {
      console.error(`❌ 文件上传失败: ${file.name}`, error);

      // 更新状态为错误
      setUploadingFiles(prev =>
        prev.map(f =>
          f.file === file
            ? {
                ...f,
                status: 'error',
                error: error instanceof Error ? error.message : '上传失败'
              }
            : f
        )
      );
    }
  };

  // Dropzone for file upload
  const { getRootProps, getInputProps, isDragActive, isDragReject } = useDropzone({
    onDrop: (acceptedFiles, rejectedFiles) => {
      // Handle rejected files
      if (rejectedFiles.length > 0) {
        console.warn('Some files were rejected:', rejectedFiles);
      }

      // Filter and add accepted files
      const validFiles = acceptedFiles.filter(file => {
        const isValidType = isSupportedFileType(file, acceptedFileTypes);
        const isValidSize = file.size <= maxFileSize;
        return isValidType && isValidSize;
      });

      // 立即开始上传文件，而不是等到发送消息时
      validFiles.forEach(file => {
        uploadFileImmediately(file);
      });

      // 仍然保留files状态用于显示（可选）
      const newFiles = [...files, ...validFiles].slice(0, maxFiles);
      setFiles(newFiles);
    },
    accept: acceptedFileTypes.reduce((acc, type) => {
      if (type.startsWith('.')) {
        // File extension
        acc[`application/*`] = [type];
      } else {
        // MIME type
        acc[type] = [];
      }
      return acc;
    }, {} as Record<string, string[]>),
    maxSize: maxFileSize,
    maxFiles: maxFiles - files.length,
    disabled: disabled || loading || !allowFileUpload,
  });

  const handleSubmit = React.useCallback(
    (e?: React.FormEvent) => {
      e?.preventDefault();

      if (!message.trim()) return; // 只检查文本，不检查文件
      if (loading || disabled) return;

      // 只发送文本消息，忽略文件（文件应该通过左侧上传区域处理）
      if (files.length > 0) {
        console.warn('已忽略文件附件，问答消息只发送文本。文件上传请使用页面左侧的上传区域。');
        // 不 return，继续发送文本消息
      }

      onSend(message.trim()); // 只发送文本
      setMessage('');
      setFiles([]); // 清除文件状态
      setShowSuggestions(false);
    },
    [message, files, onSend, loading, disabled]
  );

  const handleKeyDown = (e: React.KeyboardEvent) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault();
      handleSubmit();
    }
  };

  const removeFile = (index: number) => {
    setFiles(files.filter((_, i) => i !== index));
  };

  const handleSuggestionClick = (suggestion: string) => {
    setMessage(suggestion);
    setShowSuggestions(false);
    textareaRef.current?.focus();
  };

  const toggleRecording = () => {
    setIsRecording(!isRecording);
    // TODO: Implement voice recording
  };

  const canSend = message.trim() || files.length > 0;
  const isAtMaxLength = message.length >= maxLength;

  return (
    <div
      {...getRootProps()}
      className={cn(
        'space-y-3 input-area relative',
        isDragActive && 'ring-2 ring-blue-500 ring-offset-2 rounded-xl',
        className
      )}
    >
      <input {...getInputProps()} ref={fileInputRef} />

      {/* Drag Overlay */}
      {isDragActive && (
        <div className="absolute inset-0 bg-blue-50/90 backdrop-blur-sm rounded-xl border-2 border-dashed border-blue-500 flex items-center justify-center z-10">
          <div className="text-center">
            <div className="mb-2">
              {isDragReject ? (
                <AlertCircle className="h-12 w-12 mx-auto text-red-500" />
              ) : (
                <FileText className="h-12 w-12 mx-auto text-blue-500" />
              )}
            </div>
            <p className="text-lg font-medium text-gray-800 mb-1">
              {isDragReject ? '不支持的文件类型' : '释放文件以上传'}
            </p>
            <p className="text-sm text-gray-600">
              支持 {acceptedFileTypes.join(', ')} 文件
            </p>
          </div>
        </div>
      )}

      {/* Suggestions */}
      {suggestions.length > 0 && showSuggestions && (
        <div className="flex flex-wrap gap-2">
          {suggestions.slice(0, 3).map((suggestion, index) => (
            <Button
              key={index}
              variant="outline"
              size="sm"
              onClick={() => handleSuggestionClick(suggestion)}
              className="text-sm h-9 px-4 text-left justify-start max-w-xs truncate bg-gray-700 text-gray-200 border-gray-600 hover:bg-gray-600 hover:border-blue-500 hover:text-blue-400 transition-all duration-200"
            >
              <Sparkles className="h-3 w-3 mr-2 flex-shrink-0 text-blue-500" />
              {suggestion}
            </Button>
          ))}
        </div>
      )}

      {/* File Upload Area - Show uploading files */}
      {allowFileUpload && uploadingFiles.length > 0 && (
        <div className="border-2 border-dashed rounded-xl bg-gray-700/50 backdrop-blur-sm border-gray-600">
          <div className="p-3 space-y-2">
            {uploadingFiles.map((uploadingFile, index) => (
              <div
                key={index}
                className="flex items-center gap-3 p-3 bg-gray-600/80 backdrop-blur-sm rounded-lg border border-gray-500 shadow-sm"
              >
                <div className="flex-shrink-0">
                  {uploadingFile.status === 'completed' ? (
                    <CheckCircle className="h-4 w-4 text-green-500" />
                  ) : uploadingFile.status === 'error' ? (
                    <AlertCircle className="h-4 w-4 text-red-500" />
                  ) : uploadingFile.status === 'processing' ? (
                    <RefreshCw className="h-4 w-4 text-blue-500 animate-spin" />
                  ) : (
                    <FileText className="h-4 w-4 text-gray-500" />
                  )}
                </div>
                <div className="flex-1 min-w-0">
                  <p className="text-sm font-medium text-gray-800 truncate">{uploadingFile.file.name}</p>
                  <div className="flex items-center gap-2">
                    <p className="text-xs text-gray-500">
                      {formatFileSize(uploadingFile.file.size)}
                    </p>
                    {uploadingFile.status === 'uploading' && (
                      <span className="text-xs font-semibold text-blue-600">
                        上传中 {uploadingFile.progress}%
                      </span>
                    )}
                    {uploadingFile.status === 'processing' && (
                      <span className="text-xs font-semibold text-purple-600">
                        解析中 {uploadingFile.progress}%
                      </span>
                    )}
                    {uploadingFile.status === 'completed' && (
                      <span className="text-xs font-semibold text-green-600">
                        ✓ 已完成
                      </span>
                    )}
                    {uploadingFile.status === 'error' && (
                      <span className="text-xs font-semibold text-red-600">
                        {uploadingFile.error || '上传失败'}
                      </span>
                    )}
                  </div>
                  {(uploadingFile.status === 'uploading' || uploadingFile.status === 'processing') && (
                    <div className="mt-1.5 w-full bg-gray-200 rounded-full h-2 overflow-hidden">
                      <div
                        className={cn(
                          "h-2 rounded-full transition-all duration-500 ease-out",
                          uploadingFile.status === 'uploading'
                            ? "bg-gradient-to-r from-blue-500 to-blue-600"
                            : "bg-gradient-to-r from-purple-500 to-purple-600"
                        )}
                        style={{
                          width: `${uploadingFile.progress}%`
                        }}
                      />
                    </div>
                  )}
                </div>
                {uploadingFile.status === 'error' && (
                  <Button
                    variant="ghost"
                    size="sm"
                    onClick={() => setUploadingFiles(prev => prev.filter((_, i) => i !== index))}
                    className="h-6 w-6 p-0 hover:bg-red-100 hover:text-red-600"
                  >
                    <X className="h-3 w-3" />
                  </Button>
                )}
              </div>
            ))}
          </div>
        </div>
      )}

      {/* Traditional File Upload Area - Only show when files are present (legacy) */}
      {allowFileUpload && files.length > 0 && uploadingFiles.length === 0 && (
        <div className="border-2 border-dashed rounded-xl bg-gray-700/50 backdrop-blur-sm border-gray-600">
          <div className="p-3 space-y-2">
            {files.map((file, index) => (
              <div
                key={index}
                className="flex items-center gap-3 p-3 bg-gray-600/80 backdrop-blur-sm rounded-lg border border-gray-500 shadow-sm"
              >
                <div className="flex-shrink-0">
                  {file.type.startsWith('image/') ? (
                    <Image className="h-4 w-4 text-blue-500" />
                  ) : (
                    <FileText className="h-4 w-4 text-gray-500" />
                  )}
                </div>
                <div className="flex-1 min-w-0">
                  <p className="text-sm font-medium text-gray-800 truncate">{file.name}</p>
                  <p className="text-xs text-gray-500">
                    {formatFileSize(file.size)}
                  </p>
                </div>
                <Button
                  variant="ghost"
                  size="sm"
                  onClick={() => removeFile(index)}
                  className="h-6 w-6 p-0 hover:bg-red-100 hover:text-red-600"
                >
                  <X className="h-3 w-3" />
                </Button>
              </div>
            ))}
          </div>
        </div>
      )}

      {/* Content Generation Buttons */}
      {scenarioState.currentScenario?.id === 'tender' && (
        <ContentGenerationButtons
          onContentGenerated={(content, contentType) => {
            setMessage(content);
            textareaRef.current?.focus();
          }}
          scenarioId={scenarioState.currentScenario?.id}
          disabled={disabled || loading}
        />
      )}

      {/* Input Area */}
      <Card className="px-3 py-2 bg-gray-800 backdrop-blur-sm border border-gray-700 shadow-lg hover:shadow-xl transition-all duration-200 rounded-3xl">
        <div className="space-y-2">
          {/* Top Row: Textarea */}
          <div className="flex gap-2">
            {/* Textarea - 占满宽度 */}
            <Textarea
              ref={textareaRef}
              value={message}
              onChange={(e) => {
                setMessage(e.target.value);
              }}
              onKeyDown={handleKeyDown}
              placeholder={placeholder}
              disabled={disabled || loading}
              className="flex-1 min-h-[32px] max-h-[100px] resize-none border-0 bg-transparent p-0 px-2 leading-5 outline-none shadow-none ring-0 focus:outline-none focus:border-0 focus:shadow-none focus:ring-0 focus-visible:outline-none focus-visible:border-0 focus-visible:shadow-none focus-visible:ring-0 focus-visible:ring-offset-0 text-white placeholder:text-gray-400"
              style={{ boxShadow: 'none', outline: 'none', border: 'none' }}
              rows={1}
            />
          </div>

          {/* Bottom Row: Upload Button + Send Button */}
          <div className="flex items-center justify-between">
            {/* File Upload Button - 对话框左下角 */}
            {allowFileUpload && (
              <Button
                variant="ghost"
                size="sm"
                onClick={() => fileInputRef.current?.click()}
                disabled={disabled || loading || files.length >= maxFiles}
                className="h-7 w-7 p-0 text-white hover:text-blue-400 hover:bg-gray-700 rounded-full transition-all duration-200"
                title="上传文件"
              >
                <span className="text-2xl font-normal leading-none">+</span>
              </Button>
            )}

            {/* Send Button - 对话框右下角 */}
            <button
              onClick={handleSubmit}
              disabled={!canSend || disabled || isAtMaxLength}
              className="h-8 w-8 rounded-full flex items-center justify-center bg-white hover:bg-gray-50 disabled:bg-gray-600 disabled:opacity-50 disabled:cursor-not-allowed shadow-md transition-all duration-200"
              title="发送消息"
              style={{ backgroundColor: 'white' }}
            >
              <ArrowUp className="h-5 w-5 text-gray-900" style={{ color: '#111827' }} />
            </button>
          </div>
        </div>
      </Card>

      {/* Help Text */}
      <div className="flex items-center justify-between text-xs text-gray-500 px-1">
        <div>
          按 Enter 发送，Shift + Enter 换行
        </div>
        <div className="flex items-center gap-2">
          {uploadingFiles.length > 0 && (
            <Badge
              className={cn(
                "border-blue-200",
                uploadingFiles.some(f => f.status === 'error') ? "bg-red-100 text-red-700" :
                uploadingFiles.some(f => f.status === 'uploading' || f.status === 'processing') ? "bg-blue-100 text-blue-700" :
                "bg-green-100 text-green-700"
              )}
              size="sm"
            >
              {uploadingFiles.filter(f => f.status === 'completed').length}/{uploadingFiles.length} 文件已处理
            </Badge>
          )}
          {files.length > 0 && uploadingFiles.length === 0 && (
            <Badge className="bg-blue-100 text-blue-700 border-blue-200" size="sm">
              {files.length} 个文件已选择
            </Badge>
          )}
        </div>
      </div>
    </div>
  );
}
