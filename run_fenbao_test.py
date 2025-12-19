import json
import os
import sys
from datetime import datetime

ui_auto_path =os.path.dirname(os.path.abspath(__file__))
sys.path.append(ui_auto_path)
from tools.ocr.ocr import timeit

def log(msg):
    print(f"[{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}] {msg}")

@timeit
def run_fenbao_login_test(version):
    try:
        log("-------------------------开始执行分包登录测试-------------------------")
        version_path =  os.path.join(ui_auto_path,'configs','version.json')

        #将版本配置写入version.json文件中，用于测试用例中使用
        log(f"将测试版本号写入文件：{version_path}")
        with open(version_path, 'w') as f:
            json.dump({'version': version}, f)

        target_path = os.path.join(ui_auto_path,'test',version)
        if not os.path.exists(target_path):
            log(f"测试目录不存在：{target_path}")
            os.makedirs(target_path, exist_ok=True)
            log(f"创建测试目录成功：{target_path}")
            log(f"⚠️  请将APK文件下载到该目录：{target_path}，再次运行！！！")
            sys.exit(1)

        from src.core.step1 import main as step1_main
        from src.core.step2 import main as step2_main
        from src.core.api import get_apk_files, get_dir_list
        from src.login.test_email_login import main as run_pytest_email_login

        #如果版本文件夹下有APK文件，执行生成测试数据
        if get_apk_files(target_path):
            log(f"{target_path} 目录下检测到APK文件,开始生成测试数据")
            
            log("开始执行提取apk分包id，根据分包id创建分包文件夹，并移动apk文件到分包文件夹")
            step1_main(version)

            log("开始执行在分包文件夹创建config.json文件")
            step2_main(version)

            log("测试数据生成完毕，开始执行测试用例")

        #如果版本文件夹下没有APK文件，说明没有生成测试数据，需要将APK文件下载到版本文件夹下
        if not get_dir_list(target_path):
            log(f"⚠️  没有测试数据，请将APK文件下载到: {target_path} 目录下，再次运行！！！")
            sys.exit(1)

        log("开始执行登录测试用例")
        run_pytest_email_login(report=True)

        log("-------------------------分包登录测试结束-------------------------")
    

    except Exception as e:
        log(f"运行报错：{e}")
    except KeyboardInterrupt:
        log("ctrl+c 退出执行")
        sys.exit(0)  # 正常退出

if __name__ == '__main__':
    #pytest框架执行
    version = '1.99'
    run_fenbao_login_test(version)




