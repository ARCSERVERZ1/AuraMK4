"""
add a URL to urlpatterns:  path('blog/', include('blog.urls'))
"""
from django.contrib import admin
from django.urls import path , include
from .views import *

urlpatterns = [
    path('upload', upload, name="docma"),
    path('', home_page, name="docma"),
    path('subcategory/', view_subcategory,),
    path('images/', view_images,),
    path('test/', tester,),

]