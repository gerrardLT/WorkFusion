"""
爬虫监控系统
实时监控爬虫运行状态和性能指标
"""

import logging
import json
from datetime import datetime, timedelta
from pathlib import Path
from typing import Dict, Any, List, Optional
from collections import defaultdict

logger = logging.getLogger(__name__)


class CrawlerMonitor:
    """
    爬虫监控系统

    功能：
    - 记录爬取会话
    - 统计性能指标
    - 生成监控报告
    - 告警管理
    """

    def __init__(self, log_dir: str = 'data/crawler_logs'):
        self.log_dir = Path(log_dir)
        self.log_dir.mkdir(parents=True, exist_ok=True)

        # 内存中的数据（最近24小时）
        self.sessions: List[Dict[str, Any]] = []
        self.errors: List[Dict[str, Any]] = []
        self.alerts: List[Dict[str, Any]] = []

        # 统计指标
        self.metrics = {
            'total_crawls': 0,
            'successful_crawls': 0,
            'failed_crawls': 0,
            'total_items': 0,
            'total_duration': 0.0,
            'avg_response_time': 0.0,
        }

        # 按爬虫分类的统计
        self.spider_stats = defaultdict(lambda: {
            'total_runs': 0,
            'successful_runs': 0,
            'failed_runs': 0,
            'total_items': 0,
            'total_duration': 0.0,
        })

        # 加载历史数据
        self._load_recent_data()

    def record_crawl_session(self, session_data: Dict[str, Any]):
        """
        记录爬取会话

        Args:
            session_data: 会话数据
        """
        session_data['recorded_at'] = datetime.now().isoformat()
        self.sessions.append(session_data)

        # 更新统计指标
        self.metrics['total_crawls'] += 1
        if session_data.get('success_count', 0) > 0:
            self.metrics['successful_crawls'] += 1
        if session_data.get('failed_count', 0) > 0:
            self.metrics['failed_crawls'] += 1

        # 更新总项目数
        for result in session_data.get('results', []):
            stats = result.get('stats', {})
            total_items = stats.get('total_items', 0)
            self.metrics['total_items'] += total_items

            # 更新爬虫统计
            spider_name = result.get('spider_name', 'unknown')
            self.spider_stats[spider_name]['total_runs'] += 1
            self.spider_stats[spider_name]['total_items'] += total_items

            if result.get('success'):
                self.spider_stats[spider_name]['successful_runs'] += 1
            else:
                self.spider_stats[spider_name]['failed_runs'] += 1

        # 更新持续时间
        duration = session_data.get('duration', 0)
        self.metrics['total_duration'] += duration

        # 保存到文件
        self._save_session_log(session_data)

        # 清理过期数据（保留最近24小时）
        self._cleanup_old_data()

        logger.info(f'已记录爬取会话: {session_data.get("type", "unknown")}')

    def record_error(self, error_type: str, error_message: str, **kwargs):
        """
        记录错误

        Args:
            error_type: 错误类型
            error_message: 错误消息
            **kwargs: 其他信息
        """
        error_data = {
            'type': error_type,
            'message': error_message,
            'timestamp': datetime.now().isoformat(),
            **kwargs
        }

        self.errors.append(error_data)
        self._save_error_log(error_data)

        logger.error(f'记录错误: {error_type} - {error_message}')

    def record_alert(self, alert_data: Dict[str, Any]):
        """
        记录告警

        Args:
            alert_data: 告警数据
        """
        self.alerts.append(alert_data)
        self._save_alert_log(alert_data)

        logger.warning(f'记录告警: {alert_data.get("message", "Unknown")}')

    def generate_report(self, hours: int = 24) -> Dict[str, Any]:
        """
        生成监控报告

        Args:
            hours: 时间范围（小时）

        Returns:
            监控报告
        """
        cutoff_time = datetime.now() - timedelta(hours=hours)

        # 筛选时间范围内的数据
        recent_sessions = [
            s for s in self.sessions
            if datetime.fromisoformat(s['recorded_at']) > cutoff_time
        ]

        recent_errors = [
            e for e in self.errors
            if datetime.fromisoformat(e['timestamp']) > cutoff_time
        ]

        recent_alerts = [
            a for a in self.alerts
            if datetime.fromisoformat(a['timestamp']) > cutoff_time
        ]

        # 计算统计信息
        total_sessions = len(recent_sessions)
        successful_sessions = sum(1 for s in recent_sessions if s.get('success_count', 0) > 0)
        failed_sessions = sum(1 for s in recent_sessions if s.get('failed_count', 0) > 0)

        total_items = sum(
            sum(r.get('stats', {}).get('total_items', 0) for r in s.get('results', []))
            for s in recent_sessions
        )

        avg_duration = (
            sum(s.get('duration', 0) for s in recent_sessions) / total_sessions
            if total_sessions > 0 else 0
        )

        success_rate = (
            successful_sessions / total_sessions * 100
            if total_sessions > 0 else 0
        )

        # 爬虫统计
        spider_reports = []
        for spider_name, stats in self.spider_stats.items():
            total_runs = stats['total_runs']
            if total_runs > 0:
                spider_reports.append({
                    'spider_name': spider_name,
                    'total_runs': total_runs,
                    'successful_runs': stats['successful_runs'],
                    'failed_runs': stats['failed_runs'],
                    'success_rate': stats['successful_runs'] / total_runs * 100,
                    'total_items': stats['total_items'],
                    'avg_items_per_run': stats['total_items'] / total_runs,
                })

        report = {
            'generated_at': datetime.now().isoformat(),
            'time_range_hours': hours,
            'summary': {
                'total_sessions': total_sessions,
                'successful_sessions': successful_sessions,
                'failed_sessions': failed_sessions,
                'success_rate': round(success_rate, 2),
                'total_items_crawled': total_items,
                'avg_duration_seconds': round(avg_duration, 2),
                'total_errors': len(recent_errors),
                'total_alerts': len(recent_alerts),
            },
            'spider_statistics': spider_reports,
            'recent_errors': recent_errors[-10:],  # 最近10个错误
            'recent_alerts': recent_alerts[-10:],  # 最近10个告警
        }

        # 保存报告
        self._save_report(report)

        return report

    def get_metrics(self) -> Dict[str, Any]:
        """获取实时指标"""
        return {
            'metrics': self.metrics,
            'spider_stats': dict(self.spider_stats),
            'recent_sessions_count': len(self.sessions),
            'recent_errors_count': len(self.errors),
            'recent_alerts_count': len(self.alerts),
        }

    def get_health_status(self) -> Dict[str, Any]:
        """
        获取健康状态

        Returns:
            健康状态信息
        """
        # 检查最近1小时的爬取情况
        one_hour_ago = datetime.now() - timedelta(hours=1)
        recent_sessions = [
            s for s in self.sessions
            if datetime.fromisoformat(s['recorded_at']) > one_hour_ago
        ]

        # 判断健康状态
        if not recent_sessions:
            status = 'warning'
            message = '最近1小时无爬取记录'
        else:
            success_count = sum(s.get('success_count', 0) for s in recent_sessions)
            failed_count = sum(s.get('failed_count', 0) for s in recent_sessions)
            total = success_count + failed_count

            if total == 0:
                status = 'warning'
                message = '无有效爬取数据'
            elif failed_count / total > 0.5:
                status = 'error'
                message = f'失败率过高: {failed_count/total*100:.1f}%'
            else:
                status = 'healthy'
                message = f'运行正常，成功率: {success_count/total*100:.1f}%'

        return {
            'status': status,
            'message': message,
            'timestamp': datetime.now().isoformat(),
        }

    # ==================== 私有方法 ====================

    def _save_session_log(self, session_data: Dict[str, Any]):
        """保存会话日志"""
        date_str = datetime.now().strftime('%Y%m%d')
        log_file = self.log_dir / f'sessions_{date_str}.jsonl'

        try:
            with open(log_file, 'a', encoding='utf-8') as f:
                f.write(json.dumps(session_data, ensure_ascii=False) + '\n')
        except Exception as e:
            logger.error(f'保存会话日志失败: {e}')

    def _save_error_log(self, error_data: Dict[str, Any]):
        """保存错误日志"""
        date_str = datetime.now().strftime('%Y%m%d')
        log_file = self.log_dir / f'errors_{date_str}.jsonl'

        try:
            with open(log_file, 'a', encoding='utf-8') as f:
                f.write(json.dumps(error_data, ensure_ascii=False) + '\n')
        except Exception as e:
            logger.error(f'保存错误日志失败: {e}')

    def _save_alert_log(self, alert_data: Dict[str, Any]):
        """保存告警日志"""
        date_str = datetime.now().strftime('%Y%m%d')
        log_file = self.log_dir / f'alerts_{date_str}.jsonl'

        try:
            with open(log_file, 'a', encoding='utf-8') as f:
                f.write(json.dumps(alert_data, ensure_ascii=False) + '\n')
        except Exception as e:
            logger.error(f'保存告警日志失败: {e}')

    def _save_report(self, report: Dict[str, Any]):
        """保存监控报告"""
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        report_file = self.log_dir / f'report_{timestamp}.json'

        try:
            with open(report_file, 'w', encoding='utf-8') as f:
                json.dump(report, f, ensure_ascii=False, indent=2)
            logger.info(f'监控报告已保存: {report_file}')
        except Exception as e:
            logger.error(f'保存监控报告失败: {e}')

    def _load_recent_data(self):
        """加载最近的数据"""
        # 加载最近3天的日志文件
        for i in range(3):
            date = datetime.now() - timedelta(days=i)
            date_str = date.strftime('%Y%m%d')

            # 加载会话
            self._load_jsonl_file(
                self.log_dir / f'sessions_{date_str}.jsonl',
                self.sessions
            )

            # 加载错误
            self._load_jsonl_file(
                self.log_dir / f'errors_{date_str}.jsonl',
                self.errors
            )

            # 加载告警
            self._load_jsonl_file(
                self.log_dir / f'alerts_{date_str}.jsonl',
                self.alerts
            )

    def _load_jsonl_file(self, file_path: Path, target_list: List):
        """加载JSONL文件"""
        if not file_path.exists():
            return

        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                for line in f:
                    if line.strip():
                        target_list.append(json.loads(line))
        except Exception as e:
            logger.error(f'加载日志文件失败: {file_path}, 错误: {e}')

    def _cleanup_old_data(self):
        """清理过期数据（保留最近24小时）"""
        cutoff_time = datetime.now() - timedelta(hours=24)

        # 清理会话
        self.sessions = [
            s for s in self.sessions
            if datetime.fromisoformat(s['recorded_at']) > cutoff_time
        ]

        # 清理错误
        self.errors = [
            e for e in self.errors
            if datetime.fromisoformat(e['timestamp']) > cutoff_time
        ]

        # 清理告警
        self.alerts = [
            a for a in self.alerts
            if datetime.fromisoformat(a['timestamp']) > cutoff_time
        ]


# 全局单例
_monitor: Optional[CrawlerMonitor] = None


def get_monitor() -> CrawlerMonitor:
    """获取监控器单例"""
    global _monitor
    if _monitor is None:
        _monitor = CrawlerMonitor()
    return _monitor

