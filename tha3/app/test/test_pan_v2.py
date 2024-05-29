import wx
import math

# 定义一个贝塞尔曲线类
class BezierCurve:
    def __init__(self):
        # 初始化控制点列表和曲线点列表
        self.control_points = []
        self.curve_points = []

    def add_control_point(self, point):
        # 添加一个控制点
        self.control_points.append(point)
        # 重新计算曲线点
        self.calculate_curve_points()

    def move_control_point(self, index, point):
        # 移动一个控制点
        self.control_points[index] = point
        # 重新计算曲线点
        self.calculate_curve_points()

    def calculate_curve_points(self):
        # 计算曲线点
        self.curve_points = []
        # 如果控制点少于两个，无法生成曲线
        if len(self.control_points) < 2:
            return
        # 使用贝塞尔曲线的公式，对t从0到1进行采样，得到曲线上的点
        # 参考：https://en.wikipedia.org/wiki/B%C3%A9zier_curve#Generalization
        n = len(self.control_points) - 1 # n为控制点的个数减一
        m = 100 # m为采样的次数
        for i in range(m + 1):
            t = i / m # t为当前的采样比例
            x = 0 # x为当前的曲线点的横坐标
            y = 0 # y为当前的曲线点的纵坐标
            for j in range(n + 1):
                # 使用二项式系数和伯恩斯坦基函数计算当前控制点对曲线点的贡献
                # 参考：https://en.wikipedia.org/wiki/Binomial_coefficient
                # 参考：https://en.wikipedia.org/wiki/Bernstein_polynomial
                c = math.factorial(n) / (math.factorial(j) * math.factorial(n - j)) # c为二项式系数
                b = (t ** j) * ((1 - t) ** (n - j)) # b为伯恩斯坦基函数
                x += c * b * self.control_points[j][0] # 累加横坐标
                y += c * b * self.control_points[j][1] # 累加纵坐标
            # 将曲线点添加到列表中
            self.curve_points.append((x, y))

    def get_curve_point(self, x):
        # 根据给定的x值，返回曲线上对应的y值，如果不存在则返回None
        # 使用二分查找的方法，在曲线点列表中寻找最接近的点
        # 参考：https://en.wikipedia.org/wiki/Binary_search_algorithm
        low = 0 # low为查找的下界
        high = len(self.curve_points) - 1 # high为查找的上界
        while low <= high:
            mid = (low + high) // 2 # mid为查找的中间位置
            mid_x = self.curve_points[mid][0] # mid_x为中间位置的横坐标
            if mid_x == x:
                # 如果找到了精确的匹配，返回对应的纵坐标
                return self.curve_points[mid][1]
            elif mid_x < x:
                # 如果中间位置的横坐标小于目标值，缩小查找范围到右半部分
                low = mid + 1
            else:
                # 如果中间位置的横坐标大于目标值，缩小查找范围到左半部分
                high = mid - 1
        # 如果没有找到精确的匹配，返回None
        return None

# 定义一个贝塞尔曲线编辑器类
class BezierEditor(wx.Panel):
    def __init__(self, parent):
        # 调用父类的构造函数
        wx.Panel.__init__(self, parent)
        # 设置背景颜色为白色
        self.SetBackgroundColour(wx.WHITE)
        # 创建一个贝塞尔曲线对象
        self.curve = BezierCurve()
        # 绑定鼠标和绘图事件
        self.Bind(wx.EVT_PAINT, self.OnPaint)
        self.Bind(wx.EVT_LEFT_DOWN, self.OnLeftDown)
        self.Bind(wx.EVT_LEFT_UP, self.OnLeftUp)
        self.Bind(wx.EVT_MOTION, self.OnMotion)
        self.Bind(wx.EVT_RIGHT_DOWN, self.OnRightDown)
        # 初始化鼠标状态
        self.dragging = False # 是否正在拖动控制点
        self.drag_index = -1 # 正在拖动的控制点的索引
        self.drag_offset = (0, 0) # 鼠标相对于控制点的偏移量

    def OnPaint(self, event):
        # 处理绘图事件
        # 创建一个绘图上下文对象
        dc = wx.PaintDC(self)
        # 设置画笔和画刷的颜色和样式
        dc.SetPen(wx.Pen(wx.BLACK, 2)) # 画笔为黑色，粗细为2
        dc.SetBrush(wx.Brush(wx.RED)) # 画刷为红色
        # 绘制贝塞尔曲线的控制点和曲线点
        for point in self.curve.control_points:
            # 绘制一个半径为5的圆形作为控制点
            dc.DrawCircle(point[0], point[1], 5)
        for point in self.curve.curve_points:
            # 绘制一个半径为1的圆形作为曲线点
            dc.DrawCircle(point[0], point[1], 1)

    def OnLeftDown(self, event):
        # 处理鼠标左键按下事件
        # 获取鼠标的位置
        x, y = event.GetPosition()
        # 遍历贝塞尔曲线的控制点，判断是否有被点击的
        for i, point in enumerate(self.curve.control_points):
            # 计算鼠标位置和控制点位置的距离
            distance = math.sqrt((x - point[0]) ** 2 + (y - point[1]) ** 2)
            # 如果距离小于5，说明鼠标点击了该控制点
            if distance < 5:
                # 设置拖动状态为True
                self.dragging = True
                # 设置拖动的控制点的索引
                self.drag_index = i
                # 设置鼠标相对于控制点的偏移量
                self.drag_offset = (x - point[0], y - point[1])
                # 结束遍历
                break
        # 如果没有被点击的控制点，说明鼠标点击了空白处
        else:
            # 向贝塞尔曲线添加一个新的控制点
            self.curve.add_control_point((x, y))
            # 刷新窗口，重新绘制曲线
            self.Refresh()

    def OnLeftUp(self, event):
        # 处理鼠标左键松开事件
        # 设置拖动状态为False
        self.dragging = False
                # 设置拖动的控制点的索引为-1
        self.drag_index = -1
        # 设置鼠标相对于控制点的偏移量为(0, 0)
        self.drag_offset = (0, 0)

    def OnMotion(self, event):
        # 处理鼠标移动事件
        # 如果正在拖动控制点
        if self.dragging:
            # 获取鼠标的位置
            x, y = event.GetPosition()
            # 计算控制点的新位置，加上鼠标的偏移量
            new_x = x - self.drag_offset[0]
            new_y = y - self.drag_offset[1]
            # 移动控制点
            self.curve.move_control_point(self.drag_index, (new_x, new_y))
            # 刷新窗口，重新绘制曲线
            self.Refresh()

    def OnRightDown(self, event):
        # 处理鼠标右键按下事件
        # 获取鼠标的位置
        x, y = event.GetPosition()
        # 遍历贝塞尔曲线的控制点，判断是否有被点击的
        for i, point in enumerate(self.curve.control_points):
            # 计算鼠标位置和控制点位置的距离
            distance = math.sqrt((x - point[0]) ** 2 + (y - point[1]) ** 2)
            # 如果距离小于5，说明鼠标点击了该控制点
            if distance < 5:
                # 从贝塞尔曲线的控制点列表中删除该控制点
                del self.curve.control_points[i]
                # 重新计算曲线点
                self.curve.calculate_curve_points()
                # 刷新窗口，重新绘制曲线
                self.Refresh()
                # 结束遍历
                break

