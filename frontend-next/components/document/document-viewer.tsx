'use client';

import * as React from 'react';
import { useState, useCallback, useMemo } from 'react';
import { Document, Page, pdfjs } from 'react-pdf';
import { ChevronLeft, ChevronRight, ZoomIn, ZoomOut, Maximize2, Download, Loader2 } from 'lucide-react';
import { cn } from '@/lib/utils';
import { Risk, RiskLevel, RISK_LEVEL_COLORS } from '@/types/risk';
import { Button } from '@/components/ui/button';
import { Card } from '@/components/ui/card';
import 'react-pdf/dist/Page/AnnotationLayer.css';
import 'react-pdf/dist/Page/TextLayer.css';

// 配置PDF.js worker
pdfjs.GlobalWorkerOptions.workerSrc = `//unpkg.com/pdfjs-dist@${pdfjs.version}/build/pdf.worker.min.js`;

interface DocumentViewerProps {
  fileUrl: string;
  risks?: Risk[];
  onRiskClick?: (risk: Risk) => void;
  className?: string;
}

export function DocumentViewer({ fileUrl, risks = [], onRiskClick, className }: DocumentViewerProps) {
  const [numPages, setNumPages] = useState<number>(0);
  const [currentPage, setCurrentPage] = useState<number>(1);
  const [scale, setScale] = useState<number>(1.0);
  const [loading, setLoading] = useState<boolean>(true);
  const [error, setError] = useState<string | null>(null);

  // PDF加载成功回调
  const onDocumentLoadSuccess = useCallback(({ numPages }: { numPages: number }) => {
    setNumPages(numPages);
    setLoading(false);
    setError(null);
  }, []);

  // PDF加载失败回调
  const onDocumentLoadError = useCallback((error: Error) => {
    console.error('PDF加载失败:', error);
    setError('PDF文档加载失败，请检查文件路径或格式');
    setLoading(false);
  }, []);

  // 过滤当前页的风险
  const currentPageRisks = useMemo(() => {
    return risks.filter(risk => risk.page_number === currentPage);
  }, [risks, currentPage]);

  // 翻页
  const goToPreviousPage = useCallback(() => {
    setCurrentPage(prev => Math.max(1, prev - 1));
  }, []);

  const goToNextPage = useCallback(() => {
    setCurrentPage(prev => Math.min(numPages, prev + 1));
  }, [numPages]);

  // 缩放
  const zoomIn = useCallback(() => {
    setScale(prev => Math.min(2.0, prev + 0.1));
  }, []);

  const zoomOut = useCallback(() => {
    setScale(prev => Math.max(0.5, prev - 0.1));
  }, []);

  const resetZoom = useCallback(() => {
    setScale(1.0);
  }, []);

  // 下载PDF
  const downloadPDF = useCallback(() => {
    const link = document.createElement('a');
    link.href = fileUrl;
    link.download = 'document.pdf';
    link.click();
  }, [fileUrl]);

  return (
    <Card className={cn("flex flex-col h-full bg-gray-900 border-gray-700", className)}>
      {/* 工具栏 */}
      <div className="flex items-center justify-between p-4 border-b border-gray-700 bg-gray-800">
        <div className="flex items-center space-x-2">
          <Button
            variant="outline"
            size="icon"
            onClick={goToPreviousPage}
            disabled={currentPage <= 1 || loading}
            className="bg-gray-700 hover:bg-gray-600 border-gray-600"
          >
            <ChevronLeft className="h-4 w-4 text-gray-200" />
          </Button>
          <span className="text-sm text-gray-300 min-w-[100px] text-center">
            {loading ? '加载中...' : `${currentPage} / ${numPages}`}
          </span>
          <Button
            variant="outline"
            size="icon"
            onClick={goToNextPage}
            disabled={currentPage >= numPages || loading}
            className="bg-gray-700 hover:bg-gray-600 border-gray-600"
          >
            <ChevronRight className="h-4 w-4 text-gray-200" />
          </Button>
        </div>

        <div className="flex items-center space-x-2">
          <Button
            variant="outline"
            size="icon"
            onClick={zoomOut}
            disabled={loading}
            className="bg-gray-700 hover:bg-gray-600 border-gray-600"
          >
            <ZoomOut className="h-4 w-4 text-gray-200" />
          </Button>
          <span className="text-sm text-gray-300 min-w-[60px] text-center">
            {Math.round(scale * 100)}%
          </span>
          <Button
            variant="outline"
            size="icon"
            onClick={zoomIn}
            disabled={loading}
            className="bg-gray-700 hover:bg-gray-600 border-gray-600"
          >
            <ZoomIn className="h-4 w-4 text-gray-200" />
          </Button>
          <Button
            variant="outline"
            size="icon"
            onClick={resetZoom}
            disabled={loading}
            className="bg-gray-700 hover:bg-gray-600 border-gray-600"
          >
            <Maximize2 className="h-4 w-4 text-gray-200" />
          </Button>
          <Button
            variant="outline"
            size="icon"
            onClick={downloadPDF}
            disabled={loading}
            className="bg-gray-700 hover:bg-gray-600 border-gray-600"
          >
            <Download className="h-4 w-4 text-gray-200" />
          </Button>
        </div>
      </div>

      {/* PDF内容区域 */}
      <div className="flex-1 overflow-auto bg-gray-800 p-4">
        {error ? (
          <div className="flex items-center justify-center h-full">
            <div className="text-center">
              <p className="text-red-400 mb-2">❌ {error}</p>
              <Button onClick={() => window.location.reload()} className="bg-blue-600 hover:bg-blue-700">
                重新加载
              </Button>
            </div>
          </div>
        ) : (
          <div className="flex justify-center">
            <div className="relative inline-block">
              <Document
                file={fileUrl}
                onLoadSuccess={onDocumentLoadSuccess}
                onLoadError={onDocumentLoadError}
                loading={
                  <div className="flex items-center justify-center h-[600px]">
                    <Loader2 className="h-8 w-8 animate-spin text-blue-500" />
                    <span className="ml-2 text-gray-400">加载PDF中...</span>
                  </div>
                }
              >
                <Page
                  pageNumber={currentPage}
                  scale={scale}
                  renderTextLayer={true}
                  renderAnnotationLayer={true}
                  className="shadow-lg"
                />
              </Document>

              {/* 风险高亮层 */}
              {currentPageRisks.length > 0 && (
                <div className="absolute inset-0 pointer-events-none">
                  {currentPageRisks.map((risk) => (
                    <RiskHighlightOverlay
                      key={risk.id}
                      risk={risk}
                      onClick={() => onRiskClick?.(risk)}
                    />
                  ))}
                </div>
              )}
            </div>
          </div>
        )}
      </div>

      {/* 底部信息栏 */}
      {currentPageRisks.length > 0 && (
        <div className="p-3 border-t border-gray-700 bg-gray-800">
          <div className="flex items-center justify-between">
            <span className="text-sm text-gray-400">
              当前页发现 <span className="font-semibold text-gray-200">{currentPageRisks.length}</span> 个风险
            </span>
            <div className="flex items-center space-x-2">
              {[RiskLevel.HIGH, RiskLevel.MEDIUM, RiskLevel.LOW].map(level => {
                const count = currentPageRisks.filter(r => r.risk_level === level).length;
                if (count === 0) return null;
                const colors = RISK_LEVEL_COLORS[level];
                return (
                  <div key={level} className="flex items-center space-x-1">
                    <div
                      className="w-3 h-3 rounded-full"
                      style={{ backgroundColor: colors.border }}
                    />
                    <span className="text-xs text-gray-400">{count}</span>
                  </div>
                );
              })}
            </div>
          </div>
        </div>
      )}
    </Card>
  );
}

// 风险高亮覆盖层组件
interface RiskHighlightOverlayProps {
  risk: Risk;
  onClick: () => void;
}

function RiskHighlightOverlay({ risk, onClick }: RiskHighlightOverlayProps) {
  const colors = RISK_LEVEL_COLORS[risk.risk_level];

  // 由于我们没有精确的位置信息，这里使用简化的高亮显示
  // 在实际应用中，需要通过PDF解析获取精确的文本位置
  return (
    <div
      className="absolute top-4 right-4 pointer-events-auto cursor-pointer"
      onClick={onClick}
      style={{
        backgroundColor: colors.bg,
        border: `2px solid ${colors.border}`,
        borderRadius: '4px',
        padding: '8px 12px',
        maxWidth: '200px',
      }}
    >
      <div className="text-xs font-semibold" style={{ color: colors.border }}>
        {risk.risk_level.toUpperCase()}
      </div>
      <div className="text-xs text-gray-700 mt-1 truncate">
        {risk.title}
      </div>
    </div>
  );
}

