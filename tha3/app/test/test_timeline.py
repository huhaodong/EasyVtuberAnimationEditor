# 导入wxpython库
import wx
# 导入blender库
# import bpy

# 创建一个应用程序对象
app = wx.App()
# 创建一个主窗口
frame = wx.Frame(None, title="动画序列时间轴", size=(800, 600))
# 创建一个面板
panel = wx.Panel(frame)

# 创建一个水平的盒子布局
hbox = wx.BoxSizer(wx.HORIZONTAL)
# 创建一个垂直的盒子布局
vbox = wx.BoxSizer(wx.VERTICAL)

# 创建一个静态文本，显示当前帧数
text = wx.StaticText(panel, label="当前帧：1")
# 将静态文本添加到垂直布局中
vbox.Add(text, flag=wx.ALIGN_CENTER | wx.TOP, border=10)

# 创建一个滑动条，用于控制帧数
slider = wx.Slider(panel, value=1, minValue=1, maxValue=250, style=wx.SL_HORIZONTAL)
# 将滑动条添加到垂直布局中
vbox.Add(slider, flag=wx.EXPAND | wx.ALL, border=10)

# 创建一个按钮，用于播放动画
button = wx.Button(panel, label="播放")
# 将按钮添加到垂直布局中
vbox.Add(button, flag=wx.ALIGN_CENTER | wx.BOTTOM, border=10)

# 将垂直布局添加到水平布局中
hbox.Add(vbox, proportion=1, flag=wx.EXPAND | wx.ALL, border=10)

# 创建一个画布，用于显示blender的动画
canvas = wx.Panel(panel)
# 将画布添加到水平布局中
hbox.Add(canvas, proportion=2, flag=wx.EXPAND | wx.ALL, border=10)

# 设置面板的布局为水平布局
panel.SetSizer(hbox)

# 定义一个函数，用于更新静态文本和blender的帧数
def update(event):
    # 获取滑动条的值
    value = slider.GetValue()
    # 设置静态文本的内容为当前帧数
    text.SetLabel(f"当前帧：{value}")
    # 设置blender的帧数为滑动条的值
    # bpy.context.scene.frame_set(value)

# 绑定滑动条的值改变事件到更新函数
slider.Bind(wx.EVT_SLIDER, update)

# 定义一个函数，用于播放动画
def play(event):
    # 获取滑动条的最大值和最小值
    min = slider.GetMin()
    max = slider.GetMax()
    # 循环遍历每一帧
    for i in range(min, max + 1):
        # 设置滑动条的值为当前帧数
        slider.SetValue(i)
        # 调用更新函数
        update(None)
        # 延迟0.04秒
        wx.MilliSleep(40)

# 绑定按钮的点击事件到播放函数
button.Bind(wx.EVT_BUTTON, play)

# 显示主窗口
frame.Show()
# 运行应用程序
app.MainLoop()
