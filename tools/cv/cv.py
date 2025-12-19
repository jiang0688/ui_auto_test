import cv2
import numpy as np
from typing import Tuple, List, Optional, Dict, Any
import os


def enhance_image(image: np.ndarray) -> np.ndarray:
    """
    增强图像以提高特征点检测效果
    """
    # 转换为灰度图
    gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
    
    # 自适应直方图均衡化
    clahe = cv2.createCLAHE(clipLimit=2.0, tileGridSize=(8,8))
    gray = clahe.apply(gray)
    
    # 高斯模糊去噪
    gray = cv2.GaussianBlur(gray, (3, 3), 0)
    
    return gray

def detect_features(image: np.ndarray, method: str = 'sift') -> Tuple[np.ndarray, List]:
    """
    使用多个特征检测器检测特征点
    
    Args:
        image: 输入图像
        method: 特征检测方法,可选'sift'、'orb'、'akaze'
        
    Returns:
        descriptors: 特征描述符
        keypoints: 关键点列表
    """
    if method == 'sift':
        # SIFT检测器
        detector = cv2.SIFT_create(
            nfeatures=0,
            nOctaveLayers=5,
            contrastThreshold=0.01,
            edgeThreshold=15
        )
    elif method == 'orb':
        # ORB检测器
        detector = cv2.ORB_create(
            nfeatures=2000,
            scaleFactor=1.2,
            nlevels=8,
            edgeThreshold=31,
            firstLevel=0,
            WTA_K=2,
            scoreType=cv2.ORB_HARRIS_SCORE,
            patchSize=31,
            fastThreshold=20
        )
    elif method == 'akaze':
        # AKAZE检测器
        detector = cv2.AKAZE_create(
            descriptor_type=cv2.AKAZE_DESCRIPTOR_MLDB,
            descriptor_size=0,
            descriptor_channels=3,
            threshold=0.001,
            nOctaves=4,
            nOctaveLayers=4,
            diffusivity=cv2.KAZE_DIFF_PM_G2
        )
    else:
        raise ValueError(f"不支持的特征检测方法: {method}")
    
    # 检测关键点
    keypoints = detector.detect(image, None)
    
    # 计算描述符
    keypoints, descriptors = detector.compute(image, keypoints)
    
    return descriptors, keypoints


def match_features(desc1: np.ndarray, desc2: np.ndarray, method: str = 'sift', threshold: float = 0.7) -> List:
    """
    使用改进的特征匹配策略
    
    Args:
        desc1: 第一幅图像的特征描述符
        desc2: 第二幅图像的特征描述符
        method: 特征检测方法,可选'sift'、'orb'、'akaze'
        threshold: 比率测试阈值,默认0.7
        
    Returns:
        good_matches: 好的匹配点列表
    """
    if desc1 is None or desc2 is None:
        return []
        
    if method == 'sift':
        # SIFT使用FLANN匹配器
        FLANN_INDEX_KDTREE = 1
        index_params = dict(algorithm=FLANN_INDEX_KDTREE, trees=10)
        search_params = dict(checks=150)
        matcher = cv2.FlannBasedMatcher(index_params, search_params)
    else:
        # ORB和AKAZE使用暴力匹配
        if method == 'orb':
            matcher = cv2.BFMatcher(cv2.NORM_HAMMING, crossCheck=False)
        else:
            matcher = cv2.BFMatcher(cv2.NORM_HAMMING2, crossCheck=False)
    
    # 对两幅图像进行双向匹配
    matches1 = matcher.knnMatch(desc1, desc2, k=2)
    matches2 = matcher.knnMatch(desc2, desc1, k=2)
    
    # 应用比率测试
    good_matches1 = []
    for m, n in matches1:
        if m.distance < threshold * n.distance:
            good_matches1.append(m)
            
    good_matches2 = []
    for m, n in matches2:
        if m.distance < threshold * n.distance:
            good_matches2.append(m)
    
    # 交叉检查
    good_matches = []
    for match1 in good_matches1:
        for match2 in good_matches2:
            if match1.queryIdx == match2.trainIdx and match1.trainIdx == match2.queryIdx:
                good_matches.append(match1)
                break
                
    return good_matches


