import json
import requests
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.http import JsonResponse
from django.views.decorators.http import require_POST
from django.conf import settings
from django.db import transaction
from django.utils.translation import gettext_lazy as _
from PIL import Image as PILImage
from rest_framework import status
from rest_framework.decorators import api_view, permission_classes
from rest_framework.response import Response
from accounts.auth import HasValidAccess
from .models import UserImage, AntAnnotation
from .forms import ImageUploadForm


GBIF_SUGGEST_URL = "https://api.gbif.org/v1/species/suggest"


@api_view(["GET"])
@permission_classes([HasValidAccess])
def species_suggest(request):
    q = request.GET.get("q", "").strip()
    if len(q) < 2:
        return Response([])

    try:
        resp = requests.get(
            GBIF_SUGGEST_URL,
            params={"q": q, "rank": "SPECIES"},
            timeout=5,
        )
        if resp.status_code != 200:
            return Response({"error": _("API GBIF indisponible")}, status=status.HTTP_502_BAD_GATEWAY)

        data = [s for s in resp.json() if s.get("family") == "Formicidae"]
        return Response(data)

    except requests.RequestException:
        return Response({"error": _("Erreur de connexion à GBIF")}, status=status.HTTP_502_BAD_GATEWAY)


@login_required
def dashboard(request):
    images = UserImage.objects.filter(user=request.user)[:12]
    total_images = UserImage.objects.filter(user=request.user).count()
    total_ants = AntAnnotation.objects.filter(image__user=request.user).count()
    return render(request, "counter/dashboard.html", {
        "images": images,
        "total_images": total_images,
        "total_ants": total_ants,
    })


@login_required
def upload_image(request):
    if request.method == "POST":
        form = ImageUploadForm(request.POST, request.FILES)
        if form.is_valid():
            img = form.save(commit=False)
            img.user = request.user
            img.save()
            img.width, img.height = PILImage.open(img.image.path).size
            img.save(update_fields=["width", "height"])
            return redirect("counter:count", image_id=img.pk)
    else:
        form = ImageUploadForm()
    return render(request, "counter/upload.html", {"form": form})


@login_required
def count_view(request, image_id):
    image = get_object_or_404(UserImage, pk=image_id, user=request.user)
    annotations = AntAnnotation.objects.filter(image=image)
    return render(request, "counter/count.html", {
        "image": image,
        "annotations": list(annotations.values("x", "y", "label")),
    })


@login_required
def history(request):
    images = UserImage.objects.filter(user=request.user)
    return render(request, "counter/history.html", {"images": images})


@login_required
def get_annotations(request, image_id):
    image = get_object_or_404(UserImage, pk=image_id, user=request.user)
    annotations = AntAnnotation.objects.filter(image=image).values("x", "y", "label")
    return JsonResponse(list(annotations), safe=False)


@login_required
@require_POST
def save_annotations(request, image_id):
    image = get_object_or_404(UserImage, pk=image_id, user=request.user)
    data = json.loads(request.body)
    with transaction.atomic():
        AntAnnotation.objects.filter(image=image).delete()
        for ann in data.get("annotations", []):
            AntAnnotation.objects.create(
                image=image,
                x=ann["x"],
                y=ann["y"],
                label=ann["label"],
            )
        if data.get("species"):
            image.species = data["species"]
            image.save(update_fields=["species"])
    return JsonResponse({"status": "ok", "count": len(data.get("annotations", []))})


@login_required
@require_POST
def delete_image(request, image_id):
    image = get_object_or_404(UserImage, pk=image_id, user=request.user)
    image.delete()
    return JsonResponse({"status": "ok"})
