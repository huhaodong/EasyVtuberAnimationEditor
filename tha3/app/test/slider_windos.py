import wx
import wx.lib.scrolledpanel

class MyFrame(wx.Frame):
    def __init__(self, parent, title):
        wx.Frame.__init__(self, parent, title=title, size=(600, 400))
        self.panel = wx.lib.scrolledpanel.ScrolledPanel(self, -1)
        self.panel.SetupScrolling()
        self.sizer = wx.BoxSizer(wx.VERTICAL)
        self.button = wx.Button(self.panel, label="Centered")
        self.sizer.Add(self.button, 0, wx.CENTER)
        self.panel.SetSizer(self.sizer)
        self.Bind(wx.EVT_SIZE, self.OnSize)
        self.Centre()
        self.Show()

    def OnSize(self, event):
        self.panel.SetSize(self.GetSize())
        event.Skip()

if __name__ == "__main__":
    app = wx.App()
    frame = MyFrame(None, "wxPython Example")
    app.MainLoop()
