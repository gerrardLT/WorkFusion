'use client';

import * as React from 'react';
import { useState, useEffect, useCallback } from 'react';
import { useParams, useRouter } from 'next/navigation';
import { ArrowLeft, FileText, AlertTriangle, Filter, RefreshCw, Loader2 } from 'lucide-react';
import { DocumentViewer } from '@/components/document/document-viewer';
import { RiskDetailPanel } from '@/components/document/risk-detail-panel';
import { Button } from '@/components/ui/button';
import { Card } from '@/components/ui/card';
import { Badge } from '@/components/ui/badge';
import { Separator } from '@/components/ui/separator';
import { useToast } from '@/components/ui/use-toast';
import { getRiskReportByDocument, detectRisksAsync } from '@/lib/api-v2';
import { Risk, RiskReport, RiskLevel, RISK_LEVEL_COLORS, RISK_LEVEL_LABELS } from '@/types/risk';

export default function DocumentPreviewPage() {
  const params = useParams();
  const router = useRouter();
  const { toast } = useToast();
  const documentId = params?.documentId as string;

  const [riskReport, setRiskReport] = useState<RiskReport | null>(null);
  const [selectedRisk, setSelectedRisk] = useState<Risk | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [filterLevel, setFilterLevel] = useState<RiskLevel | 'all'>('all');
  const [detecting, setDetecting] = useState(false);

  // 获取风险报告
  const fetchRiskReport = useCallback(async () => {
    if (!documentId) return;

    setLoading(true);
    setError(null);

    try {
      const report = await getRiskReportByDocument(documentId);
      setRiskReport(report);
      toast({
        title: "风险报告加载成功",
        description: `共发现 ${report.total_risks} 个风险`,
      });
    } catch (err) {
      console.error('获取风险报告失败:', err);
      setError('未找到风险报告，请先检测风险');
    } finally {
      setLoading(false);
    }
  }, [documentId, toast]);

  // 触发风险检测
  const handleDetectRisks = useCallback(async () => {
    if (!documentId) return;

    setDetecting(true);
    try {
      await detectRisksAsync({
        document_id: documentId,
        scenario_id: 'tender',
      });

      toast({
        title: "风险检测已启动",
        description: "正在后台分析文档，请稍后刷新查看结果",
      });

      // 30秒后自动刷新
      setTimeout(() => {
        fetchRiskReport();
      }, 30000);
    } catch (err) {
      console.error('启动风险检测失败:', err);
      toast({
        title: "风险检测失败",
        description: err instanceof Error ? err.message : "未知错误",
        variant: "destructive",
      });
    } finally {
      setDetecting(false);
    }
  }, [documentId, toast, fetchRiskReport]);

  // 初始加载
  useEffect(() => {
    fetchRiskReport();
  }, [fetchRiskReport]);

  // 过滤风险
  const filteredRisks = React.useMemo(() => {
    if (!riskReport) return [];
    if (filterLevel === 'all') return riskReport.risks;
    return riskReport.risks.filter(risk => risk.risk_level === filterLevel);
  }, [riskReport, filterLevel]);

  // 统计信息
  const stats = React.useMemo(() => {
    if (!riskReport) return null;
    return {
      total: riskReport.total_risks,
      high: riskReport.high_risks,
      medium: riskReport.medium_risks,
      low: riskReport.low_risks,
    };
  }, [riskReport]);

  // PDF文件URL（这里需要根据实际情况构建）
  const pdfUrl = `/api/v2/documents/${documentId}/file`;

  if (loading) {
    return (
      <div className="flex items-center justify-center h-screen bg-gray-900">
        <div className="text-center">
          <Loader2 className="h-12 w-12 animate-spin text-blue-500 mx-auto mb-4" />
          <p className="text-gray-400">加载风险报告中...</p>
        </div>
      </div>
    );
  }

  return (
    <div className="h-screen flex flex-col bg-gray-900">
      {/* 顶部导航栏 */}
      <div className="bg-gray-800 border-b border-gray-700 p-4">
        <div className="flex items-center justify-between">
          <div className="flex items-center space-x-4">
            <Button
              variant="ghost"
              size="icon"
              onClick={() => router.back()}
              className="text-gray-400 hover:text-gray-200 hover:bg-gray-700"
            >
              <ArrowLeft className="h-5 w-5" />
            </Button>
            <div>
              <h1 className="text-xl font-bold text-gray-100 flex items-center">
                <FileText className="h-5 w-5 mr-2" />
                文档风险预览
              </h1>
              <p className="text-sm text-gray-400 mt-1">
                文档ID: {documentId}
              </p>
            </div>
          </div>

          <div className="flex items-center space-x-2">
            <Button
              variant="outline"
              onClick={fetchRiskReport}
              disabled={loading}
              className="bg-gray-700 hover:bg-gray-600 border-gray-600 text-gray-200"
            >
              <RefreshCw className="h-4 w-4 mr-2" />
              刷新
            </Button>
            {error && (
              <Button
                onClick={handleDetectRisks}
                disabled={detecting}
                className="bg-blue-600 hover:bg-blue-700"
              >
                {detecting ? (
                  <>
                    <Loader2 className="h-4 w-4 mr-2 animate-spin" />
                    检测中...
                  </>
                ) : (
                  <>
                    <AlertTriangle className="h-4 w-4 mr-2" />
                    检测风险
                  </>
                )}
              </Button>
            )}
          </div>
        </div>

        {/* 统计信息 */}
        {stats && (
          <div className="mt-4 flex items-center space-x-4">
            <div className="flex items-center space-x-2">
              <span className="text-sm text-gray-400">总风险:</span>
              <Badge variant="outline" className="bg-gray-700 text-gray-200 border-gray-600">
                {stats.total}
              </Badge>
            </div>
            <Separator orientation="vertical" className="h-4 bg-gray-600" />
            {[
              { level: RiskLevel.HIGH, count: stats.high, label: '高' },
              { level: RiskLevel.MEDIUM, count: stats.medium, label: '中' },
              { level: RiskLevel.LOW, count: stats.low, label: '低' },
            ].map(({ level, count, label }) => {
              const colors = RISK_LEVEL_COLORS[level];
              return (
                <div key={level} className="flex items-center space-x-2">
                  <div
                    className="w-3 h-3 rounded-full"
                    style={{ backgroundColor: colors.border }}
                  />
                  <span className="text-sm text-gray-400">{label}风险:</span>
                  <span className="text-sm font-semibold text-gray-200">{count}</span>
                </div>
              );
            })}
          </div>
        )}
      </div>

      {/* 主内容区域 */}
      <div className="flex-1 flex overflow-hidden">
        {/* 左侧：PDF预览 */}
        <div className="flex-1 p-4">
          {error ? (
            <Card className="h-full flex items-center justify-center bg-gray-800 border-gray-700">
              <div className="text-center">
                <AlertTriangle className="h-12 w-12 text-yellow-500 mx-auto mb-4" />
                <p className="text-gray-300 mb-4">{error}</p>
                <Button onClick={handleDetectRisks} disabled={detecting} className="bg-blue-600 hover:bg-blue-700">
                  {detecting ? (
                    <>
                      <Loader2 className="h-4 w-4 mr-2 animate-spin" />
                      检测中...
                    </>
                  ) : (
                    '开始检测风险'
                  )}
                </Button>
              </div>
            </Card>
          ) : (
            <DocumentViewer
              fileUrl={pdfUrl}
              risks={filteredRisks}
              onRiskClick={setSelectedRisk}
            />
          )}
        </div>

        {/* 右侧：风险详情面板 */}
        <div className="w-96 p-4 pl-0">
          {selectedRisk ? (
            <RiskDetailPanel
              risk={selectedRisk}
              onClose={() => setSelectedRisk(null)}
            />
          ) : (
            <Card className="h-full flex items-center justify-center bg-gray-800 border-gray-700">
              <div className="text-center p-8">
                <AlertTriangle className="h-12 w-12 text-gray-600 mx-auto mb-4" />
                <p className="text-gray-400">点击PDF中的风险标记</p>
                <p className="text-gray-500 text-sm mt-2">查看详细信息</p>
              </div>
            </Card>
          )}
        </div>
      </div>
    </div>
  );
}

