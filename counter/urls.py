from django.urls import path
from . import views

app_name = "counter"

urlpatterns = [
    path("", views.dashboard, name="dashboard"),
    path("upload/", views.upload_image, name="upload"),
    path("count/<int:image_id>/", views.count_view, name="count"),
    path("history/", views.history, name="history"),
    path("api/species-suggest/", views.species_suggest, name="species_suggest"),
    path("api/annotations/<int:image_id>/", views.get_annotations, name="get_annotations"),
    path("api/save-annotations/<int:image_id>/", views.save_annotations, name="save_annotations"),
    path("api/delete-image/<int:image_id>/", views.delete_image, name="delete_image"),
]
