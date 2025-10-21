"""
风险识别准确率验证服务
用于评估风险识别的准确率、召回率和F1分数
"""

import logging
from typing import List, Dict, Any, Optional, Tuple
from dataclasses import dataclass
from enum import Enum

logger = logging.getLogger(__name__)


class RiskMatchType(str, Enum):
    """风险匹配类型"""
    TRUE_POSITIVE = "true_positive"   # 正确识别（预测为风险，实际为风险）
    FALSE_POSITIVE = "false_positive"  # 误识别（预测为风险，实际不是）
    TRUE_NEGATIVE = "true_negative"    # 正确排除（预测不是风险，实际不是）
    FALSE_NEGATIVE = "false_negative"  # 漏识别（预测不是风险，实际为风险）


@dataclass
class GroundTruthRisk:
    """人工标注的真实风险"""
    risk_id: str
    title: str
    risk_type: str
    risk_level: str
    page_number: int
    original_text: str
    section: Optional[str] = None


@dataclass
class PredictedRisk:
    """系统预测的风险"""
    risk_id: str
    title: str
    risk_type: str
    risk_level: str
    page_number: int
    original_text: str
    confidence_score: int


@dataclass
class EvaluationMetrics:
    """评估指标"""
    precision: float      # 准确率 = TP / (TP + FP)
    recall: float         # 召回率 = TP / (TP + FN)
    f1_score: float       # F1分数 = 2 * (precision * recall) / (precision + recall)
    accuracy: float       # 整体准确率 = (TP + TN) / (TP + TN + FP + FN)

    true_positives: int   # 正确识别数量
    false_positives: int  # 误识别数量
    false_negatives: int  # 漏识别数量
    true_negatives: int   # 正确排除数量

    total_ground_truth: int   # 真实风险总数
    total_predicted: int      # 预测风险总数


