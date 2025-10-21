"""
定时任务与监控测试
验证T2.1.4任务：定时任务与监控
"""

import sys
from pathlib import Path

project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

import pytest
import logging
from datetime import datetime, timedelta

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)


class TestCrawlerScheduler:
    """调度器测试类"""

    def test_scheduler_exists(self):
        """测试1: 调度器存在"""
        from backend.crawler.scheduler import CrawlerScheduler, get_scheduler

        scheduler = get_scheduler()
        assert scheduler is not None
        assert isinstance(scheduler, CrawlerScheduler)

        logger.info("✅ 调度器验证通过")

    def test_scheduler_setup_jobs(self):
        """测试2: 设置默认任务"""
        from backend.crawler.scheduler import get_scheduler

        scheduler = get_scheduler()
        scheduler.setup_default_jobs()

        jobs = scheduler.get_jobs()
        assert len(jobs) >= 3  # 至少有3个默认任务

        job_ids = [j['id'] for j in jobs]
        assert 'daily_full_crawl' in job_ids
        assert 'incremental_crawl_2h' in job_ids
        assert 'hourly_monitor_report' in job_ids

        logger.info(f"✅ 默认任务设置验证通过，共{len(jobs)}个任务")

    def test_scheduler_add_custom_job(self):
        """测试3: 添加自定义任务"""
        from backend.crawler.scheduler import get_scheduler
        from apscheduler.triggers.interval import IntervalTrigger

        scheduler = get_scheduler()

        def test_job():
            pass

        trigger = IntervalTrigger(minutes=30)
        scheduler.add_custom_job(
            func=test_job,
            trigger=trigger,
            job_id='test_custom_job',
            name='测试自定义任务'
        )

        jobs = scheduler.get_jobs()
        job_ids = [j['id'] for j in jobs]
        assert 'test_custom_job' in job_ids

        # 清理
        scheduler.remove_job('test_custom_job')

        logger.info("✅ 自定义任务添加验证通过")

    def test_scheduler_remove_job(self):
        """测试4: 移除任务"""
        from backend.crawler.scheduler import get_scheduler
        from apscheduler.triggers.interval import IntervalTrigger

        scheduler = get_scheduler()

        # 添加测试任务
        def test_job():
            pass

        trigger = IntervalTrigger(minutes=10)
        scheduler.add_custom_job(
            func=test_job,
            trigger=trigger,
            job_id='test_remove_job',
            name='测试移除任务'
        )

        # 验证存在
        jobs_before = scheduler.get_jobs()
        job_ids_before = [j['id'] for j in jobs_before]
        assert 'test_remove_job' in job_ids_before

        # 移除
        result = scheduler.remove_job('test_remove_job')
        assert result == True

        # 验证已移除
        jobs_after = scheduler.get_jobs()
        job_ids_after = [j['id'] for j in jobs_after]
        assert 'test_remove_job' not in job_ids_after

        logger.info("✅ 任务移除验证通过")


class TestCrawlerMonitor:
    """监控器测试类"""

    def test_monitor_exists(self):
        """测试5: 监控器存在"""
        from backend.crawler.monitor import CrawlerMonitor, get_monitor

        monitor = get_monitor()
        assert monitor is not None
        assert isinstance(monitor, CrawlerMonitor)

        logger.info("✅ 监控器验证通过")

    def test_record_crawl_session(self):
        """测试6: 记录爬取会话"""
        from backend.crawler.monitor import get_monitor

        monitor = get_monitor()

        session_data = {
            'type': 'test',
            'start_time': datetime.now().isoformat(),
            'end_time': (datetime.now() + timedelta(seconds=10)).isoformat(),
            'duration': 10.0,
            'success_count': 5,
            'failed_count': 1,
            'results': [
                {
                    'spider_name': 'test_spider',
                    'success': True,
                    'stats': {'total_items': 100}
                }
            ]
        }

        initial_count = len(monitor.sessions)
        monitor.record_crawl_session(session_data)

        assert len(monitor.sessions) == initial_count + 1
        assert monitor.sessions[-1]['type'] == 'test'

        logger.info("✅ 爬取会话记录验证通过")

    def test_record_error(self):
        """测试7: 记录错误"""
        from backend.crawler.monitor import get_monitor

        monitor = get_monitor()

        initial_count = len(monitor.errors)
        monitor.record_error('test_error', '这是一个测试错误')

        assert len(monitor.errors) == initial_count + 1
        assert monitor.errors[-1]['type'] == 'test_error'

        logger.info("✅ 错误记录验证通过")

    def test_record_alert(self):
        """测试8: 记录告警"""
        from backend.crawler.monitor import get_monitor

        monitor = get_monitor()

        initial_count = len(monitor.alerts)
        monitor.record_alert({
            'message': '测试告警',
            'level': 'warning',
            'timestamp': datetime.now().isoformat()
        })

        assert len(monitor.alerts) == initial_count + 1
        assert monitor.alerts[-1]['message'] == '测试告警'

        logger.info("✅ 告警记录验证通过")

    def test_generate_report(self):
        """测试9: 生成监控报告"""
        from backend.crawler.monitor import get_monitor

        monitor = get_monitor()

        report = monitor.generate_report(hours=24)

        assert 'generated_at' in report
        assert 'summary' in report
        assert 'spider_statistics' in report

        summary = report['summary']
        assert 'total_sessions' in summary
        assert 'success_rate' in summary
        assert 'total_items_crawled' in summary

        logger.info("✅ 监控报告生成验证通过")

    def test_get_metrics(self):
        """测试10: 获取指标"""
        from backend.crawler.monitor import get_monitor

        monitor = get_monitor()

        metrics = monitor.get_metrics()

        assert 'metrics' in metrics
        assert 'spider_stats' in metrics
        assert 'recent_sessions_count' in metrics

        logger.info("✅ 指标获取验证通过")

    def test_get_health_status(self):
        """测试11: 获取健康状态"""
        from backend.crawler.monitor import get_monitor

        monitor = get_monitor()

        health = monitor.get_health_status()

        assert 'status' in health
        assert 'message' in health
        assert 'timestamp' in health
        assert health['status'] in ['healthy', 'warning', 'error']

        logger.info(f"✅ 健康状态验证通过，当前状态: {health['status']}")


class TestSchedulerMonitorIntegration:
    """调度器与监控器集成测试"""

    def test_scheduler_monitor_integration(self):
        """测试12: 调度器监控集成"""
        from backend.crawler.scheduler import get_scheduler
        from backend.crawler.monitor import get_monitor

        scheduler = get_scheduler()
        monitor = get_monitor()

        # 验证调度器可以访问监控器
        assert scheduler.monitor is not None
        assert scheduler.monitor == monitor

        logger.info("✅ 调度器监控集成验证通过")

    def test_files_exist(self):
        """测试13: 文件存在性验证"""
        components = [
            project_root / "backend" / "crawler" / "scheduler.py",
            project_root / "backend" / "crawler" / "monitor.py",
        ]

        for component in components:
            assert component.exists(), f"缺少组件: {component}"

        logger.info(f"✅ 文件完整性验证通过 - 共{len(components)}个文件")

    def test_requirements(self):
        """测试14: 依赖包验证"""
        try:
            import apscheduler
            logger.info(f"✅ APScheduler已安装，版本: {apscheduler.__version__}")
        except ImportError:
            logger.warning("⚠️ APScheduler未安装，需要执行: pip install apscheduler")


if __name__ == "__main__":
    logger.info("🧪 开始运行定时任务与监控测试...")
    pytest.main([__file__, "-v", "-s"])

