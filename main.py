import matplotlib.pyplot as plt
import tkinter as tk
from tkinter import ttk
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg,NavigationToolbar2Tk
from process import load #自訂封包
import time
import matplotlib.ticker as mticker
import matplotlib as mpl
from selenium import webdriver
from matplotlib.offsetbox import AnnotationBbox,TextArea
import os
import pandas as pd
import sqlite3

mpl.rcParams['toolbar'] = 'toolbar2'
plt.rcParams["font.family"]="Microsoft YaHei"
plt.rcParams["font.size"]=12

def draw_plot(data): #搜尋鈕 點選後畫圖
    ax1.clear()#清除前圖
    #無位與無車選項判斷
    if full.get()==empty.get()==True:
        full_data=load.warning_station(data,"full")
        empty_data=load.warning_station(data,"empty")
        new_index=full_data.index.union(empty_data.index)
        data=data.loc[new_index,:]
    elif full.get()==True:
        data=load.warning_station(data,"full")
    elif empty.get()==True:
        data=load.warning_station(data,"empty")
    global new_data,x,y
    new_data=data.copy()
    
    #若有資料===========================================
    if len(data.index)!=0:
        #處理圖表數值資訊
        y=new_data.sum()[4:]
        x=time_set(y.index)
        time_set(y.index)
        line,=ax1.plot(x,y,"-")
        plot_list=[line]
        legend_list=["正常營運時段"]
        #若資料不只一筆====================================
        if len(data.index)!=1: 
            #處理表標題
            city_tit=(lambda x:{"臺北市":"臺北市","新北市":"新北市","不限城市":"雙北"}[x])(city_combo.get())
            version_tit=(lambda x:{"1.0":"youbike1.0","2.0":"youbike2.0","不限版本":"youbike1.0 & 2.0"}[x])(version_combo.get())
            sarea_tit=area_combo.get() if area_combo.get()!="不限區域" else ""
            search_tit="關鍵字:\""+key_word.get()+"\"\n" if bool(key_word.get()) else ""
            final_tit=search_tit+city_tit+sarea_tit+version_tit
        #若資料不只一筆====================================
        #若資料僅一筆====================================
        else:
            number=int(data.index.get_level_values("number").values[0])
            final_tit=data["sna"].values[0]
            con=sqlite3.connect("merge.db")
            data_act=pd.read_sql(f"""SELECT {columns_sql} FROM act WHERE number={number}""",con,index_col=["city","version","number"])
            data_full=pd.read_sql(f"""SELECT {columns_sql} FROM bemp WHERE number={number}""",con,index_col=["city","version","number"])
            con.close()

            data_act=data_act.iloc[:,4:]
            data_empty=data.iloc[:,4:]
            data_full=data_full.iloc[:,4:]
            
            #不同狀態上色
            #滿載時段 上橘色
            fullbike_list=load.mark_period(data_full)
            for ind,i in enumerate(fullbike_list):
                if ind==0:
                    line_full,=ax1.plot(x[i[0]:i[1]],y[i[0]:i[1]],"-",color="orange")
                    continue
                ax1.plot(x[i[0]:i[1]],y[i[0]:i[1]],"-",color="orange")
            if bool(fullbike_list)==True:
                plot_list.append(line_full)
                legend_list.append("滿載時段")
            #無車時段上紅色
            nobike_list=load.mark_period(data_empty)
            for ind,i in enumerate(nobike_list): 
                if ind==0:
                    line_nobike,=ax1.plot(x[i[0]:i[1]],y[i[0]:i[1]],"-",color="red")
                    continue
                ax1.plot(x[i[0]:i[1]],y[i[0]:i[1]],"-",color="red")
            if bool(nobike_list)==True:
                plot_list.append(line_nobike)
                legend_list.append("無車時段")
            #無營運時段上黑色
            unact_list=load.mark_period(data_act)
            for ind,i in enumerate(unact_list): #遍歷非營運時段列表 
                if ind==0:
                    line_unact,=ax1.plot(x[i[0]:i[1]],y[i[0]:i[1]],"-",color="black")
                    continue
                ax1.plot(x[i[0]:i[1]],y[i[0]:i[1]],"-",color="black")#每個時段各畫一張plot 線段為黑色
            if bool(unact_list)==True:
                plot_list.append(line_unact)
                legend_list.append("無營運時段")

            ax1.legend(plot_list,legend_list)


        ax1.xaxis.set_major_locator(mticker.MultipleLocator(len(x)//5))
        ax1.tick_params(axis='x',direction='in',labelrotation=40,labelsize=10,pad=5)
        ax1.grid()
        plt.ion()
    #若無資料=========================================================
    else :
        #跳出查無此站訊息
        final_tit="查無此站"
        massageBox_popup()
    ax1.set_title(final_tit)
    f.tight_layout()
    canvs.draw()
    toolbar.update()

def mouse_select_chart(data,index_list):#選單點選畫圖
    ax1.clear()    
    data=data.loc[(slice(None),slice(None),[int(i) for i in index_list] if len(index_list)!=1 else int(index_list[0])),:]
    global x,y #(for interaction_info())
    y=data.sum()[4:]
    x=time_set(y.index)
    line,=ax1.plot(x,y,"-")
    plot_list=[line]
    legend_list=["正常營運時段"]
    if len(index_list)==1:
        number=int(data.index.get_level_values("number").values[0])
        final_tit=data["sna"].values[0]
        con=sqlite3.connect("merge.db")
        data_act=pd.read_sql(f"""SELECT {columns_sql} FROM act WHERE number={number}""",con,index_col=["city","version","number"])
        data_full=pd.read_sql(f"""SELECT {columns_sql} FROM bemp WHERE number={number}""",con,index_col=["city","version","number"])
        con.close()
        data_act=data_act.iloc[:,4:]
        data_empty=data.iloc[:,4:]
        data_full=data_full.iloc[:,4:]
        
        #不同狀態上色
        #滿載時段 上橘色
        fullbike_list=load.mark_period(data_full)
        for ind,i in enumerate(fullbike_list):
            if ind==0:
                line_full,=ax1.plot(x[i[0]:i[1]],y[i[0]:i[1]],"-",color="orange")
                continue
            ax1.plot(x[i[0]:i[1]],y[i[0]:i[1]],"-",color="orange")
        if bool(fullbike_list)==True:
            plot_list.append(line_full)
            legend_list.append("滿載時段")
        #無車時段上紅色
        nobike_list=load.mark_period(data_empty)
        for ind,i in enumerate(nobike_list): #遍歷非營運時段列表 
            if ind==0:
                line_nobike,=ax1.plot(x[i[0]:i[1]],y[i[0]:i[1]],"-",color="red")
                continue
            ax1.plot(x[i[0]:i[1]],y[i[0]:i[1]],"-",color="red")#每個時段各畫一張plot 線段為黑色
        if bool(nobike_list)==True:
            plot_list.append(line_nobike)
            legend_list.append("無車時段")
        #無營運時段上黑色
        unact_list=load.mark_period(data_act)
        for ind,i in enumerate(unact_list): #遍歷非營運時段列表 
            if ind==0:
                line_unact,=ax1.plot(x[i[0]:i[1]],y[i[0]:i[1]],"-",color="black")
                continue
            ax1.plot(x[i[0]:i[1]],y[i[0]:i[1]],"-",color="black")#每個時段各畫一張plot 線段為黑色
        if bool(unact_list)==True:
            plot_list.append(line_unact)
            legend_list.append("無營運時段")
        #以上 不同狀態上色
        ax1.legend(plot_list,legend_list)

    else:
        final_tit=f"滑鼠選取 共{len(index_list)}站"

    ax1.xaxis.set_major_locator(mticker.MultipleLocator(len(x)//5))#xticks label 區間設置
    ax1.tick_params(axis='x',direction='in',labelrotation=40,labelsize=10,pad=5)
    ax1.grid()
    plt.ion()
    ax1.set_title(final_tit)
    f.tight_layout()
    canvs.draw()
    toolbar.update()

def time_set(time_list,mark=None): #時間轉換字串(for xticks label)
    output_list=[]
    for each in time_list:
        time_str=time.strftime("%m/%d_%H:%M",(time.strptime(each,"%m_%d_%H_%M")))

        output_list.append(time_str)
    return output_list

def open_map(data): #地圖製作與開啟
    fn=load.produce_map(data)
    fn_path=os.path.abspath(fn)
    driver.get(fn_path)

def show_list(data): #查詢後顯示表單
    con=sqlite3.connect("merge.db")
    if mode=="i":
        global columns_sql 
        columns_sql="*"
    data_tot=pd.read_sql(f"""SELECT {columns_sql} FROM tot""",con,index_col=["city","version","number"])
    data_tot=data_tot.loc[data.index,:]
    for i in sheet.get_children():
        sheet.delete(i)    
    for i,index in enumerate(data.index):
        city=index[0]
        version="1.0" if index[1]==1 else "2.0"
        num=index[2]
        name=data.loc[index,"sna"]
        area=data.loc[index,"sarea"]
        tot=int(data_tot.loc[index,:].iloc[-1])
        sheet.insert("",i,values=[city,version,num,name,area,tot])
    srh_tot["text"]=f"共{len(data.index)}站"

def sheet_click(event): #表單內點選功能 分及時與歷史模式
    if mode=="h":
        num_list=[]
        for item in sheet.selection():
            item_text=sheet.item(item,"values")
            num_list.append(item_text[2])
        mouse_select_chart(new_data,num_list)
    elif mode=="i":
        index=[sheet.item(sheet.selection(),"values")[i] for i in [0,1,2]]
        index=[index[0],int(eval(index[1])),int(index[2])]
        coordinate="["+str(im_data.loc[[index],["lat","lng"]].values[0][0])+","+str(im_data.loc[[index],["lat","lng"]].values[0][1])+"]"
        load.refresh_page(coordinate,"bike_map.html",driver)

def quit_root(): #結束鈕 視窗關閉與地圖關閉
    if "driver" in globals():
        driver.quit()
    root_main.destroy()

def main_page(): #返回起始頁面 框架調整與地圖關閉
    if mode=="i" or mode=='h':
        for i in sheet.get_children():
            sheet.delete(i) 
    if mode=="i":
        driver.quit()
    root_main.overrideredirect(False)
    root_main.geometry(f"{int(w_width/4)}x{int(w_height/4)}+{int(w_width*3/8)}+{int(w_height*2/8)}")  
    left_f.pack_forget()
    right_f.pack_forget()
    main_page_f.pack()
    

def immediate_mode(): #及時模式 是窗框架調整 與開啟地圖
    time_label.grid_remove()
    to_label.grid_remove()
    date_Ecombo.grid_remove()
    date_Scombo.grid_remove()
    global mode ,driver
    mode="i"
    root_main.geometry(f"{int(w_width*ratio)}x{int(w_height)-80}+0+0")
    left_f.pack(side=tk.LEFT,expand=True,fill="both")
    right_f.pack_forget()
    main_page_f.pack_forget()
    option=webdriver.ChromeOptions()
    option.add_experimental_option("detach",True)
    option.add_experimental_option('useAutomationExtension', False)
    option.add_experimental_option('excludeSwitches', ['enable-automation'])
    driver=webdriver.Chrome(options=option)
    driver.set_window_size(int(w_width*(1-ratio)),w_height-50)
    driver.set_window_position(int(w_width*ratio),0)
    fn_path=os.path.abspath("cycling-bicycle.gif")
    driver.get(fn_path)
        
    
    
    
    
    
def history_mode(): #歷史模式 視窗框架調整
    global mode 
    mode="h"
    root_main.geometry(f"{w_width}x{int(w_height)-80}+0+0")
    main_page_f.pack_forget()
    
    right_f.pack(side=tk.RIGHT,expand=True,fill="both")
    left_f.pack(side=tk.LEFT,expand=True,fill="both")
    time_label.grid()
    to_label.grid()
    date_Ecombo.grid()
    date_Scombo.grid()

def area_combo_adjust(event):#更動地區選單項目
    
    b=city_combo.get()
    if b=="臺北市" :
        area_combo["value"]=["不限區域",'中正區','大同區','中山區','松山區','大安區','萬華區','信義區','士林區','北投區','內湖區','南港區','文山區','臺大專區']

    elif b=="新北市" :
        area_combo["value"]=['不限區域','萬里區','金山區','板橋區','汐止區','深坑區', '瑞芳區','新店區','永和區','中和區','土城區','三峽區', '樹林區', '鶯歌區','三重區','新莊區','泰山區','林口區','蘆洲區','五股區','八里區','淡水區','三芝區','石門區']
    else:
        area_combo["value"]=area_list

def interaction_info(event):#互動式圖表資訊
    if click_switch==True:
        
        if bool(event.xdata) and "x" in globals():
            offsetbox.set_text(str(x[int(event.xdata)])+"\n"+str(y[int(event.xdata)]))
            ax1.add_artist(ab)
            ab.set_visible(True)
            ab.xy=(x[int(event.xdata)],y[int(event.xdata)])
            f.canvas.draw_idle()
            direction =-1 if y[int(event.xdata)] > y.max()/2 else 1
            ab.xybox = (xybox[0], xybox[1]*direction) 

def interaction_control(event):#互動式圖表資訊開關
    global click_switch
    if event.dblclick:
        click_switch=1-bool(click_switch)

def mode_check():#查詢鈕執行 分及時與歷史模式
    par_func=lambda x:{"1.0":1,"2.0":2,"臺北市":"TP","新北市":"NTP","不限城市":None,"不限版本":None}[x]
    version_par=par_func(version_combo.get())
    city_par=par_func(city_combo.get())
    sarea_par=area_combo.get() if area_combo.get()!="不限區域" else None
    if mode=="h":
        time_span=[time_dict[date_Scombo.get()][0],time_dict[date_Ecombo.get()][1]]
        global columns_sql
        data,columns_sql=load.find(word=key_word.get(),
             city=city_par,
             version=version_par,
             sarea=sarea_par,
             time_span=time_span)
        draw_plot(data )
        show_list(new_data)
    elif mode=="i":
        state=[empty.get(),full.get()]
        data=load.find(word=key_word.get(),
                           city=city_par,
                           version=version_par,
                           sarea=sarea_par,
                           real_time=True,
                           state=state)
        global im_data
        im_data=data.copy()
        if len(data.index)!=0:
            open_map(data)
            show_list(data)
        else:
            massageBox_popup()
            
        
def massageBox_popup():#條件下無匹配站別 彈出視窗
    tk.messagebox.showinfo("注意", "無匹配站別")

#%%
#----------------------------------------------建立視窗
root_main=tk.Tk()
root_main.title("雙北youbike訊息")
#取得螢幕資訊
w_width=root_main.winfo_screenwidth()
w_height=root_main.winfo_screenheight()
ratio=1/3
main_width=int(w_width*ratio)
root_main.geometry(f"{int(w_width/4)}x{int(w_height/4)}+{int(w_width*3/8)}+{int(w_height*2/8)}")

#-------------------------------------------建立框架
#首頁
main_page_f=tk.Frame(root_main)
main_page_f.pack(expand=True,fill="both")
#選擇頁面
left_f=tk.Frame(root_main)
left_top_f=tk.Frame(left_f)
left_top_f.pack(anchor="n",fill="both")
left_bottom_f=tk.Frame(left_f)
left_bottom_f.pack(side=tk.TOP,expand=True,fill="both")
right_f=tk.Frame(root_main)
#-------------------------------------------建立畫布
f,ax1=plt.subplots(figsize=(10,7))
canvs=FigureCanvasTkAgg(f,right_f)#將畫布放進右框架
canvs.get_tk_widget().pack(expand=1)
#------------------------------------------互動式資訊標籤
offsetbox = TextArea("")
click_switch=False
f.canvas.mpl_connect("motion_notify_event", interaction_info) 
f.canvas.mpl_connect("button_press_event", interaction_control)
xybox=(10,50)
ab = AnnotationBbox(offsetbox, (1,1), xybox=xybox, xycoords='data',
                    boxcoords="offset points",  pad=0.3,  arrowprops=dict(arrowstyle="->"))
#----------------------------------------建立控制台
toolbar = NavigationToolbar2Tk(canvs,right_f,pack_toolbar=False)
toolbar.pack(side=tk.TOP)
#-----------------------------------------建立標籤
#搜尋字樣
search_label=tk.Label(left_top_f,text="關鍵字搜尋:")
search_label.grid(row=1,column=1)
#時間選取字樣
time_label=tk.Label(left_top_f,text="日期:")
time_label.grid(row=2,column=0)
to_label=tk.Label(left_top_f,text="至")
to_label.grid(row=2,column=2)
#城市選取字樣
city_label=tk.Label(left_top_f,text="城市:")
city_label.grid(row=3,column=0)
#版本選取字樣
city_label=tk.Label(left_top_f,text="ubike版本:")
city_label.grid(row=3,column=2)
#區別選取字樣
area_label=tk.Label(left_top_f,text="區別:")
area_label.grid(row=3,column=4)
#搜尋比數標籤
srh_tot=tk.Label(left_top_f)
srh_tot.grid(row=4,column=0)
#--------------------------------------建立變數
key_word=tk.StringVar()
key_word.set("夜市")
full=tk.BooleanVar()
full.set(False)
empty=tk.BooleanVar()
empty.set(False)
#----------------------------------------建立下拉式選單
#城市選單
city_combo=ttk.Combobox(left_top_f,width=7,values=["不限城市","臺北市","新北市"])
city_combo.current(0)
city_combo.grid(row=3,column=1)
city_combo["state"]="readonly"
#版本選單
version_combo=ttk.Combobox(left_top_f,width=7,values=["不限版本","1.0","2.0"])
version_combo.current(1)
version_combo.grid(row=3,column=3)
version_combo["state"]="readonly"
#區域選單
area_list=['不限區域','中正區','大同區','中山區','松山區','大安區','萬華區','信義區','士林區','北投區','內湖區','南港區','文山區','臺大專區',
           '萬里區','金山區','板橋區','汐止區','深坑區', '瑞芳區','新店區','永和區','中和區','土城區','三峽區', '樹林區', '鶯歌區','三重區','新莊區','泰山區','林口區','蘆洲區','五股區','八里區','淡水區','三芝區','石門區']
area_combo=ttk.Combobox(left_top_f,width=7,values=area_list)
area_combo["state"]="readonly"
area_combo.grid(row=3,column=5)
area_combo.current(0)
#時間選單
date_list,time_dict=load.time_list()
date_Scombo=ttk.Combobox(left_top_f,width=7,values=date_list)
date_Scombo.current(len(date_list)-1)
date_Scombo.grid(row=2,column=1)
date_Scombo["state"]="readonly"
date_Ecombo=ttk.Combobox(left_top_f,width=7,values=date_list)
date_Ecombo.current(len(date_list)-1)
date_Ecombo.grid(row=2,column=3)
date_Ecombo["state"]="readonly"
#城市選單綁定事件 動態調整區域選單
city_combo.bind("<<ComboboxSelected>>", area_combo_adjust)

#-----------------------------------------建立 查詢關鍵字輸入框
key_entry=tk.Entry(left_top_f, textvariable=key_word)
key_entry.grid(row=1,column=2,columnspan=3)
#---------------------------------------------建立條件選項
status_full=tk.Checkbutton(left_top_f,text="無位警告",variable=full,onvalue=True)
status_empty=tk.Checkbutton(left_top_f,text="無車警告",variable=empty,onvalue=True)
status_full.grid(row=4,column=1,columnspan=2)
status_empty.grid(row=4,column=3,columnspan=2)
#-------------------------------------------建立按鈕(grid)
#主頁--歷史模式鈕
history_b=tk.Button(main_page_f,text="歷史模式",command=history_mode).pack(side=tk.TOP,anchor="n",pady=5)
#主頁--及時模式鈕
immediate_b=tk.Button(main_page_f,text="及時模式",command=lambda:[immediate_mode()]).pack(side=tk.TOP,anchor="n",pady=5)
#主頁--結束鈕
main_leave_b=tk.Button(main_page_f,text="結束",command=quit_root).pack(side=tk.BOTTOM,anchor="s",pady=5)
#歷史頁左--返回鈕
leave=tk.Button(left_top_f,text="上一頁",command=main_page)
leave.grid(row=0,column=0,pady=5,padx=5)
#歷史頁左--查詢鈕
confirm=tk.Button(left_top_f,text="查詢",command=lambda:[mode_check()])
confirm.grid(row=1,column=5)
#歷史頁右--結束鈕
leave=tk.Button(left_top_f,text="結束",command=quit_root)
leave.grid(row=4,column=6,pady=5,padx=5)
#-----------------------------------------------建立表格
sheet=ttk.Treeview(left_bottom_f,columns=("city","version","num","name","area","tot"),show="headings")
for i in ["city","version","num","tot","name","area"]:
    sheet.heading(i,text=i)
sheet.column("city",width=int(main_width*2/24),anchor="center")
sheet.column("version",width=int(main_width*4/24),anchor="center")
sheet.column("num",width=0,anchor="center",minwidth=0)
sheet.column("tot",width=int(main_width*4/24),anchor="center")
sheet.column("area",width=int(main_width*5/24),anchor="center")
sheet.column("name",width=int(main_width*12/24),anchor="center")
sheet.bind("<ButtonRelease-1>",sheet_click)
sheet.pack(side=tk.LEFT,fill=tk.Y,expand=True)
#---------------------------------------------建立表格卷軸
sheet_scrollbar=tk.Scrollbar(left_bottom_f)
sheet_scrollbar.pack(side=tk.RIGHT,fill=tk.Y,expand=True)
sheet_scrollbar.config(command=sheet.yview)

root_main.mainloop()