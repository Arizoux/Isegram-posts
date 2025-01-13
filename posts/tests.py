import json
import requests
from django.test import TestCase, Client
from django.urls import reverse
from unittest.mock import patch, Mock
from posts.models import Post
from datetime import datetime


class NewPostViewTest(TestCase):
    def setUp(self):
        self.client = Client()
        self.url = reverse('newPost')
        self.valid_data = {
            "content": "This is a test post",
            "caption": "Test Caption",
            "user_id": "17264947dh3734",
            "username": "testuser",
            "media": None
        }

    @patch('requests.post')
    def test_new_post_with_empty_media(self, mock_post):
        mock_post.return_value.status_code = 200
        mock_post.return_value.json.return_value = {"IDs": []}

        response = self.client.post(self.url, data=self.valid_data, content_type='application/json')

        print("Response from newPost function:", response.content)

        self.assertEqual(response.status_code, 200)
        self.assertIn('post_id', response.json())

        mock_post.assert_not_called()

        self.assertEqual(Post.objects.count(), 1)
        post = Post.objects.first()
        self.assertEqual(post.content, self.valid_data['content'])
        self.assertEqual(post.caption, self.valid_data['caption'])
        self.assertEqual(post.username, self.valid_data['username'])
        self.assertEqual(post.user_id, self.valid_data['user_id'])
        self.assertEqual(post.media, [])



class GetPostsViewTest(TestCase):
    def setUp(self):
        self.client = Client()
        self.post = Post.objects.create(
            id="1",
            content="This is a test post",
            caption="Test Caption",
            username="testuser",
            user_id="1",
            media=["media_id_1", "media_id_2"],
            created_at="2023-01-01T00:00:00Z",
            updated_at="2023-01-01T00:00:00Z"
        )
        self.url = reverse('getOrUpdateOrDeletePost', kwargs={'id': self.post.id})

    @patch('requests.get')
    def test_get_post_with_valid_media(self, mock_get):
        mock_get.side_effect = [
            MockResponse({"url": "http://example.com/media/image1.jpg", "type": "image"}, 200),
            MockResponse({"url": "http://example.com/media/image2.jpg", "type": "image"}, 200)
        ]

        response = self.client.get(self.url)
        self.assertEqual(response.status_code, 200)

        response_data = response.json()
        self.assertEqual(response_data['post_id'], self.post.id)
        self.assertEqual(response_data['content'], self.post.content)
        self.assertEqual(response_data['caption'], self.post.caption)
        self.assertEqual(response_data['media'], [
            {"url": "http://example.com/media/image1.jpg", "type": "image"},
            {"url": "http://example.com/media/image2.jpg", "type": "image"}
        ])

    @patch('requests.get')  # Mock the media service
    def test_get_post_with_invalid_media(self, mock_get):
        mock_get.return_value = MockResponse({}, 400)

        response = self.client.get(self.url)
        self.assertEqual(response.status_code, 400)
        self.assertEqual(response.json(), {"error": "Bad request, invalid media ID"})

    @patch('requests.get')
    def test_get_post_with_not_found_media(self, mock_get):
        mock_get.return_value = MockResponse({}, 404)

        response = self.client.get(self.url)
        self.assertEqual(response.status_code, 204)

        response_data = response.json()
        self.assertEqual(response_data['media'], None)

    @patch('requests.get')
    def test_get_post_with_internal_server_error_media(self, mock_get):
        mock_get.return_value = MockResponse({}, 500)

        response = self.client.get(self.url)
        self.assertEqual(response.status_code, 500)
        self.assertEqual(response.json(), {"error": "Internal server error"})

    def test_get_post_not_found(self):
        url = reverse('getOrUpdateOrDeletePost', kwargs={'id': 999})
        response = self.client.get(url)
        self.assertEqual(response.status_code, 404)
        self.assertEqual(response.json(), {"error": "Post not found"})


class MockResponse:
    """Helper class to mock requests responses."""
    def __init__(self, json_data, status_code):
        self.json_data = json_data
        self.status_code = status_code

    def json(self):
        return self.json_data
