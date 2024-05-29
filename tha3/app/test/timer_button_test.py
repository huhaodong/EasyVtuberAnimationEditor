import wx
import glob # 用于获取文件夹中的图片文件名
import math

class Frame(wx.Frame):
    def __init__(self):
        wx.Frame.__init__(self, None, title="图片轮播器", size=(800, 600))
        self.panel = wx.Panel(self)
        self.images = glob.glob("D:\\FILES\\WorkSpace\\UE5\\output\\Squence\\human_skull\\*.png") # 假设图片文件都在images文件夹中，且为jpg格式
        self.index = 0 # 当前图片的索引
        self.image = wx.Image(self.images[self.index], wx.BITMAP_TYPE_PNG) # 加载第一张图片
        self.bitmap = wx.StaticBitmap(self.panel, -1, self.image.ConvertToBitmap()) # 创建一个静态位图控件
        self.timer = wx.Timer(self) # 创建一个定时器
        self.Bind(wx.EVT_TIMER, self.OnTimer, self.timer) # 绑定定时器事件
        self.timer.Start(math.floor(1000 / 30)) # 启动定时器，每秒30次

    def OnTimer(self, event):
        self.index = (self.index + 1) % len(self.images) # 更新图片索引
        self.image.LoadFile(self.images[self.index]) # 加载下一张图片
        self.bitmap.SetBitmap(self.image.ConvertToBitmap()) # 设置位图控件的图片

app = wx.App()
frame = Frame()
frame.Show()
app.MainLoop()
