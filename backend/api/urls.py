from django.urls import path
from . import views

urlpatterns = [
    # File uploads
    path('upload/pdf/', views.upload_pdf, name='upload_pdf'),
    path('upload/model/', views.upload_model, name='upload_model'),

    # Detection / Segmentation (image upload mode)
    path('detect/', views.detect, name='detect'),

]
