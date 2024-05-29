import argparse
import logging
import os
import sys
from typing import Any, List

sys.path.append(os.getcwd())

import PIL.Image
import numpy
import torch
import wx
import math

from tha3.poser.modes.load_poser import load_poser
from tha3.poser.poser import Poser, PoseParameterCategory, PoseParameterGroup
from tha3.util import extract_pytorch_image_from_filelike, rgba_to_numpy_image, grid_change_to_numpy_image, \
    rgb_to_numpy_image, resize_PIL_image, extract_PIL_image_from_filelike, extract_pytorch_image_from_PIL_image

# 多个slider的集合类
class MorphCategoryControlPanel(wx.Panel):
    def __init__(self,
                 parent,
                 title: str,
                 pose_param_category: PoseParameterCategory,
                 param_groups: List[PoseParameterGroup],
                 data):
        super().__init__(parent, style=wx.SIMPLE_BORDER)
        self.pose_param_category = pose_param_category
        self.sizer = wx.BoxSizer(wx.VERTICAL)
        self.SetSizer(self.sizer)
        self.SetAutoLayout(1)

        self.title = title

        self.data = data

        title_text = wx.StaticText(self, label="   ------------ %s ------------   " % title, style=wx.ALIGN_CENTER)
        self.sizer.Add(title_text, 0, wx.EXPAND)

        self.param_groups = [group for group in param_groups if group.get_category() == pose_param_category] # 获取该修改器的参数列表
        self.choice = wx.Choice(self, choices=[group.get_group_name() for group in self.param_groups]) # 根据修改器的参数列表创建一个下拉框菜单控件
        if len(self.param_groups) > 0:
            self.choice.SetSelection(0) # 默认选择第0个选项
        self.choice.Bind(wx.EVT_CHOICE, self.on_choice_updated) #绑定一个选择器修改事件
        self.sizer.Add(self.choice, 0, wx.EXPAND)

        self.left_slider = wx.Slider(self, minValue=-1000, maxValue=1000, value=-1000, style=wx.HORIZONTAL) #创建一个滑动栏，最大值1000最小值-1000，默认处于-1000处
        self.left_slider.SetName(title+"-left")
        self.sizer.Add(self.left_slider, 0, wx.EXPAND)
        self.left_slider.Bind(wx.EVT_SLIDER, self.OnSlided)

        self.right_slider = wx.Slider(self, minValue=-1000, maxValue=1000, value=-1000, style=wx.HORIZONTAL)
        self.right_slider.SetName(title+"-right")
        self.sizer.Add(self.right_slider, 0, wx.EXPAND)
        self.right_slider.Bind(wx.EVT_SLIDER, self.OnSlided)

        self.checkbox = wx.CheckBox(self, label="Show")
        self.checkbox.SetValue(True)
        self.sizer.Add(self.checkbox, 0, wx.SHAPED | wx.ALIGN_CENTER)

        self.update_ui()

        self.sizer.Fit(self)

    # slider滑动回调函数
    def OnSlided(self, event):
        slider = event.GetEventObject()
        choice = self.choice
        self.data.set_morph_control_panel_parame(slider,choice)
        self.data.update_timeline_data_map()

    def update_ui(self):
        param_group = self.param_groups[self.choice.GetSelection()]
        if param_group.is_discrete():
            self.left_slider.Enable(False)
            self.right_slider.Enable(False)
            self.checkbox.Enable(True)
        elif param_group.get_arity() == 1:
            self.left_slider.Enable(True)
            self.right_slider.Enable(False)
            self.checkbox.Enable(False)
        else:
            self.left_slider.Enable(True)
            self.right_slider.Enable(True)
            self.checkbox.Enable(False)

    def on_choice_updated(self, event: wx.Event):
        param_group = self.param_groups[self.choice.GetSelection()]
        if param_group.is_discrete():
            self.checkbox.SetValue(True)
        self.update_ui()

    def set_param_value(self, pose: List[float]):
        if len(self.param_groups) == 0:
            return
        selected_morph_index = self.choice.GetSelection()
        param_group = self.param_groups[selected_morph_index]
        param_index = param_group.get_parameter_index()
        if param_group.is_discrete():
            if self.checkbox.GetValue():
                for i in range(param_group.get_arity()):
                    pose[param_index + i] = 1.0
        else:
            param_range = param_group.get_range()
            alpha = (self.left_slider.GetValue() + 1000) / 2000.0
            pose[param_index] = param_range[0] + (param_range[1] - param_range[0]) * alpha
            if param_group.get_arity() == 2:
                alpha = (self.right_slider.GetValue() + 1000) / 2000.0
                pose[param_index + 1] = param_range[0] + (param_range[1] - param_range[0]) * alpha

# 只有一个slider的集合
class SimpleParamGroupsControlPanel(wx.Panel):
    def __init__(self, parent,
                 pose_param_category: PoseParameterCategory,
                 param_groups: List[PoseParameterGroup],
                 data):
        super().__init__(parent, style=wx.SIMPLE_BORDER)

        self.data = data

        self.sizer = wx.BoxSizer(wx.VERTICAL)
        self.SetSizer(self.sizer)
        self.SetAutoLayout(1)

        self.param_groups = [group for group in param_groups if group.get_category() == pose_param_category]
        for param_group in self.param_groups:
            assert not param_group.is_discrete()
            assert param_group.get_arity() == 1

        self.sliders = []
        for param_group in self.param_groups:
            static_text = wx.StaticText(
                self,
                label="   ------------ %s ------------   " % param_group.get_group_name(), style=wx.ALIGN_CENTER)
            self.sizer.Add(static_text, 0, wx.EXPAND)
            range = param_group.get_range()
            min_value = int(range[0] * 1000)
            max_value = int(range[1] * 1000)
            slider = wx.Slider(self, minValue=min_value, maxValue=max_value, value=0, style=wx.HORIZONTAL)
            slider.SetName(param_group.get_group_name())
            slider.Bind(wx.EVT_SLIDER, self.OnSlided)
            self.sizer.Add(slider, 0, wx.EXPAND)
            self.sliders.append(slider)

        self.sizer.Fit(self)

    # slider 回调
    def OnSlided(self,event):
        slider = event.GetEventObject()
        self.data.set_non_morph_control_panel_parame(slider)
        self.data.update_timeline_data_map()

    # 将slider中的param赋值到pose中
    def set_param_value(self, pose: List[float]):
        if len(self.param_groups) == 0:
            return
        for param_group_index in range(len(self.param_groups)):
            param_group = self.param_groups[param_group_index]
            slider = self.sliders[param_group_index]
            param_range = param_group.get_range()
            param_index = param_group.get_parameter_index()
            alpha = (slider.GetValue() - slider.GetMin()) * 1.0 / (slider.GetMax() - slider.GetMin())
            pose[param_index] = param_range[0] + (param_range[1] - param_range[0]) * alpha

def convert_output_image_from_torch_to_numpy(output_image):
    if output_image.shape[2] == 2:
        h, w, c = output_image.shape
        numpy_image = torch.transpose(output_image.reshape(h * w, c), 0, 1).reshape(c, h, w)
    elif output_image.shape[0] == 4:
        numpy_image = rgba_to_numpy_image(output_image)
    elif output_image.shape[0] == 3:
        numpy_image = rgb_to_numpy_image(output_image)
    elif output_image.shape[0] == 1:
        c, h, w = output_image.shape
        alpha_image = torch.cat([output_image.repeat(3, 1, 1) * 2.0 - 1.0, torch.ones(1, h, w)], dim=0)
        numpy_image = rgba_to_numpy_image(alpha_image)
    elif output_image.shape[0] == 2:
        numpy_image = grid_change_to_numpy_image(output_image, num_channels=4)
    else:
        raise RuntimeError("Unsupported # image channels: %d" % output_image.shape[0])
    numpy_image = numpy.uint8(numpy.rint(numpy_image * 255.0))
    return numpy_image

# 简单的文字面板类
class SimpleLableText(wx.Panel):
    def __init__(self, parent, text, font_size):
        super().__init__(parent,style=wx.NO_BORDER)
        self.sizer = wx.BoxSizer(wx.VERTICAL)
        self.SetSizer(self.sizer)
        self.SetAutoLayout(1)
        static_text = wx.StaticText(self, label=text, style=wx.CENTRE)
        font = wx.Font(font_size, wx.DEFAULT, wx.NORMAL, wx.NORMAL)
        static_text.SetFont(font)

        self.sizer.Add(static_text, 0)

        self.sizer.Fit(self)

