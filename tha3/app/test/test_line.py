# 导入matplotlib库，用于绘制函数图像
import matplotlib.pyplot as plt

# 定义一个函数，用于计算三次多项式的系数
def calculate_coefficients(x1, y1, x2, y2):
    # 建立四个方程
    equations = [
        [x1 ** 3, x1 ** 2, x1, 1, y1],
        [x2 ** 3, x2 ** 2, x2, 1, y2],
        [3 * x1 ** 2, 2 * x1, 1, 0, 0],
        [3 * x2 ** 2, 2 * x2, 1, 0, 0]
    ]
    # 用高斯消元法求解方程组
    for i in range(4):
        # 选取主元
        max_row = i
        for j in range(i + 1, 4):
            if abs(equations[j][i]) > abs(equations[max_row][i]):
                max_row = j
        # 交换行
        equations[i], equations[max_row] = equations[max_row], equations[i]
        # 消元
        for j in range(i + 1, 4):
            factor = equations[j][i] / equations[i][i]
            for k in range(i, 5):
                equations[j][k] -= factor * equations[i][k]
    # 回代
    coefficients = [0] * 4
    for i in range(3, -1, -1):
        coefficients[i] = equations[i][4] / equations[i][i]
        for j in range(i - 1, -1, -1):
            equations[j][4] -= coefficients[i] * equations[j][i]
    # 返回系数
    return coefficients

# 定义一个函数，用于计算三次多项式的值
def calculate_value(x, coefficients):
    # 使用霍纳法则
    y = 0
    for coefficient in coefficients:
        y = y * x + coefficient
    # 返回值
    return y

# 定义两个点的坐标
x1, y1 = 0, 0
x2, y2 = 1, 1

# 计算三次多项式的系数
a, b, c, d = calculate_coefficients(x1, y1, x2, y2)

# 打印三次多项式的方程
print(f"y = {a}x^3 + {b}x^2 + {c}x + {d}")

# 生成一些用于绘制的x和y的值
x_list = []
y_list = []
for i in range(101):
    x = i / 100
    y = calculate_value(x, [a, b, c, d])
    x_list.append(x)
    y_list.append(y)

# 绘制函数图像
plt.plot(x_list, y_list)
plt.xlabel("x")
plt.ylabel("y")
plt.title("A cubic polynomial function")
plt.show()
