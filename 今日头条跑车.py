#coding:utf8
import requests
from urllib.parse import urlencode
from requests import RequestException
import json
from bs4 import BeautifulSoup
import lxml
import re
import os
from hashlib import md5
import pymongo
from multiprocessing import Pool

MONGO_URL = 'localhost'
MONGO_DB = 'luxurycar'
MONGO_TABLE = 'sportcar'

keyword = '跑车'
client = pymongo.MongoClient(MONGO_URL, connect=False)
db = client[MONGO_DB]

headers={'User-Agent':'Mozilla/5.0 (Windows NT 6.1; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/61.0.3163.100 Safari/537.36'}

#mongoexport -d luxurycar  -c sportcar -f   title,url,image  --csv -o ./今日头条跑车.csv

#获取一页面
def   get_main_page(offset,keyword):
    data={'offset':offset,
        'format':'json',
        'keyword':keyword,
        'autoload':'true',
        'count':'20',
        'cur_tab':'1'}
    url='http://www.toutiao.com/search_content/?'+urlencode(data)
    try:
        response=requests.get(url,headers=headers)
        if response.status_code==200:
            print(response.text)
            return response.text
        else:
            return 1
    except RequestException:
        return 2


#爬取一页中所有链接
def  parse_main_page(text):
    try:
        items=json.loads(text)
        if items and 'data' in items.keys():
            for item in items.get('data'):
                print(item.get('article_url'))
                yield(item.get('article_url'))
    except ValueError:
        pass






#进一步获取展开页面
def get_detail_page(url):
    try:
        response=requests.get(url,headers=headers)
        if response.status_code==200:
            return response.text
        else:
            return None
    except RequestException:
        return None


#进一步爬取展开页面
#content是详情页面request返回的内容
#item是详情页面的链接
def parse_detail_page(content,item):
    try:
        soup=BeautifulSoup(content,'lxml')
        result=soup.select('title')
        title=result[0].get_text() if result else ''
        print(title)
        guize=re.compile('articleInfo:\s{.*?content:(.*?),\s*?groupId.*?subInfo.*?{.*?},\s*?tagInfo:\s{.*?}\s*?}',re.S)
        url=re.search(guize,content)
        if url:
            content2=url.group(1)
    #        guize2=re.compile('&lt.*?img src=&quot;http://(.*?)&quot;\simg_width=&quot.*?\)')
            url3=re.sub(';','#',content2)
            print(url3)
            url4=re.findall('src&#x3D#&quot#http://.*?&quot#',url3)
            if url4:
                for image in url4:
                    lianjie=re.search('src&#x3D#&quot#(.*?)&quot#',image)
                    if lianjie:
                        finallianjie=lianjie.group(1)
                        download_pic(finallianjie)
                    return({'title':title,'url':item,'image':finallianjie})
    except ValueError:
        pass


#用二进制方式下载图片
def download_pic(finallianjie):
    print('downloading picture now',finallianjie)
    try:
        response=requests.get(finallianjie,headers=headers)
        if response.status_code==200:
            save_pic(response.content)
        else:
            return None
    except RequestException:
        return None



#保存图片到本地
def save_pic(content):
    #os.path.join('C:/Users/xiaoxiong/Desktop/pythonCode/爬虫/python3','car')

    file_path='{0}/{1}.{2}'.format(os.getcwd(),md5(content).hexdigest(),'jpg')
    print(file_path)
    if not os.path.exists(file_path):
        with open(file_path,'wb') as f:
            f.write(content)
            f.close()


def save_to_mongo(result):
    if db[MONGO_TABLE].insert(result):
        print('Successfully saved to Mongo',result)
        return True
    return False



def  main(offset):
    text=get_main_page(offset,keyword)
    print(text)
    for item in parse_main_page(text):
        print(item)
        content=get_detail_page(item)
        if content:
            result=parse_detail_page(content,item)
            if result:
                save_to_mongo(result)



if __name__=='__main__':
    p=Pool(3)
    offset = [0, 20, 40, 60, 80, 100]
    p.map(main,offset)


#    main(offset)



