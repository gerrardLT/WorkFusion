# backend/services/pdf_generator.py
"""
PDF生成服务
使用ReportLab将评估报告转换为PDF
"""
import os
import logging
from pathlib import Path
from typing import Optional, Dict, Any
from datetime import datetime
from io import BytesIO

from reportlab.lib import colors
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import cm
from reportlab.platypus import (
    SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle,
    PageBreak, KeepTogether
)
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.lib.enums import TA_CENTER, TA_LEFT, TA_RIGHT

from backend.models import EvaluationReport, RecommendationLevel

logger = logging.getLogger(__name__)


class PDFGenerator:
    """PDF生成器类"""

    def __init__(self):
        """初始化PDF生成器"""
        self._register_chinese_fonts()
        self.styles = getSampleStyleSheet()
        self._setup_custom_styles()
        logger.info("PDF生成器初始化完成")

    def _register_chinese_fonts(self):
        """注册中文字体"""
        try:
            # 尝试注册系统中文字体
            # Windows系统通常有宋体（SimSun）
            font_paths = [
                "C:/Windows/Fonts/simsun.ttc",  # 宋体
                "C:/Windows/Fonts/msyh.ttc",    # 微软雅黑
                "C:/Windows/Fonts/simhei.ttf",  # 黑体
            ]

            for font_path in font_paths:
                if os.path.exists(font_path):
                    try:
                        if font_path.endswith('.ttc'):
                            # TTC字体需要指定子字体索引
                            pdfmetrics.registerFont(TTFont('Chinese', font_path, subfontIndex=0))
                        else:
                            pdfmetrics.registerFont(TTFont('Chinese', font_path))
                        logger.info(f"✅ 成功注册中文字体: {font_path}")
                        return
                    except Exception as e:
                        logger.warning(f"注册字体 {font_path} 失败: {str(e)}")
                        continue

            logger.warning("⚠️ 未找到系统中文字体，将使用默认字体")

        except Exception as e:
            logger.error(f"注册中文字体时出错: {str(e)}")

    def _setup_custom_styles(self):
        """设置自定义样式"""
        # 标题样式
        self.styles.add(ParagraphStyle(
            name='CustomTitle',
            parent=self.styles['Heading1'],
            fontName='Chinese',
            fontSize=24,
            textColor=colors.HexColor('#2c3e50'),
            spaceAfter=20,
            alignment=TA_CENTER
        ))

        # 副标题样式
        self.styles.add(ParagraphStyle(
            name='CustomSubtitle',
            parent=self.styles['Normal'],
            fontName='Chinese',
            fontSize=12,
            textColor=colors.HexColor('#7f8c8d'),
            spaceAfter=30,
            alignment=TA_CENTER
        ))

        # 章节标题样式
        self.styles.add(ParagraphStyle(
            name='SectionTitle',
            parent=self.styles['Heading2'],
            fontName='Chinese',
            fontSize=14,
            textColor=colors.HexColor('#2c3e50'),
            spaceAfter=10,
            spaceBefore=15,
            borderWidth=0,
            borderColor=colors.HexColor('#3498db'),
            borderPadding=5
        ))

        # 正文样式
        self.styles.add(ParagraphStyle(
            name='CustomBody',
            parent=self.styles['Normal'],
            fontName='Chinese',
            fontSize=10,
            textColor=colors.HexColor('#333333'),
            spaceAfter=8,
            leading=14
        ))

        # 强调文本样式
        self.styles.add(ParagraphStyle(
            name='Emphasis',
            parent=self.styles['CustomBody'],
            textColor=colors.HexColor('#e74c3c'),
            fontSize=11,
            fontName='Chinese'
        ))

    def generate_from_report(
        self,
        report: EvaluationReport,
        template_name: str = "default",
        watermark: Optional[str] = None,
        output_path: Optional[str] = None
    ) -> bytes:
        """
        从评估报告生成PDF

        Args:
            report: 评估报告对象
            template_name: 模板名称（暂未使用）
            watermark: 水印文字（暂未实现）
            output_path: 输出路径，如果指定则同时保存到文件

        Returns:
            PDF文件的字节数据
        """
        try:
            # 创建PDF文档
            buffer = BytesIO()
            doc = SimpleDocTemplate(
                buffer,
                pagesize=A4,
                rightMargin=2*cm,
                leftMargin=2*cm,
                topMargin=2*cm,
                bottomMargin=2*cm
            )

            # 构建文档内容
            story = []
            story.extend(self._build_header(report))
            story.extend(self._build_meta_info(report))
            story.extend(self._build_score_section(report))
            story.extend(self._build_project_summary(report))
            story.extend(self._build_qualification_analysis(report))
            story.extend(self._build_timeline_analysis(report))
            story.extend(self._build_historical_analysis(report))
            story.extend(self._build_risk_summary(report))
            story.extend(self._build_recommendations(report))
            story.extend(self._build_footer(report))

            # 生成PDF
            doc.build(story)

            # 获取字节数据
            pdf_bytes = buffer.getvalue()
            buffer.close()

            # 如果指定了输出路径，保存到文件
            if output_path:
                with open(output_path, 'wb') as f:
                    f.write(pdf_bytes)
                logger.info(f"PDF已保存到: {output_path}")

            logger.info(f"✅ PDF生成成功，大小: {len(pdf_bytes)} 字节")
            return pdf_bytes

        except Exception as e:
            logger.error(f"生成PDF失败: {str(e)}", exc_info=True)
            raise

    def _build_header(self, report: EvaluationReport) -> list:
        """构建报告头部"""
        elements = []

        # 标题
        title = Paragraph(report.title or "项目评估报告", self.styles['CustomTitle'])
        elements.append(title)

        # 副标题
        subtitle = Paragraph("基于AI的智能分析与决策支持", self.styles['CustomSubtitle'])
        elements.append(subtitle)

        return elements

    def _build_meta_info(self, report: EvaluationReport) -> list:
        """构建元信息表格"""
        elements = []

        project_summary = report.project_summary or {}
        created_at = report.created_at.strftime("%Y年%m月%d日 %H:%M") if report.created_at else "未知"

        data = [
            ['报告编号', report.id[:8], '生成时间', created_at],
            ['项目名称', project_summary.get('name', '未知项目'), '企业名称', '评估企业']
        ]

        table = Table(data, colWidths=[3*cm, 6*cm, 3*cm, 6*cm])
        table.setStyle(TableStyle([
            ('FONT', (0, 0), (-1, -1), 'Chinese'),
            ('FONTSIZE', (0, 0), (-1, -1), 9),
            ('BACKGROUND', (0, 0), (0, -1), colors.HexColor('#f8f9fa')),
            ('BACKGROUND', (2, 0), (2, -1), colors.HexColor('#f8f9fa')),
            ('TEXTCOLOR', (0, 0), (0, -1), colors.HexColor('#555555')),
            ('TEXTCOLOR', (2, 0), (2, -1), colors.HexColor('#555555')),
            ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
            ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
            ('GRID', (0, 0), (-1, -1), 0.5, colors.HexColor('#dddddd')),
            ('LEFTPADDING', (0, 0), (-1, -1), 8),
            ('RIGHTPADDING', (0, 0), (-1, -1), 8),
            ('TOPPADDING', (0, 0), (-1, -1), 6),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 6),
        ]))

        elements.append(table)
        elements.append(Spacer(1, 0.5*cm))

        return elements

    def _build_score_section(self, report: EvaluationReport) -> list:
        """构建评分部分"""
        elements = []

        score = f"{report.overall_score:.1f}" if report.overall_score else "N/A"
        recommendation_text = self._get_recommendation_text(report.recommendation_level)
        conclusion = report.conclusion or "暂无结论"

        # 评分框
        score_text = f'''
        <para alignment="center"><font name="Chinese" size="14" color="#ffffff">
        综合评分<br/><br/>
        <font size="36"><b>{score}</b></font><br/><br/>
        {recommendation_text}
        </font></para>
        '''

        score_para = Paragraph(score_text, self.styles['CustomBody'])
        score_table = Table([[score_para]], colWidths=[16*cm])
        score_table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, -1), colors.HexColor('#667eea')),
            ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
            ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
            ('TOPPADDING', (0, 0), (-1, -1), 15),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 15),
        ]))

        elements.append(score_table)
        elements.append(Spacer(1, 0.3*cm))

        # 结论
        conclusion_para = Paragraph(f"<b>综合结论：</b>{conclusion}", self.styles['CustomBody'])
        conclusion_table = Table([[conclusion_para]], colWidths=[16*cm])
        conclusion_table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, -1), colors.HexColor('#d1ecf1')),
            ('LEFTPADDING', (0, 0), (-1, -1), 10),
            ('RIGHTPADDING', (0, 0), (-1, -1), 10),
            ('TOPPADDING', (0, 0), (-1, -1), 10),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 10),
        ]))

        elements.append(conclusion_table)
        elements.append(Spacer(1, 0.5*cm))

        return elements

    def _build_project_summary(self, report: EvaluationReport) -> list:
        """构建项目概况"""
        elements = []

        elements.append(Paragraph("1. 项目概况", self.styles['SectionTitle']))

        project_summary = report.project_summary or {}
        timeline = report.timeline_analysis or {}

        data = [
            ['项目预算', f"{project_summary.get('budget', 'N/A')} 万元"],
            ['所在地区', project_summary.get('area', 'N/A')],
            ['投标截止', project_summary.get('deadline', 'N/A')],
            ['剩余天数', f"{timeline.get('days_remaining', 'N/A')} 天"]
        ]

        table = Table(data, colWidths=[4*cm, 12*cm])
        table.setStyle(TableStyle([
            ('FONT', (0, 0), (-1, -1), 'Chinese'),
            ('FONTSIZE', (0, 0), (-1, -1), 9),
            ('BACKGROUND', (0, 0), (0, -1), colors.HexColor('#f8f9fa')),
            ('GRID', (0, 0), (-1, -1), 0.5, colors.HexColor('#dddddd')),
            ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
            ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
            ('LEFTPADDING', (0, 0), (-1, -1), 8),
            ('TOPPADDING', (0, 0), (-1, -1), 6),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 6),
        ]))

        elements.append(table)
        elements.append(Spacer(1, 0.5*cm))

        return elements

    def _build_qualification_analysis(self, report: EvaluationReport) -> list:
        """构建资质匹配分析"""
        elements = []

        elements.append(Paragraph("2. 资质匹配分析", self.styles['SectionTitle']))

        qual_analysis = report.qualification_analysis or {}
        match_rate = qual_analysis.get('match_rate', 0) * 100

        summary = f"匹配率：{match_rate:.0f}% ({qual_analysis.get('total_matched', 0)}/{qual_analysis.get('total_required', 0)})"
        elements.append(Paragraph(summary, self.styles['CustomBody']))
        elements.append(Spacer(1, 0.2*cm))

        # 资质列表
        qualifications = qual_analysis.get('required', [])
        if qualifications:
            qual_data = [['状态', '资质名称', '等级']]
            for qual in qualifications[:10]:  # 最多显示10个
                status = '✓' if qual.get('matched') else '✗'
                name = qual.get('name', '未知')
                level = qual.get('level', '')
                qual_data.append([status, name, level])

            qual_table = Table(qual_data, colWidths=[2*cm, 10*cm, 4*cm])
            qual_table.setStyle(TableStyle([
                ('FONT', (0, 0), (-1, -1), 'Chinese'),
                ('FONTSIZE', (0, 0), (-1, -1), 9),
                ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#3498db')),
                ('TEXTCOLOR', (0, 0), (-1, 0), colors.white),
                ('GRID', (0, 0), (-1, -1), 0.5, colors.grey),
                ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
                ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
                ('LEFTPADDING', (0, 0), (-1, -1), 8),
                ('TOPPADDING', (0, 0), (-1, -1), 6),
                ('BOTTOMPADDING', (0, 0), (-1, -1), 6),
            ]))

            elements.append(qual_table)

        elements.append(Spacer(1, 0.5*cm))

        return elements

    def _build_timeline_analysis(self, report: EvaluationReport) -> list:
        """构建时间节点分析"""
        elements = []

        elements.append(Paragraph("3. 时间节点分析", self.styles['SectionTitle']))

        timeline = report.timeline_analysis or {}
        urgency = timeline.get('urgency_level', 'unknown')
        urgency_text = {'critical': '极高', 'high': '高', 'medium': '中', 'low': '低'}.get(urgency, '未知')

        text = f"<b>紧急程度：</b>{urgency_text}"
        elements.append(Paragraph(text, self.styles['CustomBody']))
        elements.append(Spacer(1, 0.5*cm))

        return elements

    def _build_historical_analysis(self, report: EvaluationReport) -> list:
        """构建历史业绩分析"""
        elements = []

        elements.append(Paragraph("4. 历史业绩分析", self.styles['SectionTitle']))

        historical = report.historical_analysis or {}

        data = [
            ['类似项目数', str(historical.get('similar_projects_count', 0))],
            ['历史中标率', f"{historical.get('success_rate', 0)*100:.0f}%"],
            ['平均中标金额', f"{historical.get('average_bid_amount', 0)} 万元"],
            ['累计中标额', f"{historical.get('total_amount', 0)} 万元"]
        ]

        table = Table(data, colWidths=[4*cm, 12*cm])
        table.setStyle(TableStyle([
            ('FONT', (0, 0), (-1, -1), 'Chinese'),
            ('FONTSIZE', (0, 0), (-1, -1), 9),
            ('BACKGROUND', (0, 0), (0, -1), colors.HexColor('#f8f9fa')),
            ('GRID', (0, 0), (-1, -1), 0.5, colors.HexColor('#dddddd')),
            ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
            ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
            ('LEFTPADDING', (0, 0), (-1, -1), 8),
            ('TOPPADDING', (0, 0), (-1, -1), 6),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 6),
        ]))

        elements.append(table)
        elements.append(Spacer(1, 0.5*cm))

        return elements

    def _build_risk_summary(self, report: EvaluationReport) -> list:
        """构建风险摘要"""
        elements = []

        risk_summary = report.risk_summary or {}
        risks = risk_summary.get('key_risks', [])

        if risks:
            elements.append(Paragraph("5. 风险提示", self.styles['SectionTitle']))

            overall_level = risk_summary.get('overall_risk_level', 'low')
            level_text = {'high': '高', 'medium': '中', 'low': '低'}.get(overall_level, '未知')

            text = f"<b>风险等级：</b>{level_text}"
            elements.append(Paragraph(text, self.styles['CustomBody']))
            elements.append(Spacer(1, 0.2*cm))

            for risk in risks[:5]:  # 最多显示5个风险
                risk_text = f"• {risk.get('title', '未知风险')}: {risk.get('description', '')}"
                elements.append(Paragraph(risk_text, self.styles['CustomBody']))

            elements.append(Spacer(1, 0.5*cm))

        return elements

    def _build_recommendations(self, report: EvaluationReport) -> list:
        """构建行动建议"""
        elements = []

        recommendations = report.recommendations or []

        if recommendations:
            elements.append(Paragraph("6. 行动建议", self.styles['SectionTitle']))

            for rec in recommendations[:10]:  # 最多显示10条建议
                priority = rec.get('priority', 'medium').upper()
                action = rec.get('action', '')
                rec_text = f"[{priority}] {action}"
                elements.append(Paragraph(rec_text, self.styles['CustomBody']))

            elements.append(Spacer(1, 0.5*cm))

        return elements

    def _build_footer(self, report: EvaluationReport) -> list:
        """构建页脚"""
        elements = []

        created_at = report.created_at.strftime("%Y年%m月%d日 %H:%M") if report.created_at else "未知"

        footer_text = f'''
        <para alignment="center"><font name="Chinese" size="8" color="#999999">
        本报告由招投标AI系统自动生成 | 报告ID：{report.id[:8]}<br/>
        生成时间：{created_at} | 系统版本：v2.8.0
        </font></para>
        '''

        elements.append(Spacer(1, 1*cm))
        elements.append(Paragraph(footer_text, self.styles['CustomBody']))

        return elements

    def _get_recommendation_text(self, level: Optional[str]) -> str:
        """获取推荐等级的文本"""
        level_texts = {
            RecommendationLevel.HIGHLY_RECOMMENDED.value: "强烈推荐参与投标",
            RecommendationLevel.RECOMMENDED.value: "推荐参与投标",
            RecommendationLevel.NEUTRAL.value: "可以考虑参与",
            RecommendationLevel.NOT_RECOMMENDED.value: "不建议参与",
            RecommendationLevel.STRONGLY_NOT_RECOMMENDED.value: "强烈不建议参与"
        }
        return level_texts.get(level, "未评级")


_pdf_generator_instance: Optional[PDFGenerator] = None


def get_pdf_generator() -> PDFGenerator:
    """获取PDFGenerator单例"""
    global _pdf_generator_instance
    if _pdf_generator_instance is None:
        _pdf_generator_instance = PDFGenerator()
    return _pdf_generator_instance
