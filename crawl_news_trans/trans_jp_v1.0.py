#coding:utf-8
import re
from bs4 import BeautifulSoup
import requests
import os, sys
import json, time, random, hashlib

txt_info = """
info：\n输入关键词，搜索页数，以及存放下载新闻的目录，选择‘开始’按钮即可实现：在
https://news.yahoo.co.jp/search/
搜索相关新闻，下载新闻正文，并使用有道翻译进行机器翻译，将结果存储于指定目录中。\n
"""


ACTIVE = True
STOP = False
thrstate = STOP
mainstate = STOP

headers = {
"User-Agent": "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/58.0.3029.81 Safari/537.36",
    #'Connection':'close',
}
url = 'https://news.yahoo.co.jp/search/?p=key_word&ei=UTF-8&b=page'
#尖閣諸島

### crawl--------------------------------------------------------
def crawl_news_links(surl, key_word = None, page_num = 1, craw_dir = None, headers = None):
    real_visited=0

    if not key_word:
        printLog("Pls Input KEYWORD\n")
        return

    surl= surl.replace('key_word',key_word)
#创建目录
    if craw_dir == None:
        craw_dir = "./crawl_%s/"%(key_word)
    else:
        craw_dir = craw_dir + "crawl_%s/"%(key_word)
    news_dir = craw_dir + "news/"
    if not os.path.exists(craw_dir):
        try:
            os.mkdir(craw_dir)
        except:
            printLog("ERROR Creating Folder..-> %s\n"%craw_dir)
            return None
    if not os.path.exists(news_dir):
        try:
            os.mkdir(news_dir)
        except:
            printLog("ERROR Creating Folder..-> %s\n"%news_dir)
            return None
    printLog("directory:\t%s\nnews:\t%s\n"%(craw_dir, news_dir))
    v_dir.set(craw_dir)

    list_file = craw_dir + 'visited-cn.txt'
    if os.path.exists(list_file):
        visited_file = open(list_file, mode = 'rb+')
    else:
        visited_file = open(list_file,'wb+')
        printLog("文件 visited-cn.txt 创建成功！\n")

    if headers == None:
        headers = {"User-Agent": "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/58.0.3029.81 Safari/537.36",}

    for page in range(page_num):
        if not thrstate:
            #printLog("停止行号：%d" % sys._getframe().f_lineno)
            break

#打开搜索页面进行搜索
        s = requests.session()
        s.keep_alive = False
        #s.proxies = {"https": "47.100.104.247:8080", "http": "36.248.10.47:8080", }
        search_url = surl.replace("page", str(page*10+1))
        printLog("\n**page: %d\n*URL: %s\n" % (page, search_url))
        retry = 3
        for i in range(retry):
            try:
                html = s.get(search_url, headers = headers, timeout = 10)
                printLog("LINK OK. page %d\n"%page)
                i = retry + 1
                break
            except:
                s.close()
                printLog("LINK Error. \n")
        s.close()
        if i < retry + 1:
            printLog("LINK ERROR. QUIT.\n" )
            continue

#解析所有新闻的url
        soup=BeautifulSoup(html.text,"html.parser")
        content  = soup.findAll("div", {"class": "l cf"}) #resultset object

        num = len(content)
        for i in range(num):
            if not thrstate:
                ##printLog("停止行号：%d" % sys._getframe().f_lineno)
                break
            #先解析出来所有新闻的标题、来源、时间、url
            p_str= content[i].find('a') #if no result then nontype object
            contenttitle=p_str.renderContents()
            contenttitle=contenttitle.decode('utf-8', 'ignore')#need it
            contenttitle= re.sub("<[^>]+>","",contenttitle)
            contentlink=str(p_str.get("href"))

#存放顺利抓取的url，查看是否之前已经抓取过
            exists = 0
            visited_file.seek(0,0)
            line = str(visited_file.readline(), 'utf-8')
            try:
                while line:
                    if contentlink == line.strip('\n'):
                        exists = 1
                        break
                    line =  str(visited_file.readline(), 'utf-8')
            except: continue
            if exists: continue