# 时间轴面板类
class TimelnePanel(wx.Panel):
    def __init__(self, main_panel, parent, timeline_width, timeline_height, slider_height, frame_num, timeline_gap, lable_len, lable_gap, data_map, item_list):
        super().__init__(parent,style=wx.SIMPLE_BORDER, size=(timeline_width, timeline_height+slider_height))
        self.main_panel = main_panel
        self.timeline_width = timeline_width
        self.timeline_height = timeline_height
        self.slider_height = slider_height
        self.timeline_gap = timeline_gap
        self.frame_num = frame_num
        self.lable_len = lable_len
        self.lable_gap = lable_gap
        self.line_gap = 5
        self.min_line_gap = 6
        self.line_gap_delta = 2
        self.data = data_map
        self.item_list = item_list

        self.sizer = wx.BoxSizer(wx.VERTICAL)
        self.SetSizer(self.sizer)
        self.SetAutoLayout(1)

        # timeline label映射表初始化
        first_lable_line_y = self.lable_gap+self.line_gap
        self.data.timeline_lable_map[self.item_list[0]]=first_lable_line_y
        self.data.timeline_lable_map[first_lable_line_y]=self.item_list[0]
        for i in range(len(self.item_list)-1):
            y = first_lable_line_y+self.min_line_gap*(i+1)*2+i+self.line_gap_delta
            self.data.timeline_lable_map[self.item_list[i+1]]=y
            self.data.timeline_lable_map[y]=self.item_list[i+1]

        # timeline画板声明
        self.timeline_draw_panel = wx.Panel(self, style=wx.NO_BORDER,size=(timeline_width, timeline_height))
        self.timeline_draw_panel.Bind(wx.EVT_PAINT, self.OnPaint)
        self.timeline_draw_panel.Refresh()

        # timelne slider
        self.timeline_slider = wx.Slider(self, minValue=0, maxValue=300, value=0, style=wx.HORIZONTAL, size=(timeline_width,slider_height))
        self.sizer.Add(self.timeline_slider, 0)
        self.timeline_slider.Bind(wx.EVT_SLIDER, self.OnSlided)

        self.sizer.Add(self.timeline_draw_panel,0)
        self.sizer.Fit(self)

    def OnPaint(self, event):
        self.timeline_draw_panel_dc = wx.PaintDC(self.timeline_draw_panel)
        self.timeline_draw_panel_dc.SetPen(wx.Pen("black", 1))
        self.timeline_draw_panel_dc.SetTextForeground("gray")
        self.timeline_draw_panel_dc.SetFont(wx.Font(5, wx.FONTFAMILY_DEFAULT, wx.FONTSTYLE_NORMAL, wx.FONTWEIGHT_NORMAL))
        tick_interval = math.ceil((self.timeline_width-self.timeline_gap*2)/self.frame_num)
        count = 9
        num = 10
        line_height = 5
        for i in range(self.frame_num+1):
            x = self.timeline_gap+tick_interval*i
            height = line_height
            count = count+1
            if count-num==0:
                count=0
                height = line_height*2
                self.timeline_draw_panel_dc.DrawText(str(i),x-2,height+1)
            self.timeline_draw_panel_dc.DrawLine(x,0,x,height)
        
        first_lable_line_y = self.lable_gap+self.line_gap
        self.timeline_draw_panel_dc.SetPen(wx.Pen("blue",1))
        self.timeline_draw_panel_dc.DrawLine(0,first_lable_line_y,self.timeline_width,first_lable_line_y)
        for i in range(self.lable_len-1):
            y = first_lable_line_y+self.min_line_gap*(i+1)*2+i+self.line_gap_delta
            self.timeline_draw_panel_dc.DrawLine(0,y,self.timeline_width,y)
        
        # 绘制标记点
        if bool(self.data.parameter_map):
            self.timeline_draw_panel_dc.SetPen(wx.Pen("red", 2))
            self.timeline_draw_panel_dc.SetBrush(wx.Brush("red"))
            for key,value in self.data.parameter_map.items():
                for k in self.data.parameter_map[key]:
                    x = self.timeline_slider_num2x(int(key))
                    y = self.data.find_lable_y(k)
                    self.DrawMarkPoint(x,y)

        # 绘制预览游标线
        slider_num = self.timeline_slider.GetValue()
        self.timeline_draw_panel_dc.SetPen(wx.Pen("red",1))
        self.DrawCursorLine(slider_num)

    # slider值换算成坐标
    def timeline_slider_num2x(self,slider_num):
        position = slider_num/300
        return math.floor(self.timeline_gap+(self.timeline_width-self.timeline_gap*2)*position)

    # 绘制游标线函数
    def DrawCursorLine(self,slider_num):
        x = self.timeline_slider_num2x(slider_num)
        self.timeline_draw_panel_dc.DrawLine(x,0,x,self.timeline_height)

    # 绘制标记点函数
    def DrawMarkPoint(self,key,value):
        self.timeline_draw_panel_dc.DrawCircle(key,value, 2)

    # 获取当前时间轴的值
    def GetTimelineValue(self):
        return self.timeline_slider.GetValue()

    # 滑动滑块的回调函数
    def OnSlided(self, event):
        self.data.set_now_key_value(self.GetTimelineValue())
        self.SetAllSliderValue()
        self.main_panel.Refresh() #刷新整个页面
        # self.timeline_draw_panel.Refresh()

    # 设置多选项的slider的值
    def SetMorphSliderValue(self,key,slider,choice):
        dirlable = ["type","left","right"]
        (classname,dirname) = slider.GetName().split("-")
        type = self.data.control_slider_morph_data_map[key][self.data.morph_lable.index(classname)][0]
        value = self.data.control_slider_morph_data_map[key][self.data.morph_lable.index(classname)][dirlable.index(dirname)]
        slider.SetValue(value)
        choice.SetSelection(type)

    # 设置单一slider的值
    def SetNonMorphSliderValue(self,key,slider):
        classname = slider.GetName()
        value = self.data.control_slider_non_morph_data_map[key][self.data.non_morph_lable.index(classname)]
        slider.SetValue(value)
    
    # 设置当前帧上的所有的slider的值
    def SetAllSliderValue(self):
        key = self.data.get_now_key_value()
        for k,v in self.main_panel.morph_control_panels.items():
            self.SetMorphSliderValue(key,v.left_slider,v.choice)
            self.SetMorphSliderValue(key,v.right_slider,v.choice)

        for k,v in self.main_panel.non_morph_control_panels.items():
            for slider in v.sliders:
                self.SetNonMorphSliderValue(key,slider)

# 曲线编辑面板类
class CurvePlottingPanel(wx.Panel):
    #pointes={start_point:(int,int),start_control_point:(int,int),end_point:(int,int),end_control_point:(int,int)}
    def __init__(self, parent):
        self.height = 237
        self.width = 450
        self.top_gap = 15
        self.left_gap = 15
        self.botton_gap = 15
        self.lable_str = "NONE"

        super().__init__(parent,style=wx.NO_BORDER,size=(self.width,self.height))
        self.Bind(wx.EVT_PAINT,self.OnPaint)
        self.Refresh()

    def OnPaint(self,event):
        self.dc = wx.PaintDC(self)
        self.dc.SetPen(wx.Pen("black",1))
        self.dc.SetTextForeground("gray")
        self.dc.SetFont(wx.Font(10, wx.FONTFAMILY_DEFAULT, wx.FONTSTYLE_NORMAL, wx.FONTWEIGHT_NORMAL))
        
        # 绘制垂线
        self.dc.DrawLine(self.left_gap, self.top_gap, self.left_gap, self.height-self.botton_gap)
        
        # 绘制横线
        self.dc.DrawLine(self.left_gap, self.height-self.botton_gap, self.width, self.height-self.botton_gap)

        # 绘制曲线标签
        self.dc.DrawText(self.lable_str,self.left_gap+5,self.height-self.botton_gap+2)

