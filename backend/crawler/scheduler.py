"""
爬虫定时任务调度器
使用APScheduler实现定时爬取
"""

import logging
import sys
from pathlib import Path
from datetime import datetime
from typing import Optional, Dict, Any, List

# 添加项目根目录到路径
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

from apscheduler.schedulers.background import BackgroundScheduler
from apscheduler.triggers.cron import CronTrigger
from apscheduler.triggers.interval import IntervalTrigger
from apscheduler.events import EVENT_JOB_EXECUTED, EVENT_JOB_ERROR

from backend.crawler.crawler_manager import get_crawler_manager
from backend.crawler.monitor import CrawlerMonitor, get_monitor

logger = logging.getLogger(__name__)


class CrawlerScheduler:
    """
    爬虫定时任务调度器

    功能：
    - 定时执行爬虫任务
    - 支持全量和增量爬取策略
    - 任务执行监控
    - 异常处理和重试
    """

    def __init__(self):
        self.scheduler = BackgroundScheduler(
            timezone='Asia/Shanghai',
            job_defaults={
                'coalesce': True,  # 合并错过的任务
                'max_instances': 1,  # 同一任务最多同时运行1个实例
                'misfire_grace_time': 300  # 错过5分钟内的任务仍然执行
            }
        )

        self.crawler_manager = get_crawler_manager()
        self.monitor = get_monitor()

        # 任务执行历史
        self.job_history: List[Dict[str, Any]] = []

        # 添加事件监听
        self.scheduler.add_listener(
            self._job_executed_listener,
            EVENT_JOB_EXECUTED | EVENT_JOB_ERROR
        )

    def setup_default_jobs(self):
        """设置默认的定时任务"""
        logger.info('设置默认定时任务...')

        # 1. 每日凌晨2点全量爬取
        self.add_full_crawl_job(
            hour=2,
            minute=0,
            job_id='daily_full_crawl'
        )

        # 2. 每隔2小时增量爬取
        self.add_incremental_crawl_job(
            hours=2,
            job_id='incremental_crawl_2h'
        )

        # 3. 每小时生成监控报告
        self.add_monitor_report_job(
            hours=1,
            job_id='hourly_monitor_report'
        )

        logger.info('默认定时任务已设置完成')

    def add_full_crawl_job(self, hour: int, minute: int, job_id: str = 'full_crawl'):
        """
        添加全量爬取任务

        Args:
            hour: 小时（0-23）
            minute: 分钟（0-59）
            job_id: 任务ID
        """
        trigger = CronTrigger(hour=hour, minute=minute)

        self.scheduler.add_job(
            func=self._run_full_crawl,
            trigger=trigger,
            id=job_id,
            name=f'全量爬取（每日{hour}:{minute:02d}）',
            replace_existing=True
        )

        logger.info(f'已添加全量爬取任务: {job_id}, 执行时间: 每日 {hour}:{minute:02d}')

    def add_incremental_crawl_job(self, hours: int, job_id: str = 'incremental_crawl'):
        """
        添加增量爬取任务

        Args:
            hours: 间隔小时数
            job_id: 任务ID
        """
        trigger = IntervalTrigger(hours=hours)

        self.scheduler.add_job(
            func=self._run_incremental_crawl,
            trigger=trigger,
            id=job_id,
            name=f'增量爬取（每{hours}小时）',
            replace_existing=True
        )

        logger.info(f'已添加增量爬取任务: {job_id}, 间隔: {hours}小时')

    def add_monitor_report_job(self, hours: int, job_id: str = 'monitor_report'):
        """
        添加监控报告任务

        Args:
            hours: 间隔小时数
            job_id: 任务ID
        """
        trigger = IntervalTrigger(hours=hours)

        self.scheduler.add_job(
            func=self._generate_monitor_report,
            trigger=trigger,
            id=job_id,
            name=f'监控报告（每{hours}小时）',
            replace_existing=True
        )

        logger.info(f'已添加监控报告任务: {job_id}, 间隔: {hours}小时')

    def add_custom_job(self,
                       func,
                       trigger,
                       job_id: str,
                       name: str,
                       **kwargs):
        """
        添加自定义任务

        Args:
            func: 要执行的函数
            trigger: 触发器（CronTrigger或IntervalTrigger）
            job_id: 任务ID
            name: 任务名称
            **kwargs: 其他参数
        """
        self.scheduler.add_job(
            func=func,
            trigger=trigger,
            id=job_id,
            name=name,
            replace_existing=True,
            **kwargs
        )

        logger.info(f'已添加自定义任务: {job_id} ({name})')

    def remove_job(self, job_id: str) -> bool:
        """
        移除任务

        Args:
            job_id: 任务ID

        Returns:
            是否成功移除
        """
        try:
            self.scheduler.remove_job(job_id)
            logger.info(f'已移除任务: {job_id}')
            return True
        except Exception as e:
            logger.error(f'移除任务失败: {job_id}, 错误: {e}')
            return False

    def start(self):
        """启动调度器"""
        if not self.scheduler.running:
            self.scheduler.start()
            logger.info('✅ 爬虫调度器已启动')
        else:
            logger.warning('调度器已经在运行中')

    def stop(self):
        """停止调度器"""
        if self.scheduler.running:
            self.scheduler.shutdown(wait=True)
            logger.info('爬虫调度器已停止')
        else:
            logger.warning('调度器未运行')

    def pause_job(self, job_id: str):
        """暂停任务"""
        self.scheduler.pause_job(job_id)
        logger.info(f'任务已暂停: {job_id}')

    def resume_job(self, job_id: str):
        """恢复任务"""
        self.scheduler.resume_job(job_id)
        logger.info(f'任务已恢复: {job_id}')

    def get_jobs(self) -> List[Dict[str, Any]]:
        """获取所有任务"""
        jobs = []
        for job in self.scheduler.get_jobs():
            # APScheduler 3.x版本兼容性处理
            next_run = getattr(job, 'next_run_time', None)
            jobs.append({
                'id': job.id,
                'name': job.name if hasattr(job, 'name') else job.id,
                'next_run_time': next_run.isoformat() if next_run else None,
                'trigger': str(job.trigger) if hasattr(job, 'trigger') else 'Unknown',
            })
        return jobs

    def get_job_history(self, limit: int = 50) -> List[Dict[str, Any]]:
        """获取任务执行历史"""
        return self.job_history[-limit:]

    # ==================== 任务执行方法 ====================

    def _run_full_crawl(self):
        """执行全量爬取"""
        logger.info('=' * 60)
        logger.info('开始执行全量爬取任务')
        logger.info('=' * 60)

        start_time = datetime.now()

        try:
            # 执行所有爬虫
            results = self.crawler_manager.run_all_spiders(
                crawl_type='full',
                max_pages=50  # 全量爬取更多页
            )

            end_time = datetime.now()
            duration = (end_time - start_time).total_seconds()

            # 统计结果
            total_success = sum(1 for r in results if r.get('success'))
            total_failed = len(results) - total_success

            logger.info(f'全量爬取完成 - 成功: {total_success}, 失败: {total_failed}, 耗时: {duration:.2f}秒')

            # 记录监控数据
            self.monitor.record_crawl_session({
                'type': 'full',
                'start_time': start_time.isoformat(),
                'end_time': end_time.isoformat(),
                'duration': duration,
                'success_count': total_success,
                'failed_count': total_failed,
                'results': results
            })

            # 检查告警条件
            self._check_alerts(results, 'full')

        except Exception as e:
            logger.error(f'全量爬取失败: {e}', exc_info=True)
            self.monitor.record_error('full_crawl', str(e))
            self._send_alert(f'全量爬取异常: {e}', 'error')

    def _run_incremental_crawl(self):
        """执行增量爬取"""
        logger.info('开始执行增量爬取任务')

        start_time = datetime.now()

        try:
            # 执行所有爬虫（增量模式）
            results = self.crawler_manager.run_all_spiders(
                crawl_type='incremental',
                max_pages=10  # 增量爬取较少页
            )

            end_time = datetime.now()
            duration = (end_time - start_time).total_seconds()

            # 统计结果
            total_success = sum(1 for r in results if r.get('success'))
            total_failed = len(results) - total_success

            logger.info(f'增量爬取完成 - 成功: {total_success}, 失败: {total_failed}, 耗时: {duration:.2f}秒')

            # 记录监控数据
            self.monitor.record_crawl_session({
                'type': 'incremental',
                'start_time': start_time.isoformat(),
                'end_time': end_time.isoformat(),
                'duration': duration,
                'success_count': total_success,
                'failed_count': total_failed,
                'results': results
            })

            # 检查告警条件
            self._check_alerts(results, 'incremental')

        except Exception as e:
            logger.error(f'增量爬取失败: {e}', exc_info=True)
            self.monitor.record_error('incremental_crawl', str(e))
            self._send_alert(f'增量爬取异常: {e}', 'error')

    def _generate_monitor_report(self):
        """生成监控报告"""
        logger.info('生成监控报告...')

        try:
            report = self.monitor.generate_report()
            logger.info('监控报告已生成')
            logger.info(f'报告摘要: {report.get("summary", {})}')

        except Exception as e:
            logger.error(f'生成监控报告失败: {e}')

    def _check_alerts(self, results: List[Dict[str, Any]], crawl_type: str):
        """
        检查告警条件

        Args:
            results: 爬取结果列表
            crawl_type: 爬取类型
        """
        # 检查失败率
        total = len(results)
        if total > 0:
            failed = sum(1 for r in results if not r.get('success'))
            failed_rate = failed / total

            # 失败率超过50%告警
            if failed_rate > 0.5:
                self._send_alert(
                    f'{crawl_type}爬取失败率过高: {failed_rate*100:.1f}% ({failed}/{total})',
                    'warning'
                )

            # 连续失败5次告警
            if failed >= 5:
                self._send_alert(
                    f'{crawl_type}爬取连续失败{failed}次',
                    'error'
                )

    def _send_alert(self, message: str, level: str = 'info'):
        """
        发送告警

        Args:
            message: 告警消息
            level: 告警级别（info/warning/error）
        """
        logger.log(
            logging.ERROR if level == 'error' else logging.WARNING if level == 'warning' else logging.INFO,
            f'[告警] {message}'
        )

        # 记录到监控系统
        self.monitor.record_alert({
            'message': message,
            'level': level,
            'timestamp': datetime.now().isoformat()
        })

        # TODO: 实际生产环境可以集成邮件/钉钉/企业微信等告警
        # 这里仅记录日志

    def _job_executed_listener(self, event):
        """任务执行事件监听器"""
        job_id = event.job_id

        if event.exception:
            logger.error(f'任务执行失败: {job_id}, 异常: {event.exception}')
            self.job_history.append({
                'job_id': job_id,
                'status': 'failed',
                'exception': str(event.exception),
                'timestamp': datetime.now().isoformat()
            })
        else:
            logger.info(f'任务执行成功: {job_id}')
            self.job_history.append({
                'job_id': job_id,
                'status': 'success',
                'timestamp': datetime.now().isoformat()
            })

        # 限制历史记录数量
        if len(self.job_history) > 1000:
            self.job_history = self.job_history[-500:]


# 全局单例
_scheduler: Optional[CrawlerScheduler] = None


def get_scheduler() -> CrawlerScheduler:
    """获取调度器单例"""
    global _scheduler
    if _scheduler is None:
        _scheduler = CrawlerScheduler()
    return _scheduler


def start_scheduler():
    """启动调度器"""
    scheduler = get_scheduler()
    scheduler.setup_default_jobs()
    scheduler.start()
    return scheduler


if __name__ == '__main__':
    # 测试运行
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )

    logger.info('启动爬虫调度器（测试模式）...')
    scheduler = start_scheduler()

    # 显示所有任务
    jobs = scheduler.get_jobs()
    logger.info(f'已注册的任务 ({len(jobs)}个):')
    for job in jobs:
        logger.info(f'  - {job["name"]} (ID: {job["id"]}) - 下次执行: {job["next_run_time"]}')

    try:
        import time
        logger.info('调度器运行中，按Ctrl+C停止...')
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        logger.info('正在停止调度器...')
        scheduler.stop()
        logger.info('调度器已停止')

