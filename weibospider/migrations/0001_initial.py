# -*- coding: utf-8 -*-
# Generated by Django 1.11.7 on 2020-07-11 10:23
from __future__ import unicode_literals

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    initial = True

    dependencies = [
    ]

    operations = [
        migrations.CreateModel(
            name='Abnormal',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('acontent', models.TextField()),
            ],
        ),
        migrations.CreateModel(
            name='Information',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('content', models.TextField(default=' ', verbose_name='正文')),
                ('publish_place', models.CharField(default='无', max_length=64, verbose_name='发布位置')),
                ('publish_time', models.DateField(verbose_name='时间')),
                ('publish_tool', models.CharField(default='无', max_length=64, verbose_name='发布工具')),
                ('approved_num', models.PositiveIntegerField(default=0, verbose_name='点赞数')),
                ('comment_num', models.PositiveIntegerField(default=0, verbose_name='评论数')),
                ('transmit_num', models.PositiveIntegerField(default=0, verbose_name='转发数')),
            ],
        ),
        migrations.CreateModel(
            name='Normal',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('ncontent', models.TextField()),
            ],
        ),
        migrations.CreateModel(
            name='UserInfo',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('nickname', models.CharField(default='无', max_length=80, verbose_name='用户昵称')),
                ('userid', models.CharField(default='无', max_length=80, verbose_name='用户ID')),
                ('weibo_num', models.PositiveIntegerField(default=0, verbose_name='微博数')),
                ('following', models.PositiveIntegerField(default=0, verbose_name='关注数')),
                ('followers', models.PositiveIntegerField(default=0, verbose_name='粉丝数')),
            ],
        ),
        migrations.AddField(
            model_name='information',
            name='tuser',
            field=models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='user_content', to='weibospider.UserInfo'),
        ),
    ]
