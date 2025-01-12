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



class PostCreationAndRetrievalTest(TestCase):
    def setUp(self):
        self.client = Client()
        self.create_url = reverse('newPost')
        self.get_url = reverse('getOrUpdateOrDeletePost')
        self.valid_data = {
            "content": "This is a test post",
            "caption": "Test Caption",
            "user_id": "1",
            "username": "testuser",
            "media": [
                {"url": "http://example.com/media/image.jpg", "type": "image"}
            ]
        }

    @patch('requests.post')
    @patch('requests.get')
    def test_create_and_retrieve_post(self, mock_get, mock_post):
        return self