import os
from pathlib import Path
import shutil
from typing import Union
from airtest.core.api import *
from airtest.core.android.adb import ADB
import json
from datetime import datetime
import logging

import requests
import re

from tqdm import tqdm
logging.basicConfig(level=logging.WARNING)  # 设置全局日志级别
logging.getLogger("airtest").setLevel(logging.FATAL)

current_dir = os.path.dirname(os.path.abspath(__file__))
ui_auto_test_path = os.path.dirname(os.path.dirname(current_dir))
images_path = os.path.join(ui_auto_test_path, 'images')         #默认保存截图的目录

def log(message):
    """打印带时间戳的日志"""
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    print(f"[{timestamp}] {message}")

def get_dir_list(folder_path):
    """
    获取指定目录下的所有子目录路径列表
    :param folder_path: 目录路径
    :return: 子目录路径列表
    """
    # print([os.path.join(folder_path, name) for name in os.listdir(folder_path) 
    #         if os.path.isdir(os.path.join(folder_path, name))])
    return [os.path.join(folder_path, name) for name in os.listdir(folder_path) 
            if os.path.isdir(os.path.join(folder_path, name))]





def get_all_apk_files(folder_path):
    """获取指定文件夹及其子文件夹中的所有APK文件"""
    apk_files = []
    for root, dirs, files in os.walk(folder_path):
        for file in files:
            if file.lower().endswith('.apk'):
                apk_files.append(os.path.join(root, file))
    return apk_files


def modify_json(json_path,success:bool):
    """
    修改json文件

    :param json_path: json文件路径
    :param success: 测试是否成功
    """
    with open(json_path, 'r', encoding='utf-8') as f:
        data = json.load(f)

    data["success"] = success
    data["last_test_time"] = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    with open(json_path, 'w', encoding='utf-8') as f:
        json.dump(data, f, indent=4, ensure_ascii=False)

    print(f"[{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}] 修改json文件成功:{json_path}")




def airtest_capture_screenshot(description="步骤截图", save_dir=None):
    """
    Airtest截图并返回文件路径
    """
    try:
        # 使用默认的 images_path 如果未指定目录
        if save_dir is None:
            save_dir = images_path
        else:
            # 确保是绝对路径
            save_dir = os.path.abspath(save_dir)
        
        os.makedirs(save_dir, exist_ok=True)
        
        # 生成唯一文件名
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S_%f")[:-3]
        safe_description = "".join(c for c in description if c.isalnum() or c in (' ', '-', '_')).rstrip()
        filename = f"{safe_description}_{timestamp}.png"
        screenshot_path = os.path.join(save_dir, filename)
        
        # 使用Airtest截图
        from airtest.core.api import snapshot
        snapshot(filename=screenshot_path, msg=description)
        
        if os.path.exists(screenshot_path):
            print(f"📷 截图已保存: {screenshot_path}")
            return screenshot_path
        else:
            print("❌ 截图保存失败")
            
    except Exception as e:
        print(f"❌ Airtest截图失败: {e}")
    
    return None



def safe_step(action_desc, func, *args, **kwargs):
    """安全执行步骤，捕获异常并记录日志"""
    try:
        return func(*args, **kwargs)
    except Exception as e:
        img_path = airtest_capture_screenshot(f"失败_{action_desc}")
        # 获取当前测试节点（pytest 会注入 request）
        import inspect
        frame = inspect.currentframe().f_back
        node = frame.f_locals.get('request').node
        node.add_screenshot_path(img_path, action_desc)
        log(f"❌ 步骤【{action_desc}】失败：{e}")
        raise e



def rm(path: Union[str, Path]) -> None:
    """
    安全删除文件或整个文件夹下的所有内容（不包括目录本身）。

    参数
    ----
    path : str | PathLike
        要删除的文件或目录路径。

    返回
    ----
    None
        成功删除时静默返回；路径不存在时打印提示，不抛异常。
    """
    if not os.path.exists(path):
        print(f"⚠️ 路径不存在：{path}")
        return

    try:
        if os.path.isfile(path):
            os.remove(path)
            print(f"✅ 已删除文件：{path}")
            return
        elif os.path.isdir(path):
            shutil.rmtree(path)
            print(f"✅ 已删除目录下所有内容：{path}")
    except Exception as e:
        print(f"❌ 删除失败：{path} -> {e}")



def get_apk_files(folder_path):
    """获取指定目录下的所有 .apk 文件，不包括子目录中的文件。"""
    apk_files = []
    for entry in os.listdir(folder_path):
        full_path = os.path.join(folder_path, entry)
        if os.path.isfile(full_path) and full_path.endswith('.apk'):
            apk_files.append(full_path)
    return apk_files





def download_apk(url, save_path):
    """
    从指定的 URL 下载 APK 文件并保存到本地路径，并显示下载进度条。
    
    :param url: APK 文件的下载链接
    :param save_path: 保存 APK 文件的本地路径
    """
    try:
        # 确保保存路径存在
        if not os.path.exists(save_path):
            os.makedirs(save_path)
            print(f"路径 {save_path} 不存在，已创建。")

        # 创建会话
        session = requests.Session()

        # 设置请求头
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/58.0.3029.110 Safari/537.3',
            'Referer': url  # 设置 Referer 为原始链接
        }

        # 发送 GET 请求获取 HTML 内容
        response = session.get(url, headers=headers)
        response.raise_for_status()  # 检查请求是否成功

        # 提取 fileName 和 sharedFileDownloadURL
        file_name_match = re.search(r'fileName: \'(.*?)\'', response.text)
        download_url_match = re.search(r'sharedFileDownloadURL: \'(.*?)\'', response.text)

        if not file_name_match or not download_url_match:
            raise ValueError("无法从 HTML 内容中提取 fileName 或 sharedFileDownloadURL")

        file_name = file_name_match.group(1)
        download_url = download_url_match.group(1)


        # 发送 GET 请求下载 APK 文件
        apk_response = session.get(download_url, headers=headers, stream=True)
        apk_response.raise_for_status()  # 检查请求是否成功

        file_path = os.path.join(save_path, file_name)




        # 以二进制模式打开文件并写入内容（显示进度条）
        """      
        # 获取文件总大小
        total_size = int(apk_response.headers.get('content-length', 0))   
        with open(file_path, 'wb') as file, tqdm(
            desc=file_name,
            total=total_size,
            unit='B',
            unit_scale=True,
            unit_divisor=1024,
        ) as bar:
            for chunk in apk_response.iter_content(chunk_size=8192):
                file.write(chunk)
                bar.update(len(chunk)) """

        # 以二进制模式打开文件并写入内容
        with open(file_path, 'wb') as file:
            for chunk in apk_response.iter_content(chunk_size=8192):
                file.write(chunk)


        log(f"下载APK成功: {file_path}")
        
    except requests.exceptions.RequestException as e:
        print(f"下载过程中发生错误: {e}")
    except PermissionError as e:
        print(f"权限错误: {e}")
    except FileNotFoundError as e:
        print(f"文件或目录未找到: {e}")
    except ValueError as e:
        print(f"值错误: {e}")
    except Exception as e:
        print(f"发生未知错误: {e}")








