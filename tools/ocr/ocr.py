import os
import re
import time
import cv2
from paddleocr import PaddleOCR


"""
    PaddleOCR==3.1.0
    OCR识别图片，根据文本匹配坐标信息，返回坐标信息列表
    官方文档：https://www.paddleocr.ai/latest/index.html

"""
from functools import wraps
def timeit(func):
    """
    装饰器，计算函数运行时间
    """
    @wraps(func)
    def wrapper(*args, **kwargs):
        start_time = time.time()
        result = func(*args, **kwargs)
        end_time = time.time()
        print(f"[耗时统计] {func.__name__} 执行时间: {end_time - start_time:.4f}秒")
        return result
    return wrapper



class OCR:

    @timeit
    def __init__(self):
        """
        初始化OCR识别类

        参数：
            img_path: 图片路径
            target_text: 目标文本
        """
        script_dir = os.path.dirname(__file__) # 获取当前脚本路径
        model_path = os.path.join(script_dir, "model") # 模型路径
        dir_list = [d for d in os.listdir(model_path) if os.path.isdir(os.path.join(model_path, d))] # 列出目录

        model_name = dir_list[0]
        model_path = os.path.join(model_path, model_name) # 选择第一个模型


        self.ocr = PaddleOCR(
            device="cpu",
            use_doc_orientation_classify=False,     # 文档方向分类模型
            use_doc_unwarping=False,                # 文本图像矫正模型
            use_textline_orientation=False,         # 文本行方向分类模型

            text_recognition_model_name=model_name,
            text_recognition_model_dir=model_path
        )

        self._last_image_path = None
        self._last_target = None
        self._last_exact = None
        self._last_matches = None


    @timeit
    def get_all_text_positions(self,img_path):
        """获取全部文本坐标信息"""

        self.image = cv2.imread(img_path)

        self.result = self.ocr.predict(self.image)
        self.result = self.result[0]

        positions = []
        for text, poly in zip(self.result["rec_texts"], self.result["rec_polys"]):
            x_coords = [p[0] for p in poly]         # 提取所有 x 坐标   
            y_coords = [p[1] for p in poly]         # 提取所有 y 坐标
            
            positions.append({
                "text": text,
                "top_left": (min(x_coords), min(y_coords)),
                "top_right": (max(x_coords), min(y_coords)),
                "bottom_left": (min(x_coords), max(y_coords)),
                "bottom_right": (max(x_coords), max(y_coords)),
                "center": ((min(x_coords) + max(x_coords))//2, 
                          (min(y_coords) + max(y_coords))//2)
            })
        # print(positions)
        return positions
    
    @timeit
    def match_text(self,image_path,target_text, exact_match=False):
        """
        匹配文本，返回匹配坐标信息列表

        参数：
            image_path: 图片路径
            target_text: 目标文本
            exact_match: 是否精确匹配，默认False

        返回：
        匹配坐标信息列表，格式为：
        [
            {
                "text": "匹配文本",
                "top_left": (x1, y1),
                "top_right": (x2, y1),
                "bottom_left": (x1, y2),
                "bottom_right": (x2, y2),
                "center": ((x1+x2)//2, (y1+y2)//2)
            },
           ...
        ]
        """
        if (
            self._last_image_path == image_path
            and self._last_target == target_text
            and self._last_exact == exact_match
            and self._last_matches is not None
        ):
            return self._last_matches
        

        text_position_list = self.get_all_text_positions(image_path)
        if exact_match:
            data = [datas for datas in text_position_list if datas["text"] == target_text]

        else:
            pattern = re.compile(target_text, re.IGNORECASE)  # 忽略大小写
            data = [datas for datas in text_position_list if pattern.search(datas["text"])]

        # 写缓存
        self._last_image_path = image_path
        self._last_target = target_text
        self._last_exact = exact_match
        self._last_matches = data

        return data
        
    def save_result_image(self, output_path,color=(0, 255, 0), thickness=2):
        """
        保存识别结果图片

        参数：  
            output_path: 保存路径
            color: 边框颜色，默认为(0, 255, 0)
            thickness: 边框粗细，默认为2
        """
        if self._last_matches is None:
            raise ValueError("请先调用 match_text() 进行文本匹配。")
        
        img = self.image.copy()
        for item in self._last_matches:
            cv2.rectangle(img, item["top_left"], item["bottom_right"], color, thickness)
            cv2.circle(img, item["center"], 3, (0, 0, 255), -1)
        return cv2.imwrite(output_path, img)
    

    @timeit
    def show_result_image(self, display_time:int=10):
        """
        显示识别结果图片

        参数:
            display_time: 显示时间，单位秒，默认为10
        """
        if self._last_matches is None:
            raise ValueError("请先调用 match_text() 进行文本匹配。")
        img = self.image.copy()


        # 绘制所有匹配结果
        for item in self._last_matches:
            cv2.rectangle(img, item["top_left"], item["bottom_right"], (0, 255, 0), 2)
        
        # 创建窗口并显示
        window_name = "OCR_result"
        cv2.namedWindow(window_name, cv2.WINDOW_NORMAL)
        cv2.imshow(window_name, img)
        
        # 自动关闭实现
        start_time = time.time()
        while True:
                # 检查是否超时
                if time.time() - start_time >= display_time:
                    break
                    
                # 检查窗口是否仍然存在
                try:
                    if cv2.getWindowProperty(window_name, cv2.WND_PROP_VISIBLE) < 1:
                        break
                except:
                    break
                    
                # 检查按键
                if cv2.waitKey(100) != -1:
                    break
            
        # 安全关闭窗口（关键修正点）
        try:
            cv2.destroyWindow(window_name)  # 必须传入窗口名称
        except:
            pass
        
        # 清理OpenCV资源
        cv2.waitKey(1)
        cv2.destroyAllWindows()



    

if __name__ == '__main__':

    currment_dir = os.path.dirname(__file__)

    img_path = os.path.join(currment_dir, "lastlogin.png")
    target_text = "上次登录"

    ocr = OCR()
    # 方法1：识别全部文本
    data = ocr.get_all_text_positions(img_path) 
    print(data)
    





    # 方法2：根据目标文本获取匹配坐标信息列表
    matches = ocr.match_text(img_path,target_text)
    for m in matches:
        print(f"文本: {m['text']}")
        print(f"中心点: {m['center']}")
    #     print(f"左上角: {m['top_left']}")
    #     print(f"右上角: {m['top_right']}")
    #     print(f"左下角: {m['bottom_left']}")
    #     print(f"右下角: {m['bottom_right']}")

    # 2. 保存识别结果图片
    # output_path = r'E:\A1myProject\python\UiAuto\ocr\ocr_result1111.png'
    # ocr.save_result_image(output_path)

    # 显示识别结果图片，10s后自动关闭
    ocr.show_result_image(display_time=10)