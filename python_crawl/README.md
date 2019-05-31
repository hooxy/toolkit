>为了做教学比赛的课件，在百度搜包图网，结果单纯的我被钓鱼到另外一个盗版模版网站上，终身会员只要39.财大气粗如我立马扫码办会员，不幸的是，同事告诉我这种网站很容易收钱跑路，时刻面临着网站打不开的危险。   
>想来想去，只有趁它倒闭之前把资源下完才对得起我的终身会员。所以有了这个工作，代码50多行，涉及到模拟浏览器行为的seleniu库和XPath，还有少许文件操作。

***建议代码在jupyter notebook上分段运行，尤其是下载部分和文件操作部分，避免下载时间太长，文件操作与下载出现冲突***

# 1. 安装
```
pip install selenium
```
- 需要用到的所有库：  
```
from selenium import webdriver   
import os, time, shutil
```   

# 2.下载浏览器驱动   

    火狐浏览器驱动，其下载地址是：https://github.com/mozilla/geckodriver/releases

    谷歌浏览器驱动，其下载地址是：
    http://chromedriver.storage.googleapis.com/index.html

    opera浏览器驱动，其下载地址是：https://github.com/operasoftware/operachromiumdriver/releases   

下载解压后，将所在的目录添加系统的环境变量中。也可以将下载下来的驱动放到python安装目录的lib目录中：/Library/Frameworks/Python.framework/Versions/3.6/bin/**chromedriver**

**我用chrome** 注意浏览器和驱动的版本匹配。

# 3. 文件夹设置
（模拟点击之后默认直接下载）
- 3.1 设置一个临时下载文件夹tmppath作为chrome的默认下载路径，初始化为空文件夹，设置对应的标题列表。
- 3.2 将所有文件下载在tmppath中，同时记录每个文件对应的标题。
- 3.3 将tmp中的所有文件名修改为其标题名称，然后将其移动到目标文件夹中pptpath。

# 4. 分析网页，执行批量下载
- 4.1 分析
  - 网页上有许多ppt模版缩略图，每个模版下方有一个下载按钮，点击该按钮可以自动下载文件至浏览器的默认下载路径中，因此用Selenium进行模拟点击。
  - 底部有下一页，可以利用模拟点击下一页来换页。一个更简单的方法是，每一页的地址存在模式，因此只需要如下更新url即可：   
  ```url = r"https://www.＊＊＊＊＊.com/ppt/pn-{}.html".format(page)```
- 4.2 实施
  - 将光标置于任意一个模版的下载按钮，右键选择**“检查”**, 在**Element**标签中对应元素上面，右键选择**Copy -> Copy XPath**, 得到该元素的XPath，通过以下代码模拟点击，就可以将文件自动下载至3.2中所设置的下载路径中。
```browser.find_element_by_xpath(XPath).click() ```   
所有的模版xpath存在一定的规律，主要是在于div的下标，找到规律之后通过```"{}".format(i)```的格式做通配迭代。

# 5. 修改文件名
- 5.1 分析
  - 下载的文件名不是模版标题，因此需要修改文件名。
  - 文件下载进程独立于本批量下载进程，因此难以在下载时直接修改文件名。
  - 解决办法：设置一个namelist列表，存入每一个模版的标题。在全部下载完毕之后，按照文件创建时间对文件排序，依序用namelist中的名字修改文件名。
- 5.2 实施
  - 5.2.1 开始下载之前，清空tmpfile（以保证下载完毕之后文件于namelist一一对应）   
  ```
  if(os.path.exists(path)):
      shutil.rmtree(path)
  os.mkdir(path)  
  ```
  - 5.2.2 下载时，用4.2的方法取得任意模版标题的XPath，从而得到标题  
  ```title ＝ browser.find_element_by_xpath(XPath).text```
  将标题append至namelist中。
  - 5.2.3 下载完毕后，对tmpfile中的文件按文件创建时间排序
  ```
  time1 = time.ctime(os.path.getmtime(tmppath + filename))
  d[time1] = filename
  t.append(time1)
  for i in sorted(t):
    fn = tmppath + d[i]  
    title ＝ namelist[n]#n from 0   
  ```
  - 5.2.4 修改文件名并移动至目的地
  ```shutil.move(fn, newfilepath)```



# 参考知识：
[selenium的一些查找方法](http://www.testclass.net/selenium_python/find-element/ )

定位一个元素 | 定位多个元素 |  含义  
:-|:-|:-
find_element_by_id | find_elements_by_id | 通过元素id定位 |
find_element_by_name |	find_elements_by_name	| 通过元素name定位 |
find_element_by_xpath|	find_elements_by_xpath	| 通过xpath表达式定位 |
find_element_by_link_text|	find_elements_by_link_tex	|通过完整超链接定位 |
find_element_by_partial_link_text|	find_elements_by_partial_link_text	|通过部分链接定位 |
find_element_by_tag_name|	find_elements_by_tag_name	|通过标签定位 |
find_element_by_class_name|	find_elements_by_class_name	|通过类名进行定位 |
find_elements_by_css_selector|	find_elements_by_css_selector	|通过css选择器进行定位 |
