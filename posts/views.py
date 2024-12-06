from datetime import datetime

from django.shortcuts import get_object_or_404
import json
from django.http import HttpResponse, JsonResponse
from rest_framework.decorators import api_view

from posts.models import Post


@api_view(['POST'])
def newPost(request):
    body_unicode = request.body.decode('utf-8')
    body = json.loads(body_unicode)
    #TODO no media and need to clarify how the json will look like
    Post.objects.create(caption=body['caption'], username=body['username'], created_at=datetime.now(), updated_at=datetime.now())

    return HttpResponse('post created')



@api_view(['DELETE'])
def deletePost(request, id):
    post = get_object_or_404(Post, id=id)
    #TODO delete the media aswell
    post.delete()
    return HttpResponse('post deleted', status=204)


@api_view(['PATCH'])
def updatePost(request, id):
    post = get_object_or_404(Post, id=id)
    body_unicode = request.body.decode('utf-8')
    body = json.loads(body_unicode)
    updated_fields = []

    for key, value in body.items():
        if key == "media":
            current_media = post.media or {}
            current_media.update(value)
            setattr(post, key, current_media)
            updated_fields.append(key)
        elif hasattr(post, key):
            setattr(post, key, value)
            updated_fields.append(key)

    post.updated_at = datetime.now()

    if updated_fields:
        post.save(update_fields=updated_fields)

    #TODO updated fields should also be returned
    return HttpResponse('post updated', status=200)


@api_view(['GET'])
def getPosts(request, id):
    post = get_object_or_404(Post, id=id)

    postData = {
        'id': post.id,
        'caption': post.caption,
        'username': post.username,
        'created_at': post.created_at,
        'updated_at': post.updated_at,
        'media': post.media,
    }

    return JsonResponse(postData)