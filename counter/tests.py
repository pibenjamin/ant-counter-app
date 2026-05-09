import io
import json
import os
import re
from PIL import Image
from django.test import TestCase, Client
from django.urls import reverse
from django.contrib.auth.models import User
from django.core.files.uploadedfile import SimpleUploadedFile
from .models import UserImage, AntAnnotation


def _create_test_image(width=200, height=150, format="JPEG"):
    img = Image.new("RGB", (width, height), color="red")
    buf = io.BytesIO()
    img.save(buf, format=format)
    buf.seek(0)
    buf.name = f"test_{width}x{height}.jpg"
    return buf


# ─────────────────────────────────────────────
# Upload → file on disk → URL serves correctly
# ─────────────────────────────────────────────

class UploadFlowE2ETest(TestCase):
    def setUp(self):
        self.client = Client()
        self.user = User.objects.create_user(username="testuser", password="pass12345")
        self.client.force_login(self.user)

    def test_upload_writes_file_to_disk(self):
        img_buf = _create_test_image()
        r = self.client.post(reverse("counter:upload"), {
            "image": img_buf,
            "title": "E2E Test",
        })
        self.assertEqual(UserImage.objects.count(), 1)
        obj = UserImage.objects.first()
        self.assertTrue(os.path.exists(obj.image.path),
                        f"File not found on disk: {obj.image.path}")

    def test_upload_redirects_to_count_page(self):
        img_buf = _create_test_image()
        r = self.client.post(reverse("counter:upload"), {
            "image": img_buf,
            "title": "E2E Test",
        })
        obj = UserImage.objects.first()
        self.assertRedirects(r, reverse("counter:count", args=[obj.pk]))

    def test_count_page_contains_valid_image_url(self):
        img_buf = _create_test_image()
        r = self.client.post(reverse("counter:upload"), {
            "image": img_buf,
            "title": "E2E Test",
        }, follow=True)
        self.assertEqual(r.status_code, 200)
        content = r.content.decode()

        match = re.search(r'window\.IMAGE_URL\s*=\s*"([^"]+)"', content)
        self.assertIsNotNone(match, "window.IMAGE_URL missing from rendered HTML")
        image_url = match.group(1)

        self.assertTrue(image_url.startswith("/media/"),
                        f"IMAGE_URL should start with /media/, got: {image_url}")
        self.assertIn(".jpg", image_url)

        # The URL must correspond to a real file on disk
        from django.conf import settings
        relative_path = image_url.replace("/media/", "", 1)
        full_path = os.path.join(settings.MEDIA_ROOT, relative_path)
        self.assertTrue(os.path.exists(full_path),
                        f"Image file not found at {full_path}")

    def test_count_page_has_correct_dimensions(self):
        img_buf = _create_test_image(width=640, height=480)
        r = self.client.post(reverse("counter:upload"), {
            "image": img_buf,
            "title": "Dims test",
        }, follow=True)
        content = r.content.decode()
        self.assertIn("window.IMAGE_WIDTH = 640", content)
        self.assertIn("window.IMAGE_HEIGHT = 480", content)

    def test_count_page_has_image_id_and_save_url(self):
        img_buf = _create_test_image()
        r = self.client.post(reverse("counter:upload"), {
            "image": img_buf,
            "title": "ID test",
        }, follow=True)
        content = r.content.decode()
        obj = UserImage.objects.first()
        self.assertIn(f"window.IMAGE_ID = {obj.pk}", content)
        self.assertIn(reverse("counter:save_annotations", args=[obj.pk]), content)

    def test_script_order_inline_before_counter_js(self):
        """window.IMAGE_URL must be set BEFORE counter.js loads (script order)"""
        img_buf = _create_test_image()
        r = self.client.post(reverse("counter:upload"), {
            "image": img_buf,
        }, follow=True)
        content = r.content.decode()
        idx_url = content.index("window.IMAGE_URL")
        idx_js = content.index("counter.js")
        self.assertLess(idx_url, idx_js,
                        "window.IMAGE_URL must appear before counter.js script")

    def test_count_page_canvas_is_present(self):
        img_buf = _create_test_image()
        r = self.client.post(reverse("counter:upload"), {
            "image": img_buf,
        }, follow=True)
        self.assertContains(r, 'id="canvas"')
        self.assertContains(r, 'id="canvasContainer"')

    def test_dashboard_shows_uploaded_image_thumbnail(self):
        img_buf = _create_test_image()
        self.client.post(reverse("counter:upload"), {
            "image": img_buf,
            "title": "Dashboard Check",
        })
        r = self.client.get(reverse("counter:dashboard"))
        self.assertContains(r, "Dashboard Check")
        self.assertContains(r, "/media/")

    def test_dashboard_image_link_goes_to_count_page(self):
        img_buf = _create_test_image()
        self.client.post(reverse("counter:upload"), {
            "image": img_buf,
        })
        obj = UserImage.objects.first()
        r = self.client.get(reverse("counter:dashboard"))
        self.assertContains(r, reverse("counter:count", args=[obj.pk]))

    def test_history_shows_uploaded_image(self):
        img_buf = _create_test_image()
        self.client.post(reverse("counter:upload"), {
            "image": img_buf,
            "title": "History Check",
            "species": "Messor barbarus",
        })
        r = self.client.get(reverse("counter:history"))
        self.assertContains(r, "History Check")
        self.assertContains(r, "Messor barbarus")

    def test_image_stored_with_correct_dimensions(self):
        img_buf = _create_test_image(width=800, height=600)
        self.client.post(reverse("counter:upload"), {
            "image": img_buf,
        })
        obj = UserImage.objects.first()
        self.assertEqual(obj.width, 800)
        self.assertEqual(obj.height, 600)

    def test_multiple_uploads_unique_files(self):
        img1 = _create_test_image()
        img2 = _create_test_image()
        self.client.post(reverse("counter:upload"), {"image": img1})
        self.client.post(reverse("counter:upload"), {"image": img2})
        self.assertEqual(UserImage.objects.count(), 2)
        paths = [obj.image.path for obj in UserImage.objects.all()]
        self.assertEqual(len(set(paths)), 2, "Each upload should create a distinct file")

    def test_upload_without_title_and_species_ok(self):
        img_buf = _create_test_image()
        r = self.client.post(reverse("counter:upload"), {"image": img_buf}, follow=True)
        self.assertEqual(r.status_code, 200)
        self.assertEqual(UserImage.objects.count(), 1)


