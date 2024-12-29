# 声明第三方库/头文件
from selenium import webdriver
from selenium.common.exceptions import TimeoutException
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from pyquery import PyQuery as pq
import time
import re   # 引入正则处理

# 配置os
import os
import django

# 设置 Django 配置模块路径
os.chdir('D:/code/python_proj/Best_Deals')
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'Best_Deals.settings')
# 初始化 Django
django.setup()
# 然后导入模型
from backend.models import Products, PriceHistory
from django.utils import timezone

# wait是Selenium中的一个等待类，用于在特定条件满足之前等待一定的时间(这里是15秒)。
# 如果一直到等待时间都没满足则会捕获TimeoutException异常
# 打开页面后会强制停止10秒
wait = None
# 全局变量
count = 1  # 写入db商品计数

def configure_browser():
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
    global wait
    wait = WebDriverWait(driver, 15)
    return driver

def login_sn(driver):
    try:
        # 2.登陆苏宁易购
        login_url = 'https://www.suning.com/'
        driver.get(login_url)

        print("进入苏宁易购，免登录...")
        # print("开始登录苏宁易购...")
        # input("请输入您的账号密码或扫描二维码登录苏宁易购……完成后点击“ENTER”键")
        # print("登录苏宁易购成功！")
    except Exception as e:
        print("登录苏宁易购时出错：",e)
        driver.quit()
        raise

# 3.获取商品信息
# 输入“关键词”，搜索
def search_goods(driver,keyword):
    try:
        print("正在搜索: {}".format(keyword))
        # 找到搜索“输入框”
        searchInput = wait.until(EC.presence_of_element_located((By.CSS_SELECTOR, "#searchKeywords")))
        # 找到“搜索”按钮
        submit = wait.until(
            EC.element_to_be_clickable((By.CSS_SELECTOR, '#searchSubmit')))
        # 输入框写入“关键词KeyWord”
        searchInput.send_keys(keyword)
        # 点击“搜索”按键
        submit.click()
        # 搜索商品后会再强制停止2秒，如有滑块请手动操作
        time.sleep(2)
        print("搜索完成！")
    except Exception as e:
        print("search_goods函数错误！搜索商品时出错：", e)
        raise

def extract_price(price_str):
    # 使用正则表达式提取价格中的数字和小数点部分
    match = re.search(r'\d+(\.\d+)?', price_str)
    if match:
        return float(match.group())
    return None

# 获取商品信息
def get_goods(driver,page):
    try:
        # 滑动到页面底端
        driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
        # 滑动到底部后停留3s
        time.sleep(3)
        driver.execute_script("window.scrollTo(document.body.scrollHeight,0);")

        # 滑动加载
        last_height = driver.execute_script("return document.body.scrollHeight")
        last_height = last_height - 1500
        driver.execute_script(f"window.scrollBy(0, {last_height});")
        time.sleep(2)

        # 动态等待所有图片加载完成
        WebDriverWait(driver, 15).until(
            EC.presence_of_all_elements_located((By.CSS_SELECTOR, "img[src]"))
        )
        # 设置计数全局变量
        global count
        # 获取html网页
        html = driver.page_source
        doc = pq(html)
        # 提取所有商品的共同父元素的类选择器//*[@id="product-wrap"]
        items = doc('#product-list .item-wrap').items()
        for item in items:
            # 二次提取数据
            # 定位商品标题
            title = item.find('.title-selling-point').text()
            # 定位价格
            price_str = item.find('.price-box').text()
            price = extract_price(price_str)
            if not price:
                price = 0.0
            # 定位交易量
            deal = item.find('.info-evaluate').text()
            # 定位店名
            shop = item.find('.store-stock').text()
            # 定位商品url
            t_url = item.find('.sellPoint')
            t_url = t_url.attr('href')
            # 定位店名url
            shop_url = item.find('.store-stock a')
            shop_url = shop_url.attr('href')
            if not shop_url or shop_url == "javascript:void(0);":
                shop_url = "https://www.suning.com"
            # 定位商品图片url
            img = item.find('.img-block a img')
            img_url = img.attr('src')
            # 如果图片 URL 为空，则设置默认图片 URL
            if not img_url:
                img_url = 'https://example.com/default_image.jpg'

            # 定位风格
            style_str = item.find('.info-config em').text()

            # 构建商品信息字典
            product_data = {
                'Page': page,
                'Num': count - 1,
                'title': title,
                'price': price,
                'deal': deal,
                'location': '',
                'shop': shop,
                'isPostFree': '',
                'url': t_url,
                'shop_url': shop_url,
                'img_url': img_url,
                'style': style_str,
                'platform':'苏宁易购',
                'category':'其他',
            }
            print(product_data)

            # 检查数据库中是否已经存在相同的商品
            existing_product = Products.objects.filter(title=product_data['title']).first()

            if existing_product:
                # 更新已有商品信息
                existing_product.price = product_data['price']
                existing_product.deal = product_data['deal']
                existing_product.location = product_data['location']
                existing_product.shop = product_data['shop']
                existing_product.is_post_free = product_data['isPostFree']
                existing_product.title_url = product_data['url']
                existing_product.shop_url = product_data['shop_url']
                existing_product.img_url = product_data['img_url']
                existing_product.style = product_data['style']
                existing_product.updated_at = timezone.now()
                existing_product.save()

                # 添加价格记录
                PriceHistory.objects.create(
                    product=existing_product,
                    price=product_data['price'],
                    recorded_at=timezone.now()
                )
            else:
                # 商品数据写入数据库
                new_product = Products(
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
                    style=product_data['style'],
                    created_at=timezone.now(),  # 获取当前时间
                    updated_at=timezone.now(),
                    platform_belong=product_data['platform'],
                    category=product_data['category'],
                )
                new_product.save()

                # 添加价格记录
                PriceHistory.objects.create(
                    product=new_product,
                    price=price,
                    recorded_at=timezone.now()
                )

            count += 1  # 下一行
    except Exception as e:
        print("get_goods函数错误！获取商品信息时出错：",e)
        raise

