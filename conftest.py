# conftest.py
import base64
from datetime import datetime
import os
from pathlib import Path
import shutil
import sys
import json
import pytest
from pytest_html import extras
from collections import defaultdict
import threading

# 项目根目录
UI_ROOT = os.path.dirname(os.path.dirname(__file__))
IMG_DIR = os.path.join(UI_ROOT, "images")
os.makedirs(IMG_DIR, exist_ok=True)
from src.core.api import rm

# ---------------- 全局日志缓存 ----------------
logs = defaultdict(list)          # 全局缓存
_local = threading.local()        # 线程局部存储

def log(msg: str):
    """用例里直接 log('xxx')，无需传 nodeid"""
    nodeid = getattr(_local, 'nodeid', None)
    if nodeid is None:
        return                    # 非 pytest 线程直接忽略
    ts = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    print(f"[{ts}] {msg}", file=sys.stderr)
    logs[nodeid].append(f"[{ts}] {msg}")

# -------------------------------------------------
# 1. 每次测试会话前清空旧图
def pytest_configure(config):
    if os.path.exists(IMG_DIR):
        shutil.rmtree(IMG_DIR)
    os.makedirs(IMG_DIR, exist_ok=True)

# -------------------------------------------------
# 2. 给每个测试节点动态绑定 add_screenshot_path
def pytest_runtest_setup(item):
    _local.nodeid = item.nodeid   # 把 nodeid 写入线程局部变量
    item._data = item.callspec.params.get("data", "") if hasattr(item, "callspec") else ""  # 保存 parametrize 的 data 参数
    def add_screenshot_path(path, desc="步骤截图"):
        if not os.path.exists(path):
            print(f"⚠️ 截图不存在: {path}")
            return
        if not hasattr(item, "_screenshots"):
            item._screenshots = []
        item._screenshots.append((path, desc))
    item.add_screenshot_path = add_screenshot_path

# -------------------------------------------------
# 3. 钩子：把截图 & 日志塞进 pytest-html
@pytest.hookimpl(hookwrapper=True)
def pytest_runtest_makereport(item, call):
    outcome = yield
    report = outcome.get_result()
    if report.when != "call":
        return

    # 确保在生成报告之前将 item._data 赋值给 report._data
    report._data = getattr(item, "_data", "")
    # ---------- 处理截图 ----------
    shots = getattr(item, "_screenshots", [])
    if shots:
        imgs_html = "".join(_make_img_tag(p, d) for p, d in shots)
        html_block = f'<div style="display:flex;flex-wrap:wrap;gap:6px;">{imgs_html}</div>'
        if not hasattr(report, "extra"):
            report.extra = []
        report.extra.append(extras.html(html_block))

    # ---------- 处理日志 ----------
    node_logs = logs.get(item.nodeid, [])
    if node_logs:
        log_html = "<br>".join(node_logs)
        log_block = (
            f'<details><summary>运行日志（{len(node_logs)} 行）</summary>'
            f'<pre style="max-height:300px;overflow:auto;background:#f6f8fa;padding:8px;border-radius:4px;">{log_html}</pre></details>')
        if not hasattr(report, "extra"):
            report.extra = []
        report.extra.append(extras.html(log_block))
    else:
        log_block = f'<details><summary>无日志输出</summary></details>'
        report.extra.append(extras.html(log_block))

# -------------------------------------------------
# 4. 生成 base64 嵌入图
def _make_img_tag(img_path, desc):
    """返回纯 HTML 片段，不用 extras.html"""
    with open(img_path, "rb") as f:
        b64 = base64.b64encode(f.read()).decode()
    return f'''
        <div style="margin:4px;text-align:center;">
          <img src="data:image/png;base64,{b64}"
               style="max-width:180px;cursor:pointer;border:1px solid #ddd;border-radius:4px;"
               onclick="this.style.maxWidth=this.style.maxWidth==='100%'?'180px':'100%'"/>
          <div style="font-size:11px;color:#555;margin-top:2px;">{desc}</div>
        </div>
    '''
# -------------------------------------------------
# 5. 报告表头 / 行自定义（可选）
def pytest_html_report_title(report):
    report.title = "自动化测试报告"

def pytest_html_results_table_header(cells):
    cells.insert(1, "<th class='sortable'>数据</th>")
    cells.insert(2, "<th class='sortable'>截图</th>")

def pytest_html_results_table_row(report, cells):
    data = getattr(report, "_data", "")
    
    if isinstance(data, dict):
        data = json.dumps(data, ensure_ascii=True, indent=2)  # 将字典转换为格式化的 JSON 字符串
    else:
        data = str(data)  # 其他类型直接转换为字符串

    data_escaped = data.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")
    cells.insert(1, f"<td><pre style='white-space:pre-wrap;'>{data_escaped}</pre></td>")

    # 原有截图统计
    count = len([e for e in getattr(report, "extra", []) if "img src=" in str(e)])
    cells.insert(2, f"<td>📸 {count}</td>")

# -------------------------------------------------
# 6. 会话结束后清空日志（防止内存累积）
def pytest_sessionfinish(session, exitstatus):
    print(f"[{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}] 清理文件夹：{IMG_DIR}")
    rm(IMG_DIR)

    if exitstatus == 0:
        pass
    else:
        print(f"[{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}] 测试被用户中断或出现错误")
        if exitstatus == 2:
            sys.exit(0)  # Ctrl+C 中断的退出代码，正常退出，不输出错误信息