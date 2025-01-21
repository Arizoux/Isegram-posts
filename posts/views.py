from datetime import datetime
from http.client import responses

from django.shortcuts import get_object_or_404
import json, requests
from django.http import HttpResponse, JsonResponse, Http404
from rest_framework.decorators import api_view
from requests_toolbelt.multipart.encoder import MultipartEncoder
import os

from posts.models import Post

MEDIA_SERVICE_URL = os.getenv("MEDIA_SERVICE_URL")

# Neue Funktion hinzugefügt
@api_view(['GET'])
def health_check(request):
    return JsonResponse({"message": "Post Service running!"}, status=200)

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
    content = request.data.get('content')
    caption = request.data.get('caption')
    user_id = request.data.get('user_id')
    username = request.data.get('username')
    
    # Sammle alle Mediendateien
    media_files = []
    i = 0
    while f'media[{i}].file' in request.FILES:
        file_obj = request.FILES[f'media[{i}].file']
        filename = request.data.get(f'media[{i}].filename')
        content_type = request.data.get(f'media[{i}].content_type')
        
        media_files.append({
            'file': file_obj,
            'filename': filename,
            'content_type': content_type
        })
        i += 1

    media = []
    if media_files:
        # Erstelle multipart request für den media service
        media_request = MultipartEncoder(
            fields={
                f'profile_picture_{user_id}': (
                    media_files[0]['filename'],
                    media_files[0]['file'],
                    media_files[0]['content_type']
                )
            }
        )
        
        try:
            post_response = requests.post(
                f'{MEDIA_SERVICE_URL}/media',
                data=media_request,
                headers={'Content-Type': media_request.content_type},
                timeout=5
            )
            post_response.raise_for_status()
            media_json = post_response.json()
            media = media_json["IDs"]
        except requests.exceptions.HTTPError as e:
            status_code = post_response.status_code if post_response else 500
            return HttpResponse({"error": str(e)}, status=status_code)
        except requests.exceptions.RequestException as e:
            return HttpResponse({"error": str(e)}, status=500)

    post = Post.objects.create(
        caption=caption,
        content=content,
        username=username,
        user_id=user_id,
        created_at=datetime.now(),
        updated_at=datetime.now(),
        media=media
    )
    
    return JsonResponse({'message': 'Post created', 'post_id': str(post.post_id)}, status=200)


def deletePost(request, id):
    try:
        post = get_object_or_404(Post, id=id)

        for media in post.media:
            media_response = requests.delete(f'/media/{media}')

            if media_response.status_code == 500:
                return HttpResponse("error: internal server error", status=500)

        reactions_response = requests.delete(f'/interactions/{post.post_id}/reactions')

        if reactions_response.status_code == 404:
            return HttpResponse("error with deleting the reactions", status=404)

        comments_response = requests.delete(f'/comments/{post.post_id}/comments')

        if comments_response.status_code == 404:
            return HttpResponse("error with deleting the comments", status=404)

        post.delete()
        return HttpResponse('post deleted', status=200)

    except Http404:
        return HttpResponse({"error": "Post not found"}, status=404)


def updatePost(request, id):
    post = get_object_or_404(Post, id=id)
    body_unicode = request.body.decode('utf-8')
    body = json.loads(body_unicode)
    updated_fields = []

    for key, value in body.items():
        if key == "media":
            continue

        elif hasattr(post, key):
            setattr(post, key, value)
            updated_fields.append(key)

    post.updated_at = datetime.now()

    if updated_fields:
        post.save(update_fields=updated_fields)

    return JsonResponse(updated_fields, status=200)


def getMedia(post):
    media_urls = []
    for media in post.media:
        response = requests.get(f'{MEDIA_SERVICE_URL}/media/{media}')

        if response.status_code != 200:
            return response.status_code

        media_urls.append(response.json())

    return media_urls

def getPosts(request, id):
    try:
        post = get_object_or_404(Post, id=id)

        media_urls = getMedia(post)

        if media_urls == 400:
            return HttpResponse({"error": "Bad request, invalid media ID"}, status=400)

        if media_urls == 404:
            postData = {
                'id': post.id,
                'caption': post.caption,
                'content': post.content,
                'username': post.username,
                'user_id': post.user_id,
                'created_at': post.created_at,
                'updated_at': post.updated_at,
                'media': None,
            }
            return JsonResponse(postData, status=204)

        if media_urls == 500:
            return HttpResponse({"error": "Internal server error"}, status=500)

        postData = {
            'post_id': post.id,
            'caption': post.caption,
            'content': post.content,
            'username': post.username,
            'user_id': post.user_id,
            'created_at': post.created_at,
            'updated_at': post.updated_at,
            'media': media_urls,
        }

        return JsonResponse(postData, status=200)

    except Http404:
        return HttpResponse({"error": "Post not found"}, status=404)

@api_view(['GET'])
def userPosts(request, id):
    posts = Post.objects.filter(user_id=id)

    if not posts.exists():
            return JsonResponse({"message": "No posts found for this user"}, status=404)

    post_list = []

    for post in posts:
        media_response = getMedia(post)

        if media_response == 400 or media_response == 404 or media_response == 500:
            post_data = {
                "post_id": post.post_id,
                "caption": post.caption,
                "content": post.content,
                "username": post.username,
                "user_id": post.user_id,
                "created_at": post.created_at,
                "updated_at": post.updated_at,
                "media": [],
            }
        else:
            post_data = {
                "post_id": post.post_id,
                "caption": post.caption,
                "content": post.content,
                "username": post.username,
                "user_id": post.user_id,
                "created_at": post.created_at,
                "updated_at": post.updated_at,
                "media": media_response,
            }
        post_list.append(post_data)

    return JsonResponse(post_list, status=200, safe=False)

@api_view(['GET'])
def allPosts(request):
    return JsonResponse(list(Post.objects.all()))