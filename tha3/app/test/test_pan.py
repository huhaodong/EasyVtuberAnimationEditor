# 导入wxpython库
import wx

# 定义一个窗口类，继承自wx.Frame
class BezierFrame(wx.Frame):
    # 初始化方法
    def __init__(self, parent, title):
        # 调用父类的初始化方法
        wx.Frame.__init__(self, parent, title=title, size=(512, 512))
        # 创建一个画板，用于绘制图形
        self.panel = wx.Panel(self)
        # 绑定画板的绘制事件，当需要更新画板时，调用OnPaint方法
        self.panel.Bind(wx.EVT_PAINT, self.OnPaint)
        # 创建一个状态栏，用于显示提示信息
        self.CreateStatusBar()
        # 设置状态栏的文本
        self.SetStatusText("请在画板上点击四个点，以创建贝塞尔曲线的控制点")
        # 创建一个列表，用于存储用户点击的点的坐标
        self.points = []
        # 绑定画板的鼠标左键点击事件，当用户点击画板时，调用OnLeftDown方法
        self.panel.Bind(wx.EVT_LEFT_DOWN, self.OnLeftDown)

    # 定义OnPaint方法，用于绘制图形
    def OnPaint(self, event):
        # 创建一个绘图上下文对象，用于操作画板
        dc = wx.PaintDC(self.panel)
        # 创建一个图形上下文对象，用于创建和绘制贝塞尔曲线
        gc = wx.GraphicsContext.Create(dc)
        # 设置画笔的颜色和宽度
        dc.SetPen(wx.Pen("black", 2))
        # 绘制一个坐标系，原点在画板的中心，横轴和纵轴分别为512像素
        dc.DrawLine(25, 487, 512, 487) # 绘制横轴
        dc.DrawLine(25, 487, 25, 0) # 绘制纵轴
        # 设置字体的颜色和大小
        dc.SetTextForeground("black")
        dc.SetFont(wx.Font(10, wx.FONTFAMILY_DEFAULT, wx.FONTSTYLE_NORMAL, wx.FONTWEIGHT_NORMAL))
        # 在横轴上标注30个刻度，每个刻度代表一个单位长度
        for i in range(1, 31):
            # 计算每个刻度的横坐标，每个单位长度为16像素
            x = 25 + i * 16 
            # 绘制一个短线段，表示刻度
            dc.DrawLine(x, 487, x, 483)
            # 绘制一个文本，表示刻度的值
            dc.DrawText(str(i), x-3 , 490)
        # 如果用户已经点击了至少一个点
        if self.points:
            # 设置画笔的颜色和宽度
            dc.SetPen(wx.Pen("red", 2))
            # 设置画刷的颜色，用于填充圆形
            dc.SetBrush(wx.Brush("red"))
            # 遍历用户点击的点的坐标
            for x, y in self.points:
                # 绘制一个半径为2像素的圆形，表示控制点
                dc.DrawCircle(x, y, 2)
                # 如果用户已经点击了四个点
                if len(self.points) == 4:
                    # 创建一个图形路径对象，用于创建贝塞尔曲线
                    path = gc.CreatePath()
                    # 移动到第一个控制点的位置
                    path.MoveToPoint(self.points[0][0], self.points[0][1])
                    # 添加一条贝塞尔曲线，使用后三个控制点作为参数
                    path.AddCurveToPoint(self.points[1][0], self.points[1][1],
                                         self.points[2][0], self.points[2][1],
                                         self.points[3][0], self.points[3][1])
                    # 设置画笔的颜色和宽度
                    gc.SetPen(wx.Pen("blue", 2))
                    # 绘制图形路径，即贝塞尔曲线
                    gc.DrawPath(path)

    # 定义OnLeftDown方法，用于处理用户的鼠标左键点击事件
    def OnLeftDown(self, event):
        # 如果用户已经点击了四个点，不再响应点击事件
        if len(self.points) == 4:
            return
        # 获取用户点击的点的坐标
        x, y = event.GetPosition()
        # 将坐标添加到列表中
        self.points.append((x, y))
        # 如果用户已经点击了四个点
        if len(self.points) == 4:
            # 设置状态栏的文本
            self.SetStatusText("已创建贝塞尔曲线，你可以拖动控制点来编辑曲线的形状")
            # 创建四个拖动点对象，用于编辑控制点的位置
            self.drag_points = [DragPoint(self.panel, self, i) for i in range(4)]
        # 刷新画板，触发绘制事件
        self.panel.Refresh()

# 定义一个拖动点类，继承自wx.Window
class DragPoint(wx.Window):
    # 初始化方法
    def __init__(self, parent, frame, index):
        # 调用父类的初始化方法
        wx.Window.__init__(self, parent, size=(8, 8))
        # 设置窗口的背景颜色为绿色
        self.SetBackgroundColour("green")
        # 获取贝塞尔曲线窗口对象
        self.frame = frame
        # 获取控制点的索引
        self.index = index
        # 获取控制点的坐标
        self.x, self.y = self.frame.points[self.index]
        # 设置窗口的位置，使其与控制点重合  
        self.SetPosition((self.x - 4, self.y - 4))
        # 绑定窗口的鼠标左键按下事件，当用户按下鼠标左键时，调用OnLeftDown方法
        self.Bind(wx.EVT_LEFT_DOWN, self.OnLeftDown)
        # 绑定窗口的鼠标左键释放事件，当用户释放鼠标左键时，调用OnLeftUp方法
        self.Bind(wx.EVT_LEFT_UP, self.OnLeftUp)
        # 绑定窗口的鼠标移动事件，当用户移动鼠标时，调用OnMotion方法
        self.Bind(wx.EVT_MOTION, self.OnMotion)
        # 初始化一个标志，用于表示是否正在拖动
        self.dragging = False

    # 定义OnLeftDown方法，用于处理用户的鼠标左键按下事件
    def OnLeftDown(self, event):
        # 设置拖动标志为True
        self.dragging = True
        # 捕获鼠标，使其只能在当前窗口内移动
        self.CaptureMouse()

    # 定义OnLeftUp方法，用于处理用户的鼠标左键释放事件
    def OnLeftUp(self, event):
        # 如果正在拖动
        if self.dragging:
            # 释放鼠标，使其可以在任意窗口内移动
            self.ReleaseMouse()
            # 设置拖动标志为False
            self.dragging = False

    # 定义OnMotion方法，用于处理用户的鼠标移动事件
    def OnMotion(self, event):
        # 如果正在拖动
        if self.dragging:
            # 获取鼠标的当前位置
            x, y = event.GetPosition()
            # 计算鼠标相对于窗口的偏移量
            dx = x - 4
            dy = y - 4
            # 更新控制点的坐标
            self.x += dx
            self.y += dy
            # 更新窗口的位置，使其与控制点重合
            self.SetPosition((self.x - 4, self.y - 4))
            # 更新贝塞尔曲线窗口对象中的控制点列表
            self.frame.points[self.index] = (self.x, self.y)
            # 刷新贝塞尔曲线窗口的画板，触发绘制事件
            self.frame.panel.Refresh()

# 创建一个应用程序对象
app = wx.App()
# 创建一个贝塞尔曲线窗口对象
frame = BezierFrame(None, "贝塞尔曲线编辑器")
# 显示窗口
frame.Show()
# 运行应用程序
app.MainLoop()
