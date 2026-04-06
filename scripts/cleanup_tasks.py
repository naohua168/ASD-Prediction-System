"""
后台任务清理脚本

定期清理已完成的分析任务记录，释放内存。
可通过系统定时任务（cron/Task Scheduler）调用。
"""
import sys
import os
import logging

# 添加项目根目录到 Python 路径
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app import create_app
from tasks.analysis_tasks import cleanup_completed_tasks

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s %(levelname)s: %(message)s'
)
logger = logging.getLogger(__name__)


def main():
    """执行任务清理"""
    app = create_app()
    
    with app.app_context():
        try:
            logger.info("开始清理已完成的任务...")
            cleanup_completed_tasks(max_age_hours=24)
            logger.info("任务清理完成")
        except Exception as e:
            logger.error(f"任务清理失败: {e}", exc_info=True)
            sys.exit(1)


if __name__ == '__main__':
    main()
