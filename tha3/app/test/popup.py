import wx

class MyFrame(wx.Frame):
    def __init__(self, parent, title):
        wx.Frame.__init__(self, parent, title=title, size=(300, 200))
        self.panel = wx.Panel(self)
        self.button = wx.Button(self.panel, label="点击我", pos=(100, 80))
        self.button.Bind(wx.EVT_BUTTON, self.on_button_click)
        self.popup = None
        # 在__init__方法中创建一个wx.Timer对象
        self.timer = wx.Timer(self)
        # 绑定wx.EVT_TIMER事件
        self.Bind(wx.EVT_TIMER, self.close_popup, self.timer)
        self.Show()

    def on_button_click(self, event):
        # 创建一个弹出窗口，显示一条消息
        self.popup = wx.PopupWindow(self, flags=wx.BORDER_SIMPLE)
        message = wx.StaticText(self.popup, label="你点击了按钮")
        self.popup.SetSize(message.GetBestSize())
        # 获取按钮的位置和大小
        button_pos = self.button.GetScreenPosition()
        button_size = self.button.GetSize()
        # 计算弹出窗口的位置，使其在按钮的正上方
        popup_pos = (button_pos[0], button_pos[1] - self.popup.GetSize()[1])
        self.popup.Position(popup_pos, (0, 0))
        self.popup.Show()
        # 启动一个定时器，1秒后关闭弹出窗口
        self.timer.Start(1000, oneShot=True)

    def close_popup(self, event):
        # 关闭弹出窗口并停止定时器
        if self.popup:
            self.popup.Destroy()
            self.popup = None
        if self.timer:
            self.timer.Stop()

if __name__ == "__main__":
    app = wx.App()
    frame = MyFrame(None, "wxPython示例")
    app.MainLoop()
