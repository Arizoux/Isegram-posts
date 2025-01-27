import json

from django.test import TestCase, Client, RequestFactory
from django.urls import reverse
from unittest.mock import patch, Mock
from posts.models import Post


class TestViews(TestCase):
    def setUp(self):
        self.client = Client()
        self.post = Post.objects.create(
            caption="Test Caption",
            content="This is a test post",
            user_id="2",
            username="testuser",
            media=[]
        )
        self.post2 = Post.objects.create(
            caption="Test Caption2",
            content="This is a test post2",
            user_id="2",
            username="testuser",
            media=[12345, 5678]
        )
        self.get_url = reverse('getPost', args=[self.post.post_id])
        self.update_url = reverse('updatePost', args=[self.post.post_id])
        self.delete_url = reverse('deletePost', args=[self.post.post_id])
        self.user_url = reverse('getUserPosts', args=[self.post.user_id])
        self.mock_media_ids = ["1234", "5678"]
        self.mock_media_data = [
            {
                "MediaId": "12345",
                "FileUrl": "https://example.com/media/12345",
                "Width": 1920,
                "Height": 1080,
                "FileType": "jpg",
                "OriginalFileName": "vacation-photo.jpg"
            },
            {
                "MediaId": "5678",
                "FileUrl": "https://example.com/media/5678",
                "Width": 1280,
                "Height": 720,
                "FileType": "png",
                "OriginalFileName": "photo2.png",
            },
        ]


    def test_update_view(self):
        response = self.client.patch(
            self.update_url,
            data=json.dumps({
                "content": "This is a test post updated",
                "caption": "Updated Caption",
                "user_id": "3",
                "username": "updateduser"
            }),
            content_type="application/json"
        )

        self.post.refresh_from_db()
        print(response.content)
        self.assertEqual(response.status_code, 200)
        self.assertEquals("This is a test post updated", self.post.content)
        self.assertEquals("Updated Caption", self.post.caption)
        self.assertEquals("3", self.post.user_id)
        print(f"post details: {self.post.content, self.post.caption, self.post.user_id, self.post.username}")


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


    @patch('posts.views.requests.get')
    def test_get_post_success(self, mock_requests_get):
        mock_media_response = Mock()
        mock_media_response.status_code = 200
        mock_media_response.json.return_value = self.mock_media_data
        mock_requests_get.return_value = mock_media_response

        response = self.client.get(self.get_url)

        self.assertEqual(response.status_code, 200)
        response_data = response.json()

        self.assertEqual(response_data['post_id'], str(self.post.post_id))
        self.assertEqual(response_data['caption'], self.post.caption)
        self.assertEqual(response_data['content'], self.post.content)
        self.assertEqual(response_data['media'], self.mock_media_data)

        print(response_data['media'], response_data['caption'], response_data['username'])