# 定义一个贝塞尔曲线窗口类
class BezierFrame(wx.Frame):
    def __init__(self, parent, title):
        # 调用父类的构造函数
        wx.Frame.__init__(self, parent, title=title, size=(800, 600))
        # 创建一个贝塞尔曲线编辑器对象
        self.editor = BezierEditor(self)
        # 创建一个水平的框架布局
        self.sizer = wx.BoxSizer(wx.HORIZONTAL)
        # 将编辑器添加到布局中，占据4/5的空间
        self.sizer.Add(self.editor, 4, wx.EXPAND)
        # 创建一个垂直的框架布局
        self.v_sizer = wx.BoxSizer(wx.VERTICAL)
        # 创建一个静态文本，用于提示用户输入x轴的值
        self.label = wx.StaticText(self, label="请输入x轴的值：")
        # 将静态文本添加到垂直布局中
        self.v_sizer.Add(self.label, 0, wx.ALIGN_CENTER | wx.ALL, 10)
        # 创建一个文本框，用于输入x轴的值
        self.text = wx.TextCtrl(self)
        # 将文本框添加到垂直布局中
        self.v_sizer.Add(self.text, 0, wx.ALIGN_CENTER | wx.ALL, 10)
        # 创建一个按钮，用于输出y轴的值
        self.button = wx.Button(self, label="输出y轴的值")
        # 将按钮添加到垂直布局中
        self.v_sizer.Add(self.button, 0, wx.ALIGN_CENTER | wx.ALL, 10)
        # 绑定按钮的点击事件
        self.button.Bind(wx.EVT_BUTTON, self.OnButton)
        # 将垂直布局添加到水平布局中，占据1/5的空间
        self.sizer.Add(self.v_sizer, 1, wx.EXPAND)
        # 设置窗口的布局
        self.SetSizer(self.sizer)
        # 显示窗口
        self.Show(True)

    def OnButton(self, event):
        # 处理按钮的点击事件
        # 获取文本框中的内容
        x = self.text.GetValue()
        # 尝试将内容转换为浮点数
        try:
            x = float(x)
        except ValueError:
            # 如果转换失败，弹出一个错误对话框
            wx.MessageBox("请输入一个有效的数字", "错误", wx.OK | wx.ICON_ERROR)
            return
        # 调用贝塞尔曲线对象的方法，根据x值获取y值
        y = self.curve.get_curve_point(x)
        # 如果y值存在
        if y is not None:
            # 弹出一个信息对话框，显示y值
            wx.MessageBox(f"y轴的值为：{y}", "信息", wx.OK | wx.ICON_INFORMATION)
        else:
            # 如果y值不存在，弹出一个警告对话框
            wx.MessageBox("x轴的值超出了曲线的范围", "警告", wx.OK | wx.ICON_WARNING)

# 创建一个应用程序对象
app = wx.App(False)
# 创建一个贝塞尔曲线窗口对象
frame = BezierFrame(None, "贝塞尔曲线编辑器")
# 进入应用程序的主循环
app.MainLoop()