class RiskEvaluationService:
    """风险识别评估服务"""

    def __init__(self, similarity_threshold: float = 0.7):
        """
        初始化评估服务

        Args:
            similarity_threshold: 文本相似度阈值，用于判断两个风险是否匹配
        """
        self.similarity_threshold = similarity_threshold

    def evaluate(
        self,
        ground_truth_risks: List[GroundTruthRisk],
        predicted_risks: List[PredictedRisk]
    ) -> EvaluationMetrics:
        """
        评估风险识别结果

        Args:
            ground_truth_risks: 人工标注的真实风险列表
            predicted_risks: 系统预测的风险列表

        Returns:
            评估指标
        """
        logger.info(f"📊 开始评估风险识别准确率...")
        logger.info(f"真实风险数量: {len(ground_truth_risks)}, 预测风险数量: {len(predicted_risks)}")

        # 匹配真实风险和预测风险
        matches = self._match_risks(ground_truth_risks, predicted_risks)

        # 计算指标
        tp = matches['true_positives']
        fp = matches['false_positives']
        fn = matches['false_negatives']
        tn = matches['true_negatives']

        # 计算准确率、召回率、F1分数
        precision = tp / (tp + fp) if (tp + fp) > 0 else 0.0
        recall = tp / (tp + fn) if (tp + fn) > 0 else 0.0
        f1_score = 2 * (precision * recall) / (precision + recall) if (precision + recall) > 0 else 0.0
        accuracy = (tp + tn) / (tp + tn + fp + fn) if (tp + tn + fp + fn) > 0 else 0.0

        metrics = EvaluationMetrics(
            precision=precision,
            recall=recall,
            f1_score=f1_score,
            accuracy=accuracy,
            true_positives=tp,
            false_positives=fp,
            false_negatives=fn,
            true_negatives=tn,
            total_ground_truth=len(ground_truth_risks),
            total_predicted=len(predicted_risks)
        )

        logger.info(f"✅ 评估完成:")
        logger.info(f"  准确率 (Precision): {precision:.2%}")
        logger.info(f"  召回率 (Recall): {recall:.2%}")
        logger.info(f"  F1分数: {f1_score:.2%}")
        logger.info(f"  整体准确率: {accuracy:.2%}")
        logger.info(f"  TP: {tp}, FP: {fp}, FN: {fn}, TN: {tn}")

        return metrics

    def _match_risks(
        self,
        ground_truth_risks: List[GroundTruthRisk],
        predicted_risks: List[PredictedRisk]
    ) -> Dict[str, int]:
        """
        匹配真实风险和预测风险

        Args:
            ground_truth_risks: 真实风险列表
            predicted_risks: 预测风险列表

        Returns:
            匹配统计字典
        """
        matched_ground_truth = set()
        matched_predicted = set()

        tp = 0  # True Positives
        fp = 0  # False Positives
        fn = 0  # False Negatives

        # 为每个预测风险寻找最佳匹配的真实风险
        for pred_risk in predicted_risks:
            best_match = None
            best_similarity = 0.0

            for gt_risk in ground_truth_risks:
                if gt_risk.risk_id in matched_ground_truth:
                    continue

                # 计算相似度（简化版：基于页码和文本相似度）
                similarity = self._calculate_similarity(gt_risk, pred_risk)

                if similarity > best_similarity and similarity >= self.similarity_threshold:
                    best_similarity = similarity
                    best_match = gt_risk

            if best_match:
                # 找到匹配，计为True Positive
                tp += 1
                matched_ground_truth.add(best_match.risk_id)
                matched_predicted.add(pred_risk.risk_id)
            else:
                # 未找到匹配，计为False Positive（误识别）
                fp += 1

        # 未被匹配的真实风险计为False Negative（漏识别）
        fn = len(ground_truth_risks) - len(matched_ground_truth)

        # True Negative较难定义，这里假设为0（因为我们只关注风险条款）
        tn = 0

        return {
            'true_positives': tp,
            'false_positives': fp,
            'false_negatives': fn,
            'true_negatives': tn
        }

    def _calculate_similarity(
        self,
        gt_risk: GroundTruthRisk,
        pred_risk: PredictedRisk
    ) -> float:
        """
        计算两个风险的相似度

        Args:
            gt_risk: 真实风险
            pred_risk: 预测风险

        Returns:
            相似度分数 (0-1)
        """
        # 1. 页码匹配（权重30%）
        page_score = 1.0 if gt_risk.page_number == pred_risk.page_number else 0.0

        # 2. 风险类型匹配（权重30%）
        type_score = 1.0 if gt_risk.risk_type == pred_risk.risk_type else 0.0

        # 3. 文本相似度（权重40%）
        text_similarity = self._text_similarity(gt_risk.original_text, pred_risk.original_text)

        # 加权平均
        similarity = 0.3 * page_score + 0.3 * type_score + 0.4 * text_similarity

        return similarity

    def _text_similarity(self, text1: str, text2: str) -> float:
        """
        计算两段文本的相似度（简化版：基于Jaccard相似度）

        Args:
            text1: 文本1
            text2: 文本2

        Returns:
            相似度分数 (0-1)
        """
        if not text1 or not text2:
            return 0.0

        # 转换为字符集合
        set1 = set(text1.replace(" ", "").replace("\n", ""))
        set2 = set(text2.replace(" ", "").replace("\n", ""))

        # 计算Jaccard相似度
        intersection = len(set1 & set2)
        union = len(set1 | set2)

        if union == 0:
            return 0.0

        return intersection / union

    def generate_report(
        self,
        metrics: EvaluationMetrics,
        misclassified_cases: Optional[List[Dict[str, Any]]] = None
    ) -> str:
        """
        生成评估报告

        Args:
            metrics: 评估指标
            misclassified_cases: 误分类案例列表

        Returns:
            评估报告（Markdown格式）
        """
        report = f"""# 风险识别准确率评估报告

## 📊 评估指标

| 指标 | 数值 | 目标 | 达标 |
|------|------|------|------|
| **准确率 (Precision)** | {metrics.precision:.2%} | >85% | {'✅' if metrics.precision > 0.85 else '❌'} |
| **召回率 (Recall)** | {metrics.recall:.2%} | >80% | {'✅' if metrics.recall > 0.80 else '❌'} |
| **F1分数** | {metrics.f1_score:.2%} | >82% | {'✅' if metrics.f1_score > 0.82 else '❌'} |
| **整体准确率** | {metrics.accuracy:.2%} | - | - |

## 📈 详细统计

- **真实风险总数：** {metrics.total_ground_truth}
- **预测风险总数：** {metrics.total_predicted}
- **正确识别 (TP)：** {metrics.true_positives}
- **误识别 (FP)：** {metrics.false_positives}
- **漏识别 (FN)：** {metrics.false_negatives}

## 🎯 误识别率

- **误识别率：** {(metrics.false_positives / metrics.total_predicted * 100) if metrics.total_predicted > 0 else 0:.2f}%
- **漏识别率：** {(metrics.false_negatives / metrics.total_ground_truth * 100) if metrics.total_ground_truth > 0 else 0:.2f}%

## 📝 结论

{'✅ **验收通过** - 所有指标均达到预期目标' if metrics.precision > 0.85 and metrics.recall > 0.80 else '⚠️ **需要优化** - 部分指标未达标，建议进行模型调优'}
"""

        if misclassified_cases:
            report += f"\n\n## ⚠️ 误分类案例\n\n共 {len(misclassified_cases)} 个案例需要分析\n"

        return report


# 单例实例
_risk_evaluation_service = None


def get_risk_evaluation_service() -> RiskEvaluationService:
    """获取风险评估服务单例"""
    global _risk_evaluation_service
    if _risk_evaluation_service is None:
        _risk_evaluation_service = RiskEvaluationService()
    return _risk_evaluation_service