# ─────────────────────────────────────────────
# Existing tests — kept unchanged
# ─────────────────────────────────────────────

class DashboardTest(TestCase):
    def setUp(self):
        self.client = Client()
        self.user = User.objects.create_user(username="testuser", password="pass12345")
        self.client.force_login(self.user)

    def test_dashboard_shows_stats(self):
        r = self.client.get(reverse("counter:dashboard"))
        self.assertEqual(r.status_code, 200)
        self.assertContains(r, "0")

    def test_dashboard_shows_uploaded_images(self):
        UserImage.objects.create(
            user=self.user, title="My colony", image="images/test.jpg"
        )
        r = self.client.get(reverse("counter:dashboard"))
        self.assertContains(r, "My colony")


class UploadTest(TestCase):
    def setUp(self):
        self.client = Client()
        self.user = User.objects.create_user(username="testuser", password="pass12345")
        self.client.force_login(self.user)

    def test_upload_page_200(self):
        r = self.client.get(reverse("counter:upload"))
        self.assertEqual(r.status_code, 200)

    def test_upload_image_success(self):
        img = _create_test_image()
        r = self.client.post(reverse("counter:upload"), {
            "image": img,
            "title": "Test colony",
            "species": "Messor barbarus",
        })
        self.assertEqual(UserImage.objects.count(), 1)
        img_obj = UserImage.objects.first()
        self.assertRedirects(r, reverse("counter:count", args=[img_obj.pk]))


