from django.urls import path
from django.views.generic.base import RedirectView
from . import views

urlpatterns = [
    # AUTH
        # LOGIN
    path('', views.login_view, name='login'),
    path('login', RedirectView.as_view(url='/', permanent=True)),
        # CHANGE PASSWORD
    path('change-password', views.change_password, name='change_password'),
        # FORGOT PASSWORD
    path('forgot-password', views.forgot_password, name='forgot_password'),
        # RESET PASSWORD
    path('reset-password/<uidb64>/<token>/', views.reset_password, name='reset_password'),
        # ACTIVATE EMAIL
    path('activate-email', views.activate_email, name='activate_email'),
    path('verify-email/<uidb64>/<token>', views.verify_email, name='verify_email'),
        # LOGOUT
    path('logout', views.logout_view, name='logout'),
    # DMS
    path('home', views.home, name='home'),
    # FORMS
        # DELETE ALL
    path('delete/all', views.delete_selected, name='delete_selected'),
        # CREATE
    path('add/folder', views.add_folder, name='add_folder'),
        # EDIT
    path('edit/folder/<str:folder_id>', views.edit_folder, name='edit_folder'),
        # DELETE
    path('delete/folder/<str:folder_id>', views.delete_folder, name='delete_folder'),
    # FOLDER
    path('folder/<str:folder_id>', views.folder, name='folder'),
    # DOCUMENT
        # CREATE
    path('upload/document', views.upload, name='upload'),
        # EDIT
    path('edit/document/<str:document_id>', views.edit_document, name='edit_document'),

    path('edit/text/document/<str:document_id>', views.edit_text, name='edit_text'),
        # DELETE
    path('delete/document/<str:document_id>', views.delete_document, name='delete_document'),
        # EXTRACT TEXT
    path('extract-text/document', views.extract_text, name='extract_text'),
        # NEW VERSION
    path('upload/version/document', views.upload_new_version, name='upload_new_version'),
        # DOWNLOAD FILE
    path('download/file', views.download_file, name='download_file'),
    # SEARCH 
    path('search', views.search, name='search'),
    # GIVE ACCESS
    path('add-access', views.add_access, name='add_access'),
    # REMOVE ACCESS
    path('remove-access', views.remove_access, name='remove_access'),
    # MOVE ITEMS
    path('move/files', views.move_files, name='move_files'),
    # STAR
        # FOLDER
            # ADD STARRED FOLDER
    path('starred/add/folder', views.add_folder_star),
            # REMOVE STARRED FOLDER
    path('starred/remove/folder', views.remove_folder_star),
        # DOCUMENT
            # ADD STARRED DOCUMENT
    path('starred/add/document', views.add_document_star),
            # REMOVE STARRED DOCUMENT
    path('starred/remove/document', views.remove_document_star),
    # MY FOLDER
    path('my-folders', views.user_folder, name='user_folder'),
    # STARRED 
    path('starred', views.user_starred, name='user_starred'),
    # SUPERADMIN
    path('archives/download', views.download_archive, name='download_archive'),
    # ADMIN
        # DASHBOARD
    path('admin', views.dashboard, name='dashboard'),
        # ARCHIVES
    path('archives', views.archives, name='archives'),
        # ACTIVITY LOGS
    path('activity-logs', views.activity_logs, name='activity_logs'),
        # USER LIST
    path('users', views.user_list, name='user_list'),
        # ADD USER
    path('users/add', views.add_user, name='add_user'),
        # DELETE USER
    path('user/delete', views.delete_user),
        # EDIT ROLE
    path('role/edit', views.edit_role),
    # NOTIFICATION
    path('notifications', views.notifications, name='notifications'),
    path('notification/<str:notification_id>', views.notification),
    # PROFILE
    path('profile', views.profile, name='profile'),
    # REVIEWER
        # REVIEW FOLDERS
    path('review/folders', views.review_folders, name='review_folders'),
        # REVIEW FOLDERS
    path('review/documents', views.review_documents, name='review_documents'),
        # ACCEPT
    path('review/accept', views.reviewer_accept),
        # REMOVE
    path('reviewer/remove', views.reviewer_remove),
    # REPORT
    path('report', views.report),
    # REPORT LIST
    path('reports', views.report_list, name='report_list'),
        # REPORT ACCEPT
    path('report/accept', views.report_accept),
        # REPORT IGNORE
    path('report/ignore', views.report_ignore),
]