def calculate_confidence(matches: List, mask: np.ndarray, H: np.ndarray, src_pts: np.ndarray, dst_pts: np.ndarray) -> float:
    """
    计算匹配置信度
    参考aircv项目的方法，使用有效匹配点数量与总特征点数量的比值
    """
    if len(matches) == 0:
        return 0.0
        
    # 计算内点数量
    inliers = np.count_nonzero(mask)
    
    # 计算匹配点的距离误差
    if H is not None and inliers >= 4:
        # 计算投影误差
        dst_pts_projected = cv2.perspectiveTransform(src_pts, H)
        errors = np.sqrt(np.sum((dst_pts - dst_pts_projected) ** 2, axis=2))
        avg_error = np.mean(errors[mask.ravel() == 1])
        
        # 根据投影误差调整置信度
        error_weight = np.exp(-avg_error / 10.0)  # 误差越大，权重越小
    else:
        error_weight = 0.5

    # 计算最终置信度
    confidence = (inliers / len(matches)) * error_weight
    
    # print(f"匹配质量分析:")
    # print(f"- 总匹配点数: {len(matches)}")
    # print(f"- 内点数量: {inliers}")
    # print(f"- 误差权重: {error_weight:.4f}")
    # print(f"- 最终置信度: {confidence:.4f}")
    
    return float(confidence)

def sort_points(points):
    """
    对四个角点进行排序，确保顺序为：左上、右上、右下、左下
    """
    # 转换为numpy数组
    pts = np.array(points)
    
    # 计算质心
    center = np.mean(pts, axis=0)
    
    # 根据点到质心的角度排序
    angles = np.arctan2(pts[:, 1] - center[1], pts[:, 0] - center[0])
    sorted_idx = np.argsort(angles)
    sorted_points = pts[sorted_idx]
    
    # 找到最上面的点的索引
    top_idx = np.argmin(sorted_points[:, 1])
    
    # 重新排序，使最上面的点为起点
    sorted_points = np.roll(sorted_points, -top_idx, axis=0)
    
    return sorted_points.tolist()


def validate_transformed_shape(points, original_shape) -> bool:
    """
    验证变换后的形状是否合理
    """
    # 计算变换后的宽高比
    width = max(
        np.linalg.norm(np.array(points[1]) - np.array(points[0])),
        np.linalg.norm(np.array(points[2]) - np.array(points[3]))
    )
    height = max(
        np.linalg.norm(np.array(points[3]) - np.array(points[0])),
        np.linalg.norm(np.array(points[2]) - np.array(points[1]))
    )
    
    if width == 0 or height == 0:
        return False
        
    # 计算原始宽高比
    original_ratio = original_shape[1] / original_shape[0]
    transformed_ratio = width / height
    
    # 允许的宽高比变化范围
    ratio_tolerance = 0.2
    
    # 检查宽高比是否在允许范围内
    if abs(transformed_ratio - original_ratio) / original_ratio > ratio_tolerance:
        # print(f"宽高比异常 - 原始: {original_ratio:.2f}, 变换后: {transformed_ratio:.2f}")
        return False
        
    # 检查面积变化是否合理
    original_area = original_shape[0] * original_shape[1]
    transformed_area = width * height
    area_ratio = transformed_area / original_area
    
    # 允许的面积变化范围
    if area_ratio < 0.5 or area_ratio > 2.0:
        print(f"面积变化异常 - 比例: {area_ratio:.2f}")
        return False
        
    return True


def calculate_center_point(points):
    """
    计算四边形的精确中心点
    
    Args:
        points: 四边形的顶点坐标列表 [[x1,y1], [x2,y2], [x3,y3], [x4,y4]]
        
    Returns:
        (center_x, center_y): 中心点坐标
    """
    # 首先对点进行排序
    sorted_pts = sort_points(points)
    pts = np.array(sorted_pts)
    
    # 计算对角线交点
    x1, y1 = pts[0]  # 左上
    x2, y2 = pts[2]  # 右下
    x3, y3 = pts[1]  # 右上
    x4, y4 = pts[3]  # 左下
    
    # 计算对角线交点
    denominator = (x1 - x2) * (y3 - y4) - (y1 - y2) * (x3 - x4)
    if abs(denominator) < 1e-10:  # 防止除以零
        # 如果对角线平行，使用中点
        center_x = np.mean(pts[:, 0])
        center_y = np.mean(pts[:, 1])
    else:
        # 计算对角线交点
        px = ((x1 * y2 - y1 * x2) * (x3 - x4) - (x1 - x2) * (x3 * y4 - y3 * x4)) / denominator
        py = ((x1 * y2 - y1 * x2) * (y3 - y4) - (y1 - y2) * (x3 * y4 - y3 * x4)) / denominator
        center_x = px
        center_y = py
    
    return center_x, center_y


