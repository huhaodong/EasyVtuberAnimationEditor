# 导入 numpy 和 matplotlib 库
import numpy as np
import matplotlib.pyplot as plt

# 定义一个三次贝塞尔缓动函数
def cubic_bezier(t, P0, P1, P2, P3):
    # 使用三次贝塞尔缓动函数的数学表达式
    return (1-t)**3*P0 + 3*(1-t)**2*t*P1 + 3*(1-t)*t**2*P2 + t**3*P3

# 定义四个控制点的坐标
P0 = np.array([0, 0]) # 起始点
P1 = np.array([1, 2]) # 第一个控制点
P2 = np.array([2, -1]) # 第二个控制点
P3 = np.array([3, 1]) # 终止点

# 定义参数 t 的范围和步长
t = 1

# 计算输出进度的值
f = cubic_bezier(t, P0, P1, P2, P3)

# 绘制曲线图
plt.plot(t, f, 'r', linewidth=2) # 红色的曲线
plt.scatter(P0[0], P0[1], color='b') # 蓝色的起始点
plt.scatter(P3[0], P3[1], color='b') # 蓝色的终止点
plt.scatter(P1[0], P1[1], color='g') # 绿色的第一个控制点
plt.scatter(P2[0], P2[1], color='g') # 绿色的第二个控制点
plt.title('Cubic Bezier Easing Function') # 标题
plt.xlabel('Input Progress') # x 轴标签
plt.ylabel('Output Progress') # y 轴标签
plt.grid() # 网格线
plt.show() # 显示图像
