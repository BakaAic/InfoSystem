import configparser
import tkinter as tk
from tkinter import ttk

_c:bool=True  #customtkinter是否已安装
try:
    import customtkinter as ctk
except ImportError:
    #未安装customtkinter,尝试安装
    try:
        import pip
        pip.main(['install', 'customtkinter'])
        #安装成功，重新导入
        import customtkinter as ctk
    except:
        #安装失败，使用标准tkinter
        _c=False

# _c=False    #强制使用标准tkinter
        
add_button:tk.Button|None=None      #新增按钮全局变量

class SYSTEM:
    #系统类，用于报错环境信息，以类方法的形式调整环境信息
    curIndex:int=0  #当前序号值
    maxInfo:int=18  #最大显示条数
    #==========================================#
    #以下为信息对应名称，可修改，第一个id/序号不可变,后续内容可自定义
    #修改时需保持与infoNames_trans对应且数量一致
    #==========================================#
    infoNames=["id","Name","SubInfo1","SubInfo2","SubInfo3"]  #信息对应名称，可修改，第一个id不可变
    infoNames_trans=["序号","名称","子信息1","子信息2","子信息3"]  #信息对应名称汉字，可修改，第一个id不可变
    dataPath="data.ini" #数据保存路径,默认为当前目录下的data.ini
    
    @classmethod
    def items(cls):
        #用于返回保存信息
        return zip(["curIndex","maxInfo"],[cls.curIndex,cls.maxInfo])
    @classmethod
    def getNewIndex(cls):
        #获取新的序号,自增1,仅可自增,不可减少
        cls.curIndex+=1
        return cls.curIndex

class Data:
    #数据类,用于抽象化数据
    def __init__(self,*args):
        self.id=args[0] #默认取第一个值为id,id为索引,不可重复
        self._all_info_=[*args] #保存所有信息,数量需吻合infoName数量
        self._all_name_=SYSTEM.infoNames    #从环境中取出当前信息名
        
    def items(self):
        #用于返回保存信息
        return zip(self._all_name_,self._all_info_)
        
    def __getitem__(self,key)->int|str:
        #通过索引查找并返回数据
        return self._all_info_[key]
    
    def __setitem__(self,key,value:int|str):
        #通过索引设置数据
        self._all_info_[key]=value
        
    def __repr__(self):
        #调整数据信息打印格式
        msg=','.join(map(lambda x:str(x[0])+"='"+str(x[1])+"'",zip(self._all_name_,self._all_info_)))
        return "Data{"+msg+"}"

class Datas:
    #数据集合类,用于管理数据
    def __init__(self):
        self.data={}    #数据集合初始状态
        self.filterData={}  #筛选后的数据集合
        self.load()     #加载数据
        
    def updateFilterData(self,filter:str,filterIndex:int):
        #更新筛选后的数据集合
        self.filterData.clear()
        for key in self.data:
            if filter in self.data[key][filterIndex]:
                self.filterData[key]=self.data[key]
        
    def add(self,data:Data):
        #添加数据到集合
        self.data[data.id]=data
        
    def remove(self,key:int):
        #删除数据
        self.data.pop(key)
        
    def save(self):
        #保存数据
        config=configparser.ConfigParser()  #使用configparser保存数据
        for key in self.data:
            config[str(key)]=self.data[key]
        config['SYSTEM']=SYSTEM
        with open(SYSTEM.dataPath,"w") as f: #保存到data.ini
            config.write(f)
    
    def load(self):
        #读取数据
        config=configparser.ConfigParser()
        config.read(SYSTEM.dataPath)    #读取data.ini
        for key in config:
            if key=="SYSTEM":   #读取系统信息
                SYSTEM.maxInfo=int(config[key]["maxInfo"])
                SYSTEM.curIndex=int(config[key]["curIndex"])
                continue
            if key=="DEFAULT":  #默认配置,忽略
                continue
            self.data[int(key)]=Data(*config[key].values()) #读取数据,并转换为Data对象,保存到data中
        
    def __getitem__(self,key)->Data:
        #通过索引查找并返回数据
        return self.data[key]
    
    def __setitem__(self,key,value:Data):
        #通过索引设置数据
        self.data[key]=value

