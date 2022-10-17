import sqlite3
import requests
import pandas as pd
import time
from apscheduler.schedulers.blocking import BlockingScheduler
from datetime import datetime,timedelta

#取得現在時刻
tn=datetime.now()
#使用timedelta計算出開始抓取時刻(10的倍數分鐘) tn
d_second=timedelta(seconds=tn.second)
d_minute=timedelta(minutes=10-tn.minute%10)
tn=tn-d_second+d_minute
#四種版本的youbike json檔介接
url_NTP_1=r"https://data.ntpc.gov.tw/api/datasets/71CD1490-A2DF-4198-BEF1-318479775E8A/json?page=0&size=10000"
url_NTP_2=r"https://data.ntpc.gov.tw/api/datasets/010E5B15-3823-4B20-B401-B1CF000550C5/json?page=0&size=10000"
url_TP_1=r"https://tcgbusfs.blob.core.windows.net/blobyoubike/YouBikeTP.json"
url_TP_2=r"https://tcgbusfs.blob.core.windows.net/dotapp/youbike/v2/youbike_immediate.json"
version_dict={0:("NTP",1),1:("NTP",2),2:("TP",1),3:("TP",2)}#版本辨識 與 multiindex設置使用
def crawler():
    try:
        con=sqlite3.connect("merge.db")
        data_time=time.strftime("%m_%d_%H_%M",time.localtime())
        sbi_final=pd.DataFrame()
        bemp_final=pd.DataFrame()
        tot_final=pd.DataFrame()
        act_final=pd.DataFrame()
        df_dict={"sbi":sbi_final,"bemp":bemp_final,"tot":tot_final,"act":act_final}
        for ind,url in  enumerate([url_NTP_1,url_NTP_2,url_TP_1,url_TP_2]):
            city,version=version_dict[ind]
            data=requests.get(url)
            data.encoding="utf8"
            if ind==2:
                data=data.json()
                data_pf=pd.DataFrame(list(data["retVal"].values()))
                data_pf["sno tot sbi bemp act".split()]=data_pf["sno tot sbi bemp act".split()].astype(int,copy=True)
                data_pf["lat lng".split()]=data_pf["lat lng".split()].astype(float,copy=True)
            else:
                data_pf=pd.read_json(data.text)
            data_pf=data_pf[['sno', 'sna', 'sarea', 'lat', 'lng','tot','act','sbi','bemp']]
            data_pf.drop_duplicates(subset=["sno"],inplace=True)
            for col in ["sbi","bemp","tot","act"]:
                new_df=data_pf.copy()
                new_df=new_df[["sno","sna","sarea","lat","lng",col]].rename(columns={col:data_time})
                if version==2: new_df["sna"]=new_df["sna"].str.partition("_")[2]
                index_df=pd.DataFrame([[city,version,i]for i in new_df["sno"]],columns=["city","version","number"])
                multi_index=pd.MultiIndex.from_frame(index_df) #生成multiindex
                new_df.index=multi_index #將new_df的index改成multiindex
                df_dict[col]=pd.concat([new_df,df_dict[col]],join="outer")#使用聯集
        for col in ["sbi","bemp","tot","act"]:
            update_df=df_dict[col]
            update_df.drop_duplicates(subset=["sno"],inplace=True)
            update_df.drop("sno",axis=1,inplace=True)
            update_df=update_df.sort_index(level="city")
            cursor=con.execute("select name from sqlite_master where type='table'") 
            if (col,) in cursor.fetchall():
                original_df=pd.read_sql(f"""SELECT * FROM {col}""",con,index_col=["city","version","number"])
                final_new_df=pd.merge(original_df,update_df.iloc[:,4:],left_index=True,right_index=True,how="outer")
                final_new_df=final_new_df.sort_index(level="city")
                final_new_df.to_sql(f"""{col}""",con,if_exists='replace',index=True)
            else:
                update_df.to_sql(f"""{col}""",con,if_exists='replace',index=True)
            con.commit()
            
        con.close()
        print(datetime.now(),"完成抓取")
    except:
        print(datetime.now(),"*****抓取失敗*****")

sched=BlockingScheduler()
sched.add_job(crawler,"interval",minutes=10,start_date=tn,max_instances=5,misfire_grace_time=300,coalesce=True)
sched.start()