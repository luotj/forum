#coding: utf-8

from django.db import models
from django.contrib.auth.models import AbstractUser


# 工具
class Pages(object):
    '''
    分页查询类
    '''
    def __init__(self, count, current_page=1, list_rows=40):
        self.total = count
        self._current = current_page
        self.size = list_rows
        self.pages = self.total // self.size + (1 if self.total % self.size else 0)

        if (self.pages == 0) or (self._current < 1) or (self._current > self.pages):
            self.start = 0
            self.end = 0
            self.index = 1
        else:
            self.start = (self._current - 1) * self.size
            self.end = self.size + self.start
            self.index = self._current
        self.has_prev = self.index > 1
        self.has_next = self.index < self.pages


# 数据库字段类型定义
class NormalTextField(models.TextField):
    '''
    models.TextField 默认在MySQL上的数据类型是longtext，用不到那
    么大，所以派生NormalTextField，只修改生成SQL时的数据类型text
    '''
    def db_type(self, connection):
        return 'text'


# Model objects
class NodeManager(models.Manager):
    '''
    Node objects
    '''
    def get_all_hot_nodes(self):
        query = self.get_query_set().filter(topic__reply_count__gt=0).order_by('-topic__reply_count')
        query.query.group_by = ['id'] # Django使用GROUP BY方法
        return query


class TopicManager(models.Manager):
    '''
    Topic objects
    '''
    def get_all_topic(self, num=36, current_page=1):
        count = self.get_query_set().count()
        page = Pages(count, current_page, num)
        query = self.get_query_set().select_related('node', 'author', 'last_replied_by').\
            all().order_by('-last_touched', '-created', '-last_replied_time', '-id')[page.start:page.end]
        return query, page

    def get_all_topics_by_node_slug(self, num = 36, current_page = 1, node_slug = None):
        count = self.get_query_set().filter(node__slug=node_slug).count()
        page = Pages(count, current_page, num)
        query = self.get_query_set().select_related('node', 'author', 'last_replied_by').\
            filter(node__slug=node_slug).order_by('-last_touched', '-created', '-last_replied_time', '-id')[page.start:page.end]
        return query, page

    def get_user_all_topics(self, uid, num = 36, current_page = 1):
        count = self.get_query_set().filter(author__id=uid).count()
        page = Pages(count, current_page, num)
        query = self.get_query_set().select_related('node', 'author', 'last_replied_by').\
            filter(author__id=uid).order_by('-id')[page.start:page.end]
        return query, page

    def get_user_all_replied_topics(self, uid, num = 36, current_page = 1):
        pass # F2E好像写的不对，留着以后有用再说

    def get_topic_by_topic_id(self, topic_id):
        query = self.get_query_set().select_related('node', 'author', 'last_replied_by').get(pk=topic_id)
        return query

    def get_user_last_created_topic(self, uid):
        query = self.get_query_set().filter(author__id=uid).order_by('-created')[0]
        return query


class ReplyManager(models.Manager):
    '''
    Reply objects
    '''
    def get_all_replies_by_topic_id(self, topic_id, num = 16, current_page = 1):
        count = self.get_query_set().filter(topic__id=topic_id).count()
        page = Pages(count, current_page, num)
        query = self.get_query_set().select_related('author').\
            filter(topic__id=topic_id).order_by('id')[page.start:page.end]
        return query, page

    def get_user_all_replies(self, uid, num = 16, current_page = 1):
        count = self.get_query_set().filter(author__id=uid).count()
        page = Pages(count, current_page, num)
        query = self.get_query_set().select_related('topic', 'author').\
            filter(author__id=uid).order_by('-id')[page.start:page.end]
        return query, page


class FavoriteManager(models.Manager):
    '''
    favorite objects
    '''
    def get_user_all_favorites(self, uid, num = 16, current_page = 1):
        count = self.get_query_set().filter(owner_user__id=uid).count()
        page = Pages(count, current_page, num)
        query = self.get_query_set().select_related('involved_topic__node', \
            'involved_topic__author', 'involved_topic__last_replied_by').\
            filter(owner_user__id=uid).order_by('-id')[page.start:page.end]
        return query, page


class NotificationManager(models.Manager):
    '''
    Notification objects
    '''
    def get_user_all_notifications(self, uid, num = 16, current_page = 1):
        count = self.get_query_set().filter(involved_user__id=uid).count()
        page = Pages(count, current_page, num)
        query = self.get_query_set().select_related('trigger_user', 'involved_topic', 'involved_user').\
            filter(involved_user__id=uid).order_by('-id')[page.start:page.end]
        return query, page


# 数据库表结构
class ForumUser(AbstractUser):
    '''
    django.contrib.auth.models.User 默认User类字段太少，用AbstractUser
    自定义一个User类，增加字段
    '''
    nickname = models.CharField(max_length=200, null=True, blank=True)
    avatar = models.CharField(max_length=200, null=True, blank=True)    # 头像
    signature = NormalTextField(null=True)                              # 签名
    location = models.CharField(max_length=200, null=True, blank=True)
    website = models.URLField(null=True, blank=True)
    company = models.CharField(max_length=200, null=True, blank=True)
    role = models.IntegerField(null=True, blank=True)                   # 角色
    balance = models.IntegerField(null=True, blank=True)                # 余额
    reputation = models.IntegerField(null=True, blank=True)             # 声誉
    self_intro = NormalTextField(null=True)                             # 自我介绍
    updated = models.DateTimeField(null=True, blank=True)
    twitter = models.CharField(max_length=200, null=True, blank=True)
    github = models.CharField(max_length=200, null=True, blank=True)
    douban = models.CharField(max_length=200, null=True, blank=True)