#如果是一个新的链接，提取其标题、日期、来源、链接，写入news file和list file
            contenttime=content[i].find('span', {"class": "d"}).renderContents() #时间
            contentauthor=content[i].find('span', {"class": "ct1"}).renderContents()#来源
            printLog("\n**%s\n%s\n%s\n%s\n" % (contenttitle, str(contentauthor, 'utf-8'), str(contenttime, 'utf-8'), contentlink))
            #printLog("\n**%s\n%s\n%s\n%s\n" % (str(contenttitle, 'utf-8'), str(contentauthor, 'utf-8'),str(contenttime, 'utf-8'),str(contentlink, 'utf-8')))

            real_visited+=1
            filetitle = validateTitle(contenttitle[:10])
            file_name=news_dir + "%d_%s.txt"%(real_visited, filetitle)
            try:
                file = open(file_name,'wb+')
                file.write(contenttitle.encode('utf-8'))
                file.write(u'\n'.encode('utf-8'))
                file.write(contentauthor)
                file.write(u'\n'.encode('utf-8'))
                file.write(contenttime)
                file.write((u'\n'+contentlink+u'\n').encode('utf-8'))
                file.close()
#将新抓取的链接写入list file
                visited_file.seek(0,2)
                visited_file.write((contentlink+u'\n').encode('utf-8'))
            except:
                printLog("FILE open Error.%s\n"%file_name)

    visited_file.close()#及时close
    printLog("Done 1. %d\n"%real_visited)
    return news_dir

### trans--------------------------------------------------------
def dl_trans(news_dir):
    real_trans = 0
    if not news_dir:
        return
    for news_file in os.listdir(news_dir):
        if not thrstate:
            #printLog("停止行号：%d" % sys._getframe().f_lineno)
            break
        printLog("downloading ... %s\n"%news_file )
        if news_file.endswith(".txt"):
            try:
                file = open(news_dir + news_file,'rb+')
            except:
                printLog("FILE open Error. %s\nplease check if file \"visited_cn.txt\" got some error."% news_file)
                continue
            if str(file.readline(), 'utf-8').strip('\n') == u'OK':
                printLog("News already EXISTS.\n")
                continue
            file.seek(0,0)

            line = str(file.readline(), 'utf-8')
            try:
                while line:
                    if line.startswith("http"):
                        contentlink = line.strip('\n')
                        break
                    line = str(file.readline(), 'utf-8')
            except: continue

            content_text = ""
            trans_text = ""
            retry = 3
            for i in range(retry):
                if not thrstate:
                    #printLog("停止行号：%d" % sys._getframe().f_lineno)
                    break
                try:
                    printLog("%s\n"%contentlink)
                    content_text = get_news_content(contentlink)
                    if content_text != None:
                        for j in range(retry):
                            try:
                                printLog("translating... %s\n"%news_file)
                                trans_text = youdao_translate(content_text)
                                break
                            except: pass
                    break
                except: pass
            if content_text != None and trans_text != None:
                file.seek(0,0)
                file.write(u'OK\n'.encode('utf-8'))
                file.seek(0,2)
                file.write(u'\n新闻原文：\n'.encode('utf-8'))
                file.write(content_text.encode('utf-8'))
                file.write(u'\n\n机器翻译：\n'.encode('utf-8'))
                file.write(trans_text.encode('utf-8'))
                file.close()
                printLog(" OK.\n")
                real_trans += 1
    printLog("Done download and trans. %s\n"% real_trans)

