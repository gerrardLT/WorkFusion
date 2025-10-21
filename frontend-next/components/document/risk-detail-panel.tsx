'use client';

import * as React from 'react';
import { X, AlertTriangle, Info, Lightbulb, FileText, MapPin } from 'lucide-react';
import { cn } from '@/lib/utils';
import { Risk, RiskLevel, RISK_LEVEL_COLORS, RISK_TYPE_LABELS, RISK_LEVEL_LABELS } from '@/types/risk';
import { Button } from '@/components/ui/button';
import { Card } from '@/components/ui/card';
import { Badge } from '@/components/ui/badge';
import { Separator } from '@/components/ui/separator';

interface RiskDetailPanelProps {
  risk: Risk | null;
  onClose: () => void;
  className?: string;
}

export function RiskDetailPanel({ risk, onClose, className }: RiskDetailPanelProps) {
  if (!risk) return null;

  const colors = RISK_LEVEL_COLORS[risk.risk_level];
  const riskTypeLabel = RISK_TYPE_LABELS[risk.risk_type];
  const riskLevelLabel = RISK_LEVEL_LABELS[risk.risk_level];

  return (
    <Card className={cn(
      "w-full h-full overflow-auto bg-gray-900 border-gray-700",
      className
    )}>
      {/* 头部 */}
      <div className="sticky top-0 z-10 bg-gray-800 border-b border-gray-700 p-4">
        <div className="flex items-start justify-between">
          <div className="flex-1">
            <div className="flex items-center space-x-2 mb-2">
              <Badge
                className={cn("px-2 py-1 text-xs font-semibold")}
                style={{
                  backgroundColor: colors.bg,
                  color: colors.border,
                  border: `1px solid ${colors.border}`,
                }}
              >
                {riskLevelLabel}
              </Badge>
              <Badge variant="outline" className="bg-gray-700 text-gray-200 border-gray-600">
                {riskTypeLabel}
              </Badge>
            </div>
            <h3 className="text-lg font-bold text-gray-100">{risk.title}</h3>
          </div>
          <Button
            variant="ghost"
            size="icon"
            onClick={onClose}
            className="ml-2 text-gray-400 hover:text-gray-200 hover:bg-gray-700"
          >
            <X className="h-5 w-5" />
          </Button>
        </div>
      </div>

      {/* 内容 */}
      <div className="p-4 space-y-4">
        {/* 位置信息 */}
        {(risk.page_number || risk.section || risk.clause_number) && (
          <div className="flex items-start space-x-2 text-sm text-gray-400">
            <MapPin className="h-4 w-4 mt-0.5 flex-shrink-0" />
            <div>
              {risk.page_number && <span>第 {risk.page_number} 页</span>}
              {risk.section && <span className="ml-2">· {risk.section}</span>}
              {risk.clause_number && <span className="ml-2">· 条款 {risk.clause_number}</span>}
            </div>
          </div>
        )}

        <Separator className="bg-gray-700" />

        {/* 风险描述 */}
        <div>
          <div className="flex items-center space-x-2 mb-2">
            <Info className="h-4 w-4 text-blue-400" />
            <h4 className="text-sm font-semibold text-gray-200">风险描述</h4>
          </div>
          <p className="text-sm text-gray-300 leading-relaxed pl-6">
            {risk.description || '暂无详细描述'}
          </p>
        </div>

        {/* 原文内容 */}
        {risk.original_text && (
          <>
            <Separator className="bg-gray-700" />
            <div>
              <div className="flex items-center space-x-2 mb-2">
                <FileText className="h-4 w-4 text-purple-400" />
                <h4 className="text-sm font-semibold text-gray-200">原文内容</h4>
              </div>
              <div className="pl-6 p-3 bg-gray-800 border border-gray-700 rounded-md">
                <p className="text-sm text-gray-300 italic leading-relaxed">
                  "{risk.original_text}"
                </p>
              </div>
            </div>
          </>
        )}

        {/* 影响分析 */}
        {risk.impact_description && (
          <>
            <Separator className="bg-gray-700" />
            <div>
              <div className="flex items-center space-x-2 mb-2">
                <AlertTriangle className="h-4 w-4 text-yellow-400" />
                <h4 className="text-sm font-semibold text-gray-200">影响分析</h4>
              </div>
              <p className="text-sm text-gray-300 leading-relaxed pl-6">
                {risk.impact_description}
              </p>
            </div>
          </>
        )}

        {/* 缓解建议 */}
        {risk.mitigation_suggestion && (
          <>
            <Separator className="bg-gray-700" />
            <div>
              <div className="flex items-center space-x-2 mb-2">
                <Lightbulb className="h-4 w-4 text-green-400" />
                <h4 className="text-sm font-semibold text-gray-200">应对建议</h4>
              </div>
              <div className="pl-6 p-3 bg-green-900/20 border border-green-700/50 rounded-md">
                <p className="text-sm text-gray-300 leading-relaxed">
                  {risk.mitigation_suggestion}
                </p>
              </div>
            </div>
          </>
        )}

        {/* 置信度 */}
        {risk.confidence_score !== undefined && (
          <>
            <Separator className="bg-gray-700" />
            <div className="flex items-center justify-between text-sm">
              <span className="text-gray-400">识别置信度</span>
              <div className="flex items-center space-x-2">
                <div className="w-32 h-2 bg-gray-700 rounded-full overflow-hidden">
                  <div
                    className="h-full bg-blue-500 transition-all"
                    style={{ width: `${risk.confidence_score}%` }}
                  />
                </div>
                <span className="text-gray-200 font-semibold">{risk.confidence_score}%</span>
              </div>
            </div>
          </>
        )}

        {/* 时间信息 */}
        <Separator className="bg-gray-700" />
        <div className="text-xs text-gray-500 space-y-1">
          <div>识别时间: {new Date(risk.created_at).toLocaleString('zh-CN')}</div>
          {risk.updated_at !== risk.created_at && (
            <div>更新时间: {new Date(risk.updated_at).toLocaleString('zh-CN')}</div>
          )}
        </div>
      </div>
    </Card>
  );
}

