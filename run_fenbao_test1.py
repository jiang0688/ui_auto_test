import json
import shutil
import os,sys
import time
import re
from datetime import datetime
import traceback

ui_auto_path =os.path.dirname(os.path.abspath(__file__))
sys.path.append(ui_auto_path)
from tools.ocr.ocr import timeit


def log(msg):
    print(f"[{time.strftime('%Y-%m-%d %H:%M:%S')}] {msg}")
    sys.stdout.flush()


def run_funbao_login_test():
    if len(sys.argv) < 2:
        log("版本号或下载地址不能为空")
        sys.exit(1)


    version = sys.argv[1]   # 网页输入版本号
    links = sys.argv[2]     # 网页输入下载地址
    log(f"测试版本号：{version}")
    log(f"测试下载地址：{links}")
    url_list = []
    urls = re.findall(r'https?://[^\s]+', links)
    for i, url in enumerate(urls, 1):
            url_list.append(url)
    if len(url_list) == 0:
        log("输入的下载地址不正确") 
        sys.exit(1)

    log("-------------------------开始执行分包登录测试-------------------------")
    version_cfg_path =  os.path.join(ui_auto_path,'configs','version.json')
    log(f"将测试版本号写入文件：{version_cfg_path}")
    with open(version_cfg_path, 'w') as f:
            json.dump({'version': version}, f)

    target_path = os.path.join(ui_auto_path,'test',version)   # 工作目录
    if not os.path.exists(target_path):
        log(f"工作目录不存在：{target_path}，执行创建目录")
        os.makedirs(target_path, exist_ok=True)
        log(f"创建工作目录成功：{target_path}")
    else:
        log(f"工作目录已存在,清除目录：{target_path}")
        shutil.rmtree(target_path)
        os.makedirs(target_path, exist_ok=True)



    log(f"开始下载分包apk文件")
    from src.core.api import download_apk
    for url in url_list:
        download_apk(url,save_path=target_path)


    from src.core.step1 import main as step1_main
    from src.core.step2 import main as step2_main
    from src.core.api import get_apk_files, get_dir_list
    from src.login.test_email_login import main as run_pytest_email_login

    #生成测试数据
    log(f"开始根据分包ID创建目录并将APK移动到目录")
    if not get_apk_files(target_path):
        log(f"没有找到APK文件，请确认下载地址是否正确")
        sys.exit(1)

    log("开始执行提取apk分包id，根据分包id创建分包文件夹，并移动apk文件到分包文件夹")
    step1_main(version)

    log("开始生成数据，生成config.json文件")
    step2_main(version)

    if not get_dir_list(target_path):
        log(f"⚠️  数据生成失败，请检查分包apk是否下载成功")
        sys.exit(1)

    log("测试数据生成完毕，开始执行测试用例")

    #这里需要加上自动化测试用例的执
    from src.login.test_email_login_run import Test_Email_Login
    run_login = Test_Email_Login()
    run_login.run(version)

    log("-------------------------分包登录测试结束-------------------------")
    log("===TEST_COMPLETED===")#测试结束标识




if __name__ == '__main__':
    #非pytest框架运行
    try:
        run_funbao_login_test()


    except Exception as e:
        error_message = traceback.format_exc()
        log(f"测试失败：{error_message}")
        sys.exit(1)