def get_news_content(link, headers = None):
    '''given links , get content text'''
    if headers == None:
        headers = {
            "User-Agent": "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/58.0.3029.81 Safari/537.36",
            #'Connection':'close',
        }
    s = requests.session()
    s.keep_alive = False
    html = None
    retry = 3
    for i in range(retry):
        if not thrstate:
            #printLog("停止行号：%d" % sys._getframe().f_lineno)
            break
        try:
            html=s.get(link, headers = headers, timeout = 10)
            break
        except:
            s.close()
            printLog("LINK Error. \n")
    s.close()
    if i >= retry - 1:
        printLog("LINK ERROR. QUIT.\n" )
        html = None

    if html!=None:# and infoencode!=None:#提取内容不为空，error.或者用else
        printLog("LINK Established.\n")
        newspage = html.text.encode(html.encoding)
        soup=BeautifulSoup(newspage, "html.parser")
        content=soup.renderContents()
        content_text=extract(content.decode(html.encoding))#提取新闻网页中的正文部分，化为无换行的一段文字
        content_text= re.sub("&nbsp;"," ",content_text)
        content_text= re.sub("&gt;","",content_text)
        content_text= re.sub("&quot;",'""',content_text)
        content_text= re.sub("<[^>]+>","",content_text)
        content_text=re.sub("\n","",content_text)
        return content_text
    return None

def youdao_translate(content):
    s = requests.Session()

    # 构造有道的加密参数
    client = "fanyideskweb"
    ts = int(time.time() * 1000)
    salt = str(ts + random.randint(1, 10))
    flowerStr = "n%A-rKaT5fb[Gy?;N5@Tj"
    sign = hashlib.md5((client + content + salt + flowerStr).encode('utf-8')).hexdigest()
    bv = '53539dde41bde18f4a71bb075fcf2e66'
    youdao_url = 'http://fanyi.youdao.com/translate?smartresult=dict&smartresult=rule'
    data = {}
    # 调接口时所需参数，看自己情况修改，不改也可调用
    data['i'] = content
    data['from'] = 'AUTO'
    data['to'] = 'AUTO'
    data['smartresult'] = 'dict'
    data['client'] = 'fanyideskweb'
    data['doctype'] = 'json'
    data['version'] = '2.1'
    data['keyfrom'] = 'fanyi.web'
    #data['action'] = 'FY_BY_CLICKBUTTION'
    data['typoResult'] = 'false'
    data['smartresult'] = 'dict'
    data['client'] = client
    data['salt'] = salt
    data['sign'] = sign
    data['ts'] = ts
    data['bv'] = bv
    data['action'] = 'FY_BY_REALTIME'
    #utfdata = json.dumps(data).encode("utf-8")
    try:
        youdao_html = requests.post(youdao_url, headers = headers, data=data)
    except:
        printLog("ERROR. youdao Link fail.")
    #翻译结果
    translate_results = json.loads(youdao_html.text)
    rslt = []
    for items in translate_results["translateResult"]:
        for it in items:
            rslt.append(it['tgt'])
    return "".join(rslt)

#提取网页正文，放入txt中
def remove_js_css (content):
    """ remove the the javascript and the stylesheet and the comment content (<script>....</script> and <style>....</style> <!-- xxx -->) """
    r = re.compile(r'''<script.*?</script>''',re.I|re.M|re.S)
    s = r.sub ('',content)
    r = re.compile(r'''<style.*?</style>''',re.I|re.M|re.S)
    s = r.sub ('', s)
    r = re.compile(r'''<!--.*?-->''', re.I|re.M|re.S)
    s = r.sub('',s)
    r = re.compile(r'''<meta.*?>''', re.I|re.M|re.S)
    s = r.sub('',s)
    r = re.compile(r'''<ins.*?</ins>''', re.I|re.M|re.S)
    s = r.sub('',s)
    return s

def remove_empty_line (content):
    """remove multi space """
    r = re.compile(r'''^\s+$''', re.M|re.S)
    s = r.sub ('', content)
    r = re.compile(r'''\n+''',re.M|re.S)
    s = r.sub('\n',s)
    return s

def remove_any_tag (s):
    s = re.sub(r'''<[^>]+>''','',s)
    return s.strip()