# 参数类
class ParameterStore:
    def __init__(self):
        self.now_key_value = 0
        self.frame_num = 300
        self.morph_lable = ["eyebrow","eye","mouth","iris_morphs"]
        self.non_morph_lable = ["iris_rotation_x","iris_rotation_y","head_x","head_y","neck_z","body_y","body_z","breathing"]
        self.temp_delete_parameter_map = {}
        self.parameter_map = {}
        self.timeline_lable_map = {}
        self.control_slider_morph_data_map = [[[0,-1000,-1000] for j in range(len(self.morph_lable))] for k in range(self.frame_num+1)] # [[[type,left,right]]]
        self.control_slider_non_morph_data_map = [[0 for i in range(len(self.non_morph_lable))] for j in range(self.frame_num+1)] # [[value]]

    def set(self,num,map):
        self.parameter_map[num] = map
    
    def find_lable_y(self, lable_name):
        if lable_name in self.timeline_lable_map:
            return self.timeline_lable_map[lable_name]
        else:
            return -1
        
    def set_now_key_value(self,v):
        self.now_key_value = v

    def get_now_key_value(self):
        return self.now_key_value
    
    def clear_timeline_current_data(self):
        if self.now_key_value in self.parameter_map:
            self.temp_delete_parameter_map.clear()
            self.temp_delete_parameter_map[self.now_key_value] = self.parameter_map[self.now_key_value]
            del self.parameter_map[self.now_key_value]

    # 三次贝塞尔缓动曲线函数求值
    def cubic_bezier(self,in_x,start_x,start_y,start_c_x,start_c_y,end_c_x,end_c_y,end_x,end_y):
        x = in_x
        if x < start_x:
            x = 0
        else:
            x = x-start_x
        x0 = 0
        y0 = start_y
        x1 = start_c_x + x0
        y1 = start_c_y+ y0
        x3 = end_x-start_x
        y3 = end_y
        x2 = end_c_x+x3
        y2 = end_c_y+y3

        P0 = (x0,y0)
        P1 = (x1,y1)
        P2 = (x2,y2)
        P3 = (x3,y3)

        # 定义三次方程的系数
        a = P0[0] - 3 * P1[0] + 3 * P2[0] - P3[0]
        b = 3 * P1[0] - 6 * P2[0] + 3 * P3[0]
        c = 3 * P2[0] - 3 * P3[0]
        d = P3[0] - x

        roots = numpy.roots([a, b, c, d])
        t = None
        for root in roots:
            if numpy.isreal(root) and 0 <= root <= 1:
                t = root.real
                break

        y = None
        # 如果找到了合适的t值，就代入y轴的方程，得到y值
        if t is not None:
            t = 1-t
            y = (1 - t) ** 3 * P0[1] + 3 * (1 - t) ** 2 * t * P1[1] + 3 * (1 - t) * t ** 2 * P2[1] + t ** 3 * P3[1]
            y = math.floor(y)
        else:
            print("没有找到合适的t值")
        return y

    # 向后寻找匹配的key返回的是一个map
    def find_back_key(self,key_parameter_map,parameter_map,key_index,timeline_keys,lables):
        ret_map = {}
        current_key = timeline_keys[key_index]
        if lables[0] in self.morph_lable:
            for i in range(key_index+1,len(timeline_keys)):
                key = timeline_keys[i]
                if lables[0] in parameter_map[key] and lables[1] in parameter_map[key][lables[0]] and bool(parameter_map[key][lables[0]][lables[1]]):
                    type = key_parameter_map[current_key][lables[0]]["type"]
                    start = (current_key,key_parameter_map[current_key][lables[0]][lables[1]]["value"])
                    start_control = (key_parameter_map[current_key][lables[0]][lables[1]]["control"]["start"][0],key_parameter_map[current_key][lables[0]][lables[1]]["control"]["start"][1])
                    end = (key,parameter_map[key][lables[0]][lables[1]]["value"])
                    end_control = (parameter_map[key][lables[0]][lables[1]]["control"]["end"][0],parameter_map[key][lables[0]][lables[1]]["control"]["end"][1])
                    ret_map = {
                        "type":type,
                        "start":start,
                        "start_control":start_control,
                        "end":end,
                        "end_control":end_control
                    }
                    break
            if not bool(ret_map):
                type = key_parameter_map[current_key][lables[0]]["type"]
                end = (self.frame_num+1,key_parameter_map[current_key][lables[0]][lables[1]]["value"])
                end_control = (0,0)
                start = (current_key,key_parameter_map[current_key][lables[0]][lables[1]]["value"])
                start_control = (0,0)
                ret_map = {
                        "type":type,
                        "start":start,
                        "start_control":start_control,
                        "end":end,
                        "end_control":end_control
                    }
        else:
            for i in range(key_index+1,len(timeline_keys)):
                key = timeline_keys[i]
                if lables[0] in parameter_map[key] and bool(parameter_map[key][lables[0]]):
                    start = (current_key,key_parameter_map[current_key][lables[0]]["value"])
                    start_control = (key_parameter_map[current_key][lables[0]]["control"]["start"][0],key_parameter_map[current_key][lables[0]]["control"]["start"][1])
                    end = (key,parameter_map[key][lables[0]]["value"])
                    end_control = (parameter_map[key][lables[0]]["control"]["end"][0],parameter_map[key][lables[0]]["control"]["end"][1])
                    ret_map = {
                        "start":start,
                        "start_control":start_control,
                        "end":end,
                        "end_control":end_control
                    }
                    break

            if not bool(ret_map):
                end = (self.frame_num+1,key_parameter_map[current_key][lables[0]]["value"])
                end_control = (0,0)
                start = (current_key,key_parameter_map[current_key][lables[0]]["value"])
                start_control = (0,0)
                ret_map = {
                        "start":start,
                        "start_control":start_control,
                        "end":end,
                        "end_control":end_control
                    }

        return ret_map

    # 向前寻找匹配的key返回的是一个map
    def find_front_key(self,key_parameter_map, parameter_map,key_index,timeline_keys,lables):
        ret_map = {}
        current_key = timeline_keys[key_index]
        if lables[0] in self.morph_lable:
            for i in range(key_index-1,-1,-1):
                key = timeline_keys[i]
                if lables[0] in parameter_map[key] and lables[1] in parameter_map[key][lables[0]] and bool(parameter_map[key][lables[0]][lables[1]]):
                    type = parameter_map[key][lables[0]]["type"]
                    start = (key,parameter_map[key][lables[0]][lables[1]]["value"])
                    start_control = (parameter_map[key][lables[0]][lables[1]]["control"]["start"][0],parameter_map[key][lables[0]][lables[1]]["control"]["start"][1])
                    end = (current_key,key_parameter_map[current_key][lables[0]][lables[1]]["value"])
                    end_control = (key_parameter_map[current_key][lables[0]][lables[1]]["control"]["end"][0],key_parameter_map[current_key][lables[0]][lables[1]]["control"]["end"][1])
                    ret_map = {
                        "type":type,
                        "start":start,
                        "start_control":start_control,
                        "end":end,
                        "end_control":end_control
                    }
                    break
            if not bool(ret_map):
                type = key_parameter_map[current_key][lables[0]]["type"]
                start = (0,key_parameter_map[current_key][lables[0]][lables[1]]["value"])
                start_control = (0,0)
                end = (current_key,key_parameter_map[current_key][lables[0]][lables[1]]["value"])
                end_control = (0,0)
                ret_map = {
                        "type":type,
                        "start":start,
                        "start_control":start_control,
                        "end":end,
                        "end_control":end_control
                    }
        else:
            for i in range(key_index-1,-1,-1):
                key = timeline_keys[i]
                if lables[0] in parameter_map[key] and bool(parameter_map[key][lables[0]]):
                    start = (key,parameter_map[key][lables[0]]["value"])
                    start_control = (parameter_map[key][lables[0]]["control"]["start"][0],parameter_map[key][lables[0]]["control"]["start"][1])
                    end = (current_key,key_parameter_map[current_key][lables[0]]["value"])
                    end_control = (key_parameter_map[current_key][lables[0]]["control"]["end"][0],key_parameter_map[current_key][lables[0]]["control"]["end"][1])
                    ret_map = {
                        "start":start,
                        "start_control":start_control,
                        "end":end,
                        "end_control":end_control
                    }
                    break

            if not bool(ret_map):
                start = (0,key_parameter_map[current_key][lables[0]]["value"])
                start_control = (0,0)
                end = (current_key,key_parameter_map[current_key][lables[0]]["value"])
                end_control = (0,0)
                ret_map = {
                        "start":start,
                        "start_control":start_control,
                        "end":end,
                        "end_control":end_control
                    }

        return ret_map

    # 找到比当前游标小但最邻近的点
    def find_nearest_key(self,key,timeline_keys):
        count = 0
        for i in timeline_keys:
            if key > i:
                count += 1
        return count
    
    # 找到时间轴上邻接的两个点，返回一个point map，都将被放到function map的start字段下
    def find_nearest_point_key(self,key,timeline_keys):
        key_index = self.find_nearest_key(key,timeline_keys)
        timeline_keys_temp = timeline_keys
        timeline_keys_temp.insert(key_index,key)
        function_map = {"start":{},"end":{}}

        if key in self.temp_delete_parameter_map:
            for k,v in self.temp_delete_parameter_map[key].items():
                # 如果是含有多个预设的slider运行下面的代码
                if k in self.morph_lable and bool(self.temp_delete_parameter_map[key][k]):
                    if "left" in self.temp_delete_parameter_map[key][k] and bool(self.temp_delete_parameter_map[key][k]["left"]):
                        lables = [k,"left"]
                        type = 0
                        start = (0,0)
                        end = (0,0)
                        start_control = (0,0)
                        end_control = (0,0)

                        point_map_back = self.find_back_key(key_parameter_map=self.temp_delete_parameter_map,
                                                        parameter_map=self.parameter_map,
                                                        key_index=key_index,
                                                        timeline_keys=timeline_keys_temp,
                                                        lables=lables)
                        point_map_front = self.find_front_key(key_parameter_map=self.temp_delete_parameter_map,
                                                        parameter_map=self.parameter_map,
                                                        key_index=key_index,
                                                        timeline_keys=timeline_keys_temp,
                                                        lables=lables)
                        if bool(point_map_back) and bool(point_map_front):
                            type = point_map_front["type"]
                            start = point_map_front["start"]
                            start_control = point_map_front["start_control"]
                            end = point_map_back["end"]
                            end_control = point_map_back["end_control"]

                            if point_map_back["end"][0] not in self.parameter_map:
                                end = (self.frame_num+1,-1000)
                                
                            if point_map_front["start"][0] not in self.parameter_map:
                                start = (0,-1000)

                        elif bool(point_map_back):
                            type = 0
                            start = (0,-1000)
                            end = point_map_back["end"]
                            start_control = (0,0)
                            end_control = point_map_back["end_control"]

                            if point_map_back["end"][0] not in self.parameter_map:
                                end = (self.frame_num+1,-1000)

                        elif bool(point_map_front):
                            type = point_map_front["type"]
                            start = point_map_front["start"]
                            end = (self.frame_num+1,-1000)
                            start_control = point_map_front["start_control"]
                            end_control = (0,0)
                            
                            if point_map_front["start"][0] not in self.parameter_map:
                                start = (0,-1000)
                        
                        else:
                            type=0
                            start = (0,-1000)
                            start_control = (0,0)
                            end = (self.frame_num+1,-1000)
                            end_control = (0,0)

                        if k in function_map["start"] and bool(function_map["start"][k]):
                            function_map["start"][k]["type"] = type
                            function_map["start"][k]["left"] = {"start":start,
                                                                "end":end,
                                                                "start_control":start_control,
                                                                "end_control":end_control
                                                                }
                        else:
                            function_map["start"][k] = {"type":type,
                                                    "left":{"start":start,
                                                            "end":end,
                                                            "start_control":start_control,
                                                            "end_control":end_control}}
                            
                    if "right" in self.temp_delete_parameter_map[key][k] and bool(self.temp_delete_parameter_map[key][k]["right"]):
                        lables = [k,"right"]
                        type = 0
                        start = (0,0)
                        end = (0,0)
                        start_control = (0,0)
                        end_control = (0,0)

                        point_map_back = self.find_back_key(key_parameter_map=self.temp_delete_parameter_map,
                                                        parameter_map=self.parameter_map,
                                                        key_index=key_index,
                                                        timeline_keys=timeline_keys_temp,
                                                        lables=lables)
                        point_map_front = self.find_front_key(key_parameter_map=self.temp_delete_parameter_map,
                                                        parameter_map=self.parameter_map,
                                                        key_index=key_index,
                                                        timeline_keys=timeline_keys_temp,
                                                        lables=lables)
                        if bool(point_map_back) and bool(point_map_front):
                            type = point_map_front["type"]
                            start = point_map_front["start"]
                            start_control = point_map_front["start_control"]
                            end = point_map_back["end"]
                            end_control = point_map_back["end_control"]

                            if point_map_back["end"][0] not in self.parameter_map:
                                end = (self.frame_num+1,-1000)
                                
                            if point_map_front["start"][0] not in self.parameter_map:
                                start = (0,-1000)

                        elif bool(point_map_back):
                            type = 0
                            start = (0,-1000)
                            end = point_map_back["end"]
                            start_control = (0,0)
                            end_control = point_map_back["end_control"]

                            if point_map_back["end"][0] not in self.parameter_map:
                                end = (self.frame_num+1,-1000)

                        elif bool(point_map_front):
                            type = point_map_front["type"]
                            start = point_map_front["start"]
                            end = (self.frame_num+1,-1000)
                            start_control = point_map_front["start_control"]
                            end_control = (0,0)
                            
                            if point_map_front["start"][0] not in self.parameter_map:
                                start = (0,-1000)
                        
                        else:
                            type=0
                            start = (0,-1000)
                            start_control = (0,0)
                            end = (self.frame_num+1,-1000)
                            end_control = (0,0)

                        if k in function_map["start"] and bool(function_map["start"][k]):
                            function_map["start"][k]["type"] = type
                            function_map["start"][k]["right"] = {"start":start,
                                                                "end":end,
                                                                "start_control":start_control,
                                                                "end_control":end_control
                                                                }
                        else:
                            function_map["start"][k] = {"type":type,
                                                    "right":{"start":start,
                                                            "end":end,
                                                            "start_control":start_control,
                                                            "end_control":end_control}}

                # 如果是单一slider类则运行下面的代码
                elif k in self.non_morph_lable and bool(self.temp_delete_parameter_map[key][k]):
                    lables = [k]
                    start = (0,0)
                    end = (0,0)
                    start_control = (0,0)
                    end_control = (0,0)

                    point_map_back = self.find_back_key(key_parameter_map=self.temp_delete_parameter_map,
                                                    parameter_map=self.parameter_map,
                                                    key_index=key_index,
                                                    timeline_keys=timeline_keys_temp,
                                                    lables=lables)
                    point_map_front = self.find_front_key(key_parameter_map=self.temp_delete_parameter_map,
                                                    parameter_map=self.parameter_map,
                                                    key_index=key_index,
                                                    timeline_keys=timeline_keys_temp,
                                                    lables=lables)
                    if bool(point_map_back) and bool(point_map_front):
                        start = point_map_front["start"]
                        start_control = point_map_front["start_control"]
                        end = point_map_back["end"]
                        end_control = point_map_back["end_control"]

                        if point_map_back["end"][0] not in self.parameter_map:
                            end = (self.frame_num+1,0)
                            
                        if point_map_front["start"][0] not in self.parameter_map:
                            start = (0,0)

                    elif bool(point_map_back):
                        start = (0,0)
                        end = point_map_back["end"]
                        start_control = (0,0)
                        end_control = point_map_back["end_control"]

                        if point_map_back["end"][0] not in self.parameter_map:
                            end = (self.frame_num+1,0)

                    elif bool(point_map_front):
                        start = point_map_front["start"]
                        end = (self.frame_num+1,0)
                        start_control = point_map_front["start_control"]
                        end_control = (0,0)
                        
                        if point_map_front["start"][0] not in self.parameter_map:
                            start = (0,0)
                    
                    else:
                        start = (0,0)
                        start_control = (0,0)
                        end = (self.frame_num+1,0)
                        end_control = (0,0)

                    function_map["start"][k] = {"start":start,
                                                    "end":end,
                                                    "start_control":start_control,
                                                    "end_control":end_control}

        return function_map

    #找到临近的前后符合条件的关键点
    def find_keys(self):
        key = self.get_now_key_value() # 当前时间轴的位置
        timeline_list = self.parameter_map.keys()
        timeline_list = list(timeline_list)
        timeline_keys = sorted(timeline_list) # 获取所有的修改过的关键帧
        function_map = {"start":{},"end":{}}

        if key in self.parameter_map:
            key_index = timeline_keys.index(key)

            # 遍历当前帧中被修改过的参数，并获取对应的前后邻接点
            for k,v in self.parameter_map[key].items():
                # 如果是含有多个预设的slider运行下面的代码
                if k in self.morph_lable and bool(self.parameter_map[key][k]):
                    if "left" in self.parameter_map[key][k] and bool(self.parameter_map[key][k]["left"]):
                        lables = [k,"left"]
                        point_map = self.find_back_key(key_parameter_map=self.parameter_map,
                                                        parameter_map=self.parameter_map,
                                                        key_index=key_index,
                                                        timeline_keys=timeline_keys,
                                                        lables=lables)
                        if bool(point_map):
                            if k in function_map["start"] and bool(function_map["start"][k]):
                                function_map["start"][k]["type"] = point_map["type"]
                                function_map["start"][k]["left"] = {"start":point_map["start"],
                                                                    "end":point_map["end"],
                                                                    "start_control":point_map["start_control"],
                                                                    "end_control":point_map["end_control"]
                                                                    }
                            else:
                                function_map["start"][k] = {"type":point_map["type"],
                                                            "left":{"start":point_map["start"],
                                                                    "end":point_map["end"],
                                                                    "start_control":point_map["start_control"],
                                                                    "end_control":point_map["end_control"]}}
                        point_map = self.find_front_key(key_parameter_map=self.parameter_map,
                                                        parameter_map=self.parameter_map,
                                                        key_index=key_index,
                                                        timeline_keys=timeline_keys,
                                                        lables=lables)
                        if bool(point_map):
                            if k in function_map["end"] and bool(function_map["end"][k]):
                                function_map["end"][k]["type"] = point_map["type"]
                                function_map["end"][k]["left"] = {"start":point_map["start"],
                                                                    "end":point_map["end"],
                                                                    "start_control":point_map["start_control"],
                                                                    "end_control":point_map["end_control"]
                                                                    }
                            else:
                                function_map["end"][k] = {"type":point_map["type"],
                                                            "left":{"start":point_map["start"],
                                                                    "end":point_map["end"],
                                                                    "start_control":point_map["start_control"],
                                                                    "end_control":point_map["end_control"]}}
                    if "right" in self.parameter_map[key][k] and bool(self.parameter_map[key][k]["right"]):
                        lables = [k,"right"]
                        point_map = self.find_back_key(key_parameter_map=self.parameter_map,
                                                        parameter_map=self.parameter_map,
                                                        key_index=key_index,
                                                        timeline_keys=timeline_keys,
                                                        lables=lables)
                        if bool(point_map):
                            if k in function_map["start"] and bool(function_map["start"][k]):
                                function_map["start"][k]["type"] = point_map["type"]
                                function_map["start"][k]["right"] = {"start":point_map["start"],
                                                                    "end":point_map["end"],
                                                                    "start_control":point_map["start_control"],
                                                                    "end_control":point_map["end_control"]
                                                                    }
                            else:
                                function_map["start"][k] = {"type":point_map["type"],
                                                            "right":{"start":point_map["start"],
                                                                    "end":point_map["end"],
                                                                    "start_control":point_map["start_control"],
                                                                    "end_control":point_map["end_control"]}}
                        point_map = self.find_front_key(key_parameter_map=self.parameter_map,
                                                        parameter_map=self.parameter_map,
                                                        key_index=key_index,
                                                        timeline_keys=timeline_keys,
                                                        lables=lables)
                        if bool(point_map):
                            if k in function_map["end"] and bool(function_map["end"][k]):
                                function_map["end"][k]["type"] = point_map["type"]
                                function_map["end"][k]["right"] = {"start":point_map["start"],
                                                                    "end":point_map["end"],
                                                                    "start_control":point_map["start_control"],
                                                                    "end_control":point_map["end_control"]
                                                                    }
                            else:
                                function_map["end"][k] = {"type":point_map["type"],
                                                            "right":{"start":point_map["start"],
                                                                    "end":point_map["end"],
                                                                    "start_control":point_map["start_control"],
                                                                    "end_control":point_map["end_control"]}}
                # 如果是单一slider类则运行下面的代码
                elif k in self.non_morph_lable and bool(self.parameter_map[key][k]):
                    lables = [k]
                    # 找到后面的关键点
                    point_map = self.find_back_key(key_parameter_map=self.parameter_map,
                                                        parameter_map=self.parameter_map,
                                                        key_index=key_index,
                                                        timeline_keys=timeline_keys,
                                                        lables=lables)
                    if bool(point_map):
                        function_map["start"][k] = {"start":point_map["start"],
                                                    "end":point_map["end"],
                                                    "start_control":point_map["start_control"],
                                                    "end_control":point_map["end_control"]
                                                    }
                    # 找到前面的关键点
                    point_map = self.find_front_key(key_parameter_map=self.parameter_map,
                                                        parameter_map=self.parameter_map,
                                                        key_index=key_index,
                                                        timeline_keys=timeline_keys,
                                                        lables=lables)
                    if bool(point_map):
                        function_map["end"][k] = {"start":point_map["start"],
                                                    "end":point_map["end"],
                                                    "start_control":point_map["start_control"],
                                                    "end_control":point_map["end_control"]}
        
        else: # 更新的时候当前点被删除了，需要接上两边的端点
            
            function_map = self.find_nearest_point_key(key,timeline_keys)
                        
        if not bool(function_map["start"]) and not bool(function_map["end"]):
            function_map = {}
        
        return function_map

    # 将有多个预设的slider的值存到data中
    def set_morph_control_panel_parame(self, slider, choice):
        key_num = self.get_now_key_value()
        (classname,dirname) = slider.GetName().split("-")
        v = slider.GetValue()
        if key_num in self.parameter_map:
            if classname in self.parameter_map[key_num]:
                self.parameter_map[key_num][classname]["type"] = choice.GetSelection()
                if dirname in self.parameter_map[key_num][classname]:
                    self.parameter_map[key_num][classname][dirname]["value"] = v
                else:
                    self.parameter_map[key_num][classname][dirname] = {"value":v,"control":{"start":[0,0],"end":[0,0]}}
            else:
                self.parameter_map[key_num][classname] = {dirname:{"value":v,"control":{"start":[0,0],"end":[0,0]}}}
        else:
            self.parameter_map[key_num] = {classname: {dirname: {"value": v, "control": {"start": [0, 0], "end": [0, 0]}}}}

    # 将只有一个预设的slider的值存到data中
    def set_non_morph_control_panel_parame(self, slider):
        key_num = self.get_now_key_value()
        classname = slider.GetName()
        v = slider.GetValue()
        if key_num in self.parameter_map:
            if classname in self.parameter_map[key_num]:
                self.parameter_map[key_num][classname]["value"] = v
            else:
                self.parameter_map[key_num][classname] = {"value":v,"control":{"start":[0,0],"end":[0,0]}}
        else:
            self.parameter_map[key_num] = {classname:{"value":v,"control":{"start":[0,0],"end":[0,0]}}}

    # 更新时间轴数据板的子函数，更新函数
    def update_timeline_data_map_sub_func(self,function_map,stat):
        for k,v in function_map[stat].items():
            if k in self.morph_lable:
                type = v["type"]
                if "left" in v and bool(v["left"]):
                    begin  = v["left"]["start"][0]
                    end = v["left"]["end"][0]
                    start_x = v["left"]["start"][0]
                    start_y = v["left"]["start"][1]
                    start_control_x = v["left"]["start_control"][0]
                    start_control_y = v["left"]["start_control"][1]
                    end_x = v["left"]["end"][0]
                    end_y = v["left"]["end"][1]
                    end_control_x = v["left"]["end_control"][0]
                    end_control_y = v["left"]["end_control"][1]
                    for i in range(begin,end):
                        self.control_slider_morph_data_map[i][self.morph_lable.index(k)][0] = type
                        self.control_slider_morph_data_map[i][self.morph_lable.index(k)][1] = self.cubic_bezier(in_x=i,
                                                                                                          start_x=start_x,
                                                                                                          start_y=start_y,
                                                                                                          start_c_x=start_control_x,
                                                                                                          start_c_y=start_control_y,
                                                                                                          end_x=end_x,
                                                                                                          end_y=end_y,
                                                                                                          end_c_x=end_control_x,
                                                                                                          end_c_y=end_control_y)
                if "right" in v and bool(v["right"]):
                    begin  = v["right"]["start"][0]
                    end = v["right"]["end"][0]
                    start_x = v["right"]["start"][0]
                    start_y = v["right"]["start"][1]
                    start_control_x = v["right"]["start_control"][0]
                    start_control_y = v["right"]["start_control"][1]
                    end_x = v["right"]["end"][0]
                    end_y = v["right"]["end"][1]
                    end_control_x = v["right"]["end_control"][0]
                    end_control_y = v["right"]["end_control"][1]
                    for i in range(begin,end):
                        self.control_slider_morph_data_map[i][self.morph_lable.index(k)][0] = type
                        self.control_slider_morph_data_map[i][self.morph_lable.index(k)][2] = self.cubic_bezier(in_x=i,
                                                                                                          start_x=start_x,
                                                                                                          start_y=start_y,
                                                                                                          start_c_x=start_control_x,
                                                                                                          start_c_y=start_control_y,
                                                                                                          end_x=end_x,
                                                                                                          end_y=end_y,
                                                                                                          end_c_x=end_control_x,
                                                                                                          end_c_y=end_control_y)
            elif k in self.non_morph_lable:
                begin  = v["start"][0]
                end = v["end"][0]
                start_x = v["start"][0]
                start_y = v["start"][1]
                start_control_x = v["start_control"][0]
                start_control_y = v["start_control"][1]
                end_x = v["end"][0]
                end_y = v["end"][1]
                end_control_x = v["end_control"][0]
                end_control_y = v["end_control"][1]
                for i in range(begin,end):

                    self.control_slider_non_morph_data_map[i][self.non_morph_lable.index(k)] = self.cubic_bezier(in_x=i,
                                                                                                        start_x=start_x,
                                                                                                        start_y=start_y,
                                                                                                        start_c_x=start_control_x,
                                                                                                        start_c_y=start_control_y,
                                                                                                        end_x=end_x,
                                                                                                        end_y=end_y,
                                                                                                        end_c_x=end_control_x,
                                                                                                        end_c_y=end_control_y)


    # 更新时间轴参数板
    def update_timeline_data_map(self):
        key = self.get_now_key_value()
        # timeline_keys = list(self.parameter_map.keys()).sort()
        function_map = self.find_keys()

        if bool(function_map):
            self.update_timeline_data_map_sub_func(function_map=function_map,stat="start")
            self.update_timeline_data_map_sub_func(function_map=function_map,stat="end")