def try_template_matching(screenshot: np.ndarray, target: np.ndarray, threshold: float = 0.8) -> Optional[Dict[str, Any]]:
    """
    使用改进的模板匹配方法
    """
    # 转换为灰度图
    if len(screenshot.shape) == 3:
        gray_screenshot = cv2.cvtColor(screenshot, cv2.COLOR_BGR2GRAY)
    else:
        gray_screenshot = screenshot.copy()
        
    if len(target.shape) == 3:
        gray_target = cv2.cvtColor(target, cv2.COLOR_BGR2GRAY)
    else:
        gray_target = target.copy()
    
    # 使用更密集的缩放步长
    scales = np.linspace(0.5, 1.5, 21)  # 0.5到1.5之间21个尺度
    best_result = None
    best_confidence = -1
    
    # 尝试多种模板匹配方法
    methods = [
        (cv2.TM_CCOEFF_NORMED, 1.0),
        (cv2.TM_CCORR_NORMED, 0.9),  # 相关系数法权重略低
        (cv2.TM_SQDIFF_NORMED, 0.8)  # 平方差匹配法权重最低
    ]
    
    for scale in scales:
        # 缩放目标图像
        scaled_w = int(target.shape[1] * scale)
        scaled_h = int(target.shape[0] * scale)
        scaled_target = cv2.resize(gray_target, (scaled_w, scaled_h))
        
        for method, weight in methods:
            if method == cv2.TM_SQDIFF_NORMED:
                result = 1 - cv2.matchTemplate(gray_screenshot, scaled_target, method)
            else:
                result = cv2.matchTemplate(gray_screenshot, scaled_target, method)
                
            min_val, max_val, min_loc, max_loc = cv2.minMaxLoc(result)
            
            # 加权计算置信度
            confidence = max_val * weight
            
            if confidence > best_confidence:
                best_confidence = confidence
                
                # 计算矩形框的四个角点
                top_left = max_loc
                bottom_right = (top_left[0] + scaled_w, top_left[1] + scaled_h)
                
                # 计算四个角点坐标
                points = [
                    [top_left[0], top_left[1]],  # 左上
                    [bottom_right[0], top_left[1]],  # 右上
                    [bottom_right[0], bottom_right[1]],  # 右下
                    [top_left[0], bottom_right[1]]  # 左下
                ]
                
                # 计算中心点
                center_x = (top_left[0] + bottom_right[0]) // 2
                center_y = (top_left[1] + bottom_right[1]) // 2
                
                best_result = {
                    "center": [int(center_x), int(center_y)],
                    "rectangle": [[int(x), int(y)] for x, y in points],
                    "confidence": float(confidence),
                    "scale": scale,
                    "method_type": {
                        cv2.TM_CCOEFF_NORMED: "TM_CCOEFF_NORMED",
                        cv2.TM_CCORR_NORMED: "TM_CCORR_NORMED",
                        cv2.TM_SQDIFF_NORMED: "TM_SQDIFF_NORMED"
                    }[method]
                }
    
    if best_result and best_result["confidence"] >= threshold:
        # print(f"模板匹配结果:")
        # print(f"- 置信度: {best_result['confidence']:.4f}")
        # print(f"- 最佳缩放比例: {best_result['scale']:.2f}")
        # print(f"- 使用的方法: {best_result['method_type']}")
        return best_result
    
    return None