data=Datas()    #数据集合对象实例化

def updateTree(filter=False):
    #更新tree内容
    tree.delete(*tree.get_children())   #清空tree
    if filter==False:
        for key in data.data:
            tree.insert("", "end", text=str(key), values=data.data[key]._all_info_[1:])   #插入数据
    else:
        for key in data.filterData:
            tree.insert("", "end", text=str(key), values=data.filterData[key]._all_info_[1:])
        

def edit_start(event):
    #双击产生编辑框
    item = tree.selection()[0]  #获取选中的行
    column = tree.identify_column(event.x)  #获取选中的列
    region = tree.identify_region(event.x, event.y) #获取选中的区域类别
    if column == "#0" or region!="cell":    #如果选中的是id列或者不是单元格，则忽略
        return
    # 获取单元格的位置
    x, y, width, height = tree.bbox(item, column)
    # 获取对应单元格的值
    value = tree.set(item, column)
    # 创建编辑框
    entry = ttk.Entry(tree, width=width)
    entry.place(x=x, y=y, width=width, height=height)
    entry.insert(0, value)
    #设置焦点
    entry.focus()
    #绑定事件,因lambda函数通过闭包方式传递的参数内容会固定，所以每次点击时用不同参数覆盖后续触发动作
    entry.bind("<Return>", lambda event: edit_finished(entry, item, column))    #按下回车键后，结束编辑
    entry.bind("<FocusOut>", lambda event: edit_finished(entry, item, column))  #编辑框失去焦点后，结束编辑
    
def edit_finished(entry, item, column):
    #编辑框失去焦点或者按下回车键后，将编辑框中的值赋给单元格
    value = entry.get()
    try:    #如果输入时被删除会报错，需捕获异常
        tree.set(item, column, value)   #设置单元格的值
        itemObj=tree.item(item=item)    #获取行的信息->Treeview.Item对象
        data[int(itemObj["text"])][int(column[1])]=value    #设置数据的值
    except:
        pass
    entry.destroy() #销毁编辑框
    
def showButton():
    global add_button
    # 显示新增按钮    
    if add_button:  #如果按钮已经存在，则删除
        add_button.destroy()
    info_count=len(tree.get_children())  #获取tree的行数
    #如果使用customtkinter,则使用CTkButton
    if _c:
        #显示行数小于最大行数时，动态调整按钮位置，否则固定在最下方
        if info_count<SYSTEM.maxInfo:
            add_button = ctk.CTkButton(tree, text="新增", height=3,width=630, command=add_info) #父控件为tree(Treeview)，将按钮放在tree最后一条内容的下方
            add_button.place(x=4, y=(info_count+1)*20+5) #将按钮放在tree的下方
        else:
            add_button = ctk.CTkButton(L2, text="新增", height=3,width=630, command=add_info)   #父控件为L2(LabelFrame)，将按钮放在L2的底部
            add_button.pack(side="bottom")
    else:   #使用标准tkinter版本
        if info_count<SYSTEM.maxInfo:
            tree.configure(height=SYSTEM.maxInfo)
            add_button = ttk.Button(tree, text="新增",width=88, command=add_info)
            add_button.place(x=4, y=(info_count+1)*20+5) #将按钮放在tree的下方
        else:
            tree.configure(height=SYSTEM.maxInfo-1)
            add_button = ttk.Button(L2, text="新增",width=88, command=add_info)
            add_button.pack(side="bottom")
        
def visiableButton(status:bool):
    #根据鼠标进入或离开，显示或隐藏新增按钮
    if status==False:
        #鼠标离开时，隐藏按钮
        #因为有两种布局方式，所以需要分别处理
        add_button.place_forget()
        add_button.pack_forget()
    else:
        #鼠标进入时，显示按钮
        showButton()
        