class MainFrame(wx.Frame):
    def __init__(self, poser: Poser, device: torch.device):
        super().__init__(None, wx.ID_ANY, "Poser")
        self.poser = poser
        self.isplaying=False
        self.fps = 30
        self.dtype = self.poser.get_dtype()
        self.device = device
        self.image_size = self.poser.get_image_size()
        self.data = ParameterStore() # 存放时间轴数据的对象
        self.morph_categories = [
            PoseParameterCategory.EYEBROW,
            PoseParameterCategory.EYE,
            PoseParameterCategory.MOUTH,
            PoseParameterCategory.IRIS_MORPH
        ]

        self.non_morph_categories = [
            PoseParameterCategory.IRIS_ROTATION,
            PoseParameterCategory.FACE_ROTATION,
            PoseParameterCategory.BODY_ROTATION,
            PoseParameterCategory.BREATHING
        ]
        # 多个预设组的slider控制组件集合
        self.morph_control_panels = {}
        # 没有预设组的slider控制组件集合
        self.non_morph_control_panels = {}

        self.wx_source_image = None
        self.torch_source_image = None

        self.big_main_sizer = wx.BoxSizer(wx.VERTICAL)
        self.SetSizer(self.big_main_sizer)
        self.SetAutoLayout(1)

        self.main_panel = wx.Panel(self, style=wx.NO_BORDER)
        self.main_sizer = wx.BoxSizer(wx.HORIZONTAL)
        self.main_panel.SetSizer(self.main_sizer)
        self.main_panel.SetAutoLayout(1)
        self.init_left_panel()
        self.init_control_panel()
        self.init_right_panel()
        self.main_sizer.Fit(self.main_panel)
        self.big_main_sizer.Add(self.main_panel, 0, wx.FIXED_MINSIZE)
        self.init_botton_panel()
        self.big_main_sizer.Fit(self)

        # 定时刷新图片，刷新图片的时候会调用get_current_pose函数，将当前的slider中的值更新为当前pose
        self.timer = wx.Timer(self, wx.ID_ANY)
        self.Bind(wx.EVT_TIMER, self.update_images, self.timer)

        # 点击播放后的timer，用于播放时间轴上的关键点
        self.play_timer = wx.Timer(self, wx.ID_ANY)
        self.Bind(wx.EVT_TIMER, self.on_play_timer, self.play_timer)

        save_image_id = wx.NewIdRef()
        self.Bind(wx.EVT_MENU, self.on_save_image, id=save_image_id)
        accelerator_table = wx.AcceleratorTable([
            (wx.ACCEL_CTRL, ord('S'), save_image_id)
        ])
        self.SetAcceleratorTable(accelerator_table)

        self.last_pose = None
        self.last_output_index = self.output_index_choice.GetSelection()
        self.last_output_numpy_image = None

        self.wx_source_image = None
        self.torch_source_image = None
        self.source_image_bitmap = wx.Bitmap(self.image_size, self.image_size)
        self.result_image_bitmap = wx.Bitmap(self.image_size, self.image_size)
        self.source_image_dirty = True

    def init_botton_panel(self):
        item_list = ["eyebrow","eye","mouth","iris_morphs","iris_rotation_x","iris_rotation_y","head_x","head_y","neck_z","body_y","body_z","breathing"]
        botton_width = self.image_size*2+240
        height_size = 200
        frame_num = 300
        timeline_gap = 13
        timeline_width = frame_num*3+timeline_gap*2
        slider_height = 22
        timeline_height = height_size-slider_height
        font_size = 9
        lable_gap = 18

        self.botton_panel = wx.Panel(self, style=wx.SIMPLE_BORDER, size=(botton_width, height_size))
        self.botton_panel_sizer = wx.BoxSizer(wx.HORIZONTAL)
        self.botton_panel.SetSizer(self.botton_panel_sizer)
        self.botton_panel.SetAutoLayout(1)
        
        # 左侧的标签栏
        self.botton_lable_panel = wx.Panel(self.botton_panel, style=wx.NO_BORDER)
        self.botton_lable_sizer = wx.BoxSizer(wx.VERTICAL)
        self.botton_lable_panel.SetSizer(self.botton_lable_sizer)
        self.botton_panel.SetAutoLayout(1)
        
        self.static_text_list = []

        for text_index in range(len(item_list)):
            
            lable_panel = SimpleLableText(self.botton_lable_panel,item_list[text_index],font_size)
            self.static_text_list.append(lable_panel)
            self.botton_lable_sizer.Add(lable_panel, 0, wx.ALIGN_RIGHT)

        # 将标签栏加入到botton panel中
        self.botton_lable_sizer.Fit(self.botton_lable_panel)
        self.botton_panel_sizer.Add(self.botton_lable_panel, 1, wx.TOP,slider_height+lable_gap)

        # 时间轴面板添加到底部面板中
        self.botton_timeline_panel = TimelnePanel(self,
                                                  self.botton_panel,
                                                  timeline_width=timeline_width, 
                                                  timeline_height=timeline_height, 
                                                  slider_height=slider_height,
                                                  frame_num=frame_num,
                                                  timeline_gap=timeline_gap,
                                                  lable_len=len(item_list),
                                                  lable_gap=lable_gap,
                                                  data_map = self.data,
                                                  item_list=item_list)
        self.botton_panel_sizer.Add(self.botton_timeline_panel, 1)

        # 将按钮加入到底部栏中
        self.botton_button_panel = wx.Panel(self.botton_panel, style=wx.NO_BORDER)
        self.botton_button_sizer = wx.BoxSizer(wx.VERTICAL)
        self.botton_button_panel.SetSizer(self.botton_button_sizer)
        self.botton_button_panel.SetAutoLayout(1)

        self.button_play = wx.Button(self.botton_button_panel, wx.ID_ANY, "\nPLAY\n")
        self.botton_button_sizer.Add(self.button_play, 1, wx.EXPAND)
        self.button_play.Bind(wx.EVT_BUTTON, self.on_play)

        # self.button_pause = wx.Button(self.botton_button_panel, wx.ID_ANY, "\nPAUSE\n")
        # self.botton_button_sizer.Add(self.button_pause, 1, wx.EXPAND)
        
        self.button_delete = wx.Button(self.botton_button_panel, wx.ID_ANY, "\nDELETE\n")
        self.botton_button_sizer.Add(self.button_delete, 1, wx.EXPAND)

        self.button_clear = wx.Button(self.botton_button_panel, wx.ID_ANY, "\nCLEAR\n")
        self.botton_button_sizer.Add(self.button_clear, 1, wx.EXPAND)
        self.button_clear.Bind(wx.EVT_BUTTON, self.clear_current_data)

        self.botton_panel_sizer.Add(self.botton_button_panel, 0)

        # 将底部状态栏加入到整体面板中
        self.botton_panel_sizer.Fit(self.botton_panel)
        self.big_main_sizer.Add(self.botton_panel, 0)

    def init_left_panel(self):
        self.control_panel = wx.Panel(self.main_panel, style=wx.SIMPLE_BORDER, size=(self.image_size, -1))
        self.left_panel = wx.Panel(self.main_panel, style=wx.SIMPLE_BORDER)
        left_panel_sizer = wx.BoxSizer(wx.VERTICAL)
        self.left_panel.SetSizer(left_panel_sizer)
        self.left_panel.SetAutoLayout(1)

        self.source_image_panel = wx.Panel(self.left_panel, size=(self.image_size, self.image_size),
                                           style=wx.SIMPLE_BORDER)
        self.source_image_panel.Bind(wx.EVT_PAINT, self.paint_source_image_panel)
        self.source_image_panel.Bind(wx.EVT_ERASE_BACKGROUND, self.on_erase_background)
        left_panel_sizer.Add(self.source_image_panel, 0, wx.FIXED_MINSIZE)

        self.load_image_button = wx.Button(self.left_panel, wx.ID_ANY, "\nLoad Image\n\n")
        left_panel_sizer.Add(self.load_image_button, 1, wx.EXPAND)
        self.load_image_button.Bind(wx.EVT_BUTTON, self.load_image)

        # 添加曲线绘制面板
        self.curve_panel = CurvePlottingPanel(self.left_panel)
        left_panel_sizer.Add(self.curve_panel, 0, wx.EXPAND)

        left_panel_sizer.Fit(self.left_panel)
        self.main_sizer.Add(self.left_panel, 0, wx.FIXED_MINSIZE)

    def on_erase_background(self, event: wx.Event):
        pass

    def init_control_panel(self):
        self.control_panel_sizer = wx.BoxSizer(wx.VERTICAL)
        self.control_panel.SetSizer(self.control_panel_sizer)
        self.control_panel.SetMinSize(wx.Size(256, 1))

        morph_categories = self.morph_categories
        morph_category_titles = {
            PoseParameterCategory.EYEBROW: "eyebrow",
            PoseParameterCategory.EYE: "eye",
            PoseParameterCategory.MOUTH: "mouth",
            PoseParameterCategory.IRIS_MORPH: "iris_morphs",
        }
        for category in morph_categories:
            param_groups = self.poser.get_pose_parameter_groups() # 获取的是所有的修改器的预设参数列表，比如眉毛是笑的状态还是怒的状态等等
            filtered_param_groups = [group for group in param_groups if group.get_category() == category] # 遍历状态列表，找到参数对应的状态列表，比如眉毛的状态
            if len(filtered_param_groups) == 0:
                continue # 如果不是具有预设参数的修改器则跳过。
            control_panel = MorphCategoryControlPanel(
                self.control_panel,
                morph_category_titles[category],
                category,
                self.poser.get_pose_parameter_groups(),
                data=self.data)
            self.morph_control_panels[category] = control_panel
            self.control_panel_sizer.Add(control_panel, 0, wx.EXPAND)

        non_morph_categories = self.non_morph_categories

        for category in non_morph_categories:
            param_groups = self.poser.get_pose_parameter_groups()
            filtered_param_groups = [group for group in param_groups if group.get_category() == category]
            if len(filtered_param_groups) == 0:
                continue
            control_panel = SimpleParamGroupsControlPanel(
                self.control_panel,
                category,
                self.poser.get_pose_parameter_groups(),
                data=self.data)
            self.non_morph_control_panels[category] = control_panel
            self.control_panel_sizer.Add(control_panel, 0, wx.EXPAND)

        self.control_panel_sizer.Fit(self.control_panel)
        self.main_sizer.Add(self.control_panel, 1, wx.FIXED_MINSIZE)

    def init_right_panel(self):
        self.right_panel = wx.Panel(self.main_panel, style=wx.NO_BORDER)
        right_panel_sizer = wx.BoxSizer(wx.VERTICAL)
        self.right_panel.SetSizer(right_panel_sizer)
        self.right_panel.SetAutoLayout(1)

        self.result_image_panel = wx.Panel(self.right_panel,
                                           size=(self.image_size, self.image_size),
                                           style=wx.SIMPLE_BORDER)
        self.result_image_panel.Bind(wx.EVT_PAINT, self.paint_result_image_panel)
        self.result_image_panel.Bind(wx.EVT_ERASE_BACKGROUND, self.on_erase_background)

        self.output_index_choice = wx.Choice(
            self.right_panel,
            choices=[str(i) for i in range(self.poser.get_output_length())])
        self.output_index_choice.SetSelection(0)
        right_panel_sizer.Add(self.result_image_panel, 0, wx.FIXED_MINSIZE)
        right_panel_sizer.Add(self.output_index_choice, 0, wx.EXPAND)

        self.save_image_button = wx.Button(self.right_panel, wx.ID_ANY, "Save Image")
        right_panel_sizer.Add(self.save_image_button, 1, wx.EXPAND)
        self.save_image_button.Bind(wx.EVT_BUTTON, self.on_save_image)

        # 添加预设下拉选择框
        self.preset_choice = wx.Choice(self.right_panel, choices=["a","b","c"])
        right_panel_sizer.Add(self.preset_choice, 1, wx.EXPAND)

        # 添加保存和加载按钮
        self.preset_panel = wx.Panel(self.right_panel, size=(35, 5), style=wx.NO_BORDER)
        preset_panel_sizer = wx.BoxSizer(wx.HORIZONTAL)
        self.preset_panel.SetSizer(preset_panel_sizer)
        self.preset_panel.SetAutoLayout(1)

        self.preset_save_button = wx.Button(self.preset_panel, wx.ID_ANY, "Save Preset")
        self.preset_load_button = wx.Button(self.preset_panel, wx.ID_ANY, "Load Preset")
        preset_panel_sizer.Add(self.preset_save_button, 1, wx.EXPAND)
        preset_panel_sizer.Add(self.preset_load_button, 1, wx.EXPAND)

        preset_panel_sizer.Fit(self.preset_panel)
        right_panel_sizer.Add(self.preset_panel, 1, wx.EXPAND)

        # 添加跳转面板
        self.time_jump_panel = wx.Panel(self.right_panel, style=wx.NO_BORDER)
        time_jump_panel_sizer = wx.BoxSizer(wx.HORIZONTAL)
        self.time_jump_panel.SetSizer(time_jump_panel_sizer)
        self.time_jump_panel.SetAutoLayout(1)

        self.s_text_ctrl = wx.TextCtrl(self.time_jump_panel, wx.ID_ANY, "00", size=(30,-1))
        self.colon_static_text = wx.StaticText(self.time_jump_panel, label=":", style=wx.ALIGN_CENTER)
        self.z_text_ctrl = wx.TextCtrl(self.time_jump_panel, wx.ID_ANY, "00", size=(30,-1))
        self.goto_button = wx.Button(self.time_jump_panel, wx.ID_ANY, "GO TO")

        time_jump_panel_sizer.Add(self.s_text_ctrl, 1, wx.EXPAND)
        time_jump_panel_sizer.Add(self.colon_static_text, 1, wx.EXPAND)
        time_jump_panel_sizer.Add(self.z_text_ctrl, 1, wx.EXPAND)
        time_jump_panel_sizer.Add(self.goto_button, 1, wx.EXPAND)

        time_jump_panel_sizer.Fit(self.time_jump_panel)
        right_panel_sizer.Add(self.time_jump_panel, 0, wx.EXPAND|wx.TOP, 5)

        # 记录当前的关键帧
        self.key_frames_button = wx.Button(self.right_panel, wx.ID_ANY, "KEY FRAMES")
        right_panel_sizer.Add(self.key_frames_button, 0, wx.EXPAND|wx.TOP, 5)
        self.key_frames_button.Bind(wx.EVT_BUTTON, self.on_key_frames_button)

        # 添加切换按钮
        self.switch_button = wx.Button(self.right_panel, wx.ID_ANY, "CURVE SWITCH")
        right_panel_sizer.Add(self.switch_button, 0, wx.EXPAND|wx.TOP, 5)

        # 添加渲染按钮
        self.render_button = wx.Button(self.right_panel, wx.ID_ANY, "Render")
        right_panel_sizer.Add(self.render_button, 0, wx.EXPAND|wx.TOP, 5)

        right_panel_sizer.Fit(self.right_panel)
        self.main_sizer.Add(self.right_panel, 0, wx.EXPAND)

    def create_param_category_choice(self, param_category: PoseParameterCategory):
        params = []
        for param_group in self.poser.get_pose_parameter_groups():
            if param_group.get_category() == param_category:
                params.append(param_group.get_group_name())
        choice = wx.Choice(self.control_panel, choices=params)
        if len(params) > 0:
            choice.SetSelection(0)
        return choice

    # 清除当前时间帧下的数据
    def clear_current_data(self, event):
        self.data.clear_timeline_current_data()
        self.data.update_timeline_data_map()
        self.Refresh()

    # 播放定时器
    def on_play_timer(self,event):
        key = self.data.get_now_key_value()
        if key < self.data.frame_num:
            self.botton_timeline_panel.timeline_slider.SetValue(key+1)
            wx.PostEvent(self.botton_timeline_panel.timeline_slider, wx.CommandEvent(wx.EVT_SLIDER.typeId, self.botton_timeline_panel.timeline_slider.GetId()))
        else:
            self.botton_timeline_panel.timeline_slider.SetValue(0)
            wx.PostEvent(self.botton_timeline_panel.timeline_slider, wx.CommandEvent(wx.EVT_SLIDER.typeId, self.botton_timeline_panel.timeline_slider.GetId()))
        
        self.update_images_func()

    # 播放按钮回调
    def on_play(self,event):
        if self.isplaying:
            self.play_timer.Stop()
            self.timer.Start(self.fps)
            self.button_play.SetLabel("\nPLAY\n")
            self.isplaying = False
        else:
            self.timer.Stop()
            self.play_timer.Start(1000//self.fps)
            self.button_play.SetLabel("\nSTOP\n")
            self.isplaying = True

    # 记录当前所有参数到关键帧
    def on_key_frames_button(self, event):
        for k,v in self.morph_control_panels.items():
            self.data.set_morph_control_panel_parame(v.left_slider,v.choice)
            self.data.set_morph_control_panel_parame(v.right_slider,v.choice)

        for k,v in self.non_morph_control_panels.items():
            for slider in v.sliders:
                self.data.set_non_morph_control_panel_parame(slider)
        
        self.data.update_timeline_data_map()
        self.botton_panel.Refresh()

    def load_image(self, event: wx.Event):
        dir_name = "data/images"
        file_dialog = wx.FileDialog(self, "Choose an image", dir_name, "", "*.png", wx.FD_OPEN)
        if file_dialog.ShowModal() == wx.ID_OK:
            image_file_name = os.path.join(file_dialog.GetDirectory(), file_dialog.GetFilename())
            try:
                pil_image = resize_PIL_image(extract_PIL_image_from_filelike(image_file_name),
                                             (self.poser.get_image_size(), self.poser.get_image_size()))
                w, h = pil_image.size
                if pil_image.mode != 'RGBA':
                    self.source_image_string = "Image must have alpha channel!"
                    self.wx_source_image = None
                    self.torch_source_image = None
                else:
                    self.wx_source_image = wx.Bitmap.FromBufferRGBA(w, h, pil_image.convert("RGBA").tobytes())
                    self.torch_source_image = extract_pytorch_image_from_PIL_image(pil_image)\
                        .to(self.device).to(self.dtype)
                self.source_image_dirty = True
                self.Refresh()
                self.Update()
            except:
                message_dialog = wx.MessageDialog(self, "Could not load image " + image_file_name, "Poser", wx.OK)
                message_dialog.ShowModal()
                message_dialog.Destroy()
        file_dialog.Destroy()

    def paint_source_image_panel(self, event: wx.Event):
        wx.BufferedPaintDC(self.source_image_panel, self.source_image_bitmap)

    def paint_result_image_panel(self, event: wx.Event):
        wx.BufferedPaintDC(self.result_image_panel, self.result_image_bitmap)

    def draw_nothing_yet_string_to_bitmap(self, bitmap):
        dc = wx.MemoryDC()
        dc.SelectObject(bitmap)

        dc.Clear()
        font = wx.Font(wx.FontInfo(14).Family(wx.FONTFAMILY_SWISS))
        dc.SetFont(font)
        w, h = dc.GetTextExtent("Nothing yet!")
        dc.DrawText("Nothing yet!", (self.image_size - w) // 2, (self.image_size - - h) // 2)

        del dc

    def get_current_pose(self):
        current_pose = [0.0 for i in range(self.poser.get_num_parameters())]
        for morph_control_panel in self.morph_control_panels.values():
            morph_control_panel.set_param_value(current_pose)
        for rotation_control_panel in self.non_morph_control_panels.values():
            rotation_control_panel.set_param_value(current_pose)
        return current_pose

    # 更新图像的函数
    def update_images_func(self):
        current_pose = self.get_current_pose()
        if not self.source_image_dirty \
                and self.last_pose is not None \
                and self.last_pose == current_pose \
                and self.last_output_index == self.output_index_choice.GetSelection():
            return
        self.last_pose = current_pose
        self.last_output_index = self.output_index_choice.GetSelection()

        if self.torch_source_image is None:
            self.draw_nothing_yet_string_to_bitmap(self.source_image_bitmap)
            self.draw_nothing_yet_string_to_bitmap(self.result_image_bitmap)
            self.source_image_dirty = False
            self.Refresh()
            self.Update()
            return

        if self.source_image_dirty:
            dc = wx.MemoryDC()
            dc.SelectObject(self.source_image_bitmap)
            dc.Clear()
            dc.DrawBitmap(self.wx_source_image, 0, 0)
            self.source_image_dirty = False

        pose = torch.tensor(current_pose, device=self.device, dtype=self.dtype)
        output_index = self.output_index_choice.GetSelection()
        with torch.no_grad():
            output_image = self.poser.pose(self.torch_source_image, pose, output_index)[0].detach().cpu() # 运算输出变换后的图片

        numpy_image = convert_output_image_from_torch_to_numpy(output_image)
        self.last_output_numpy_image = numpy_image
        wx_image = wx.ImageFromBuffer(
            numpy_image.shape[0],
            numpy_image.shape[1],
            numpy_image[:, :, 0:3].tobytes(),
            numpy_image[:, :, 3].tobytes())
        wx_bitmap = wx_image.ConvertToBitmap()

        dc = wx.MemoryDC()
        dc.SelectObject(self.result_image_bitmap)
        dc.Clear()
        dc.DrawBitmap(wx_bitmap,
                      (self.image_size - numpy_image.shape[0]) // 2,
                      (self.image_size - numpy_image.shape[1]) // 2,
                      True)
        del dc

        self.Refresh()
        self.Update()

    # 定时更新图像的回调函数
    def update_images(self, event: wx.Event):
        self.update_images_func()

    def on_save_image(self, event: wx.Event):
        if self.last_output_numpy_image is None:
            logging.info("There is no output image to save!!!")
            return

        dir_name = "data/images"
        file_dialog = wx.FileDialog(self, "Choose an image", dir_name, "", "*.png", wx.FD_SAVE)
        if file_dialog.ShowModal() == wx.ID_OK:
            image_file_name = os.path.join(file_dialog.GetDirectory(), file_dialog.GetFilename())
            try:
                if os.path.exists(image_file_name):
                    message_dialog = wx.MessageDialog(self, f"Override {image_file_name}", "Manual Poser",
                                                      wx.YES_NO | wx.ICON_QUESTION)
                    result = message_dialog.ShowModal()
                    if result == wx.ID_YES:
                        self.save_last_numpy_image(image_file_name)
                    message_dialog.Destroy()
                else:
                    self.save_last_numpy_image(image_file_name)
            except:
                message_dialog = wx.MessageDialog(self, f"Could not save {image_file_name}", "Manual Poser", wx.OK)
                message_dialog.ShowModal()
                message_dialog.Destroy()
        file_dialog.Destroy()

    def save_last_numpy_image(self, image_file_name):
        numpy_image = self.last_output_numpy_image
        pil_image = PIL.Image.fromarray(numpy_image, mode='RGBA')
        os.makedirs(os.path.dirname(image_file_name), exist_ok=True)
        pil_image.save(image_file_name)


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description='Manually pose a character image.')
    parser.add_argument(
        '--model',
        type=str,
        required=False,
        default='standard_float',
        choices=['standard_float', 'separable_float', 'standard_half', 'separable_half'],
        help='The model to use.')
    args = parser.parse_args()

    device = torch.device('cuda')
    try:
        poser = load_poser(args.model, device)
    except RuntimeError as e:
        print(e)
        sys.exit()

    app = wx.App()
    main_frame = MainFrame(poser, device)
    main_frame.Show(True)
    main_frame.timer.Start(30)
    app.MainLoop()
