import cv2
import numpy as np

# 讀取圖像
image = cv2.imread('chessboard7.jpg')
gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)

# 預處理：模糊處理和邊緣檢測
blurred = cv2.GaussianBlur(gray, (5, 5), 0)
edges = cv2.Canny(blurred, 60, 150)

# 找出所有輪廓
contours, _ = cv2.findContours(edges, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)

# 找到棋盤輪廓
chessboard_contour = None
for contour in contours:
    approx = cv2.approxPolyDP(contour, 0.02 * cv2.arcLength(contour, True), True)
    if len(approx) == 4:
        x, y, w, h = cv2.boundingRect(approx)
        aspect_ratio = w / float(h)
        if 0.9 < aspect_ratio < 1.1 and w > 100 and h > 100:
            chessboard_contour = approx
            break

if chessboard_contour is None:
    print("未找到棋盤輪廓，請檢查圖片或調整參數！")
else:
    points = chessboard_contour.reshape(4, 2)
    points = points[np.argsort(points[:, 1])]
    top_two = points[:2][np.argsort(points[:2, 0])]
    bottom_two = points[2:][np.argsort(points[2:, 0])]
    top_left, top_right = top_two
    bottom_left, bottom_right = bottom_two

    src_points = np.array([top_left, top_right, bottom_right, bottom_left], dtype="float32")
    dest_points = np.array([[0, 0], [800, 0], [800, 800], [0, 800]], dtype="float32")
    matrix = cv2.getPerspectiveTransform(src_points, dest_points)
    warped = cv2.warpPerspective(image, matrix, (800, 800))

    # 分割棋盤
    square_size = warped.shape[0] // 8
    chessboard_status = []

    for row in range(8):
        row_status = []
        for col in range(8):
            x_start, y_start = col * square_size, row * square_size
            x_end, y_end = x_start + square_size, y_start + square_size
            square = warped[y_start:y_end, x_start:x_end]

            # 預處理
            square_gray = cv2.cvtColor(square, cv2.COLOR_BGR2GRAY)
            binary = cv2.adaptiveThreshold(square_gray, 255, cv2.ADAPTIVE_THRESH_GAUSSIAN_C,
                                           cv2.THRESH_BINARY_INV, 15, 5)
            edges = cv2.Canny(binary, 60, 150)
            black_mask = cv2.inRange(square, (0, 0, 0), (40, 40, 40))
            white_mask = cv2.inRange(square, (220, 220, 220), (255, 255, 255))

            # 特徵提取
            mean_val = np.mean(square_gray)
            std_dev = np.std(square_gray)
            circles = cv2.HoughCircles(square_gray, cv2.HOUGH_GRADIENT, dp=1.5, minDist=30,
                                       param1=100, param2=30, minRadius=15, maxRadius=25)

            # 判斷是否有棋子
            if (mean_val < 200 and std_dev > 20) or circles is not None or \
               (cv2.countNonZero(black_mask) > 500 or cv2.countNonZero(white_mask) > 500):
                row_status.append(1)
                cv2.rectangle(warped, (x_start, y_start), (x_end, y_end), (0, 255, 0), 2)
            else:
                row_status.append(0)
        chessboard_status.append(row_status)

    for row in chessboard_status:
        print(row)

    cv2.imshow("Detected Chessboard", warped)
    cv2.waitKey(0)
    cv2.destroyAllWindows()
