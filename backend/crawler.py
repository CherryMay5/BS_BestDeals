# 声明第三方库/头文件
from selenium import webdriver
from selenium.common.exceptions import TimeoutException
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from pyquery import PyQuery as pq
import time


# 配置os
import os
import django

# 设置 Django 配置模块路径
os.chdir('D:/code/python_proj/Best_Deals')
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'Best_Deals.settings')
# 初始化 Django
django.setup()
# 然后导入模型
from backend.models import Products
from django.utils import timezone


# 浏览器配置对象
options = webdriver.ChromeOptions() # 启动ChromeDriver服务
# 禁用自动化栏：关闭自动测试状态显示 // 会导致浏览器报：请停用开发者模式
options.add_experimental_option("excludeSwitches", ['enable-automation'])
# 屏蔽保存密码提示框
prefs = {'credentials_enable_service': False, 'profile.password_manager_enabled': False}
options.add_experimental_option('prefs', prefs)
# 反爬机制
options.add_argument('--disable-blink-features=AutomationControlled')

# 1.打开浏览器
driver = webdriver.Chrome(options=options)
# 窗口最大化
driver.maximize_window()
# 移除selenium当中爬虫的特征
driver.execute_cdp_cmd("Page.addScriptToEvaluateOnNewDocument",
                       {"source": """Object.defineProperty(navigator, 'webdriver', {get: () => undefined})"""})


# 2.登陆淘宝
login_url = 'https://login.taobao.com/member/login.jhtml?spm=a21bo.jianhua/a.action.dlogin.5af92a89pc6lGc&f=top&redirectURL=http%3A%2F%2Fwww.taobao.com%2F'
driver.get(login_url)
# wait是Selenium中的一个等待类，用于在特定条件满足之前等待一定的时间(这里是15秒)。
# 如果一直到等待时间都没满足则会捕获TimeoutException异常
# 打开页面后会强制停止10秒
wait = WebDriverWait(driver, 10)
account = wait.until(EC.presence_of_element_located((By.CSS_SELECTOR, '#fm-login-id')))
account.send_keys('18858113974')
password = wait.until(EC.presence_of_element_located((By.CSS_SELECTOR, '#fm-login-password')))
password.send_keys('ZMJX2004abc!')
# driver.find_element(by=By.CSS_SELECTOR,value='#fm-login-id').send_keys('18858113974')
# driver.find_element(by=By.CSS_SELECTOR,value='#fm-login-password').send_keys('ZMJX2004abc!')
driver.find_element(by=By.CSS_SELECTOR,value='#login-form > div.fm-btn > button').click()
time.sleep(15)  # 过滑块


# 3.获取商品信息
# 全局变量
count = 1  # 写入db商品计数

# 输入“关键词”，搜索
def search_goods(keyword):
    try:
        print("正在搜索: {}".format(keyword))
        # 找到搜索“输入框”
        searchInput = wait.until(EC.presence_of_element_located((By.CSS_SELECTOR, "#q")))
        # 找到“搜索”按钮
        submit = wait.until(
            EC.element_to_be_clickable((By.CSS_SELECTOR, '#J_TSearchForm > div.search-button > button')))
        # 输入框写入“关键词KeyWord”
        searchInput.send_keys(keyword)
        # 点击“搜索”按键
        submit.click()
        # 搜索商品后会再强制停止2秒，如有滑块请手动操作
        time.sleep(2)
        print("搜索完成！")
    except Exception as e:
        print("search_goods函数错误！")
        print(e)

