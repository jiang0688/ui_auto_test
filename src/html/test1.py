from flask import Flask, render_template, Response
import logging
import time
import threading
import sys, os

current_path = os.path.dirname(os.path.abspath(__file__))
log_path = os.path.join(current_path, 'log.txt')

app = Flask(__name__)

# 配置日志
logging.basicConfig(
    level=logging.DEBUG,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler(log_path, mode='w', encoding='utf-8'),
        logging.StreamHandler()
    ]
)

# 创建一个 logger
logger = logging.getLogger()

# 重定向 stdout 和 stderr 到 logger
class StreamToLogger:
    def __init__(self, logger, log_level=logging.INFO):
        self.logger = logger
        self.log_level = log_level
        self.linebuf = ''

    def write(self, buf):
        for line in buf.rstrip().splitlines():
            self.logger.log(self.log_level, line.rstrip())

    def flush(self):
        pass

sys.stdout = StreamToLogger(logger, logging.INFO)
sys.stderr = StreamToLogger(logger, logging.ERROR)

# 定义一个函数来生成日志内容
def generate_log():
    logger.debug("Starting to generate log")
    with open(log_path, 'r', encoding='utf-8') as file:
        while True:
            line = file.readline()
            if not line:
                # logger.debug("No new log content, waiting...")
                time.sleep(0.1)  # 等待新内容
                continue
            # logger.debug(f"Yielding log line: {line.strip()}")
            yield f"data: {line}\n\n"

# 定义一个后台线程来写入日志
def write_log():
    while True:
        logger.info("这是一个普通的日志信息")
        time.sleep(5)

# 启动后台线程
threading.Thread(target=write_log, daemon=True).start()

@app.route('/')
def index():
    logger.info("Rendering index1.html")
    return render_template('index1.html')

@app.route('/log')
def log():
    logger.info("Log route accessed")
    return Response(generate_log(), mimetype='text/event-stream')

if __name__ == '__main__':
    app.run(debug=True)