def remove_any_tag_but_a (s):
    text = re.findall (r'''<a[^r][^>]*>(.*?)</a>''',s,re.I|re.S|re.S)
    text_b = remove_any_tag (s)
    return len(''.join(text)),len(text_b)

def remove_image (s,n=50):
    image = 'a' * n
    r = re.compile (r'''<img.*?>''',re.I|re.M|re.S)
    s = r.sub(image,s)
    return s

def remove_video (s,n=1000):
    video = 'a' * n
    r = re.compile (r'''<embed.*?>''',re.I|re.M|re.S)
    s = r.sub(video,s)
    return s

def sum_max (values):
    cur_max = values[0]
    glo_max = -999999
    left,right = 0,0
    for index,value in enumerate (values):
        cur_max += value
        if (cur_max > glo_max) :
            glo_max = cur_max
            right = index
        elif (cur_max < 0):
            cur_max = 0

    for i in range(right, -1, -1):
        glo_max -= values[i]
        if abs(glo_max < 0.00001):
            left = i
            break
    return left,right+1

def method_1 (content, k=1):
    if not content:
        return None,None,None,None
    tmp = content.split('\n')
    group_value = []
    for i in range(0,len(tmp),k):
        group = '\n'.join(tmp[i:i+k])
        group = remove_image (group)
        group = remove_video (group)
        text_a,text_b= remove_any_tag_but_a (group)
        temp = (text_b - text_a) - 8
        group_value.append (temp)
    left,right = sum_max (group_value)
    return left,right, len('\n'.join(tmp[:left])), len ('\n'.join(tmp[:right]))

def extract (content):
    content = remove_empty_line(remove_js_css(content))
    left,right,x,y = method_1 (content)
    return '\n'.join(content.split('\n')[left:right])

def validateTitle(title):
    rstr = r"[\/\\\:\*\?\"\<\>\|]"  # '/ \ : * ? " < > |'
    new_title = re.sub(rstr, "_", title)  # 替换为下划线
    return new_title

### gui--------------------------------------------------------
import tkinter as tk
from tkinter import ttk
from tkinter import scrolledtext
from tkinter import filedialog
import os
import threading

########响应
#打开文件夹button
#选择目录button
def hitb_dir():
    global main_dir
    file_path = filedialog.askdirectory()
    #v_dir.set(file_path.replace('\\', '/') + '/')
    v_dir.set(file_path.replace('/', '\\') + '\\')
    main_dir = v_dir.get()

#打开文件夹button
def hitb_opendir():
    printLog("Open directory: %s\n" %v_dir.get())
#     os.system("start explorer %s" % v_dir.get())
    #os.system("open %s" % v_dir.get())
    #printLog("停止行号：%d" % sys._getframe().f_lineno)
    os.system("explorer %s" % v_dir.get())

#开始结束button
def hitb_sp():
    global thrstate,mainstate
    if thrstate == STOP and mainstate == STOP: #开始
        thrstate = ACTIVE
        mainstate = ACTIVE
        b_SP['text'] = '停止'
        b_reset['state'] = 'disabled'
        thread = start_play_video_thread(url)

    else:#停止
        printLog("STOP SEARCHING！！！！\n")
        thrstate = STOP
        b_SP['text'] = '停止中...'

#重置button
def hitb_reset():
    global thrstate
    cb_pg.current(0)
    e_kw.delete(0, tk.END)
    t_log.delete(0.0, tk.END)
    thrstate = STOP
    printLog(txt_info)

def printLog(log):
    t_log.insert(tk.END, log)
    t_log.see(tk.END)
    t_log.update()

########调用工作线程
def start_play_video_thread(surl):
    thread=threading.Thread(target=start, args=(surl,))
    thread.daemon = True
    thread.start()
    return thread
