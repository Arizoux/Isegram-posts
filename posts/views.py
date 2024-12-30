from datetime import datetime
from http.client import responses

from django.shortcuts import get_object_or_404
import json, requests
from django.http import HttpResponse, JsonResponse
from rest_framework.decorators import api_view

from posts.models import Post


@api_view(['DELETE', 'PATCH', 'GET'])
def apiHandler(request, id):
    if request.method == 'DELETE':
        deletePost(request, id)

    elif request.method == 'PATCH':
        updatePost(request, id)

    elif request.method == 'GET':
        getPosts(request, id)


@api_view(['POST'])
def newPost(request):
    body_unicode = request.body.decode('utf-8')
    body = json.loads(body_unicode)
    media_urls = body['media_urls'] #muss noch auf variablennamen geeinigt werden
    post_response = None

    payload = {
        "media_urls": media_urls
    }

    try:
        post_response = requests.post("http://127.0.0.1:8000/media/", json=payload, timeout=5)
        post_response.raise_for_status()
        media = post_response.json()

    except requests.exceptions.HTTPError as e:
        return HttpResponse({"error": str(e)}, status=post_response.status_code)
    except requests.exceptions.RequestException as e:
        return HttpResponse({"error": str(e)}, status=post_response.status_code)


    Post.objects.create(caption=body['caption'], username=body['username'], created_at=datetime.now(), updated_at=datetime.now(), media=media)

    return HttpResponse('post created')


def deletePost(request, id):
    post = get_object_or_404(Post, id=id)
    #TODO delete the media aswell
    response = requests.delete('yunus url', json=post.media)

    #TODO
    #if response.status_code != 200:   noch nicht sicher


    post.delete()
    return HttpResponse('post deleted', status=204)


def updatePost(request, id):
    post = get_object_or_404(Post, id=id)
    body_unicode = request.body.decode('utf-8')
    body = json.loads(body_unicode)
    updated_fields = []

    for key, value in body.items():
        if key == "media":
            current_media = post.media
            current_media.update(value)
            #TODO send to media

            setattr(post, key, current_media)
            updated_fields.append(key)

        elif hasattr(post, key):
            setattr(post, key, value)
            updated_fields.append(key)

    post.updated_at = datetime.now()

    if updated_fields:
        post.save(update_fields=updated_fields)

    return JsonResponse(updated_fields, status=200)


def getPosts(request, id):
    post = get_object_or_404(Post, id=id)

    response = requests.get(f"http://127.0.0.1:8000/media/{post.id}")

    if response.status_code == 400:
        return HttpResponse({"error": "Bad request: invalid ID"}, status=400)

    if response.status_code == 404:
        postData = {
            'id': post.id,
            'caption': post.caption,
            'username': post.username,
            'created_at': post.created_at,
            'updated_at': post.updated_at,
            'media': [],
        }
        return JsonResponse(postData, status=204)

    if response.status_code == 500:
        return HttpResponse({"error": "Internal Server Error"}, status=500)

    media_urls = response.json()

    postData = {
        'id': post.id,
        'caption': post.caption,
        'username': post.username,
        'created_at': post.created_at,
        'updated_at': post.updated_at,
        'media': media_urls,
    }

    return JsonResponse(postData, status=200)