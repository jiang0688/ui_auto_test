import os
import sys

import subprocess
from datetime import datetime

current_dir = os.path.dirname(os.path.abspath(__file__))
ui_auto_test_path = os.path.dirname(os.path.dirname(current_dir))
sys.path.append(ui_auto_test_path)

from src.core.api import *
from src.login.login_step import *

def log(msg):
    print(f"[{time.strftime('%Y-%m-%d %H:%M:%S')}] {msg}")
    sys.stdout.flush()

#获取版本号
def get_version():
    version_json_path = os.path.join(ui_auto_test_path,'configs',"version.json")
    with open(version_json_path, 'r', encoding='utf-8') as f:
        version = json.load(f)["version"]
    return version


def get_datas(folder_path):
    """获取测试数据"""
    target_folder = os.path.join(ui_auto_test_path,'test',folder_path)
    data_list = []
    for path in get_dir_list(target_folder):
        config_path = os.path.join(path,'config.json')
        if os.path.exists(config_path):
            with open(config_path, 'r', encoding='utf-8') as f:
                config = json.load(f)
        # log(config)

        data ={
            "folder_path": path,
            "data": config
        }
        data_list.append(data)
    return data_list



class Test_Email_Login:
    def __init__(self):
        log("\n-----------初始化测试环境-----------")
        ST.FIND_TIMEOUT = 60  # 影响所有wait(), exists()等查找操作
        try:
            self.dev = connect_device("Android:///")
            self.dev.shell("echo ping")
            log(f"设备连接成功：{self.dev.uuid}")
            screen_on = self.dev.is_screenon()
            if not screen_on:
                self.dev.wake()
            self.results = {
                "success": 0,
                "failed": 0,
                "total": 0,
                "failure_pck": []
            }
            
        except Exception as e:
            log(f"设备连接失败：{e}")
            sys.exit(1)

    def __del__(self):
        home()
        self.dev.disconnect()

        
    def run(self,version):
        data_list = get_datas(version)
        if not data_list:
            log("测试数据为空，可能生成测试数据的步骤有问题")
            sys.exit(1)



        for datas in data_list:
            folder_path = datas['folder_path']       #包体分区目录
            data = datas['data']
            email = data['email']                   # 邮箱
            password = data['password']             # 密码
            package_id = data['package_id']         # 分区id
            apk_file = data['apk_file']             # apk文件路径
            package_name = data['package_name']     # 包名
            version = data['version']               # 包体版本


            log(f"========= 开始执行分包：{package_id}  =========")
            package_list = self.dev.list_app()

            if package_name in package_list:
                log(f"存在旧版应用，卸载：{package_name}")
                self.dev.uninstall_app(package_name)
                log(f"卸载成功")

            log(f"开始安装最新版应用:{apk_file}")
            log(f"包体版本号：{version}")
            self.dev.install_app(apk_file)

            package_list = self.dev.list_app()
            if package_name in package_list:
                log(f"安装成功")

            log(f"启动应用，等待20秒进入登录页面......")
            self.dev.start_app(package_name)
            sleep(20)
            
            log("点击更多登录方式按钮")
            click_more()


            log("点击邮箱图标")
            eml_btn_pos, pwd_btn_pos, login_btn_pos = click_email_icon()

            log(f"点击输入邮箱")
            click_email_input(eml_btn_pos,email)
            touch((0.1,0.1))    #用于关闭输入法

            log(f"点击输入密码")
            click_password_input(pwd_btn_pos,password)
            touch((0.1,0.1))    #用于关闭输入法

            log("点击登录按钮")
            click_login_btn(login_btn_pos)
            log("等待20秒，加载首页UI......")
            sleep(20)

            home_img_path = os.path.join(ui_auto_test_path,"images",f"{package_id}_{datetime.now().strftime('%Y%m%d_%H%M%S')}_home.png")
            log("开始截图，进行断言文本匹配......")
            log(f"截图路径:{home_img_path}")
            snapshot(filename=home_img_path)

            target_text = "装扮商城"
            ocr = get_ocr()
            result = ocr.match_text(home_img_path,target_text)
            log(f"匹配结果：{result}")

            success = bool(result)
            log(f"{package_id}_测试结果：{success}")
            json_path = os.path.join(folder_path,"config.json")
            log(f"将测试结果写入json文件：{json_path}")
            modify_json(json_path,success)


            if not success:
                self.results["failure_pck"].append(package_id)
                self.results["failed"] += 1
            else:
                self.results["success"] += 1
            self.results["total"] += 1
            log(f"========= 结束执行分包：{package_id}  =========")

        report_json_path = os.path.join(ui_auto_test_path,"report",f"report.json")
        os.makedirs(os.path.dirname(report_json_path), exist_ok=True)
        with open(report_json_path, 'w', encoding='utf-8') as f:
            self.results['last_test_time'] = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            json.dump(self.results, f, indent=4, ensure_ascii=False)

        log("========= 测试结果汇总 =========")
        log(f"总共{self.results['total']}个分包")
        log(f"成功： {self.results['success']}")
        log(f"失败： {self.results['failed']}")
        if self.results['failure_pck']:
            log(f"失败分包ID：{self.results['failure_pck']}")
        log(f"成功率: {self.results['success'] / self.results['total'] * 100:.2f}%")
        
        