from selenium.webdriver.common.action_chains import ActionChains
from selenium.webdriver.common.keys import Keys
# 翻页至第pageStart页
def turn_pageStart(driver,pageStart):
    try:
        print("正在翻转:第{}页".format(pageStart))
        # 滑动到页面底端
        driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
        # 滑动到底部后停留3s
        time.sleep(3)
        driver.execute_script("window.scrollTo(document.body.scrollHeight,0);")

        # 滑动加载
        last_height = driver.execute_script("return document.body.scrollHeight")
        last_height = last_height - 1500
        driver.execute_script(f"window.scrollBy(0, { last_height });")
        time.sleep(2)
        # 找到输入“页面”的表单，输入“起始页”
        pageInput = wait.until(EC.presence_of_element_located(
            (By.XPATH,'//*[@id="bottomPage"]')))
        pageInput.send_keys(pageStart)

        # 找到页面跳转的“确定”按钮，并且点击
        ensure_btn = driver.find_element(By.CSS_SELECTOR, '#bottom_pager > div > a.page-more.ensure')
        # 修改属性
        driver.execute_script("arguments[0].removeAttribute('aria-hidden');", ensure_btn)
        driver.execute_script("arguments[0].setAttribute('tabindex', '0');", ensure_btn)
        driver.execute_script("arguments[0].click();", ensure_btn)  # 确保按钮在视图中

        print("已翻至:第{}页".format(pageStart))
    except Exception as e:
        print("turn_pageStart函数错误！: ",e)
        raise

# 翻页函数
def page_turning(driver,page_number):
    try:
        print("正在翻页: 第{}页".format(page_number))
        print("wait:",wait)
        # 滑动到底部以确保所有数据加载完成
        # driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
        # 强制等待3秒后翻页
        time.sleep(3)
        # 找到“下一页”的按钮
        next_button = wait.until(EC.element_to_be_clickable(
            (By.XPATH, '//*[@id="nextPage"]')))
        next_button.click()
        # next_page = driver.find_element(By.ID, "nextPage")
        # driver.execute_script("arguments[0].click();", next_page)
        # next_page.click()

        # 判断页数是否相等
        wait.until(EC.text_to_be_present_in_element(
            (By.CSS_SELECTOR,'#bottom_pager > div > a.cur'), str(page_number)))
        print("已翻至: 第{}页".format(page_number))
    except TimeoutException:
        print(f"页面加载超时，第{page_number}页未能正确加载。")

        get_goods(driver,page_number)
        page_turning(driver,page_number)
    except Exception as e:
        print("page_turning函数错误！: ",e)
        raise

# 爬虫main函数
def crawler_sn(driver,keyword,pageStart,pageEnd):
    try:
        # 搜索KEYWORD
        search_goods(driver, keyword)
        # 判断pageStart是否为第1页
        if pageStart != 1:
            turn_pageStart(driver,pageStart)
        # 爬取PageStart的商品信息
        get_goods(driver,pageStart)
        # 从PageStart+1爬取到PageEnd
        for i in range(pageStart + 1, pageEnd + 1):
            page_turning(driver,i)
            get_goods(driver,i)
    except Exception as e:
        print("crawler_sn函数错误！: ",e)
        raise


# if __name__ == '__main__':
def crawler2(keyword):
    driver = configure_browser()
    try:
        # keyword = ""  # 替换为需要搜索的关键词
        page_start=2
        page_end=3
        # 开始爬取数据
        login_sn(driver)
        crawler_sn(driver, keyword, page_start, page_end)
        print("爬取成功！")
    except Exception as e:
        print(e)
    finally:
        driver.quit()