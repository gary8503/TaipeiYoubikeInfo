import os
import pandas as pd
import folium
import re
import sqlite3
# pd.set_option("display.max_rows",None)
# pd.set_option("display.max_columns",None)


#篩選特殊狀態時段
def mark_period(data):#引數必須為 sbi,act or bemp檔案中單列之series
    mark_list=[]
    if 0 in data.values[0]:#判斷是否有需標記時段 sbi中無車 act中無營運 bemp中無位
        mark=False #需標記時段開始與結束標記
        for num,c in enumerate(data.columns): #逐欄檢視 標記狀態
            v=data[c].values[0]
            if v==0 and mark==False:#需標記 但mark為false  視為啟始
                mark=True  #將mark改為true
                start_code=num #紀錄起始點
                continue
            elif v!=0 and mark==True:#無需標記 但mark為true 視為終點
                mark=False #將mark改為false
                end_code=num #用此圈索引 作為 標記時段的終點
                mark_list.append([start_code,end_code]) #將起末點標記加入列表
                continue
            if (v==0 and mark==True) and num+1==len(data.columns):#若最後時間點為非營運
                mark_list.append([start_code,num+1])#則直接將其視為非營運終點
    return mark_list #回傳為列表內容為每段連續特殊狀態的頭與尾索引

#開啟檔案與條件篩選
def find(word=None,city=None,version=None,sarea=None,real_time=False,state=[False,False],time_span=None):
    
    con=sqlite3.connect("merge.db")
    condition_list=[]
    if word!=None: condition_list+=[f"sna LIKE '%{word}%'"]
    if city!=None: condition_list+=[f"city='{city}'"]
    if version!=None: condition_list+=[f"version={version}"]
    if sarea!=None: condition_list+=[f"sarea LIKE '%{sarea}%'"]
    if condition_list==[]:
        condition_str="" 
    else:
        condition_str=" WHERE "+" AND ".join(condition_list)
    
    
    if real_time==False:#歷史模式
        conm=sqlite3.connect("merge.db")#連線合併資料庫
        cursorm=conm.execute("PRAGMA  table_info([sbi])")#取得合併後資料欄位名(時間)
        time_s=pd.DataFrame(cursorm.fetchall())[1][7:].tolist()#時間軸生成列表
        conm.commit()
        conm.close()
        time_s=time_s[time_span[0]:time_span[1]]
        columns_str=str(time_s)
        columns_sql="city,version,number,sna,sarea,lat,lng,"+re.sub("[\[\]]","",columns_str)
        columns_sql=re.sub("'","\"",columns_sql)
        sql_str=f"""SELECT {columns_sql} FROM sbi"""
        data=pd.read_sql(sql_str+condition_str,con,index_col=["city","version","number"])

    
        con.close()
        return data,columns_sql 
    else:#及時模式
        sql_str="""SELECT * FROM sbi"""
        data=pd.read_sql(sql_str+condition_str,con,index_col=["city","version","number"])
        
        sql_str="""SELECT * FROM act"""
        data_act=pd.read_sql(sql_str+condition_str,con,index_col=["city","version","number"])
        act_mask=data_act.iloc[:,-1].values!=0
        #原始索引與正常營運索引交集 >新索引
        new_index=data.index.intersection(data_act[act_mask].index)
        
        if state==[True,False]:#無車
            sbi_mask=data.iloc[:,-1].values==0
            #新索引 與 無車站索引交集 > 新索引
            new_index=new_index.intersection(data[sbi_mask].index)
            con.close()
            return data.loc[new_index,:]
        elif state==[False,True]:#無位
            sql_str="""SELECT * FROM bemp"""
            data_bemp=pd.read_sql(sql_str+condition_str,con,index_col=["city","version","number"])
            bemp_mask=data_bemp.iloc[:,-1].values==0
            #新索引與 無位站索引交集>新索引
            new_index=new_index.intersection(data_bemp[bemp_mask].index)
            con.close()    
            return data.loc[new_index,:]
        elif state==[True,True]:
            sbi_mask=data.iloc[:,-1].values==0
            #新索引 與 無車站索引交集 > 新索引
            # new_index=new_index.intersection(data[sbi_mask].index)
            sql_str="""SELECT * FROM bemp"""
            data_bemp=pd.read_sql(sql_str+condition_str,con,index_col=["city","version","number"])
            bemp_mask=data_bemp.iloc[:,-1].values==0
            #無車與 無位站索引交集>交集索引
            union_index=data[sbi_mask].index.union(data_bemp[bemp_mask].index)            
            new_index=union_index.intersection(new_index)
            con.close()    
            return data.loc[new_index,:]
        elif state==[False,False]:
            con.close()
            return data.loc[new_index,:]
