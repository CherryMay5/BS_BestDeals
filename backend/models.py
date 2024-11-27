from django.db import models

# Create your models here.

# class Products(models.Model):


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