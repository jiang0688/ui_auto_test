import json
import sys
import time
from flask import Flask, render_template, request, jsonify
import subprocess
import threading
import re
import os
import signal
from datetime import datetime
from threading import Lock

current_dir = os.path.dirname(os.path.abspath(__file__))
ui_auto_test_path = os.path.dirname(os.path.dirname(current_dir))

report_json_path = os.path.join(ui_auto_test_path, "report", "report.json")  # 测试结果报告json文件路径
test_html_path = os.path.join(ui_auto_test_path, "run_fenbao_test1.py")
log_path = os.path.join(current_dir, 'logs.txt')

app = Flask(__name__)

# 存储日志的全局变量
log_contents = []
process = None
is_running = False  # 添加全局运行状态变量

process_lock = Lock()# 添加线程锁，防止并发操作

def run_script(version, links):
    global log_contents, process, is_running
    is_running = True
    log_contents = []

    try:
        # 使用当前Python解释器
        process = subprocess.Popen(
            [sys.executable, test_html_path, version, links],
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            universal_newlines=True,
            encoding='gbk',  # 直接使用GBK编码
            errors='replace'  # 用�替换无法解码的字符
        )
        
        # 实时读取输出
        for line in process.stdout:
            if not is_running:
                break
            clean_line = line.strip()
            if clean_line:
                log_contents.append(clean_line)
                print(clean_line)
            
        # 等待进程完成
        return_code = process.wait()
        log_contents.append(f"进程结束，返回码: {return_code}")
        print(f"脚本执行完成，返回码: {return_code}")
            
    except Exception as e:
        error_msg = f"错误: {str(e)}"
        log_contents.append(error_msg)
        print(f"运行脚本时出错: {error_msg}")
        import traceback
        traceback.print_exc()
    finally:
        is_running = False
        # 确保进程已经结束再删除文件
        safe_remove_file(log_path)
        print(f"{log_path} 清理临时日志完成，避免占用磁盘空间")

def safe_remove_file(file_path):
    """安全删除文件，处理文件被占用的情况"""
    if not os.path.exists(file_path):
        return
        
    max_retries = 5
    for i in range(max_retries):
        try:
            os.remove(file_path)
            print(f"成功删除文件: {file_path}")
            return
        except PermissionError:
            if i < max_retries - 1:
                print(f"文件被占用，等待重试... ({i+1}/{max_retries})")
                time.sleep(0.5)  # 等待0.5秒再重试
            else:
                print(f"无法删除文件 {file_path}，可能仍被占用")
        except Exception as e:
            print(f"删除文件时出错: {e}")
            break

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/run', methods=['POST'])
def run():
    global process, is_running
    
    # 检查是否已经有进程在运行
    if is_running:
        return jsonify({'status': 'error', 'message': '已有测试正在运行，请等待完成后再操作'})
    
    # 尝试获取锁，如果获取不到说明有其他操作在进行
    if not process_lock.acquire(blocking=False):
        return jsonify({'status': 'error', 'message': '系统繁忙，请稍后再试'})
    
    try:
        # 如果已有进程在运行，先终止它
        if process and process.poll() is None:
            process.terminate()
            try:
                process.wait(timeout=5)
            except:
                pass
        
        data = request.json
        version = data.get('version', '')
        links = data.get('links', '')
        
        if not version or not links:
            # 释放锁
            process_lock.release()
            return jsonify({'status': 'error', 'message': '版本号和链接不能为空'})
        
        print(f"收到运行请求: 版本={version}, 链接数={len(links.splitlines())}")
        
        # 在新线程中运行脚本
        thread = threading.Thread(target=run_script, args=(version, links))
        thread.daemon = True
        thread.start()
        
        return jsonify({'status': 'started', 'message': '脚本开始执行'})
    
    except Exception as e:
        # 确保异常时释放锁
        if process_lock.locked():
            process_lock.release()
        return jsonify({'status': 'error', 'message': f'启动失败: {str(e)}'})

@app.route('/logs')
def get_logs():
    # 检查日志中是否有完成标记
    completed = any("===TEST_COMPLETED===" in log for log in log_contents)
    # 如果进程已经结束但日志中没有完成标记，也认为是完成了
    if not completed and process and process.poll() is not None:
        completed = True
        log_contents.append("===TEST_COMPLETED===")
    
    return jsonify({'logs': log_contents, 'completed': completed})