#篩選特定狀態站別
def warning_station(data,status):#查詢資料中發生指定狀態之站別
    mid_data=data.copy() #設定中間產物
    con=sqlite3.connect("merge.db")
    data_tot=pd.read_sql("""SELECT * FROM tot""",con,index_col=["city","version","number"])
    tot_index=data.index.intersection(data_tot.index)
    data_tot.loc[tot_index,:]
    if status=="full": #若判斷狀態為滿站
        marker=1
        mid_data.iloc[:,4:]=data.iloc[:,4:]/data_tot.iloc[:,4:]
    elif status=="empty":
        marker=0
    status_mask=mid_data.iloc[:,4:].values==marker #建立判斷篩選
    data=data[status_mask].drop_duplicates()#去除重複索引
    return data

def refresh_page(new_coordinate,fn,driver_object):#清單點選時刷新地圖
    #更新中心點
    source=driver_object.page_source
    source=re.sub(r"(?<=center:\s)\[.*\](?=,)",new_coordinate,source)
    
    #重設popup
    insert_str='.openPopup()' #使標籤預設跳出 欲加入網頁原始碼
    source=re.sub(r"\.openPopup\(\)",'',source) #將前一站的預設跳出去除
    #將座標字串 修改成 正則表示法
    coord_str=[f"{i}" if i not in ["[","]","."] else f"\{i}"for i in new_coordinate]
    coord_str[coord_str.index(",")]=",\s"
    coord_str="".join(coord_str)
    #找出欲插入位置
    pattern1=re.compile(f"(?<={coord_str})[\s\S]*?bindPopup[\s\S]*?(?=;)")
    end_index=pattern1.search(source).end()
    #重組成新原始碼
    new_source=source[:end_index]+insert_str+source[end_index:]
    #更新檔案
    fn_path=os.path.abspath(fn)
    with open(fn_path,"w",encoding="utf8") as f:
        f.write(new_source)
    #更新網頁
    driver_object.refresh()

def produce_map(data):#產生地圖
    lat_mean=data["lat"].mean()
    lng_mean=data["lng"].mean()
    index=data.index
    bike_map=folium.Map(location=[lat_mean,lng_mean],zoom_start=12,tiles="Stamen Terrain")
    con=sqlite3.connect("merge.db")
    data_bemp=pd.read_sql("""SELECT * FROM bemp""",con,index_col=["city","version","number"])
    data_bemp=data_bemp.loc[index,:]
    data_tot=pd.read_sql("""SELECT * FROM tot""",con,index_col=["city","version","number"])
    data_tot=data_tot.loc[index,:]
    for ind in data.index:
        try:
            lat=data.loc[ind,"lat"].values[0]
            lng=data.loc[ind,"lng"].values[0]
        except :
            lat=data.loc[ind,"lat"]
            lng=data.loc[ind,"lng"]
        if data_bemp.loc[ind,:][-1]==0 and data.loc[ind,:][-1]==0:
            color="black"
        elif data_bemp.loc[ind,:][-1]==0:
            color="orange"
        elif data.loc[ind,:][-1]==0:
            color="red"
        else:
            color="blue"
        if ind[1]==1:
            
            folium.RegularPolygonMarker(location=[lat,lng],
                                    popup=folium.Popup(data.loc[ind,"sna"]+str(ind[1])+".0\n"+str(data.loc[ind,:][-1])+"/"+str(data_tot.loc[ind,:][-1])),
                                    number_of_sides=4,
                                    color=color,
                                    radius=10,
                                    fill=True).add_to(bike_map)

        else:
            folium.RegularPolygonMarker(location=[lat,lng],popup=data.loc[ind,"sna"]+str(ind[1])+".0\n"+str(data.loc[ind,:][-1])+"/"+str(data_tot.loc[ind,:][-1]),number_of_sides=100,color=color,radius=10,fill=True).add_to(bike_map)
    fn="bike_map.html"
    bike_map.save(fn)
    return fn

def time_list():#獲取資料時間列表 merge.db欄名
    conm=sqlite3.connect("merge.db")#連線合併資料庫
    cursorm=conm.execute("PRAGMA  table_info([sbi])")#取得合併後資料欄位名(時間)
    time_s=pd.DataFrame(cursorm.fetchall())[1][7:].tolist()#時間軸生成列表
    conm.commit()
    conm.close()
    #取得首個與末個時間點
    date_index=dict()
    date_choice_list=[]
    for ind,i in enumerate(time_s):
        date_str="/".join(i.split("_")[:2])
        if date_str not in date_choice_list or time_s[-1]==i:
            if date_str not in date_choice_list:
                date_choice_list.append(date_str)
            if "start_ind" in locals() or time_s[-1]==i: #參數使否已存在判斷
                if len(time_s)!=1 and time_s[-1]!=i:
                    end_ind=ind
                else:
                    end_ind=ind+1
                    if len(time_s)==1:
                        start_ind=ind
                        pre_date=date_str
                date_index.update({pre_date:(start_ind,end_ind)})#undefined警告可忽略
            start_ind=ind
            pre_date=date_str
    return date_choice_list,date_index #回傳日期列表(作為選單)、日期對應索引字典(作為篩選)






