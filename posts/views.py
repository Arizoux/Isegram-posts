import os

from django.shortcuts import get_object_or_404
import json, requests
from django.http import HttpResponse, JsonResponse, Http404
from rest_framework.decorators import api_view

from posts.models import Post

MEDIA_SERVICE_URL = os.getenv("MEDIA_SERVICE_URL")
INTERACTIONS_SERVICE_URL = os.getenv("INTERACTIONS_SERVICE_URL")

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
    if request.POST.get('user_id') is None or request.POST.get('username') is None:
        return HttpResponse("missing data!", status=400)

    #get the data from the request
    content = request.POST.get('content')
    caption = request.POST.get('caption')
    user_id = request.POST.get('user_id')
    username = request.POST.get('username')

    #get the media files
    media_files = request.FILES

    media = []
    response = None

    #send the media files to the media microservice and recieve ids to store
    if media_files and media_files != {}:
        try:
            response = requests.post(f"{MEDIA_SERVICE_URL}/media", files=media_files)
            response.raise_for_status()
            media = json.loads(response.content)
            media = media['IDs']
        except requests.HTTPError as e:
            return HttpResponse(f"Media service error: {e}", status=response.status_code)

    #create the post with all the given data + the media ids and store it in the db
    post = Post.objects.create(caption=caption, content=content, username=username,
                        user_id=user_id, media=media)

    return JsonResponse({'post_id': post.post_id}, status=200)


"""
This function deletes a post with a certain post_id.
The function sends the saved media id's to the media microservice, which then also deletes the media.
A delete request is also made to the interactions microservice, which handles the comments, likes etc.
"""

@api_view(['DELETE'])
def deletePost(request, post_id):
    try:
        # get post from db with post_id
        post = get_object_or_404(Post, post_id=post_id)

        for media in post.media:
            #send a delete request for each media id
            media_response = requests.delete(f'{MEDIA_SERVICE_URL}/media/{media}')

            if media_response.status_code == 500:
                return HttpResponse("error: internal server error", status=500)

        #delete the reactions
        reactions_response = requests.delete(f'{INTERACTIONS_SERVICE_URL}/interactions/{post.post_id}/reactions')

        if reactions_response.status_code == 404:
            return HttpResponse("error with deleting the reactions", status=404)

        #delete the comments
        comments_response = requests.delete(f'{INTERACTIONS_SERVICE_URL}/comments/{post.post_id}/comments')

        if comments_response.status_code == 404:
            return HttpResponse("error with deleting the comments", status=404)

        #delete the post
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
    post = get_object_or_404(Post, post_id=post_id) #get post from db with post_id
    body = json.loads(request.body)
    updated_fields = {}

    #update each key that was requested
    for key, value in body.items():
        if key == "media":
            continue

        #check if the post has the key field that is requested to be updated
        elif hasattr(post, key):
            setattr(post, key, value)
            updated_fields[key] = value

        else:
            return HttpResponse({"error": "a field that was requested to be updated was not found"}, status=403)

    #update the post
    if updated_fields:
        post.save(update_fields=updated_fields.keys())

    return JsonResponse(updated_fields, status=200)


"""
This function gets the media data for a post by sending a get request to the media microservice.
It then builds the post data to be returned as a get response for this microservice.  
"""

def getData(post):
    media_response = None
    media_json = None

    #check if the post has media_ids to send to the media microservice
    if post.media != []:
        response = requests.get(
            f'{MEDIA_SERVICE_URL}/media',
            data=json.dumps(post.media),
            headers={'Content-Type': 'application/json'}
        )

        #parse the response body
        media_json = response.json()
        media_response = response.status_code

    if media_response == 200:
        post_data = {
            "post_id": post.post_id,
            "caption": post.caption,
            "content": post.content,
            "username": post.username,
            "user_id": post.user_id,
            "created_at": post.created_at,
            "updated_at": post.updated_at,
            "media": media_json,
        }
    else:
        #if the media microservice returned an error or None, leave the media field as an empty list
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

    return post_data


"""
This function gets the post data for a given post_id.
If no media is found or if there was a problem with the media microservice,
the posts data is returned with no media data and with status code 204.
"""

@api_view(['GET'])
def getPosts(request, post_id):
    try:
        #get post from db with post_id
        post = get_object_or_404(Post, post_id=post_id)
        post_data = getData(post)

        return JsonResponse(post_data, status=200, safe=False)

    except Http404:
        return HttpResponse({"error": "Post not found"}, status=404)


"""
This function gets all posts from a certain user_id.
If there was a problem with the media microservice, the media for that post is left empty.
A JSON containing all posts from the user is returned.
"""

@api_view(['GET'])
def userPosts(request, user_id):

    # get all posts from db with user_id
    posts = Post.objects.filter(user_id=user_id)
    post_list = []

    #check if the user has any posts
    if not posts.exists():
        return JsonResponse({"message": "No posts found for this user"}, status=404)

    #iterate through the posts and get the media data
    for post in posts:
        post_data = getData(post)
        post_list.append(post_data)

    return JsonResponse(post_list, status=200, safe=False)


@api_view(['GET'])
def getFeedPosts(request):
    #extract tags from the request from the request query
    tags = request.query_params.getlist('tags', [])
    post_list = []

    if not tags:
        posts = Post.objects.all()[:200]

        for post in posts:
            post_data = getData(post)
            post_list.append(post_data)

        #return the first 200 posts
        return JsonResponse(post_list, status=201, safe=False)

    #gets all the posts that contain tags from the request query list "tags"
    posts = Post.objects.filter(tags__overlap=tags)

    if not posts.exists():
        return JsonResponse({"message": "No posts found for the given tags"}, status=405)

    #iterate through all the posts that contain the tags and append them to a list
    for post in posts:
        post_data = getData(post)
        post_list.append(post_data)

    return JsonResponse(post_list, status=200, safe=False)