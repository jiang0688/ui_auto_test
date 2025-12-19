import logging
import os,sys
current_path = os.path.dirname(os.path.abspath(__file__))
log_path = os.path.join(current_path, 'log.txt')



class StreamToLogger:
    """
    Fake file-like stream object that redirects writes to a logger instance.
    """
    def __init__(self, logger, log_level=logging.INFO):
        self.logger = logger
        self.log_level = log_level
        self.linebuf = ''

    def write(self, buf):
        for line in buf.rstrip().splitlines():
            self.logger.log(self.log_level, line.rstrip())

    def flush(self):
        # This flush method is needed for python 3 compatibility.
        # This handles the flush command by doing nothing.
        # You might want to extend it to flush the underlying logger.
        pass

# 配置日志
logging.basicConfig(
    level=logging.DEBUG,  # 设置日志级别
    format='%(asctime)s - %(levelname)s - %(message)s',  # 设置日志格式
    handlers=[
        logging.FileHandler(log_path, mode='w', encoding='utf-8'),  # 指定日志文件名、模式和编码
        logging.StreamHandler()  # 同时将日志输出到控制台
    ]
)

# 创建一个 logger
logger = logging.getLogger()

# 重定向 stdout 和 stderr 到 logger
sys.stdout = StreamToLogger(logger, logging.INFO)
sys.stderr = StreamToLogger(logger, logging.ERROR)

# 示例代码
print("这是一个普通的打印信息")
print("这是一条包含中文的信息")
logger.debug("这是一个调试信息")
logger.warning("这是一个警告信息")
logger.error("这是一个错误信息")
logger.critical("这是一个严重错误信息")
print("程序结束运行1111111111111")