@app.route('/stop', methods=['POST'])
def stop_test():
    global process, is_running
    # 检查是否有进程在运行
    if not is_running:
        return jsonify({'status': 'not_running', 'message': '没有正在运行的脚本'})
    
    if process and process.poll() is None:
        # 终止进程
        try:
            is_running = False  # 设置停止标志
            
            # 在Windows上
            if os.name == 'nt':
                process.terminate()
            # 在Unix/Linux上
            else:
                os.kill(process.pid, signal.SIGTERM)
            
            # 等待进程结束
            process.wait(timeout=5)
            log_contents.append("===TEST_STOPPED===")
            # 释放锁
            if process_lock.locked():
                process_lock.release()

            return jsonify({'status': 'stopped', 'message': '脚本已停止'})
        except Exception as e:
            return jsonify({'status': 'error', 'message': str(e)})
    
    return jsonify({'status': 'not_running', 'message': '没有正在运行的脚本'})

@app.route('/api/test-results')
def get_test_results():
    # 检查文件是否存在
    if not os.path.exists(report_json_path):
        return jsonify({'error': '测试结果文件不存在'}), 404
    
    try:
        # 读取JSON文件
        with open(report_json_path, 'r', encoding='utf-8') as f:
            results_data = json.load(f)
        
        # 验证数据格式
        if validate_results_data(results_data):
            return jsonify(results_data)
        else:
            return jsonify({'error': '测试结果数据格式不正确'}), 400
    
    except json.JSONDecodeError:
        return jsonify({'error': 'JSON格式错误，无法解析'}), 400
    except Exception as e:
        return jsonify({'error': f'读取文件时出错: {str(e)}'}), 500

def validate_results_data(data):
    """验证测试结果数据格式"""
    if not isinstance(data, dict):
        return False
    
    required_fields = ['success', 'failed', 'total', 'failure_pck', 'last_test_time']
    
    # 检查所有必需字段都存在
    for field in required_fields:
        if field not in data:
            return False
    
    # 检查数据类型
    if (not isinstance(data['success'], int) or 
        not isinstance(data['failed'], int) or 
        not isinstance(data['total'], int) or
        not isinstance(data['last_test_time'], str) or
        not isinstance(data['failure_pck'], list)):
        return False
    
    # 检查数值合理性
    if data['success'] < 0 or data['failed'] < 0 or data['total'] < 0:
        return False
    
    # # 检查总数一致性
    # if data['total'] != data['success'] + data['failed']:
    #     return False
    
    # # 检查时间格式（简单验证）
    # if len(data['last_test_time']) < 10:  # 至少要有日期部分
    #     return False
    
    return True



@app.route('/status')
def get_status():
    return jsonify({
        'is_running': is_running,
        'process_exists': process is not None,
        'process_alive': process and process.poll() is None if process else False,
        'log_lines': len(log_contents),
        'can_start_new': not is_running and not process_lock.locked()
    })

@app.route('/api/check-results')
def check_results():
    """检查测试结果文件是否存在且有效"""
    if not os.path.exists(report_json_path):
        return jsonify({'exists': False, 'valid': False})
    
    try:
        with open(report_json_path, 'r', encoding='utf-8') as f:
            data = json.load(f)
        
        valid = validate_results_data(data)
        return jsonify({'exists': True, 'valid': valid})
    
    except:
        return jsonify({'exists': True, 'valid': False})

@app.route('/api/system-status')
def system_status():
    """获取系统状态信息"""
    return jsonify({
        'is_running': is_running,
        'process_alive': process and process.poll() is None if process else False,
        'lock_acquired': process_lock.locked(),
        'can_start_new': not is_running and not process_lock.locked(),
        'process_return_code': process.returncode if process else None,
        'log_count': len(log_contents)
    })

@app.before_request
def check_system_status():
    """在每次请求前检查系统状态"""
    # 如果进程已经结束但状态未更新，更新状态
    if process and process.poll() is not None and is_running:
        is_running = False
        if process_lock.locked():
            process_lock.release()



if __name__ == '__main__':
    
    app.run(debug=True, host='0.0.0.0', port=5000)