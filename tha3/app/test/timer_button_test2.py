# 导入wxpython库
import wx
import glob

# 定义一个播放器类，继承自wx.Frame
class Player(wx.Frame):
    # 初始化方法
    def __init__(self, images):
        # 调用父类的初始化方法
        wx.Frame.__init__(self, None, title="图片序列播放器", size=(800, 600))
        # 设置窗口居中
        self.Centre()
        # 创建一个面板
        self.panel = wx.Panel(self)
        # 创建一个静态位图控件，用于显示图片
        self.bitmap = wx.StaticBitmap(self.panel)
        # 创建一个滑动条控件，用于调整播放进度
        self.slider = wx.Slider(self.panel, value=0, minValue=0, maxValue=len(images)-1)
        # 创建一个按钮控件，用于控制播放和暂停
        self.button = wx.Button(self.panel, label="播放")
        # 创建一个水平布局管理器
        self.hbox = wx.BoxSizer(wx.HORIZONTAL)
        # 将按钮和滑动条添加到水平布局管理器中
        self.hbox.Add(self.button, 0, wx.ALIGN_CENTER | wx.ALL, 10)
        self.hbox.Add(self.slider, 1, wx.ALIGN_CENTER | wx.ALL, 10)
        # 创建一个垂直布局管理器
        self.vbox = wx.BoxSizer(wx.VERTICAL)
        # 将位图和水平布局管理器添加到垂直布局管理器中
        self.vbox.Add(self.bitmap, 1, wx.EXPAND | wx.ALL, 10)
        self.vbox.Add(self.hbox, 0, wx.EXPAND | wx.ALL, 10)
        # 设置面板的布局管理器
        self.panel.SetSizer(self.vbox)
        # 绑定按钮的点击事件
        self.Bind(wx.EVT_BUTTON, self.on_button, self.button)
        # 绑定滑动条的滑动事件
        self.Bind(wx.EVT_SLIDER, self.on_slider, self.slider)
        # 定义一个定时器，用于控制播放速度
        self.timer = wx.Timer(self)
        # 绑定定时器的触发事件
        self.Bind(wx.EVT_TIMER, self.on_timer, self.timer)
        # 定义一个属性，用于存储图片序列
        self.images = images
        # 定义一个属性，用于记录当前播放的图片索引
        self.index = 0
        # 定义一个属性，用于记录当前是否在播放状态
        self.playing = False
        # 显示第一张图片
        self.show_image()

    # 定义一个方法，用于显示图片
    def show_image(self):
        # 获取当前图片
        image = self.images[self.index]
        # 将图片缩放为原来大小的三分之一
        # image = image.Scale(image.GetWidth() // 3, image.GetHeight() // 3)
        # 将图片转换为位图
        bitmap = image.ConvertToBitmap()
        # 设置位图控件的位图
        self.bitmap.SetBitmap(bitmap)
        # 设置滑动条的值
        self.slider.SetValue(self.index)

    # 定义一个方法，用于处理按钮的点击事件
    def on_button(self, event):
        # 判断当前是否在播放状态
        if self.playing:
            # 如果是，停止定时器
            self.timer.Stop()
            # 设置按钮的标签为“播放”
            self.button.SetLabel("播放")
            # 设置播放状态为False
            self.playing = False
        else:
            # 如果不是，启动定时器，每秒触发30次
            self.timer.Start(1000 // 30)
            # 设置按钮的标签为“暂停”
            self.button.SetLabel("暂停")
            # 设置播放状态为True
            self.playing = True

    # 定义一个方法，用于处理滑动条的滑动事件
    def on_slider(self, event):
        # 获取滑动条的值
        self.index = self.slider.GetValue()
        # 显示对应的图片
        self.show_image()

    # 定义一个方法，用于处理定时器的触发事件
    def on_timer(self, event):
        # 判断当前图片是否是最后一张
        if self.index == len(self.images) - 1:
            # # 如果是，停止定时器
            # self.timer.Stop()
            # # 设置按钮的标签为“播放”
            # self.button.SetLabel("播放")
            # # 设置播放状态为False
            # self.playing = False
            self.index = 0
        else:
            # 如果不是，将图片索引加一
            self.index += 1
            # 显示下一张图片
            self.show_image()

# 定义一个函数，用于加载图片序列
def load_images():
    # 定义一个空列表，用于存储图片
    images = []
    source_images = glob.glob("D:\\Program Files\\EasyVtuber-main\\data\\images\\render_output\\girl_01_breathing\\*.png") # 假设图片文件都在images文件夹中，且为jpg格式
    # 遍历图片的文件名
    for filename in source_images:
        # 加载图片
        image = wx.Image(filename, wx.BITMAP_TYPE_PNG)
        # 将图片添加到列表中
        images.append(image)
    # 返回图片列表
    return images

# 定义主函数
def main():
    # 创建一个应用对象
    app = wx.App()
    # 创建一个播放器对象，传入图片序列
    player = Player(load_images())
    # 显示播放器窗口
    player.Show()
    # 进入应用的主循环
    app.MainLoop()

# 判断是否是主模块
if __name__ == "__main__":
    # 调用主函数
    main()