# 获取商品信息
def get_goods(page):
    try:
        # 设置计数全局变量
        global count
        # items = driver.find_element(by=By.CSS_SELECTOR,value='#content_items_wrapper')
        # 获取html网页
        html = driver.page_source
        doc = pq(html)
        # 提取所有商品的共同父元素的类选择器
        items = doc('div.content--CUnfXXxv > div > div').items()
        for item in items:
            # 二次提取数据
            # 定位商品标题
            title = item.find('.title--qJ7Xg_90 span').text()
            # 定位价格
            price_int = item.find('.priceInt--yqqZMJ5a').text()
            price_float = item.find('.priceFloat--XpixvyQ1').text()
            if price_int and price_float:
                price = float(f"{price_int}{price_float}")
            else:
                price = 0.0
            # 定位交易量
            deal = item.find('.realSales--XZJiepmt').text()
            # 定位所在地信息
            location = item.find('.procity--wlcT2xH9 span').text()
            # 定位店名
            shop = item.find('.shopNameText--DmtlsDKm').text()
            # 定位包邮的位置
            postText = item.find('.subIconWrapper--Vl8zAdQn').text()
            postText = "包邮" if "包邮" in postText else "/"
            # 定位商品url
            t_url = item.find('.doubleCardWrapperAdapt--mEcC7olq')
            t_url = t_url.attr('href')
            # t_url = item.attr('a.doubleCardWrapperAdapt--mEcC7olq href')
            # 定位店名url
            shop_url = item.find('.TextAndPic--grkZAtsC a')
            shop_url = shop_url.attr('href')
            # 定位商品图片url
            img = item.find('.mainPicAdaptWrapper--V_ayd2hD img')
            img_url = img.attr('src')
            # 定位风格
            style_list = item('div.abstractWrapper--whLX5va5 > div').items()
            style = []
            for s in style_list:
                s_span = s('div.descBox--RunOO4S3 > span').text()
                if s_span != '':
                    style.append(s_span)

            # 构建商品信息字典
            product_data = {
                'Page': page,
                'Num': count - 1,
                'title': title,
                'price': price,
                'deal': deal,
                'location': location,
                'shop': shop,
                'isPostFree': postText,
                'url': t_url,
                'shop_url': shop_url,
                'img_url': img_url
            }
            print(product_data)

            # 商品数据写入数据库
            product = Products(
                platform_belong='淘宝',
                page=product_data['Page'],
                num=product_data['Num'],
                title=product_data['title'],
                price=product_data['price'],
                deal=product_data['deal'],
                location=product_data['location'],
                shop=product_data['shop'],
                is_post_free=product_data['isPostFree'],
                title_url=product_data['url'],
                shop_url=product_data['shop_url'],
                img_url=product_data['img_url'],
                time_catch=timezone.now()  # 获取当前时间
            )
            product.save()
            count += 1  # 下一行
    except Exception as e:
        print("get_goods函数错误！")
        print(e)

# 翻页至第pageStart页
def turn_pageStart(pageStart):
    try:
        print("正在翻转:第{}页".format(pageStart))
        # 滑动到页面底端
        driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
        # 滑动到底部后停留3s
        time.sleep(3)
        # 找到输入“页面”的表单，输入“起始页”
        pageInput = wait.until(EC.presence_of_element_located(
                    (By.CSS_SELECTOR,
                 '#search-content-leftWrap > div.leftContent--BdYLMbH8 > div.pgWrap--RTFKoWa6 > div > div > span.next-input.next-medium.next-pagination-jump-input'))
        )
        pageInput.send_keys(pageStart)
        # 找到页面跳转的“确定”按钮，并且点击
        ensure_btn = wait.until(EC.element_to_be_clickable(
                    (By.CSS_SELECTOR,
                     '#search-content-leftWrap > div.leftContent--BdYLMbH8 > div.pgWrap--RTFKoWa6 > div > div > button.next-btn.next-medium.next-btn-normal.next-pagination-jump-go'))
        )
        ensure_btn.click()
        print("已翻至:第{}页".format(pageStart))
    except Exception as e:
        print("turn_pageStart函数错误！")
        print(e)

# 翻页函数
def page_turning(page_number):
    try:
        print("正在翻页: 第{}页".format(page_number))
        # 滑动到底部以确保所有数据加载完成
        driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
        # 强制等待2秒后翻页
        time.sleep(2)
        # 找到“下一页”的按钮
        submit = wait.until(EC.element_to_be_clickable(
            (By.CSS_SELECTOR, '#search-content-leftWrap > div.leftContent--BdYLMbH8 > div.pgWrap--RTFKoWa6 > div > div > button.next-btn.next-medium.next-btn-normal.next-pagination-item.next-next')))
        submit.click()
        # 判断页数是否相等
        wait.until(EC.text_to_be_present_in_element(
            (By.CSS_SELECTOR, '#search-content-leftWrap > div.leftContent--BdYLMbH8 > div.pgWrap--RTFKoWa6 > div > div > span.next-pagination-display'), str(page_number)))
        print("已翻至: 第{}页".format(page_number))
    except Exception as e:
        print("page_turning函数错误！")
        print(e)

# 爬虫main函数
def crawler_tb(keyword):
    pageStart=1
    pageEnd=10
    try:
        # 搜索KEYWORD
        search_goods(keyword)
        # 判断pageStart是否为第1页
        if pageStart != 1:
            turn_pageStart(pageStart)
        # 爬取PageStart的商品信息
        get_goods(1)
        # 从PageStart+1爬取到PageEnd
        for i in range(pageStart + 1, pageEnd + 1):
            page_turning(i)
            get_goods(i)
    except Exception as e:
        print("Crawler_tb函数错误！")
        print(e)

# if __name__ == '__main__':
def crawler(keyword):
    try:
        # 开始爬取数据
        crawler_tb(keyword)
        print("爬取成功！")
    except Exception as e:
        print(e)