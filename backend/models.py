from django.utils import timezone
from django.db import models

# Create your models here.

class Platform(models.Model):
	# 如果没有指定主键的话Django会自动新增一个自增id作为主键
	name = models.CharField(max_length=50, verbose_name='电商平台名称')
	base_url = models.URLField(max_length=500, blank=True, null=True, verbose_name='电商平台URL')


	def __unicode__(self):
		return self.name

	def __str__(self):
		return self.name

	class Meta:
		db_table = 'platform'


class Products(models.Model):
	page = models.IntegerField(verbose_name='页码')
	num = models.IntegerField(verbose_name='序号')
	title = models.CharField(max_length=255,verbose_name='商品标题')
	price = models.FloatField(verbose_name='商品价格')
	deal = models.CharField(max_length=255,verbose_name='成交销量')
	location = models.CharField(max_length=255,verbose_name='地理位置')
	shop = models.CharField(max_length=255,verbose_name='店铺名称')
	is_post_free = models.CharField(max_length=255,verbose_name='是否包邮')
	title_url = models.TextField(verbose_name='商品详情页链接')
	shop_url = models.TextField(verbose_name='商铺链接')
	img_url = models.TextField(verbose_name='图片链接')
	style = models.TextField(verbose_name='风格', blank=True, null=True)
	time_catch = models.DateTimeField(default=timezone.now)
	platform_belong = models.CharField(max_length=255, verbose_name='所属电商平台', blank=True, null=True)
	def __str__(self):
		return self.title

	class Meta:
		db_table = 'products'