def mouseMenu(event):
    #右键菜单
    tree.selection_set(tree.identify_row(event.y))  #选中右键点击的行,避免右键点击后被选中的行不是右键点击的行
    menu = tk.Menu(root, tearoff=0, takefocus=0)    #创建菜单
    menu.add_command(label="新增", command=add_info)
    menu.add_command(label="修改", command=lambda :edit_start(event))   #修改功能与双击相同，通过传入event，确保选中的是右键点击的行
    menu.add_command(label="保存", command=data.save)
    menu.add_separator()    #分割线
    menu.add_command(label="删除", command=del_info)
    menu.post(event.x_root, event.y_root)   #根据鼠标位置显示菜单
    
def del_info(*event):
    #删除一行
    item=tree.selection()[0]   #获取选中的行
    #需先删除数据在删除tree中的行，否则找不到对应的数据
    data.remove(int(tree.item(item,"text")))    #删除数据
    tree.delete(item)   #删除tree中的行
    showButton()   #重新显示按钮    

def add_info():
    global add_button
    #新增一行
    index=SYSTEM.getNewIndex()    #获取新的id
    tree.insert("", "end", text=str(index), values=tuple(["" for i in range(len(SYSTEM.infoNames)-1)]) )  #插入一行,默认值全部为空，长度取自infoNames（不包含id）
    data.add(Data(index,*["" for i in range(len(SYSTEM.infoNames)-1)]))    #添加数据，id为index，其余为默认值，长度取自infoNames（不包含id）
    showButton()   #重新显示按钮
    if len(tree.get_children())>=SYSTEM.maxInfo:
        tree.yview_moveto(1)    #滚动到最底部
    
def trigger_filter(*event):
    #触发筛选信息
    root.after(10,filter_info)    #延迟10ms后执行筛选方法,因为触发事件时输入框内容还未更新

def filter_info():
    #筛选信息
    filter_text=filter_entry.get()  #获取输入框内容
    if filter_text=="": #如果输入框内容为空，则直接更新，使用非筛选模式
        updateTree()
    filter_type=SYSTEM.infoNames[SYSTEM.infoNames_trans.index(C1.get())]    #获取筛选方式，并转换为对应的infoNames
    data.updateFilterData(filter_text,SYSTEM.infoNames.index(filter_type))  #更新筛选后的数据集合
    updateTree(True)    #更新tree内容，使用筛选模式
    
if _c:
    #使用customtkinter,设置为dark风格
    ctk.set_appearance_mode("dark")
    root = ctk.CTk()
else:
    #使用标准tkinter的情况下，不设置风格
    root = tk.Tk()

root.title("信息管理系统")  #设置窗口标题
root.resizable(0,0) #设置窗口大小不可变
#创建两个LabelFrame,通过Frame进行空间区分
L1=ttk.LabelFrame(root,text="查询",width=658,height=70)
L2=ttk.LabelFrame(root,text="信息",width=630,height=500)

#布局
L1.grid(row=0,column=0,padx=5,pady=0)
L1.grid_propagate(0)    #设置不自动调整大小
L1.pack_propagate(0)    #设置不自动调整大小,支持pack布局
L2.grid(row=1,column=0,padx=5,pady=0)
L2.grid_propagate(0)    #设置不自动调整大小

tree = ttk.Treeview(L2, columns=tuple(SYSTEM.infoNames[1:]),height=SYSTEM.maxInfo)
tree.heading("#0", text="id")   #添加表头名称
for i in range(1,len(SYSTEM.infoNames)):
    tree.heading(SYSTEM.infoNames[i], text=SYSTEM.infoNames_trans[i])   #从环境变量中动态添加各项表头名称