class Plane(models.Model):
    '''
    论坛节点分类
    '''
    name = models.CharField(max_length=200, null=True)
    created = models.DateTimeField(null=True, blank=True)
    updated = models.DateTimeField(null=True, blank=True)

    def __unicode__(self):
        return self.name


class Node(models.Model):
    '''
    论坛板块单位，节点
    '''
    name = models.CharField(max_length=200, null=True)
    slug = NormalTextField(null=True)                           # 块，作为node的识别url
    thumb = NormalTextField(null=True)                          # 拇指?
    introduction = NormalTextField(null=True)                   # 介绍
    created = models.DateTimeField(null=True, blank=True)
    updated = models.DateTimeField(null=True, blank=True)
    plane = models.ForeignKey(Plane, null=True, blank=True)
    topic_count = models.IntegerField(null=True, blank=True)
    custom_style = NormalTextField(null=True)
    limit_reputation = models.IntegerField(null=True, blank=True) # 最小声誉，估计是权限控制

    objects = NodeManager()

    def __unicode__(self):
        return self.name


class Topic(models.Model):
    '''
    话题表，定义了论坛帖子的基本单位
    '''
    title = NormalTextField(null=True)
    content = NormalTextField(null=True)
    status = models.IntegerField(null=True, blank=True)
    hits = models.IntegerField(null=True, blank=True)
    created = models.DateTimeField(null=True, blank=True)
    updated = models.DateTimeField(null=True, blank=True)
    node = models.ForeignKey(Node, null=True, blank=True)
    author = models.ForeignKey(ForumUser, related_name='topic_author', null=True, blank=True)
    reply_count = models.IntegerField(null=True, blank=True)
    last_replied_by = models.ForeignKey(ForumUser, related_name='topic_last', null=True, blank=True)
    last_replied_time = models.DateTimeField(null=True, blank=True)
    up_vote = models.IntegerField(null=True, blank=True)
    down_vote = models.IntegerField(null=True, blank=True)
    last_touched = models.DateTimeField(null=True, blank=True)

    objects = TopicManager()

    def __unicode__(self):
        return self.title


class Reply(models.Model):
    '''
    话题的回复
    '''
    topic = models.ForeignKey(Topic, null=True, blank=True)
    author = models.ForeignKey(ForumUser, related_name='reply_author', null=True, blank=True)
    content = NormalTextField(null=True)
    created = models.DateTimeField(null=True, blank=True)
    updated = models.DateTimeField(null=True, blank=True)
    up_vote = models.IntegerField(null=True, blank=True)
    down_vote = models.IntegerField(null=True, blank=True)
    last_touched = models.DateTimeField(null=True, blank=True)

    objects = ReplyManager()


class Favorite(models.Model):
    '''
    用户收藏的话题或回复
    '''
    owner_user = models.ForeignKey(ForumUser, related_name='fav_user', null=True, blank=True)
    involved_type = models.IntegerField(null=True, blank=True)
    involved_topic = models.ForeignKey(Topic, related_name='fav_topic', null=True, blank=True)
    involved_reply = models.ForeignKey(Reply, related_name='fav_reply', null=True, blank=True)
    created = models.DateTimeField(null=True, blank=True)

    objects = FavoriteManager()


class Notification(models.Model):
    '''
    通知消息
    '''
    content = NormalTextField(null=True)
    status = models.IntegerField(null=True, blank=True)
    involved_type = models.IntegerField(null=True, blank=True)
    involved_user = models.ForeignKey(ForumUser, related_name='notify_user', null=True, blank=True)
    involved_topic = models.ForeignKey(Topic, related_name='notify_topic', null=True, blank=True)
    involved_reply = models.ForeignKey(Reply, related_name='notify_reply', null=True, blank=True)
    trigger_user = models.ForeignKey(ForumUser, related_name='notify_trigger', null=True, blank=True)
    occurrence_time = models.DateTimeField(null=True, blank=True)

    objects = NotificationManager()


class Transaction(models.Model):
    '''
    交易
    '''
    type = models.IntegerField(null=True, blank=True)
    reward = models.IntegerField(null=True, blank=True)
    user = models.ForeignKey(ForumUser, related_name='trans_user', null=True, blank=True)
    current_balance = models.IntegerField(null=True, blank=True)
    involved_user = models.ForeignKey(ForumUser, related_name='trans_involved', null=True, blank=True)
    involved_topic = models.ForeignKey(Topic, related_name='trans_topic', null=True, blank=True)
    involved_reply = models.ForeignKey(Reply, related_name='trans_reply', null=True, blank=True)
    occurrence_time = models.DateTimeField(null=True, blank=True)


class Vote(models.Model):
    '''
    投票
    '''
    status = models.IntegerField(null=True, blank=True)
    involved_type = models.IntegerField(null=True, blank=True)
    involved_user = models.ForeignKey(ForumUser, related_name='vote_user', null=True, blank=True)
    involved_topic = models.ForeignKey(Topic, related_name='vote_topic', null=True, blank=True)
    involved_reply = models.ForeignKey(Reply, related_name='vote_reply', null=True, blank=True)
    trigger_user = models.ForeignKey(ForumUser, related_name='vote_trigger', null=True, blank=True)
    occurrence_time = models.DateTimeField(null=True, blank=True)
