# 导入wxPython库
import wx
import random

# 定义一个自定义的窗口类，继承自wx.Panel
class MyPanel(wx.Panel):

    def __init__(self, parent):
        # 调用父类的构造方法
        super().__init__(parent)

        # 设置窗口的背景颜色为白色
        self.SetBackgroundColour(wx.WHITE)

        # 创建一个字体对象，用于显示文本
        self.font = wx.Font(10, wx.FONTFAMILY_DEFAULT, wx.FONTSTYLE_NORMAL, wx.FONTWEIGHT_NORMAL)

        # 创建一个列表，用于存储10个圆点的坐标和半径
        self.circles = []

        # 生成10个随机的圆点
        for i in range(10):
            # 随机生成圆点的x坐标，范围是0到窗口的宽度
            x = random.randint(0, self.GetSize().width)
            # 随机生成圆点的y坐标，范围是0到窗口的高度
            y = random.randint(0, self.GetSize().height)
            # 设置圆点的半径为2
            r = 2
            # 将圆点的坐标和半径添加到列表中
            self.circles.append((x, y, r))

        # 绑定鼠标左键点击事件的处理函数
        self.Bind(wx.EVT_LEFT_DOWN, self.on_left_down)

        # 绑定窗口绘制事件的处理函数
        self.Bind(wx.EVT_PAINT, self.on_paint)

    # 定义鼠标左键点击事件的处理函数
    def on_left_down(self, event):
        # 获取鼠标点击的位置
        x, y = event.GetPosition()

        # 定义一个变量，用于记录是否点击了某个圆点
        hit = False

        # 遍历圆点列表
        for i, circle in enumerate(self.circles):
            # 获取圆点的坐标和半径
            cx, cy, cr = circle[:3]
            # 计算鼠标点击位置到圆点中心的距离
            distance = ((x - cx) ** 2 + (y - cy) ** 2) ** 0.5
            # 如果距离小于等于圆点的半径，说明点击了该圆点
            if distance <= cr:
                # 设置hit为True
                hit = True
                # 将该圆点的半径改为3，颜色改为绿色
                self.circles[i] = (cx, cy, 3, wx.GREEN)
                # 跳出循环
                # break
            # 否则，如果该圆点是绿色的，说明之前点击过该圆点
            elif len(circle) == 4 and circle[3] == wx.GREEN:
                # 将该圆点的半径恢复为2，颜色恢复为红色
                self.circles[i] = (cx, cy, 2, wx.RED)

        # 刷新窗口，触发绘制事件
        self.Refresh()

        # 创建一个绘图设备上下文对象，用于在窗口上绘制文本
        dc = wx.ClientDC(self)
        # 设置字体
        dc.SetFont(self.font)
        # 设置文本颜色为黑色
        dc.SetTextForeground(wx.BLACK)
        # 设置文本背景颜色为白色
        dc.SetTextBackground(wx.WHITE)

        # 如果点击了某个圆点
        if hit:
            # 在窗口的右上角打印该圆点的坐标
            text = f"({cx}, {cy})"
            # 计算文本的宽度和高度
            tw, th = dc.GetTextExtent(text)
            # 计算文本的位置，使其靠近窗口的右上角
            tx = self.GetSize().width - tw - 10
            ty = 10
            # 在窗口上绘制文本
            dc.DrawText(text, tx, ty)
        # 否则
        else:
            # 在窗口的右上角提示没有点中任何的点
            text = "没有点中任何的点"
            # 计算文本的宽度和高度
            tw, th = dc.GetTextExtent(text)
            # 计算文本的位置，使其靠近窗口的右上角
            tx = self.GetSize().width - tw - 10
            ty = 10
            # 在窗口上绘制文本
            dc.DrawText(text, tx, ty)

    # 定义窗口绘制事件的处理函数
    def on_paint(self, event):
        # 创建一个绘图设备上下文对象，用于在窗口上绘制图形
        dc = wx.PaintDC(self)
        # 设置画笔颜色为黑色
        dc.SetPen(wx.Pen(wx.BLACK))

        # 遍历圆点列表
        for circle in self.circles:
            # 获取圆点的坐标和半径
            x, y, r = circle[:3]
            # 如果圆点有颜色属性，设置画刷颜色为该颜色
            if len(circle) == 4:
                dc.SetBrush(wx.Brush(circle[3]))
            # 否则，设置画刷颜色为红色
            else:
                dc.SetBrush(wx.Brush(wx.RED))
            # 在窗口上绘制圆点
            dc.DrawCircle(x, y, r)


# 定义一个自定义的框架类，继承自wx.Frame
class MyFrame(wx.Frame):

    def __init__(self):
        # 调用父类的构造方法
        super().__init__(None, title="wxPython示例", size=(800, 600))

        # 创建一个自定义的窗口对象
        panel = MyPanel(self)

        # 显示框架
        self.Show()


# 创建一个应用对象
app = wx.App()
# 创建一个自定义的框架对象
frame = MyFrame()
# 进入应用的主事件循环
app.MainLoop()