tree.column("#0", width=35, anchor="center")    #设置单元格宽度及对齐方式
for i in range(1,len(SYSTEM.infoNames)):
    tree.column(SYSTEM.infoNames[i], width=150, anchor="center")    #动态设置单元格宽度及对齐方式
    
if _c:
    #使用customtkinter的情况
    filter_entry = ctk.CTkEntry(L1, width=250)    #查询输入框
    filter_entry.configure(text_color="gray")    #设置字体颜色为灰色
    C1=ctk.CTkComboBox(L1, values=SYSTEM.infoNames_trans[1:], width=140)    #筛选方式下拉框
    #用来lambda函数完成多个事件绑定
    _FI=lambda event: [filter_entry.delete(0, tk.END),filter_entry.configure(text_color="white"),trigger_filter()]   #输入框获取焦点时清空内容
    _FO=lambda event: [filter_entry.delete(0, tk.END),filter_entry.insert(0, "请输入查询内容"),filter_entry.configure(text_color="gray")]\
        if filter_entry.get()=='' else filter_entry.configure(text_color="white")   #输入框失去焦点时显示提示内容同时修改颜色,判断如果输入框内容有值则不显示提示内容
else:
    #使用标准tkinter的情况
    filter_entry = ttk.Entry(L1, width=34)    #查询输入框
    filter_entry.configure(foreground="gray")    #设置字体颜色为灰色
    C1=ttk.Combobox(L1, values=SYSTEM.infoNames_trans[1:],width=13)   #筛选方式下拉框  
    C1.set(SYSTEM.infoNames_trans[1])   #设置默认值
    _FI=lambda event: [filter_entry.delete(0, tk.END),filter_entry.configure(foreground="black"),trigger_filter()]
    _FO=lambda event: [filter_entry.delete(0, tk.END),filter_entry.insert(0, "请输入查询内容"),filter_entry.configure(foreground="gray")]\
        if filter_entry.get()=='' else filter_entry.configure(foreground="black")
    
ttk.Label(L1, text="查询条件：").pack(side="left", padx=3, pady=5)
filter_entry.pack(side="left", padx=3, pady=5) 
ttk.Label(L1, text="筛选方式：").pack(side="left", padx=3, pady=5)
C1.pack(side="left", padx=3, pady=5)

filter_entry.insert(0, "请输入查询内容")    #默认显示内容


filter_entry.bind("<Return>", trigger_filter)    #绑定回车键查询
C1.bind("<<ComboboxSelected>>",trigger_filter)  #绑定下拉框选择事件
filter_entry.bind("<FocusIn>", _FI)    #绑定输入框获取焦点时清空内容
filter_entry.bind("<FocusOut>", _FO)    #绑定输入框失去焦点时显示提示内容
filter_entry.bind("<Key>", trigger_filter)    #绑定输入框输入时字体颜色变为白色

#绑定方法
tree.bind("<Double-1>", edit_start)             #鼠标左键点击时进入编辑模式
tree.bind("<Button-3>", mouseMenu)              #鼠标右键唤起菜单
tree.bind("<Enter>", lambda event: visiableButton(True))    #鼠标进入时显示新增按钮
L2.bind("<Enter>", lambda event: visiableButton(True))      #鼠标进入时显示新增按钮
L2.bind("<Leave>", lambda event: visiableButton(False))     #鼠标离开时隐藏新增按钮
root.bind("<Control-s>", lambda event: data.save())    #绑定Ctrl+s保存数据
root.bind("<Destroy>", lambda event: data.save())    #窗口关闭时自动保存数据

#添加滚动条并绑定tree控件
scorllbar = ttk.Scrollbar(L2, orient="vertical", command=tree.yview)
tree.configure(yscrollcommand=scorllbar.set)
scorllbar.pack(side="right", fill="y")

#完成tree的布局
tree.pack(fill=tk.BOTH, expand=True)

updateTree()    #载入数据
root.update()   #载入数据后刷新显示，否则控件各项属性无法及时更新
showButton()    #显示新增按钮

root.mainloop()
