from django.db import models
from django.contrib.auth.models import User
from cloudinary.models import CloudinaryField
from datetime import date
from django.core.cache import cache
import datetime
from social_network import settings
from chats.models import Message

# Create your models here.
class Profile(models.Model):
    user = models.OneToOneField(
        User,
        on_delete=models.CASCADE,
        related_name='profile'
    )
    avatar = CloudinaryField(
        'avatar',
        folder='avatars',
        null=True,
        blank=True
    )
    birth_date = models.DateField(
        blank=True,
        null=True
    )
    first_name = models.CharField(
        max_length=25,
        blank=True,
        null=True
    )
    last_name = models.CharField(
        max_length=25,
        blank=True,
        null=True
    )
    friends = models.ManyToManyField(
        'self',
        blank=True,
        related_name='friends'
    )
    country = models.CharField(
        max_length=25,
        blank=True,
        null=True
    )
    city = models.CharField(
        max_length=25,
        blank=True,
        null=True
    )
    bio = models.TextField(
        max_length=100,
        blank=True,
        null=True
    )
        

    def __str__(self):
        if self.first_name and self.last_name:
            return f'{self.first_name} {self.last_name}'
        if self.first_name:
            return self.first_name
        return self.user.username
    
    @property
    def avatar_url(self):
        if self.avatar:
            return self.avatar.url
        # if no avatar, return default avatar from static folder (images/default_avatar.svg)
        return '/static/images/default_avatar.svg'

    @property
    def age(self):
        if self.birth_date:
            today = date.today()
            return today.year - self.birth_date.year - ((today.month, today.day) < (self.birth_date.month, self.birth_date.day))
        return None

    @property
    def location(self):
        if self.country and self.city:
            return f'{self.country}, {self.city}'
        if self.country:
            return self.country
        if self.city:
            return self.city
        return None

    @property
    def pending_friends_in(self):
        profiles_list = []
        for friend_request in self.friend_request_to_profile.all():
            if not friend_request.accepted and not friend_request.declined:
                profiles_list.append(friend_request.from_profile)
        return profiles_list
    
    @property
    def pending_requests_count(self):
        return len(self.pending_friends_in)
    
    @property
    def pending_friends_out(self):
        profiles_list = []
        for friend_request in self.friend_request_from_profile.all():
            if not friend_request.accepted and not friend_request.declined:
                profiles_list.append(friend_request.to_profile)
        return profiles_list
    
    @property
    def unread_messages_count(self):
        # need to find all unread messages in chats that user a member of that are unread
        messages = Message.objects.filter(
            chat__members=self.user,
            is_read=False
            ).exclude(
                author=self.user
                ).count()
        return messages
        

    def last_seen(self):
        return cache.get('seen_%s' % self.user.username)
    
    @property
    def online(self):
        if self.last_seen():
            now = datetime.datetime.now()
            if now > self.last_seen() + datetime.timedelta(
                        seconds=settings.USER_ONLINE_TIMEOUT):
                return False
            else:
                return True
        else:
            return False 