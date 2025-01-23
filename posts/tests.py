import json

from django.http.response import JsonResponse
from django.test import TestCase, Client
from django.test.client import RequestFactory
from django.urls import reverse
from unittest.mock import patch, Mock
from posts.models import Post
from datetime import datetime
import uuid


class TestViews(TestCase):
    def setUp(self):
        self.client = Client()
        self.post = Post.objects.create(
            caption="Test Caption",
            content="This is a test post",
            user_id="1",
            username="testuser",
            media=[]
        )
        self.post2 = Post.objects.create(
            caption="Test Caption2",
            content="This is a test post2",
            user_id="2",
            username="testuser",
            media=[]
        )
        self.get_url = reverse('getPost', args=[self.post.post_id])
        self.update_url = reverse('updatePost', args=[self.post.post_id])
        self.delete_url = reverse('deletePost', args=[self.post.post_id])
        self.user_url = reverse('getUserPosts', args=[self.post.user_id])


    def test_update_view(self):
        response = self.client.patch(
            self.update_url,
            data=json.dumps({
                "content": "This is a test post updated",
                "caption": "Updated Caption",
                "user_id": "3"
            }),
            content_type="application/json"
        )

        self.post.refresh_from_db()
        print(response.content)
        self.assertEqual(response.status_code, 200)
        self.assertEquals("This is a test post updated", self.post.content)
        self.assertEquals("Updated Caption", self.post.caption)
        self.assertEquals("3", self.post.user_id)
        self.assertEquals(datetime.now(), self.post.updated_at)


    def test_update_wrong_values(self):
        response = self.client.patch(
            self.update_url,
            data=json.dumps({
                'name': "felix"
            })
        )

        self.post.refresh_from_db()
        self.assertEqual(response.status_code, 403)


    def test_update_wrong_post_id(self):
        response = self.client.patch(
            reverse('updatePost', args=["ab9cd5a2-9a6e-4566-9adf-a0ef4ab31834"]),
            data=json.dumps({})
        )
        self.post.refresh_from_db()
        self.assertEqual(response.status_code, 404)


    def test_get_view(self):

        response = self.client.get(self.get_url)
        print(response.json())
        self.assertEqual(response.status_code, 200)


    @patch('posts.views.requests.delete')
    @patch('posts.views.get_object_or_404')
    def test_delete_post_success(self, mock_get_object, mock_requests_delete):
        mock_get_object.return_value = self.post

        mock_media_response = Mock()
        mock_media_response.status_code = 200
        mock_requests_delete.return_value = mock_media_response

        response = self.client.delete(self.delete_url)

        self.assertEqual(response.status_code, 200)
        self.assertIn('post deleted', response.content.decode())
        self.assertEquals(Post.objects.count(), 1)

        post_exists = Post.objects.filter(post_id=self.post.post_id).exists()
        self.assertFalse(post_exists)
        print(Post.objects.all())