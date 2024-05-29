import wx
import math

class MyPanel(wx.Panel):
    def __init__(self, parent):
        wx.Panel.__init__(self, parent)
        self.circle_x = 100 # 圆点的x坐标
        self.circle_y = 100 # 圆点的y坐标
        self.circle_r = 2 # 圆点的半径
        self.Bind(wx.EVT_PAINT, self.OnPaint) # 绑定绘图事件
        self.Bind(wx.EVT_LEFT_UP, self.OnClick) # 绑定鼠标左键点击事件

    def OnPaint(self, event):
        dc = wx.PaintDC(self) # 创建一个设备上下文
        dc.SetBrush(wx.Brush(wx.Colour(255, 0, 0))) # 设置画刷颜色为红色
        dc.DrawCircle(self.circle_x, self.circle_y, self.circle_r) # 在panel上绘制一个圆点

    def OnClick(self, event):
        mouse_x, mouse_y = event.GetPosition() # 获取鼠标的位置
        distance = math.sqrt((mouse_x - self.circle_x) ** 2 + (mouse_y - self.circle_y) ** 2) # 计算鼠标位置和圆点中心的距离
        if distance <= self.circle_r: # 如果距离小于等于圆点半径
            print("You clicked the circle!") # 打印信息
        else: # 否则
            print("You missed the circle!") # 打印信息

class MyFrame(wx.Frame):
    def __init__(self):
        wx.Frame.__init__(self, None, title="Click the circle")
        panel = MyPanel(self) # 创建一个自定义的panel
        self.Show()

app = wx.App()
frame = MyFrame()
app.MainLoop()