def start(surl):
    global thrstate, mainstate
    thrstate = ACTIVE
    key_word = e_kw.get()
    pages = int(cb_pg.get())
    if not key_word:
        printLog("Pls Input KEYWORD\n")
    else:
        filedir = main_dir
        printLog('####START\nkeyword:\t%s\npages:\t%s\n' % (key_word, pages))

        printLog('SEARCHING........\n')
        news_dir = crawl_news_links(surl= surl, key_word=key_word, page_num = pages, craw_dir = filedir)
        printLog('\n**************\nSAVING and TRANSLATING........\n')
        dl_trans(news_dir)
        printLog('news are saved in directory:\t%s\n-----------------\n\n' % news_dir)
    b_SP['text'] = '开始'
    b_reset['state'] = 'normal'
    thrstate = STOP
    mainstate = STOP


window = tk.Tk()
window.title("雅虎新闻小工具")
window.resizable(width=False, height=True)

v_dir = tk.StringVar()
v_dir.set("")
# v_log = tk.StringVar()
# v_log.set("")
number = tk.StringVar()

main_dir = ''
# def createWidget(window):
frame0 = tk.Frame(window)
frame1 = tk.Frame(frame0)
frame1_left = tk.Frame(frame1)
frame1_right = tk.Frame(frame1)
frame2 = tk.Frame(frame0)
frame3 = tk.Frame(frame0)

lb_kw = tk.Label( frame1_left, text='关键词：')
lb_pg = tk.Label( frame1_left,  text='页数：')
lb_dir = tk.Label( frame1_left, text='存放目录：')

e_kw = tk.Entry(frame1_right)

cb_pg = ttk.Combobox(frame1_right, textvariable=number, state='readonly')
cb_pg['values'] = tuple(range(1,11))     # 设置下拉列表的值
cb_pg.current(0)    # 设置下拉列表默认显示的值，0为 numberChosen['values'] 的下标值

e_dir = tk.Entry(frame1_right, textvariable = v_dir, state='readonly')
b_dir = tk.Button(frame1_right, text='..', state = 'normal', command=hitb_dir, width = 3)

b_opendir = tk.Button(frame2, text='打开文件夹', width=10, height=1, command=hitb_opendir)
b_SP = tk.Button(frame2, text='开始', width=10, height=1, command=hitb_sp)
b_reset = tk.Button(frame2, text='重置', state = 'normal', width=10, height=1, command=hitb_reset)

lb_log = tk.Label( frame3, text='输出：')
#m_log = tk.Message( frame3, textvariable=v_log, anchor = 'nw', justify='left') #relief=tk.RAISED )
t_log = scrolledtext.ScrolledText(frame3, height=20,width=50, wrap=tk.WORD)

##布局
lb_kw.pack(side = tk.TOP, anchor = 'e')
lb_pg.pack(side = tk.TOP, anchor = 'e')
lb_dir.pack(side = tk.TOP, anchor = 'e')

e_kw.pack(side = tk.TOP, fill = 'x')
cb_pg.pack(side = tk.TOP, fill = 'x')
b_dir.pack(side = tk.RIGHT )
e_dir.pack(side = tk.TOP, fill = 'x')

b_opendir.pack(side = tk.LEFT)
b_SP.pack(side = tk.LEFT)
b_reset.pack(side = tk.LEFT)

lb_log.pack(side = tk.TOP, anchor = 'w')
t_log.pack(expand=tk.YES,fill=tk.BOTH)

frame1_left.pack(side=tk.LEFT) #labels
frame1_right.pack(side=tk.LEFT, expand=tk.YES,fill=tk.X) #entries
frame1.pack(side=tk.TOP, expand=tk.NO,fill=tk.X)

frame2.pack(side=tk.TOP,fill=tk.Y) #buttons
frame3.pack(side=tk.TOP, expand=tk.YES,fill=tk.BOTH) #text
frame0.pack(side=tk.TOP, expand=tk.YES,fill=tk.BOTH)

printLog(txt_info)

window.mainloop()
