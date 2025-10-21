'use client';

import { useState, useEffect } from 'react';
import { useRouter, useParams } from 'next/navigation';
import { Card } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Badge } from '@/components/ui/badge';
import {
  ArrowLeft,
  Download,
  CheckCircle,
  XCircle,
  AlertTriangle,
  TrendingUp,
  FileText,
  Calendar,
  DollarSign,
  MapPin,
  Building2
} from 'lucide-react';
import type { EvaluationReport } from '@/types/evaluation';
import { getEvaluationReport, downloadReportPDF } from '@/lib/api-v2';

export default function EvaluationDetailPage() {
  const router = useRouter();
  const params = useParams();
  const reportId = params.reportId as string;

  const [loading, setLoading] = useState(true);
  const [report, setReport] = useState<EvaluationReport | null>(null);

  useEffect(() => {
    const loadReport = async () => {
      setLoading(true);
      try {
        const data = await getEvaluationReport(reportId);
        setReport(data);
      } catch (error: any) {
        console.error('加载报告失败:', error);
        alert(error.message || '加载失败');
      } finally {
        setLoading(false);
      }
    };

    loadReport();
  }, [reportId]);

  // 下载PDF
  const handleDownloadPDF = async () => {
    if (!report) return;

    try {
      const blob = await downloadReportPDF(reportId);
      const url = window.URL.createObjectURL(blob);
      const a = document.createElement('a');
      a.href = url;
      a.download = `${report.project_summary.title}_评估报告.pdf`;
      document.body.appendChild(a);
      a.click();
      window.URL.revokeObjectURL(url);
      document.body.removeChild(a);
    } catch (error: any) {
      console.error('下载PDF失败:', error);
      alert(error.message || '下载失败');
    }
  };

  if (loading) {
    return (
      <div className="min-h-screen bg-gray-900 p-8 flex items-center justify-center">
        <div className="text-center">
          <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-blue-500 mx-auto mb-4"></div>
          <p className="text-gray-400">加载中...</p>
        </div>
      </div>
    );
  }

  if (!report) {
    return (
      <div className="min-h-screen bg-gray-900 p-8 flex items-center justify-center">
        <div className="text-center">
          <p className="text-gray-400 mb-4">报告未找到</p>
          <Button onClick={() => router.push('/evaluations')} className="bg-blue-600 hover:bg-blue-700">
            返回列表
          </Button>
        </div>
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-gray-900 p-8">
      <div className="max-w-5xl mx-auto">
        {/* 标题栏 */}
        <div className="mb-8">
          <Button
            variant="ghost"
            onClick={() => router.push('/evaluations')}
            className="mb-4 text-gray-300 hover:text-white"
          >
            <ArrowLeft className="h-4 w-4 mr-2" />
            返回列表
          </Button>

          <div className="flex items-start justify-between">
            <div>
              <h1 className="text-3xl font-bold text-white mb-2">
                {report.project_summary.title}
              </h1>
              <p className="text-gray-400">评估报告</p>
            </div>
            <Button
              onClick={handleDownloadPDF}
              className="bg-blue-600 hover:bg-blue-700 text-white"
            >
              <Download className="h-4 w-4 mr-2" />
              下载PDF
            </Button>
          </div>
        </div>

        {/* 1. 项目概况摘要 */}
        <Card className="bg-gray-800 border-gray-700 p-6 mb-6">
          <h2 className="text-xl font-semibold text-white mb-4 flex items-center gap-2">
            <FileText className="h-5 w-5 text-blue-500" />
            项目概况
          </h2>
          <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
            <div>
              <div className="text-sm text-gray-500 mb-1">发布方</div>
              <div className="text-white flex items-center gap-2">
                <Building2 className="h-4 w-4" />
                {report.project_summary.publisher}
              </div>
            </div>
            {report.project_summary.budget && (
              <div>
                <div className="text-sm text-gray-500 mb-1">预算</div>
                <div className="text-white flex items-center gap-2">
                  <DollarSign className="h-4 w-4" />
                  {report.project_summary.budget}万元
                </div>
              </div>
            )}
            {report.project_summary.area && (
              <div>
                <div className="text-sm text-gray-500 mb-1">地域</div>
                <div className="text-white flex items-center gap-2">
                  <MapPin className="h-4 w-4" />
                  {report.project_summary.area}
                </div>
              </div>
            )}
            {report.project_summary.deadline && (
              <div>
                <div className="text-sm text-gray-500 mb-1">截止时间</div>
                <div className="text-white flex items-center gap-2">
                  <Calendar className="h-4 w-4" />
                  {new Date(report.project_summary.deadline).toLocaleDateString('zh-CN')}
                </div>
              </div>
            )}
          </div>
          {report.project_summary.description && (
            <div className="mt-4">
              <div className="text-sm text-gray-500 mb-2">项目描述</div>
              <div className="text-gray-300 text-sm">{report.project_summary.description}</div>
            </div>
          )}
        </Card>

        {/* 2. 核心资质要求对比 */}
        <Card className="bg-gray-800 border-gray-700 p-6 mb-6">
          <h2 className="text-xl font-semibold text-white mb-4 flex items-center gap-2">
            <CheckCircle className="h-5 w-5 text-green-500" />
            核心资质要求对比
          </h2>
          <div className="mb-4">
            <div className="flex items-center gap-4 text-sm">
              <span className="text-gray-400">匹配度:</span>
              <span className="text-2xl font-bold text-blue-400">
                {report.qualification_analysis.match_rate.toFixed(0)}%
              </span>
              <span className="text-gray-500">
                ({report.qualification_analysis.matched_requirements}/{report.qualification_analysis.total_requirements})
              </span>
            </div>
          </div>
          <div className="space-y-3">
            {report.qualification_analysis.details.map((qual, index) => (
              <div key={index} className="flex items-start gap-3 p-3 bg-gray-700/50 rounded-lg">
                {qual.company_has ? (
                  <CheckCircle className="h-5 w-5 text-green-500 flex-shrink-0 mt-0.5" />
                ) : (
                  <XCircle className="h-5 w-5 text-red-500 flex-shrink-0 mt-0.5" />
                )}
                <div className="flex-1">
                  <div className="text-white font-medium mb-1">{qual.requirement}</div>
                  {qual.company_qualification && (
                    <div className="text-sm text-gray-400">
                      企业持有: {qual.company_qualification}
                    </div>
                  )}
                  {qual.notes && (
                    <div className="text-xs text-gray-500 mt-1">{qual.notes}</div>
                  )}
                </div>
                <Badge variant={qual.company_has ? 'default' : 'outline'} className={
                  qual.company_has
                    ? 'bg-green-600 text-white'
                    : 'bg-red-900/20 text-red-400 border-red-800'
                }>
                  {qual.match_score}分
                </Badge>
              </div>
            ))}
          </div>
        </Card>

        {/* 3. 关键时间节点表 */}
        <Card className="bg-gray-800 border-gray-700 p-6 mb-6">
          <h2 className="text-xl font-semibold text-white mb-4 flex items-center gap-2">
            <Calendar className="h-5 w-5 text-purple-500" />
            关键时间节点
          </h2>
          <div className="space-y-3">
            {report.timeline.map((item, index) => (
              <div key={index} className="flex items-center gap-4 p-3 bg-gray-700/50 rounded-lg">
                <div className={`w-3 h-3 rounded-full ${
                  item.status === 'passed' ? 'bg-gray-500' :
                  item.status === 'current' ? 'bg-blue-500 animate-pulse' :
                  'bg-green-500'
                }`} />
                <div className="flex-1">
                  <div className="text-white font-medium">{item.event}</div>
                  <div className="text-sm text-gray-400">{item.date}</div>
                </div>
                {item.days_left !== undefined && item.days_left >= 0 && (
                  <Badge variant="outline" className={
                    item.days_left <= 3
                      ? 'bg-red-900/20 text-red-400 border-red-800'
                      : 'bg-blue-900/20 text-blue-400 border-blue-800'
                  }>
                    {item.days_left}天后
                  </Badge>
                )}
              </div>
            ))}
          </div>
        </Card>

        {/* 4. 历史类似项目中标情况分析 */}
        <Card className="bg-gray-800 border-gray-700 p-6 mb-6">
          <h2 className="text-xl font-semibold text-white mb-4 flex items-center gap-2">
            <TrendingUp className="h-5 w-5 text-orange-500" />
            历史类似项目分析
          </h2>
          <div className="grid grid-cols-4 gap-4 mb-4">
            <div className="text-center p-3 bg-gray-700/50 rounded-lg">
              <div className="text-2xl font-bold text-white">{report.historical_analysis.total_similar_projects}</div>
              <div className="text-xs text-gray-400 mt-1">相似项目</div>
            </div>
            <div className="text-center p-3 bg-gray-700/50 rounded-lg">
              <div className="text-2xl font-bold text-green-400">{report.historical_analysis.won_projects}</div>
              <div className="text-xs text-gray-400 mt-1">中标</div>
            </div>
            <div className="text-center p-3 bg-gray-700/50 rounded-lg">
              <div className="text-2xl font-bold text-red-400">{report.historical_analysis.lost_projects}</div>
              <div className="text-xs text-gray-400 mt-1">未中标</div>
            </div>
            <div className="text-center p-3 bg-gray-700/50 rounded-lg">
              <div className="text-2xl font-bold text-blue-400">{report.historical_analysis.win_rate.toFixed(0)}%</div>
              <div className="text-xs text-gray-400 mt-1">中标率</div>
            </div>
          </div>
          {report.historical_analysis.projects.length > 0 && (
            <div className="space-y-2">
              {report.historical_analysis.projects.slice(0, 5).map((project, index) => (
                <div key={index} className="flex items-center justify-between p-2 bg-gray-700/30 rounded">
                  <div className="flex-1">
                    <div className="text-white text-sm">{project.title}</div>
                    <div className="text-xs text-gray-500">{project.year}年 · {project.amount}万</div>
                  </div>
                  <Badge variant={project.result === 'won' ? 'default' : 'outline'} className={
                    project.result === 'won'
                      ? 'bg-green-600 text-white'
                      : 'bg-gray-700 text-gray-300 border-gray-600'
                  }>
                    {project.result === 'won' ? '中标' : '未中标'}
                  </Badge>
                </div>
              ))}
            </div>
          )}
        </Card>

        {/* 5. 风险点提示 */}
        <Card className="bg-gray-800 border-gray-700 p-6 mb-6">
          <h2 className="text-xl font-semibold text-white mb-4 flex items-center gap-2">
            <AlertTriangle className="h-5 w-5 text-yellow-500" />
            风险点提示
          </h2>
          <div className="grid grid-cols-4 gap-4 mb-4">
            <div className="text-center p-3 bg-gray-700/50 rounded-lg">
              <div className="text-2xl font-bold text-white">{report.risks.total_risks}</div>
              <div className="text-xs text-gray-400 mt-1">风险总数</div>
            </div>
            <div className="text-center p-3 bg-red-900/20 rounded-lg border border-red-800">
              <div className="text-2xl font-bold text-red-400">{report.risks.high_risks}</div>
              <div className="text-xs text-red-400 mt-1">高风险</div>
            </div>
            <div className="text-center p-3 bg-yellow-900/20 rounded-lg border border-yellow-800">
              <div className="text-2xl font-bold text-yellow-400">{report.risks.medium_risks}</div>
              <div className="text-xs text-yellow-400 mt-1">中风险</div>
            </div>
            <div className="text-center p-3 bg-green-900/20 rounded-lg border border-green-800">
              <div className="text-2xl font-bold text-green-400">{report.risks.low_risks}</div>
              <div className="text-xs text-gray-400 mt-1">低风险</div>
            </div>
          </div>
          <div className="space-y-3">
            {report.risks.items.map((risk, index) => (
              <div key={index} className="p-3 bg-gray-700/50 rounded-lg">
                <div className="flex items-start gap-3">
                  <Badge variant="outline" className={
                    risk.level === 'high'
                      ? 'bg-red-900/20 text-red-400 border-red-800'
                      : risk.level === 'medium'
                      ? 'bg-yellow-900/20 text-yellow-400 border-yellow-800'
                      : 'bg-green-900/20 text-green-400 border-green-800'
                  }>
                    {risk.level === 'high' ? '高' : risk.level === 'medium' ? '中' : '低'}
                  </Badge>
                  <div className="flex-1">
                    <div className="text-white font-medium mb-1">{risk.category}</div>
                    <div className="text-sm text-gray-300 mb-2">{risk.description}</div>
                    {risk.mitigation && (
                      <div className="text-xs text-gray-400 bg-gray-800 p-2 rounded">
                        <span className="text-blue-400">建议:</span> {risk.mitigation}
                      </div>
                    )}
                  </div>
                </div>
              </div>
            ))}
          </div>
        </Card>

        {/* 6. 综合评估结论和建议 */}
        <Card className="bg-gradient-to-br from-blue-900/20 to-purple-900/20 border-blue-800 p-6">
          <h2 className="text-xl font-semibold text-white mb-4 flex items-center gap-2">
            <CheckCircle className="h-5 w-5 text-blue-500" />
            综合评估结论
          </h2>

          {/* 评分和推荐 */}
          <div className="flex items-center justify-between mb-6 p-4 bg-gray-800/50 rounded-lg">
            <div>
              <div className="text-sm text-gray-400 mb-1">综合评分</div>
              <div className="text-4xl font-bold text-blue-400">{report.conclusion.overall_score}</div>
            </div>
            <div>
              {report.conclusion.recommendation === 'highly_recommended' && (
                <Badge className="bg-green-600 text-white text-lg px-4 py-2">强烈推荐参与</Badge>
              )}
              {report.conclusion.recommendation === 'recommended' && (
                <Badge className="bg-blue-600 text-white text-lg px-4 py-2">推荐参与</Badge>
              )}
              {report.conclusion.recommendation === 'consider' && (
                <Badge className="bg-yellow-600 text-white text-lg px-4 py-2">谨慎考虑</Badge>
              )}
              {report.conclusion.recommendation === 'not_recommended' && (
                <Badge className="bg-red-600 text-white text-lg px-4 py-2">不建议参与</Badge>
              )}
            </div>
          </div>

          {/* 优势 */}
          {report.conclusion.strengths.length > 0 && (
            <div className="mb-4">
              <div className="text-sm font-semibold text-green-400 mb-2">✓ 优势</div>
              <ul className="space-y-1">
                {report.conclusion.strengths.map((strength, index) => (
                  <li key={index} className="text-sm text-gray-300 pl-4">• {strength}</li>
                ))}
              </ul>
            </div>
          )}

          {/* 劣势 */}
          {report.conclusion.weaknesses.length > 0 && (
            <div className="mb-4">
              <div className="text-sm font-semibold text-red-400 mb-2">✗ 劣势</div>
              <ul className="space-y-1">
                {report.conclusion.weaknesses.map((weakness, index) => (
                  <li key={index} className="text-sm text-gray-300 pl-4">• {weakness}</li>
                ))}
              </ul>
            </div>
          )}

          {/* 建议 */}
          {report.conclusion.suggestions.length > 0 && (
            <div className="mb-4">
              <div className="text-sm font-semibold text-blue-400 mb-2">💡 建议</div>
              <ul className="space-y-1">
                {report.conclusion.suggestions.map((suggestion, index) => (
                  <li key={index} className="text-sm text-gray-300 pl-4">• {suggestion}</li>
                ))}
              </ul>
            </div>
          )}

          {/* 最终结论 */}
          <div className="mt-6 p-4 bg-gray-800/50 rounded-lg border-l-4 border-blue-500">
            <div className="text-sm font-semibold text-blue-400 mb-2">最终结论</div>
            <div className="text-gray-300">{report.conclusion.final_verdict}</div>
          </div>
        </Card>
      </div>
    </div>
  );
}