def match_template(screenshot_path, target_path, threshold: float = 0.85, method: str = 'sift') -> Optional[Dict[str, Any]]:
    """
    使用改进的混合匹配策略进行图像匹配
    """
    screenshot = cv2.imread(screenshot_path)
    target = cv2.imread(target_path)

    # print(f"开始匹配，图片尺寸 - 截图: {screenshot.shape}, 目标图: {target.shape}")
    
    # 1. 特征点匹配
    feature_result = None
    try:
        # 增强图像
        screenshot_enhanced = enhance_image(screenshot)
        target_enhanced = enhance_image(target)
        
        # 检测特征点
        desc1, kp1 = detect_features(target_enhanced, method=method)
        desc2, kp2 = detect_features(screenshot_enhanced, method=method)
        
        # print(f"检测到的特征点数量 - 目标图: {len(kp1)}, 截图: {len(kp2)}")
        
        if len(kp1) >= 4 and len(kp2) >= 4:
            # 特征匹配
            matches = match_features(desc1, desc2, method=method, threshold=0.6)  # 降低特征匹配阈值
            # print(f"匹配的特征点数量: {len(matches)}")
            
            if len(matches) >= 4:
                # 获取匹配点坐标
                src_pts = np.float32([kp1[m.queryIdx].pt for m in matches]).reshape(-1, 1, 2)
                dst_pts = np.float32([kp2[m.trainIdx].pt for m in matches]).reshape(-1, 1, 2)
                
                # 使用RANSAC算法估计变换矩阵
                H, mask = cv2.findHomography(src_pts, dst_pts, cv2.RANSAC, 5.0)
                
                if H is not None:
                    # 计算置信度
                    confidence = calculate_confidence(matches, mask, H, src_pts, dst_pts)
                    # print(f"特征点匹配置信度: {confidence:.4f}")
                    
                    if confidence >= threshold * 0.7:  # 降低特征点匹配的阈值要求
                        # 获取目标区域的边界框
                        h, w = target.shape[:2]
                        pts = np.float32([[0, 0], [w-1, 0], [w-1, h-1], [0, h-1]]).reshape(-1, 1, 2)
                        dst = cv2.perspectiveTransform(pts, H)
                        
                        # 整理角点并计算中心点
                        points = [[p[0][0], p[0][1]] for p in dst]
                        sorted_points = sort_points(points)
                        
                        # 验证变换后的形状是否合理
                        if validate_transformed_shape(sorted_points, target.shape):
                            center_x, center_y = calculate_center_point(sorted_points)
                            feature_result = {
                                "center": [int(center_x), int(center_y)],
                                "rectangle": [[int(x), int(y)] for x, y in sorted_points],
                                "confidence": confidence,
                                "method": "feature"
                            }
    except Exception as e:
        print(f"特征点匹配出错: {str(e)}")
    
    # 2. 模板匹配
    template_result = try_template_matching(screenshot, target, threshold=threshold)
    if template_result:
        template_result["method"] = "template"
    
    # 3. 结果选择
    if feature_result and template_result:
        # 根据置信度加权选择
        feature_weight = feature_result["confidence"]
        template_weight = template_result["confidence"] * 1.2  # 给模板匹配结果略高的权重
        
        if feature_weight > template_weight:
            print("使用特征点匹配结果（置信度更高）")
            return feature_result
        else:
            print("使用模板匹配结果（置信度更高）")
            return template_result
    elif feature_result:
        return feature_result
    elif template_result:
        return template_result
    
    print("未找到匹配结果")
    return None




if __name__ == '__main__':

    currment_dir = os.path.dirname(os.path.abspath(__file__))
    target = os.path.join(currment_dir, "mail.png")
    background = os.path.join(currment_dir, "background1.png")



    result = match_template(background, target, threshold=0.85, method='orb')
    # 4. 处理结果
    if result:
        print("匹配成功！")
        print(f"中心坐标: {result['center']}")
        print(f"矩形角点: {result['rectangle']}")
        print(f"置信度: {result['confidence']:.2f}")
        print(f"匹配方法: {result['method']}")

        # 可视化结果（可选）
        # 在截图上绘制矩形和中心点
        s = cv2.imread(background)
        pts = np.array(result["rectangle"], dtype=np.int32)
        cv2.polylines(s, [pts], isClosed=True, color=(0, 255, 0), thickness=2)
        cv2.circle(s, tuple(result["center"]), 5, (0, 0, 255), -1)
        
        # 显示结果
        cv2.namedWindow("Match Result", cv2.WINDOW_NORMAL)  # 允许手动调整窗口大小
        cv2.imshow("Match Result", s)
        cv2.waitKey(0)
        cv2.destroyAllWindows()
    else:
        print("匹配失败！")
