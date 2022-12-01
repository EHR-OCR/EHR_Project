"""EHR_NER URL Configuration

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/4.0/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  path('', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  path('', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.urls import include, path
    2. Add a URL to urlpatterns:  path('blog/', include('blog.urls'))
"""
from django.contrib import admin
from django.urls import path, include
from ehr_app import views
from django.conf import settings
from django.conf.urls.static import static


urlpatterns = [
    path('admin/', admin.site.urls),
    path('', views.start),
    path('signIn/', views.signIn, name="signin"),
    path('postsignIn/', views.postsignIn),
    path('signUp/', views.signUp, name="signup"),
    path('logout/', views.logout, name="log"),
    path('postsignUp/', views.postsignUp),

    path('home/',views.home, name="pHome"),
    path('Healthdashboard/',views.pDash, name="pDash"),
    path('Timeline/',views.timeline, name = "timeline"),
    path('addDoctor/', views.addDoctor),
    path('removeDoctor/', views.removeDoctor),

    path('docHome/', views.docHome, name="docHome"),
    path('docProfile/', views.docProfile, name="docProfile"),
    path('viewPatient/', views.viewPatient, name = "viewPatient"), 
    path('docPatientHome/', views.docPatientHome, name = "docPatientHome"),

    path('uploadDoc/', views.uploadDoc, name = "uploadDoc"),
    path('downloadReport/', views.downloadReport, name = "downloadReport"),

    path('hrHome/', views.hrHome, name="hrHome"),
    path('hrDownload/', views.hrDownload, name="hrDownload")
]


