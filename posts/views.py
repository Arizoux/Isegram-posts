from datetime import datetime

from django.shortcuts import get_object_or_404
import json, requests
from django.http import HttpResponse, JsonResponse, Http404
from rest_framework.decorators import api_view
from posts.models import Post

# Neue Funktion hinzugefügt
@api_view(['GET'])
def health_check(request):
    return JsonResponse({"message": "Post Service running!"}, status=200)


"""
This function creates a new post with the given data from the request.
If there is media data, it is sent to the media microservice, which returns a json that contains the media_id's.
A new post is then created and the posts id is returned. 
"""

@api_view(['POST'])
def newPost(request):
    if request.data.get('content') is None or request.data.get('caption') is None or request.data.get('user_id') is None or request.data.get('username') is None:
        return HttpResponse("missing data!", status=400)

    content = request.data.get('content')
    caption = request.data.get('caption')
    user_id = request.data.get('user_id')
    username = request.data.get('username')
    media_data = request.data.get('media')

    media = []
    post_response = None

    if media_data and media_data != []:
        payload = {"media": media_data}
        try:
            post_response = requests.post("/media", json=payload, timeout=5)
            post_response.raise_for_status()
            media_json = post_response.json()
            media = media_json["IDs"]

        except requests.exceptions.HTTPError as e:
            status_code = post_response.status_code if post_response else 500
            return HttpResponse({"error": str(e)}, status=status_code)
        except requests.exceptions.RequestException as e:
            return HttpResponse({"error": str(e)}, status=500)

    post = Post.objects.create(caption=caption, content=content, username=username,
                        user_id=user_id, created_at=datetime.now(), updated_at=datetime.now(), media=media)

    return JsonResponse({'message': 'Post created', 'post_id': post.post_id}, status=200)


"""
This function deletes a post with a certain post_id.
The function sends the saved media id's to the media microservice, which then also deletes the media.
A delete request is also made to the interactions microservice, which handles the comments, likes etc.
"""
@api_view(['DELETE'])
def deletePost(request, post_id):
    try:
        post = get_object_or_404(Post, post_id=post_id)

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


"""
This function updates a post with a certain post_id.
Media update is not supported.
A list of updated fields (caption, content etc...) is returned.
"""

@api_view(['PATCH'])
def updatePost(request, post_id):
    post = get_object_or_404(Post, post_id=post_id)
    body = json.loads(request.body)
    updated_fields = {}

    for key, value in body.items():
        if key == "media":
            continue

        elif hasattr(post, key):
            setattr(post, key, value)
            updated_fields[key] = value

        else:
            return HttpResponse({"error": "a field that was requested to be updated was not found"}, status=403)

    if updated_fields:
        post.save(update_fields=updated_fields.keys())

    return JsonResponse(updated_fields, status=200)


"""
This function sends a get request to the media microservice with the media id's, 
which returns a json that contains the media data.
"""

def getMedia(post):
    media_urls = []
    for media in post.media:
        response = requests.get(f'/media/{media}')

        if response.status_code != 200:
            return response.status_code

        media_urls.append(response.json())

    return media_urls or []


"""
This function gets the post data for a given post_id.
If no media is found or if there was a problem with the media microservice,
the posts data is returned with no media data and with status code 204.
"""


@api_view(['GET'])
def getPosts(request, post_id):
    try:
        post = get_object_or_404(Post, post_id=post_id)
        #ToDo the way media is sent to the frontend will change(mulitpart)
        media_urls = getMedia(post)

        if media_urls == 400:
            return HttpResponse({"error": "Bad request, invalid media ID"}, status=400)

        if media_urls == 404:
            postData = {
                'post_id': post.post_id,
                'caption': post.caption,
                'content': post.content,
                'username': post.username,
                'user_id': post.user_id,
                'created_at': post.created_at,
                'updated_at': post.updated_at,
                'media': [],
            }
            return JsonResponse(postData, status=204)

        if media_urls == 500:
            return HttpResponse({"error": "Internal server error"}, status=500)

        postData = {
            "post_id": post.post_id,
            "caption": post.caption,
            "content": post.content,
            "username": post.username,
            "user_id": post.user_id,
            "created_at": post.created_at,
            "updated_at": post.updated_at,
            #'media': media_urls,
            "media": []
        }

        return JsonResponse(postData, status=200)
        
        
    except Http404:
        return HttpResponse({"error": "Post not found"}, status=404)


"""
This function gets all posts from a certain user_id.
If there was a problem with the media microservice, the media for that post is left empty.
A JSON containing all posts from the user is returned.
"""

@api_view(['GET'])
def userPosts(request, user_id):
    posts = Post.objects.filter(user_id=user_id)

    if not posts.exists():
            return JsonResponse({"message": "No posts found for this user"}, status=404)

    post_list = {}

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

    return JsonResponse(post_list, status=200)

@api_view(['GET'])
def allPosts(request):
    return JsonResponse(list(Post.object.all()))