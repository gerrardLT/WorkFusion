'use client';

import * as React from 'react';
import { useState, useEffect } from 'react';
import { Sparkles, Loader2 } from 'lucide-react';
import { Button } from '@/components/ui/button';
import { Badge } from '@/components/ui/badge';
import { useToast } from '@/components/ui/use-toast';
import { generateContent, getContentTypes, type ContentType, type ContentGenerationRequest } from '@/lib/api-v2';

interface ContentGenerationButtonsProps {
  onContentGenerated: (content: string, contentType: string) => void;
  scenarioId?: string;
  projectName?: string;
  disabled?: boolean;
}

export function ContentGenerationButtons({
  onContentGenerated,
  scenarioId = 'tender',
  projectName,
  disabled = false
}: ContentGenerationButtonsProps) {
  const { toast } = useToast();
  const [contentTypes, setContentTypes] = useState<ContentType[]>([]);
  const [generatingType, setGeneratingType] = useState<string | null>(null);
  const [loading, setLoading] = useState(false);

  // 加载内容类型
  useEffect(() => {
    const loadContentTypes = async () => {
      try {
        const types = await getContentTypes();
        setContentTypes(types);
      } catch (error) {
        console.error('加载内容类型失败:', error);
        toast({
          title: "加载失败",
          description: "无法加载内容类型列表",
          variant: "destructive",
        });
      }
    };

    loadContentTypes();
  }, [toast]);

  // 生成内容
  const handleGenerate = async (contentType: string, label: string) => {
    if (disabled || generatingType) return;

    setGeneratingType(contentType);
    setLoading(true);

    try {
      const request: ContentGenerationRequest = {
        content_type: contentType,
        project_name: projectName,
        use_knowledge_base: true,
        scenario_id: scenarioId
      };

      const response = await generateContent(request);

      if (response.success && response.content) {
        onContentGenerated(response.content, contentType);
        toast({
          title: "生成成功",
          description: `已生成${label}（${response.word_count}字）`,
        });
      } else {
        throw new Error(response.error || '生成失败');
      }
    } catch (error) {
      console.error('内容生成失败:', error);
      toast({
        title: "生成失败",
        description: error instanceof Error ? error.message : "未知错误",
        variant: "destructive",
      });
    } finally {
      setGeneratingType(null);
      setLoading(false);
    }
  };

  // 显示的内容类型（最多显示4个常用的）
  const displayTypes = contentTypes.slice(0, 4);

  if (contentTypes.length === 0) {
    return null;
  }

  return (
    <div className="mb-3">
      <div className="flex items-center gap-2 mb-2">
        <Sparkles className="h-4 w-4 text-blue-400" />
        <span className="text-xs text-gray-400">快速生成标书内容</span>
      </div>
      <div className="grid grid-cols-2 gap-2">
        {displayTypes.map((type) => (
          <Button
            key={type.value}
            variant="outline"
            size="sm"
            onClick={() => handleGenerate(type.value, type.label)}
            disabled={disabled || loading}
            className={`
              relative overflow-hidden
              bg-gray-700 hover:bg-gray-600
              border-gray-600 hover:border-blue-500
              text-gray-200 hover:text-white
              transition-all duration-200
              ${generatingType === type.value ? 'border-blue-500 bg-gray-600' : ''}
            `}
          >
            {generatingType === type.value ? (
              <>
                <Loader2 className="h-3 w-3 mr-1 animate-spin" />
                生成中...
              </>
            ) : (
              <>
                {type.icon && <span className="mr-1">{type.icon}</span>}
                {type.label}
              </>
            )}
          </Button>
        ))}
      </div>
      {contentTypes.length > 4 && (
        <div className="mt-2 text-center">
          <Badge variant="outline" className="text-xs bg-gray-700 text-gray-300 border-gray-600">
            还有 {contentTypes.length - 4} 种内容类型
          </Badge>
        </div>
      )}
    </div>
  );
}

