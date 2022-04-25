"""gland_site URL Configuration

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
from django.urls import path
import general.views as general
import vv_reports.views as vv_reports
import events_visits.views as events_visits
from django.conf.urls.static import static
from django.conf import settings

urlpatterns =[
    path("admin/", admin.site.urls),
    path("", general.general),
    path("menu/", general.menu),
    path("members/", general.members),
    path("members2/", general.members2),
    path("create_qr_code/", general.create_qr_code),
    path("add_mem_qrsend/", general.add_mem_qrsend),
    path("qr_email_sending/", general.qr_email_sending),
    path("add_members/", general.add_members),
    path("vv_reports_menu/", vv_reports.vv_reports_menu),
    path("vv_cards_correct/", vv_reports.vv_cards_correct),
    path("vv_nocard_emails/", vv_reports.vv_nocard_emails),
    path("vv_all_members_report/", vv_reports.vv_all_members_report),
    path("vv_events_visits_report/", vv_reports.vv_events_visits_report),
    path("events_visits_menu/", events_visits.events_visits_menu),
    path("events_visits_import/", events_visits.events_visits_import),

]
# включаем возможность обработки картинок
if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
