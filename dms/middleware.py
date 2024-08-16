from django.shortcuts import redirect
from django.urls import reverse

from django.http import HttpResponseNotFound, HttpResponseRedirect
from django.shortcuts import get_object_or_404
from .models import *

class FolderMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response
    
    def __call__(self, request):
        if request.path.startswith('/folder/'):
            folder_id = request.path_info.split('/')[2]
            folder = get_object_or_404(Folder, id=folder_id)

            if folder.is_deleted or folder.type == 'PRIVATE' and request.user not in folder.allowed_users.all():
                return HttpResponseNotFound()
        
        elif request.path.startswith('/edit/folder'):
            folder_id = request.path_info.split('/')[3]
            folder = get_object_or_404(Folder, id=folder_id)

            if folder.is_deleted or folder.type == 'PRIVATE' and request.user not in folder.allowed_users.all():
                return HttpResponseNotFound()
            
        response = self.get_response(request)
        return response
    
class DocumentMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        if request.path.startswith('/edit/document/'):
            document_id = request.path_info.split('/')[3]
            document = get_object_or_404(Document, id=document_id)
            print(document.is_deleted)
            if document.is_deleted:
                return HttpResponseNotFound()
            elif document.folder.type == 'PRIVATE' and not document.folder.allowed_users.filter(id=request.user.id).exists():
                return HttpResponseNotFound()
            
        return self.get_response(request)
    
class MediaAccessMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        if request.path.startswith('/media/'):
            if not request.user.is_authenticated:
                return redirect(reverse('login'))

        if request.path.startswith('/media/documents/'):
            file_path = request.path.replace('/media/', '', 1)
            document = Document.objects.get(file=file_path, is_deleted=False)
            if 'document' in locals() and document.folder.type == 'PRIVATE' and not document.folder.allowed_users.filter(id=request.user.id).exists():
                return HttpResponseNotFound()
        elif request.path.startswith('/media/archives/'):
            if not request.user.user_type == 'SUPERADMIN':
                return HttpResponseNotFound()

        response = self.get_response(request)
        return response

class ChangePasswordMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        if request.path == '/' or request.path == '/logout' or request.path == '/forgot-password' or request.path.startswith('/reset-password/') or request.path.startswith('/verify-email/') or request.path.startswith('/admin/'):
            return self.get_response(request)
        if request.path in [reverse('activate_email'), reverse('change_password')]:
            return self.get_response(request)
        
        if request.user.is_authenticated:
            user = request.user

            if not user.is_email_verified or not user.is_changepass:
                if not user.is_email_verified:
                    return redirect(reverse('activate_email'))
                if not user.is_changepass:
                    return redirect(reverse('change_password'))
                
        response = self.get_response(request)
        return response