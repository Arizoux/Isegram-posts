from django.shortcuts import render
from django.shortcuts import get_object_or_404
import json
from django.http import HttpResponse, JsonResponse
from django.template.context_processors import request
from rest_framework.decorators import api_view

from posts.models import Post


@api_view(['POST'])
def newPost(request):

    return HttpResponse('post created')



@api_view(['GET'])
def getPosts(request):
    path = request.path
    userId = path.split('/')[-1]
    post = get_object_or_404(Post, id=userId)

    postData = {
        'id': post.id,
        'caption': post.caption,
        'username': post.user,
        'created_at': post.created_at,
        'updated_at': post.updated_at,
        'media': post.media,
    }

    return JsonResponse(postData)