class CountViewTest(TestCase):
    def setUp(self):
        self.client = Client()
        self.user = User.objects.create_user(username="testuser", password="pass12345")
        self.client.force_login(self.user)
        buf = _create_test_image()
        uploaded = SimpleUploadedFile("test.jpg", buf.getvalue(), content_type="image/jpeg")
        self.image = UserImage.objects.create(
            user=self.user, title="Test", image=uploaded
        )

    def test_count_page_200(self):
        r = self.client.get(reverse("counter:count", args=[self.image.pk]))
        self.assertEqual(r.status_code, 200)
        self.assertContains(r, "Comptage")

    def test_count_page_other_user_404(self):
        other = User.objects.create_user(username="other", password="pass12345")
        self.client.force_login(other)
        r = self.client.get(reverse("counter:count", args=[self.image.pk]))
        self.assertEqual(r.status_code, 404)

    def test_save_annotations(self):
        url = reverse("counter:save_annotations", args=[self.image.pk])
        data = {
            "annotations": [
                {"x": 10, "y": 20, "label": 1},
                {"x": 30, "y": 40, "label": 2},
            ],
            "species": "Lasius niger",
        }
        r = self.client.post(
            url, json.dumps(data), content_type="application/json"
        )
        self.assertEqual(r.status_code, 200)
        self.assertEqual(AntAnnotation.objects.count(), 2)
        self.image.refresh_from_db()
        self.assertEqual(self.image.species, "Lasius niger")

    def test_save_annotations_overwrites(self):
        AntAnnotation.objects.create(image=self.image, x=1, y=1, label=1)
        url = reverse("counter:save_annotations", args=[self.image.pk])
        data = {"annotations": [{"x": 99, "y": 88, "label": 1}], "species": ""}
        self.client.post(url, json.dumps(data), content_type="application/json")
        self.assertEqual(AntAnnotation.objects.count(), 1)
        ann = AntAnnotation.objects.first()
        self.assertEqual(ann.x, 99)

    def test_get_annotations(self):
        AntAnnotation.objects.create(image=self.image, x=10, y=20, label=1)
        AntAnnotation.objects.create(image=self.image, x=30, y=40, label=2)
        r = self.client.get(reverse("counter:get_annotations", args=[self.image.pk]))
        self.assertEqual(r.status_code, 200)
        data = r.json()
        self.assertEqual(len(data), 2)

    def test_save_other_users_image_404(self):
        other = User.objects.create_user(username="other", password="pass12345")
        self.client.force_login(other)
        url = reverse("counter:save_annotations", args=[self.image.pk])
        r = self.client.post(
            url, json.dumps({"annotations": []}), content_type="application/json"
        )
        self.assertEqual(r.status_code, 404)


class HistoryTest(TestCase):
    def setUp(self):
        self.client = Client()
        self.user = User.objects.create_user(username="testuser", password="pass12345")
        self.client.force_login(self.user)

    def test_history_empty(self):
        r = self.client.get(reverse("counter:history"))
        self.assertEqual(r.status_code, 200)

    def test_history_with_images(self):
        UserImage.objects.create(
            user=self.user, title="Colony A", image="images/a.jpg"
        )
        UserImage.objects.create(
            user=self.user, title="Colony B", image="images/b.jpg"
        )
        r = self.client.get(reverse("counter:history"))
        self.assertContains(r, "Colony A")
        self.assertContains(r, "Colony B")


class DeleteImageTest(TestCase):
    def setUp(self):
        self.client = Client()
        self.user = User.objects.create_user(username="testuser", password="pass12345")
        self.client.force_login(self.user)
        self.image = UserImage.objects.create(
            user=self.user, title="Delete me", image="images/del.jpg"
        )

    def test_delete_image(self):
        url = reverse("counter:delete_image", args=[self.image.pk])
        r = self.client.post(url)
        self.assertEqual(r.status_code, 200)
        self.assertEqual(UserImage.objects.count(), 0)

    def test_delete_other_users_image_404(self):
        other = User.objects.create_user(username="other", password="pass12345")
        self.client.force_login(other)
        url = reverse("counter:delete_image", args=[self.image.pk])
        r = self.client.post(url)
        self.assertEqual(r.status_code, 404)
