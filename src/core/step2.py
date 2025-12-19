from datetime import datetime
import json
import os
import subprocess
import re
import sys
from pathlib import Path

# 获取当前脚本所在目录并构建aapt路径
current_dir = os.path.dirname(os.path.abspath(__file__))
ui_auto_test_path = os.path.dirname(os.path.dirname(current_dir))

sys.path.append(ui_auto_test_path)
from src.core.log import log
aapt_path = os.path.join(ui_auto_test_path, "tools", "aapt.exe")

def get_package_name(apk_path, aapt_path=aapt_path):  # 使用默认参数
    """
    获取 APK 的包名
    :param apk_path: APK 文件路径（如 "D:/app.apk"）
    :param aapt_path: aapt 可执行文件路径，默认为项目tools目录下的aapt.exe
    :return: 包名（如 "com.example.app"），失败返回 None
    """
    try:
        # 检查文件是否存在
        if not os.path.exists(apk_path):
            raise FileNotFoundError(f"APK文件不存在: {apk_path}")
        if not os.path.exists(aapt_path):
            raise FileNotFoundError(f"aapt工具不存在: {aapt_path}")
        
        # 构造命令
        cmd = [aapt_path, "dump", "badging", apk_path]
        
        # 执行命令并捕获输出
        output = subprocess.check_output(
            cmd, 
            stderr=subprocess.STDOUT,
            encoding='gbk',  # Windows中文系统编码
            errors='ignore'
        )
        
        # log(output)
        # 提取包名
        match = re.search(r"package: name='([^']+)'", output)
        # 多字段正则匹配
        patterns = {
            'package': r"name='([^']+)'",
            'version': r"versionName='([^']+)'",
            'sdk': r"targetSdkVersion='([^']+)'"
        }
        results = {}
        for key, pattern in patterns.items():
            match = re.search(pattern, output)
            results[key] = match.group(1) if match else None
        
        return results.get('package'), results.get('version')
        
    except Exception as e:
        log(f"获取APK信息失败: {str(e)}")
        return None, None



    
def main(folder_name):
    """
    生成测试数据config文件
    
    1.在ui_auto_test/test/{folder_name} 目录下:获取所有根据分包id创建的目录
    2.遍历全部分包id目录，获取apk路径，包名，版本号，email等
    3.生成config.json文件，内容包括email，密码，分包id，apk路径，包名，版本号，测试结果，最后测试时间
    """

    version_path = os.path.join(ui_auto_test_path, 'test',folder_name)
    with os.scandir(version_path) as entries:
        folder_path_lists = [entry.path for entry in entries if entry.is_dir()]
    
    if folder_path_lists:
        for folder_path in folder_path_lists:
            log(f"文件夹路径: {folder_path}")
            dir_path = Path(folder_path)

            apk_files = [(str(p)) for p in dir_path.rglob('*.apk')]  # 获取apk文件路径

            package_id = os.path.basename(folder_path)          #分包id
            apk_file = apk_files[0] if apk_files else None      #安装包路径
            
            package_name,version_name = get_package_name(apk_file)
            
            emails = {
                # XIAOMI
                "B0001":"xiaomi@end.tv",
                "B0002":"xiaomi02@end.tv",
                "B0003":"xiaomi03@end.tv",
                
                # VIVO
                "C0001":"vivo@end.tv",
                "C0002":"vivo02@end.tv",
                "C0003":"vivo03@end.tv",

                # SAMSUNG
                "D0001":"samsung@end.tv",
                "D0002":"samsung02@end.tv",
                "D0003":"samsung03@end.tv",

                # OPPO
                "E0001":"oppo@end.tv",
                "E0002":"oppo02@end.tv",
                "E0003":"oppo03@end.tv",

                "E0001":"oppo@end.tv",
                "E0002":"oppo02@end.tv",
                "E0003":"oppo03@end.tv",

                # DLIGHTEK
                "F0001":"dlightek@end.tv",
                "F0002":"dlightek02@end.tv",
                "F0003":"dlightek03@end.tv",

                # APKPURE
                "G0001":"apkpure@end.tv",
                "G0002":"apkpure02@end.tv",
                "G0003":"apkpure03@end.tv",

                # APTOIDE
                "H0001":"aptoide@end.tv",
                "H0002":"aptoide02@end.tv",
                "H0003":"aptoide03@end.tv"
            }




            # email = emails[package_id]
            if package_name == "com.newlang.weelife":
                email = "test001@uuf.me"
            elif package_name == "com.newlang.weelife.ar":
                email = "test002@uuf.me"
            elif package_name == "com.newlang.weelife.in":
                email = "test003@uuf.me"
            

            data = {
                "email":email,
                "password":'12345678',
                "package_id":package_id,
                "apk_file":apk_file,
                "package_name":package_name,
                "version":version_name,
                "success":"",
                "last_test_time":datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            }
            config_path = Path(folder_path) / "config.json"
            # 写入文件（带格式化和UTF-8编码）
            with open(config_path, 'w', encoding='utf-8') as f:
                json.dump(data, f, indent=4, ensure_ascii=False)
            log(f"写入配置文件: {config_path}")
            # log(f"配置文件内容: {data}")
            



if __name__ == '__main__':
    # 测试代码
    apk_path = r"D:\Download\866-meta-android-global-v1.94.0.0.866_290-STABLE-release_v1.94.0-release_1.94_Android-Debug-20250814094556.apk"
    # result = get_package_name(apk_path)
    # log(result)
    # log(f"aapt路径: {aapt_path}")
    # log(f"包名: {result}" if result else "获取包名失败")

    folder_name = '1.93'
    log(f"获取文件夹下所有文件: {folder_name}")
    main(folder_name)

    