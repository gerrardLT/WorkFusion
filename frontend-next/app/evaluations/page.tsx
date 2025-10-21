'use client';

import { useState, useEffect } from 'react';
import { useRouter } from 'next/navigation';
import { Card } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Badge } from '@/components/ui/badge';
import {
  ArrowLeft,
  FileText,
  Download,
  Eye,
  Trash2,
  RefreshCw,
  CheckCircle,
  AlertCircle,
  Clock
} from 'lucide-react';
import type { EvaluationReport } from '@/types/evaluation';
import { listEvaluationReports, downloadReportPDF } from '@/lib/api-v2';

export default function EvaluationsPage() {
  const router = useRouter();
  const [loading, setLoading] = useState(true);
  const [reports, setReports] = useState<EvaluationReport[]>([]);
  const [total, setTotal] = useState(0);
  const [page, setPage] = useState(1);
  const [pageSize] = useState(20);

  // 加载报告列表
  const loadReports = async () => {
    setLoading(true);
    try {
      const response = await listEvaluationReports({
        page,
        page_size: pageSize,
      });
      setReports(response.reports);
      setTotal(response.total);
    } catch (error: any) {
      console.error('加载评估报告失败:', error);
      alert(error.message || '加载失败');
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    loadReports();
  }, [page]);

  // 下载PDF
  const handleDownloadPDF = async (reportId: string, projectTitle: string) => {
    try {
      const blob = await downloadReportPDF(reportId);
      const url = window.URL.createObjectURL(blob);
      const a = document.createElement('a');
      a.href = url;
      a.download = `${projectTitle}_评估报告.pdf`;
      document.body.appendChild(a);
      a.click();
      window.URL.revokeObjectURL(url);
      document.body.removeChild(a);
    } catch (error: any) {
      console.error('下载PDF失败:', error);
      alert(error.message || '下载失败');
    }
  };

  // 获取推荐标签
  const getRecommendationBadge = (recommendation: string) => {
    switch (recommendation) {
      case 'highly_recommended':
        return <Badge className="bg-green-600 text-white">强烈推荐</Badge>;
      case 'recommended':
        return <Badge className="bg-blue-600 text-white">推荐</Badge>;
      case 'consider':
        return <Badge className="bg-yellow-600 text-white">考虑</Badge>;
      case 'not_recommended':
        return <Badge className="bg-red-600 text-white">不推荐</Badge>;
      default:
        return <Badge variant="outline">未知</Badge>;
    }
  };

  // 获取状态图标
  const getStatusIcon = (status: string) => {
    switch (status) {
      case 'final':
        return <CheckCircle className="h-4 w-4 text-green-500" />;
      case 'draft':
        return <Clock className="h-4 w-4 text-yellow-500" />;
      case 'archived':
        return <AlertCircle className="h-4 w-4 text-gray-500" />;
      default:
        return null;
    }
  };

  return (
    <div className="min-h-screen bg-gray-900 p-8">
      <div className="max-w-7xl mx-auto">
        {/* 标题栏 */}
        <div className="mb-8">
          <Button
            variant="ghost"
            onClick={() => router.push('/')}
            className="mb-4 text-gray-300 hover:text-white"
          >
            <ArrowLeft className="h-4 w-4 mr-2" />
            返回首页
          </Button>
          <div className="flex items-center justify-between">
            <div>
              <h1 className="text-3xl font-bold text-white mb-2">评估报告</h1>
              <p className="text-gray-400">
                查看和下载项目评估报告
              </p>
            </div>
            <Button
              variant="outline"
              onClick={loadReports}
              disabled={loading}
              className="border-gray-600 text-gray-300 hover:bg-gray-700"
            >
              <RefreshCw className={`h-4 w-4 mr-2 ${loading ? 'animate-spin' : ''}`} />
              刷新
            </Button>
          </div>
        </div>

        {/* 统计信息 */}
        <div className="mb-6">
          <p className="text-gray-400 text-sm">
            共有 <span className="text-white font-semibold">{total}</span> 份评估报告
          </p>
        </div>

        {/* 报告列表 */}
        {loading ? (
          <Card className="bg-gray-800 border-gray-700 p-12 text-center">
            <div className="flex flex-col items-center gap-4">
              <RefreshCw className="h-8 w-8 text-blue-500 animate-spin" />
              <p className="text-gray-400">加载中...</p>
            </div>
          </Card>
        ) : reports.length === 0 ? (
          <Card className="bg-gray-800 border-gray-700 p-12 text-center">
            <FileText className="h-16 w-16 text-gray-600 mx-auto mb-4" />
            <p className="text-gray-400 mb-4">暂无评估报告</p>
            <p className="text-gray-500 text-sm mb-6">
              在项目推荐列表中点击"快速评估"生成报告
            </p>
            <Button
              onClick={() => router.push('/projects')}
              className="bg-blue-600 hover:bg-blue-700 text-white"
            >
              前往项目推荐
            </Button>
          </Card>
        ) : (
          <Card className="bg-gray-800 border-gray-700 overflow-hidden">
            <div className="divide-y divide-gray-700">
              {reports.map((report) => (
                <div
                  key={report.id}
                  className="p-6 hover:bg-gray-700/50 transition-colors"
                >
                  <div className="flex items-start justify-between">
                    <div className="flex-1">
                      {/* 标题和状态 */}
                      <div className="flex items-center gap-3 mb-3">
                        {getStatusIcon(report.status)}
                        <h3 className="text-white font-semibold text-lg">
                          {report.project_summary.title}
                        </h3>
                        {getRecommendationBadge(report.conclusion.recommendation)}
                      </div>

                      {/* 项目信息 */}
                      <div className="grid grid-cols-2 md:grid-cols-4 gap-4 mb-4">
                        <div>
                          <div className="text-xs text-gray-500 mb-1">发布方</div>
                          <div className="text-sm text-gray-300">{report.project_summary.publisher}</div>
                        </div>
                        <div>
                          <div className="text-xs text-gray-500 mb-1">预算</div>
                          <div className="text-sm text-gray-300">
                            {report.project_summary.budget
                              ? `${report.project_summary.budget}万`
                              : '未公开'}
                          </div>
                        </div>
                        <div>
                          <div className="text-xs text-gray-500 mb-1">资质匹配度</div>
                          <div className="text-sm text-gray-300">
                            {report.qualification_analysis.match_rate.toFixed(0)}%
                          </div>
                        </div>
                        <div>
                          <div className="text-xs text-gray-500 mb-1">综合评分</div>
                          <div className="text-sm font-semibold text-blue-400">
                            {report.conclusion.overall_score}分
                          </div>
                        </div>
                      </div>

                      {/* 风险统计 */}
                      <div className="flex items-center gap-4 text-sm">
                        <div className="flex items-center gap-1">
                          <span className="text-gray-500">风险:</span>
                          <span className="text-red-400">{report.risks.high_risks} 高</span>
                          <span className="text-yellow-400">{report.risks.medium_risks} 中</span>
                          <span className="text-green-400">{report.risks.low_risks} 低</span>
                        </div>
                        <div className="text-gray-500 text-xs">
                          生成于 {new Date(report.generated_at).toLocaleString('zh-CN')}
                        </div>
                      </div>
                    </div>

                    {/* 操作按钮 */}
                    <div className="flex items-center gap-2 ml-4">
                      <Button
                        variant="outline"
                        size="sm"
                        onClick={() => router.push(`/evaluations/${report.id}`)}
                        className="border-gray-600 text-gray-300 hover:bg-gray-700"
                      >
                        <Eye className="h-4 w-4 mr-2" />
                        查看
                      </Button>
                      <Button
                        variant="outline"
                        size="sm"
                        onClick={() => handleDownloadPDF(report.id, report.project_summary.title)}
                        className="border-gray-600 text-gray-300 hover:bg-blue-600 hover:text-white hover:border-blue-600"
                      >
                        <Download className="h-4 w-4 mr-2" />
                        下载PDF
                      </Button>
                    </div>
                  </div>
                </div>
              ))}
            </div>
          </Card>
        )}

        {/* 分页 */}
        {!loading && reports.length > 0 && (
          <div className="mt-6 flex items-center justify-center gap-2">
            <Button
              variant="outline"
              onClick={() => setPage((p) => Math.max(1, p - 1))}
              disabled={page === 1}
              className="border-gray-600 text-gray-300 hover:bg-gray-700"
            >
              上一页
            </Button>
            <span className="text-gray-400 px-4">
              第 {page} 页 / 共 {Math.ceil(total / pageSize)} 页
            </span>
            <Button
              variant="outline"
              onClick={() => setPage((p) => p + 1)}
              disabled={page >= Math.ceil(total / pageSize)}
              className="border-gray-600 text-gray-300 hover:bg-gray-700"
            >
              下一页
            </Button>
          </div>
        )}
      </div>
    </div>
  );
}

