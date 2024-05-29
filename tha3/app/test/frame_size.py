import wx

class MyFrame(wx.Frame):
    def __init__(self, parent, title):
        super(MyFrame, self).__init__(parent, title=title, style=wx.DEFAULT_FRAME_STYLE)

if __name__ == '__main__':
    app = wx.App()
    frame = MyFrame(None, 'My Frame')
    frame.Show()
    app.MainLoop()
