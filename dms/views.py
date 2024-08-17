from django.shortcuts import render, redirect
from .forms import *
from django.contrib.auth import authenticate, login, logout, update_session_auth_hash
from django.contrib.auth.decorators import login_required
from django.views.decorators.http import require_POST
from django.http import HttpResponse, JsonResponse
from .models import *
from django.shortcuts import get_object_or_404
from django.contrib import messages
from django.db.models import Q
import json
from .utils import process_document_ai
from django.conf import settings
import mimetypes
from .decorators import *
from django.utils.translation import gettext_lazy as _
from django.core.mail import send_mail
from django.template.loader import render_to_string
from django.db.models import Count
import random, string
from django.contrib.auth.hashers import make_password
from django.contrib.auth.tokens import default_token_generator
from django.utils.http import urlsafe_base64_encode, urlsafe_base64_decode
from django.utils.encoding import force_bytes
from datetime import timedelta
import zipfile
# Create your views here.

"""

    USER ROLES = [SUPERADMIN, ADMIN, REVIEWER, STAFF]

"""

"""

    AUTHENTICATION

"""
def login_view(request):
    if request.user.is_authenticated:
        if request.user.user_type == 'SUPERADMIN' or request.user.user_type == 'ADMIN':
            return redirect('dashboard')
        elif request.user.user_type == 'STAFF':
            return redirect('home')
        elif request.user.user_type == 'REVIEWER':
            return redirect('review_folders')
        
    if request.method == 'POST':
        form = LoginForm(request.POST)
        if form.is_valid():
            email = request.POST.get('email')
            password = request.POST.get('password')
            user = authenticate(request, email=email, password=password)
            try:
                user_obj = User.objects.get(email=email)
            except User.DoesNotExist:
                form.add_error('email', 'No account found using email provided.')

            if user is not None:
                login(request, user)

                ActivityLog.objects.create(
                    user = request.user,
                    kind = 'LOGIN/LOGOUT',
                    status = 'LOGGED IN',
                    text = f'{request.user.user_type} {user.id} logged in.'
                )

                if 'next' in request.POST:
                    return redirect(request.POST.get('next'))

                if request.user.user_type == 'SUPERADMIN' or request.user.user_type == 'ADMIN':
                    return redirect('dashboard')
                elif request.user.user_type == 'REVIEWER':
                    return redirect('review_folders')
                elif request.user.user_type == 'STAFF':
                    return redirect('home')
            else:
                form.add_error('password', "Incorrect password.")
    else:
        form = LoginForm()
        
    return render(request, 'auth/login.html', {'form': form})

@require_POST
def logout_view(request):
    if not request.user.is_authenticated:
        return HttpResponse(status=404)

    ActivityLog.objects.create(
        user = request.user,
        kind = 'LOGIN/LOGOUT',
        status = 'LOGGED OUT',
        text = f'{request.user.user_type} {request.user.id} logged out.'
    )

    logout(request)

    messages.success(request, 'You have been logged out.')
    return redirect('login')

"""

    ADMIN

"""
@login_required
@for_admins
def dashboard(request):
    documents = Document.objects.filter(is_deleted=False).count()
    folders = Folder.objects.filter(is_deleted=False).count()
    public_folders = Folder.objects.filter(is_deleted=False, type='PUBLIC').count()
    private_folders = Folder.objects.filter(is_deleted=False, type='PRIVATE').count()
    users = User.objects.filter(is_deleted=False, is_email_verified=True).count()
    documents_extracted = Document.objects.filter(is_deleted=False, extracted_text__isnull=False).count()
    document_instances = Document.objects.filter(is_deleted=False)
    document_list = [document.created_at.isoformat() for document in document_instances]
    top_users_instance = User.objects.filter(is_deleted=False).annotate(num_documents=Count('document_created_by')).order_by('-num_documents')[:5]
    top_users = []
    top_counts = []
    for user in top_users_instance:
        top_users.append(user.name)
        top_counts.append(user.num_documents)

    most_altered_documents = Document.objects.order_by('-version')[:5]
    most_doc_name = []
    most_doc_version = []
    for doc in most_altered_documents:
        most_doc_name.append(doc.title)
        most_doc_version.append(doc.version)

    context = {
        'documents': documents,
        'folders': folders,
        'public_folders': public_folders,
        'private_folders': private_folders,
        'users': users,
        'documents_extracted':documents_extracted,
        'document_list': document_list,
        'top_users': top_users,
        'top_counts': top_counts,
        'most_doc_name': most_doc_name,
        'most_doc_version': most_doc_version,
    }

    return render(request, 'admin/dashboard.html', context)

@login_required
@for_admins
def archives(request):
    documents = ArchiveVersion.objects.all()

    return render(request, 'admin/archives.html', {'documents': documents})

"""

    DMS

"""
@login_required
@anti_reviewer
def home(request):
    user = request.user
    # Fetch all the Root Folders using parent field that are null
    root_folders = Folder.objects.filter(Q(parent__isnull=True) & Q(is_deleted=False) & Q(type='PUBLIC'))
    private_folders = Folder.objects.filter(parent__isnull=True, is_deleted=False, type='PRIVATE', allowed_users=user)
    folders = Folder.objects.all()
    documents = Document.objects.all()
    all_folders = Folder.objects.filter(is_deleted=False)
    context = {
        'root_folders': root_folders,
        'private_folders': private_folders,
        'documents': documents,
        'folders': folders,
        'all_folders': all_folders
    }

    return render(request, 'dms/home.html', context)

"""

    GET FOLDER PATH

"""
def get_folder_path(folder):
    path = []
    while folder is not None:
        path.insert(0, folder)
        folder = folder.parent
    return path

@login_required
@anti_reviewer
def folder(request, folder_id):
    folder = get_object_or_404(Folder, id=folder_id)

    # if folder.is_deleted:
    #     return HttpResponse(status=404)
    # elif folder.type == 'PRIVATE' and folder.created_by != request.user:
    #     return HttpResponse(status=404)

    folders = Folder.objects.filter(Q(parent=folder) & Q(is_deleted=False))
    folder_path = get_folder_path(folder)
    documents = Document.objects.filter(Q(folder=folder.id) & Q(is_deleted=False))

    all_folders = Folder.objects.filter(is_deleted=False)

    if request.method == 'POST':
        Folder.objects.create(
            name = request.POST.get('name', 'Untitled Folder View'),
            parent = folder,
            type = request.POST.get('type'),
            created_by = request.user
        )

        messages.success(request, 'Folder created successfully.')

        return redirect('folder', folder_id=folder.id)

    context = {
        'folder': folder,
        'folders': folders,
        'documents': documents,
        'folder_path': folder_path,
        'all_folders': all_folders
        # 'form': form
    }

    return render(request, 'dms/folder.html', context)

@login_required
@require_POST
def add_folder(request):
    # New Folder Form Submission
    name = request.POST.get('name')
    type = request.POST.get('type')
    parent = request.POST.get('parent')

    if parent == '':
        parent = None;
    else:
        parent = get_object_or_404(Folder, id=parent)

    if name == '':
        name = 'Untitled Folder'
    folder = Folder.objects.create(
        name = name,
        parent = parent,
        created_by = request.user,
        type = type
    )
    folder.allowed_users.add(request.user)

    if not folder.parent is None:
        if not folder.parent.created_by == request.user:
            Notification.objects.create(
                recipient = folder.parent.created_by,
                doer = request.user,
                type_id = folder.id,
                kind = 'FOLDER',
                text = f'User {folder.parent.created_by.id} created a folder inside your folder {folder.id}.'
            )

    ActivityLog.objects.create(
        user = request.user,
        kind = 'FOLDER',
        type_id = folder.id,
        status = 'CREATED',
        text = f'{request.user.user_type} {request.user.id} created folder {folder.id}.'
    )

    messages.success(request, 'Folder created successfully.')

    return JsonResponse({'message': 'Folder created successfully.'})

@login_required
@anti_reviewer
def edit_folder(request, folder_id):
    folder = get_object_or_404(Folder, id=folder_id)
    users = User.objects.filter(Q(user_type='STAFF') & Q(is_deleted=False) | Q(user_type='ADMIN') & Q(is_deleted=False) | Q(user_type='SUPERADMIN') & Q(is_deleted=False)).exclude(id=request.user.id)
    allowed_users = folder.allowed_users.all().exclude(id=folder.created_by.id)
    app_url = settings.APP_URL

    is_folder_starred = False

    if request.user.starred_folders is not None:
        starred_folders = request.user.starred_folders.split(',')
    
        if folder.id in starred_folders:
            is_folder_starred = True

    if request.method == 'POST':
        name = request.POST.get('name')
        if name == '':
            name = 'Untitled Folder'
        type = request.POST.get('type')
        if type == '':
            type = 'PUBLIC'
        elif type == 'PUBLIC':
            type == 'PUBLIC'
        elif type == 'PRIVATE':
            folder_users = User.objects.filter(starred_folders__isnull=False)
            document_users = User.objects.filter(starred_documents__isnull=False)

            for user in folder_users:
                user = get_object_or_404(User, id=user.id)
                folders = user.starred_folders.split(',') if user.starred_folders else []

                if str(folder.id) in folders:
                    folders.remove(str(folder.id))

                user.starred_folders = ','.join(folders)
                user.save()


            for user in document_users:
                user = get_object_or_404(User, id=user.id)
                documents = user.starred_documents.split(',')

                documents = [doc_id for doc_id in documents if not Document.objects.filter(id=doc_id, folder__id=folder.id).exists()]
                user.starred_documents = ','.join(documents)
                user.save()
                
        folder.name = name
        folder.updated_by = request.user

        def update_children(folder, type, user):
            folder.type = type
            folder.save()
            children = folder.children.all()
            for child in children:
                update_children(child, type, user)

        update_children(folder, type, request.user)

        if not folder.created_by == request.user:
            Notification.objects.create(
                recipient = folder.created_by,
                doer = request.user,
                type_id = folder.id,
                kind = 'FOLDER',
                text = f'{request.user.user_type} {request.user.id} edited your folder {folder.id}.'
            )

        ActivityLog.objects.create(
            user = request.user,
            kind = 'FOLDER',
            type_id = folder.id,
            status = 'EDITED',
            text = f'{request.user.user_type} {request.user.id} edited folder {folder.id}.'
        )

        messages.success(request, f'Folder {folder.id} edited succesfully.')

        return JsonResponse({'success': f'Folder {folder.id} edited successfully.'})

    context = {
        'folder': folder,
        'users': users,
        'allowed_users': allowed_users,
        'is_folder_starred': is_folder_starred,
        'app_url': app_url
    }
    return render(request, 'dms/folder-edit.html', context)

def delete_folder_children(parent):
    children = Folder.objects.filter(parent=parent)
    users = User.objects.all()

    for child in children:
        for user in users:
            starred_list = user.starred_folders.split(',')
            folder_id = str(child.id)
            if folder_id in starred_list:
                starred_list.remove(folder_id)

                user.starred_folders = ','.join(starred_list)
                user.save()

        documents = Document.objects.all()

        for doc in documents:
            if child.id == doc.folder.id:
                path = doc.file.path
                if os.path.exists(path):
                    os.remove(path)

        child.is_deleted = True
        child.save()
        delete_folder_children(child)

@login_required
@require_POST
@anti_reviewer
def delete_folder(request, folder_id):
    folder = get_object_or_404(Folder, id=folder_id)
    folder_id = folder.id 

    if folder.type == 'PRIVATE':
        if not request.user == folder.created_by:
            messages.error(request, 'Cannot process this request at the moment.')

            return JsonResponse({'message': 'Cannot process this request at the moment.'})
    
    if folder.parent is None:
        delete_folder_children(folder)

    documents = Document.objects.all()

    for doc in documents:
        if folder_id == doc.folder.id:
            path = doc.file.path
            if os.path.exists(path):
                os.remove(path)

    folder.is_deleted = True
    folder.save()

    user = request.user
    starred_list = user.starred_folders.split(',')
    if folder_id in starred_list:
        starred_list.remove(folder_id)

        user.starred_folders = ','.join(starred_list)
        user.save()

    # folder.delete()

    ActivityLog.objects.create(
        user = request.user,
        kind = 'FOLDER',
        type_id = folder.id,
        status = 'DELETED',
        text = f'{request.user.user_type} {request.user.id} deleted folder {folder.id}.'
    )

    messages.success(request, f'Folder {folder_id} deleted successfully.')

    return JsonResponse({'message': 'Folder deleted successfully.'})

@login_required
@require_POST
def delete_selected(request):
    data = json.loads(request.body)
    folders = data.get('folders', [])
    documents = data.get('documents', [])

    for id in folders:
        folder = get_object_or_404(Folder, id=id)

        if not folder.created_by == request.user:
            messages.error(request, "You are not authorized to delete other users' folders/documents.")

            return JsonResponse({'message': "You are not authorized to delete other users' folders/documents."})

    for id in documents:      
        document = get_object_or_404(Document, id=id)

        if not document.created_by == request.user:
            messages.error(request, "You are not authorized to delete other users' folders/documents.")

            return JsonResponse({'message': "You are not authorized to delete other users' folders/documents."})
        
        if document.folder.type == 'PRIVATE' and not document.folder.created_by == request.user:
            messages.error(request, 'Cannot process this request at the moment.1')
            return JsonResponse({'message': 'Cannot process this request at the moment.'})
        
        elif document.folder.type == 'PUBLIC' and not document.created_by == request.user:
            messages.error(request, 'Cannot process this request at the moment.2')
            return JsonResponse({'message': 'Cannot process this request at the moment.'})
        
    for id in folders:
        folder = get_object_or_404(Folder, id=id)

        if folder.type == 'PRIVATE' and not request.user == folder.created_by:
            messages.error(request, 'Cannot process this request at the moment.')

            return JsonResponse({'message': 'Cannot process this request at the moment.'})
        
        if folder.parent is None:
            delete_folder_children(folder)

        documents = Document.objects.all()

        for doc in documents:
            if folder.id == doc.folder.id:
                path = doc.file.path
                if os.path.exists(path):
                    os.remove(path)

        folder.is_deleted = True
        folder.save()

        user = request.user
        starred_list = user.starred_folders.split(',')
        if folder.id in starred_list:
            starred_list.remove(folder.id)

            user.starred_folders = ','.join(starred_list)
            user.save()
        
    for id in documents:
        document = get_object_or_404(Document, id=id)
    
        document.is_deleted = True
        document.save()

        document_versions = DocumentVersion.objects.filter(document=document)
        for version in document_versions:
            v_path = version.file.path
            if os.path.exists(v_path):
                os.remove(v_path)

        path = document.file.path
        if os.path.exists(path):
            os.remove(path)
        

    messages.success(request, 'Selected item/s deleted successfully.')

    return JsonResponse({'message': 'Selected item/s deleted successfully.'})

"""

    Documents

"""
@login_required
@require_POST
def upload(request):
    if request.FILES:
        file = request.FILES['file']

        id = request.POST.get('folder_id')
        folder = get_object_or_404(Folder, id=id)
        document = Document(file=file)
        document.title = file
        document.folder = folder
        document.created_by = request.user
        document.save()

        DocumentVersion.objects.create(
            document=document,
            file=file,
            created_by=document.created_by
        )

        ArchiveVersion.objects.create(
            file=file,
            created_by=document.created_by
        )

        ActivityLog.objects.create(
            user = request.user,
            kind = 'DOCUMENT',
            type_id = document.id,
            status = 'UPLOAD',
            text = f'{request.user.user_type} {request.user.id} uploaded document {document.id}.'
        )

        if not document.folder is None:
            if not document.folder.created_by == request.user:
                Notification.objects.create(
                    recipient = document.folder.created_by,
                    doer = request.user,
                    type_id = document.id,
                    kind = 'DOCUMENT',
                    text = f'User {document.folder.created_by.id} uploaded a document inside your folder {document.folder.id}.'
            )

        messages.success(request, 'Document uploaded successfully.')

        return JsonResponse({'message': 'Document uploaded successfully.'})
    
@login_required
@require_POST
def upload_new_version(request):
    if request.FILES:
        file = request.FILES['file']

        id = request.POST.get('document_id')
        document = get_object_or_404(Document, id=id)

        path = document.file.path
        if os.path.exists(path):
            os.remove(path)

        document.file = file
        document.updated_by = request.user
        current_version = document.version
        document.version = current_version + 1
        document.is_reviewed = False
        document.save()

        DocumentVersion.objects.create(
            document=document,
            file=file,
            created_by=document.updated_by,
            version=document.version
        )

        ActivityLog.objects.create(
            user = request.user,
            kind = 'DOCUMENT',
            type_id = document.id,
            status = 'UPLOAD',
            text = f'{request.user.user_type} {request.user.id} uploaded new version of document {document.id}.'
        )

        ArchiveVersion.objects.create(
            file=file,
            created_by=document.created_by
        )

        if not document.created_at == request.user:
            Notification.objects.create(
                recipient = document.created_by,
                doer = request.user,
                type_id = document.id,
                kind = 'DOCUMENT',
                text = f'{request.user.user_type} {request.user.id} uploaded a new version of your document {document.id}.'
            )

        messages.success(request, 'New document version uploaded successfully.')

        return JsonResponse({'message': 'New document version uploaded successfully.'})

@login_required
@require_POST
def delete_document(request, document_id):
    document = get_object_or_404(Document, id=document_id)
    document.is_deleted = True
    document.save()

    document_versions = DocumentVersion.objects.filter(document=document)
    for version in document_versions:
        v_path = version.file.path
        if os.path.exists(v_path):
            os.remove(v_path)

    path = document.file.path
    if os.path.exists(path):
        os.remove(path)

    ActivityLog.objects.create(
        user = request.user,
        kind = 'DOCUMENT',
        type_id = document.id,
        status = 'DELETE',
        text = f'{request.user.user_type} {request.user.id} deleted document {document.id}.'
    )

    messages.success(request, f'Document {document.id} delete successfully.')

    return JsonResponse({'message': 'Document deleted successfully.'})

@login_required
@anti_reviewer
def edit_document(request, document_id):
    document = get_object_or_404(Document, id=document_id)
    versions = DocumentVersion.objects.filter(document=document)

    is_document_starred = False

    if request.user.starred_documents is not None:
        starred_documents = request.user.starred_documents.split(',')

        if document.id in starred_documents:
            is_document_starred = True

    if request.method == 'POST':
        title = request.POST.get('name')
        document.title = title
        document.updated_by = request.user
        document.save()

        ActivityLog.objects.create(
            user = request.user,
            kind = 'DOCUMENT',
            type_id = document.id,
            status = 'EDITED',
            text = f'{request.user.user_type} {request.user.id} edited document {document.id}.'
        )

        messages.success(request, f'Document {document.id} edited successfully.')

        return JsonResponse({'message': f'Document {document.id} edited successfully.'})
        
        
    return render(request, 'dms/document-edit.html', {'document': document, 'versions': versions, 'is_document_starred': is_document_starred})


@login_required
@require_POST
@anti_reviewer
def edit_text(request, document_id):
    document = get_object_or_404(Document, id=document_id)

    data = json.loads(request.body)
    text = data.get('text')

    document.extracted_text = text
    document.updated_by = request.user
    document.save()

    messages.success(request, 'Extracted text updated successfully.')

    return JsonResponse({'message': 'Ok.'})

@login_required
@require_POST
def extract_text(request):
    allowed_types = ['image/jpeg', 'image/png', 'application/pdf']
    data = json.loads(request.body)
    folders = data.get('folders', [])
    documents = data.get('documents', [])

    if len(folders) > 0:
        messages.error(request, 'Please select documents only.')
        return JsonResponse({'message': 'Please select documents only.'})
    
    documents_to_extract = []

    for id in documents:
        document = get_object_or_404(Document, id=id)
        file_instance = document.file

        mime_type, _ = mimetypes.guess_type(file_instance.name)

        if mime_type not in allowed_types:
            messages.error(request, 'Please select image and pdf files only.')
            return JsonResponse({'message': 'Please select image and pdf files only.'})
        else:
            documents_to_extract.append(document)

    for document in documents_to_extract:
        project_id = settings.PROJECT_ID
        location = settings.LOCATION
        processor_id = settings.PROCESSOR_ID

        file_path = document.file.path

        result_json = process_document_ai(project_id, location, file_path, processor_id)

        if result_json:
            extracted_text = result_json.get('text', '')

        document.extracted_text = extracted_text
        document.save()

    messages.success(request, 'Texts of selected documents extracted successfully.')

    return JsonResponse({'message': 'Texts of selected documents extracted successfully.'})

@login_required
@require_POST
def new_version(request):
    if request.FILES:
        file = request.FILES['file']

        id = request.POST.get('document_id')
        document = get_object_or_404(Document, id=id)
        document.file = file
        document.version += 1
        document.save()

        items = []
        old_versions = DocumentVersion.objects.filter(document=document)

        for item in old_versions:
            items.append(item.version)

        new_version_id = items.sort[-1]
        
        new_version_instance = get_object_or_404(DocumentVersion, id=new_version_id)

        DocumentVersion.objects.create(
            file=file,
            document=document,
            created_by=request.user,
            version=new_version_instance.version + 1
        )

        messages.success(request, 'Document uploaded successfully.')

        return JsonResponse({'message': 'Document uploaded successfully.'})

@login_required
@require_POST
def search(request):
    data = json.loads(request.body)
    keyword = data.get('input', '')
    id = data.get('id', '')

    if id == '':
        if keyword == '':
            # folder_result = Folder.objects.filter(Q(parent=None) & Q(is_deleted=False)).exclude(is_deleted=True)
            folder_result = Folder.objects.filter(Q(parent=None) & Q(is_deleted=False) & Q(allowed_users=request.user))
            document_result = Document.objects.none()
        else:
            folder_result = Folder.objects.filter(name__icontains=keyword).exclude(is_deleted=True)
            document_result = Document.objects.filter(Q(title__icontains=keyword) | Q(extracted_text__icontains=keyword)).exclude(is_deleted=True)
    else: 
        folder = Folder.objects.get(id=id)
        if keyword == '':
            folder_result = Folder.objects.filter(parent=folder).exclude(is_deleted=True)
            document_result = Document.objects.filter(folder=folder).exclude(is_deleted=True)
        else:
            folder_result = Folder.objects.filter(parent=folder, name__icontains=keyword).exclude(is_deleted=True)
            document_result = Document.objects.filter(Q(folder=folder) & Q(title__icontains=keyword) | Q(extracted_text__icontains=keyword)).exclude(is_deleted=True)

    data = {
        'folders': list(folder_result.values()),  # Convert QuerySet to list of dicts
        'documents': list(document_result.values()) if document_result else [],  # Convert QuerySet to list of dicts, handle None case
    }
    return JsonResponse(data)

@login_required
@require_POST
def add_access(request):
    data = json.loads(request.body)
    user_id = data.get('selectedId')
    folder_id = data.get('folderId')

    folder = get_object_or_404(Folder, id=folder_id)

    user = get_object_or_404(User, id=user_id)

    folder.allowed_users.add(user)

    return JsonResponse({'message': 'User access edited successfully.'})

@login_required
@require_POST
def remove_access(request):
    data = json.loads(request.body)
    user_id = data.get('selectedId', '')
    folder_id = data.get('folderId', '')

    folder = get_object_or_404(Folder, id=folder_id)

    user_obj = get_object_or_404(User, id=user_id)
    folder.allowed_users.remove(user_obj)

    starred_list = user_obj.starred_folders.split(',')

    if folder_id in starred_list:
        starred_list.remove(folder_id)

        user_obj.starred_folders = ','.join(starred_list)
        user_obj.save()

    return JsonResponse({'message': 'Remove access successful.'})

@login_required
@require_POST
def download_file(request):
    data = json.loads(request.body)
    document_id = data.get('documents', '')

    document = get_object_or_404(Document, id=document_id)

    file_path = document.file.path
    file_name = document.file.name.split('/')[-1]

    with open(file_path, 'rb') as f:
        response = HttpResponse(f.read(), content_type=mimetypes.guess_type(file_path)[0])
        response['Content-Disposition'] = 'attachment; filename=%s' % file_name
        return response

@login_required
@require_POST
def move_files(request):
    data = json.loads(request.body)
    folder_id = data.get('folderId')
    documents_to_move = data.get('documents')
    folders_to_move = data.get('folders')

    folder = get_object_or_404(Folder, id=folder_id)

    for id in documents_to_move:
        document = get_object_or_404(Document, id=id)
        document.folder = folder
        document.save()

    for id in folders_to_move:
        folder_instance = get_object_or_404(Folder, id=id)
        folder_instance.parent = folder
        folder_instance.save()

    messages.success(request, 'Selected items moved successfully.')

    return JsonResponse({'message': 'Selected items moved successfully.'})

@login_required
@require_POST
def add_folder_star(request):
    data = json.loads(request.body)
    user = request.user
    folder_id = data.get('folderId')

    if user.starred_folders == '':
        user.starred_folders = folder_id
    else:
        current = user.starred_folders
        user.starred_folders = current + ',' + folder_id

    user.save()

    messages.success(request, 'Folder added to starred.')

    return JsonResponse({'message': 'success'})

@login_required
@require_POST
def remove_folder_star(request):
    data = json.loads(request.body)
    folder_id = data.get('folderId')
    user = request.user

    starred_list = user.starred_folders.split(',')

    if folder_id in starred_list:
        starred_list.remove(folder_id)

        user.starred_folders = ','.join(starred_list)
        user.save()

    messages.success(request, 'Folder removed from starred.')

    return JsonResponse({'message': 'success'})

@login_required
@require_POST
def add_document_star(request):
    data = json.loads(request.body)
    user = request.user
    document_id = data.get('documentId')

    if user.starred_documents == '':
        user.starred_documents = document_id
    else:
        current = user.starred_documents
        user.starred_documents = current + ',' + document_id

    user.save()

    messages.success(request, 'Document added to starred.')

    return JsonResponse({'message': 'success'})

@login_required
@require_POST
def remove_document_star(request):
    data = json.loads(request.body)
    document_id = data.get('documentId')
    user = request.user

    starred_list = user.starred_documents.split(',')

    if document_id in starred_list:
        starred_list.remove(document_id)

        user.starred_documents = ','.join(starred_list)
        user.save()

    messages.success(request, 'Document removed from starred.')

    return JsonResponse({'message': 'success'})

@login_required
@anti_reviewer
def user_folder(request):
    user = request.user
    folders = Folder.objects.filter(created_by=user).exclude(is_deleted=True)
    documents = Document.objects.filter(created_by=user).exclude(is_deleted=True)
    
    return render(request, 'dms/folder-user.html', {'folders': folders, 'documents': documents})

@login_required
@anti_reviewer
def user_starred(request):
    user = request.user
    folders = []
    documents = []

    if not user.starred_folders == '':
        folder_list = user.starred_folders.split(',')

        for id in folder_list:
            folder = get_object_or_404(Folder, id=id)
            folders.append(folder)

    if not user.starred_documents == '':
        document_list = user.starred_documents.split(',')
        for id in document_list:
            document = get_object_or_404(Document, id=id)
            documents.append(document)

    context = {
        'folders': folders,
        'documents': documents
    }

    return render(request, 'dms/starred.html', context)

@login_required
@anti_reviewer
def notifications(request):
    unread_notifications = Notification.objects.filter(recipient=request.user, is_read=False).order_by('-created_at')
    notifications = Notification.objects.filter(recipient=request.user, is_read=True).order_by('-created_at')

    if request.method == 'POST':
        data = json.loads(request.body)
        is_read = data.get('isRead')

        if is_read == 'True':
            for notification in unread_notifications:
                notification.is_read = True
                notification.save()

    return render(request, 'dms/notifications.html', {'notifications': notifications, 'unread_notifications': unread_notifications})
    
@login_required
@anti_reviewer
def notification(request, notification_id):
    notification = get_object_or_404(Notification, id=notification_id)

    return render(request, 'dms/notification.html', {'notification': notification})

@login_required
@for_admins
def activity_logs(request):
    activity_logs = ActivityLog.objects.all()

    return render(request, 'admin/activity-logs.html', {'activity_logs': activity_logs})

@login_required
@for_admins
def user_list(request):
    users = User.objects.all().exclude(is_deleted=True)

    return render(request, 'admin/user-list.html', {'users': users})

@login_required
@for_admins
def add_user(request):
    def generate_password(length=8):
        char = string.ascii_letters + string.digits
        
        password = ''.join(random.choice(char) for _ in range(length))

        return password
    
    if request.method == 'POST':
        form = NewUserForm(request.POST)
        if form.is_valid():
            raw_password = generate_password()
            password = make_password(raw_password)

            email = request.POST.get('email')

            try:
                user_obj = User.objects.get(email=email)
                if user_obj is not None:
                    form.add_error('email', 'Email address already exists.')
            except User.DoesNotExist:
                user = User.objects.create(
                    email = email,
                    name = request.POST.get('name'),
                    user_type = request.POST.get('user_type'),
                    password = password
                )

                # Send Email
                template = 'mail/email.html'
                subject = 'Account Created at OCRVault'
                app_url = settings.APP_URL
                context = {
                    'name': user.name,
                    'email': user.email,
                    'password': raw_password,
                    'url': app_url
                }
                html_message = render_to_string(template, context)
                from_email = settings.DEFAULT_FROM_EMAIL
                to_email = user.email
                send_mail(subject, message='', from_email=from_email, recipient_list=[to_email], html_message=html_message)

                messages.success(request, f'{user.user_type} {user.id} has been created.')
                return redirect('add_user')
    else:
        form = NewUserForm()

    return render(request, 'admin/user-add.html', {'form': form})

@login_required
def activate_email(request):
    if request.user.is_email_verified:
        return HttpResponse(status=404)
    
    if request.method == 'POST':
        user = request.user
        template = 'mail/activate-email.html'
        subject = 'Email Verification at OCRVault'

        token = default_token_generator.make_token(user)

        token_encoded = urlsafe_base64_encode(force_bytes(token))
        uidb64 = urlsafe_base64_encode(force_bytes(user.pk))

        user.email_token = token_encoded
        user.email_token_created_at = timezone.now()
        user.save()

        app_url = settings.APP_URL

        verify_url = f'{app_url}/verify-email/{uidb64}/{token_encoded}'

        context = {
            'name': user.name,
            'email': user.email,
            'verify_url': verify_url,
            'url': app_url
        }
        html_message = render_to_string(template, context)
        from_email = settings.DEFAULT_FROM_EMAIL
        to_email = user.email
        send_mail(subject, message='', from_email=from_email, recipient_list=[to_email], html_message=html_message)

        messages.success(request, 'Email verification sent to email.')
        return JsonResponse({'message': 'Email verification sent to email.'})
    
    return render(request, 'auth/activate-email.html')

@login_required
def verify_email(request, uidb64, token):
    if request.user.is_email_verified:
        return HttpResponse(status=404)

    user_id = urlsafe_base64_decode(uidb64).decode('utf-8')
    user = User.objects.get(pk=user_id)

    if not user.email_token == token:
        messages.error(request, 'Invalid verification link.')
        return redirect('activate_email')
    elif user.email_token == None:
        messages.error(request, 'No verification link provided.')
        return redirect('activate_email')

    if user.email_token == token:
        user.is_email_verified = True
        user.save()

        return redirect('change_password')
    
    return render(request, 'auth/activate-email.html')
    # else:
    #     return HttpResponse(status=404)
    
@login_required
@for_admins
@require_POST
def delete_user(request):
    data = json.loads(request.body)
    user_id = data.get('userId')
    user = get_object_or_404(User, id=user_id)

    user.is_deleted = True
    user.save()

    messages.success(request, f'User {user.id} has been deleted successfully.')

    return JsonResponse({'message': f'User {user.id} has been deleted successfully.'})

@login_required
def profile(request):
    user = get_object_or_404(User, id=request.user.id)
    
    if request.method == 'POST':
        form = EditUserForm(request.POST)
        if form.is_valid():
            prev_email = user.email
            new_email = form.cleaned_data['email']
            if not prev_email == new_email:
                user.is_email_verified = False
                user.email_token = None
                user.email_token_created_at = None
            user.email = form.cleaned_data['email']
            user.name = form.cleaned_data['name']
            user.save()

            if not prev_email == new_email:
                messages.success(request, 'Please verify your email again.')
            else:
                messages.success(request, 'Profile updated successfully.')

            return redirect('profile')
    else:
        form = EditUserForm()

    return render(request, 'auth/profile.html', {'user': user, 'form': form})

@login_required
@for_admins
@require_POST
def edit_role(request):
    data = json.loads(request.body)
    user_id = data.get('userId')
    role = data.get('role')

    user = get_object_or_404(User, id=user_id)
    user.user_type = role
    user.save()

    messages.success(request, f'Successful changed of role for {user.id} to {role}')

    return JsonResponse({'messages': f'Successful changed of role for {user.id} to {role}'})

@login_required
def change_password(request):
    if request.user.is_email_verified == False:
        return redirect('activate_email')
    
    if request.method == 'POST':
        form =PasswordChangeForm(request.user, request.POST)

        if form.is_valid():
            user = form.save()
            user.is_changepass = True
            user.save()
            update_session_auth_hash(request, user)
            messages.success(request, 'Your password was saved successfully.')
            return redirect('change_password')
    else:
        form = PasswordChangeForm(request.user)

    return render(request, 'auth/change-password.html', {'form': form})

@anti_login
def forgot_password(request):
    if request.method == 'POST':
        form = ForgotPasswordForm(request.POST)
        if form.is_valid():
            email = form.cleaned_data['email']
            try:
                user = User.objects.get(email=email)

                token = default_token_generator.make_token(user)

                uidb64 = urlsafe_base64_encode(force_bytes(user.pk))
                token_encoded = urlsafe_base64_encode(force_bytes(token))

                user.password_reset_token = token_encoded
                user.password_reset_token_created_at = timezone.now()
                user.save()

                app_url = settings.APP_URL

                reset_link = f'{app_url}/reset-password/{uidb64}/{token_encoded}'


                # Send Email
                template = 'mail/reset-password.html'
                subject = 'Request for Change Password at OCRVault'
                app_url = settings.APP_URL
                context = {
                    'name': user.name,
                    'url': app_url,
                    'reset_link': reset_link
                }

                html_message = render_to_string(template, context)
                from_email = settings.DEFAULT_FROM_EMAIL
                to_email = user.email
                send_mail(subject, message='', from_email=from_email, recipient_list=[to_email], html_message=html_message)

                messages.success(request, 'Reset link has been sent to your email.')
                return redirect('login')
            except User.DoesNotExist:
                form.add_error('email', 'Account with email provided not found.')
    else:
        form = ForgotPasswordForm()

    return render(request, 'auth/login.html', {'form': form})

@anti_login
def reset_password(request, uidb64, token):
    if request.user.is_authenticated:
        if request.user.user_type == 'SUPERADMIN' or request.user.user_type == 'ADMIN':
            return redirect('dashboard')
        elif request.user.user_type == 'STAFF':
            return redirect('home')
        elif request.user.user_type == 'REVIEWER':
            return redirect('review_folders')
    try:
        user_id = urlsafe_base64_decode(uidb64).decode('utf-8')
        user = User.objects.get(pk=user_id)

        if user.password_reset_token is None:
            messages.error(request, 'Invalid reset link.')
            return redirect('login')
        else:
            diff = user.password_reset_token_created_at - timezone.now()

            if diff > timedelta(hours=1):
                messages.error(request, 'Expired reset link.')
                return redirect('login')
        
        if request.method == 'POST':
            form = PasswordChangeForm(user, request.POST)
            if form.is_valid():
                user = form.save()
                user.password_reset_token = None
                user.password_reset_token_created_at = None
                user.save()
                update_session_auth_hash(request, user)
                return redirect('login')
        else:
            form = PasswordChangeForm(user)
    except (User.DoesNotExist, UnicodeDecodeError, ValueError):
        messages.error(request, 'Invalid reset link. User not found.')
        return redirect('login')
    
    return render(request, 'auth/reset-password.html', {'form': form, 'uidb64': uidb64, 'token': token, 'user': user})

"""

    # REVIEWER

"""
@login_required
@for_reviewer
def review_folders(request):
    folders = Folder.objects.filter(is_reviewed=False).exclude(is_deleted=True)

    context = {
        'folders': folders
    }

    return render(request, 'reviewer/review-folders.html', context)

@login_required
@for_reviewer
def review_documents(request):
    documents = Document.objects.filter(is_reviewed=False).exclude(is_deleted=True)

    context = {
        'documents': documents
    }

    return render(request, 'reviewer/review-documents.html', context)

@login_required
@require_POST
def reviewer_accept(request):
    data = json.loads(request.body)
    id = data.get('id')
    kind = data.get('kind')

    if kind == 'FOLDER':
        folder = get_object_or_404(Folder, id=id)
        folder.is_reviewed = True
        folder.reviewed_at = timezone.now()
        folder.save()
        
        ActivityLog.objects.create(
            text = f'{request.user.user_type} {request.user.id} accepted folder {folder.id}.'
        )

        Notification.objects.create(
            recipient = folder.created_by,
            doer = request.user,
            type_id = folder.id,
            kind = 'FOLDER',
            text = f'Your folder {folder.id} was reviewed and accepted.'
        )

        messages.success(request, f'Folder {folder.id} accepted.')
    elif kind == 'DOCUMENT':
        document = get_object_or_404(Document, id=id)
        document.is_reviewed = True
        document.reviewed_at = timezone.now()
        document.save()

        ActivityLog.objects.create(
            text = f'{request.user.user_type} {request.user.id} accepted document {document.id}.'
        )

        Notification.objects.create(
            recipient = document.created_by,
            doer = request.user,
            type_id = document.id,
            kind = 'DOCUMENT',
            text = f'Your document {document.id} is reviewed and accepted.'
        )

        messages.success(request, f'Document {document.id} accepted.')
    
    return JsonResponse({'message': 'Accepted.'})

@login_required
@require_POST
def reviewer_remove(request):
    data = json.loads(request.body)
    id = data.get('id')
    kind = data.get('kind')

    if kind == 'FOLDER':
        folder = get_object_or_404(Folder, id=id)
        folder.is_deleted = True
        folder.is_reviewed = True
        folder.reviewed_at = timezone.now()
        folder.save()

        ActivityLog.objects.create(
            text = f'{request.user.user_type} {request.user.id} removed folder {folder.id}.'
        )

        Notification.objects.create(
            recipient = folder.created_by,
            doer = request.user,
            type_id = folder.id,
            kind = 'FOLDER',
            text = f'Your folder {folder.id} was reviewed and removed.'
        )

        messages.success(request, f'Folder {folder.id} removed.')
    elif kind == 'DOCUMENT':
        document = get_object_or_404(Document, id=id)
        document.is_deleted = True
        document.is_reviewed = True
        document.reviewed_at = timezone.now()
        document.save()

        ActivityLog.objects.create(
            text = f'{request.user.user_type} {request.user.id} removed document {document.id}.'
        )

        Notification.objects.create(
            recipient = document.created_by,
            doer = request.user,
            type_id = document.id,
            kind = 'DOCUMENT',
            text = f'Your document {document.id} is reviewed and accepted.'
        )

        messages.success(request, f'Document {document.id} removed.')

    return JsonResponse({'message': 'Removed.'})

@login_required
@require_POST
def report(request):
    data = json.loads(request.body)
    id = data.get('id')
    kind = data.get('kind')
    type = data.get('type')
    details = data.get('details')

    Report.objects.create(
        user = request.user,
        type_id = id,
        kind = kind,
        type = type,
        details = details
    )

    messages.success(request, 'Report submitted.')

    return JsonResponse({'message': 'Report submitted.'})

@login_required
@for_admins
def report_list(request):
    reports = Report.objects.filter(is_verified=False)

    return render(request, 'admin/report-list.html', {'reports': reports})

@login_required
@require_POST
def report_accept(request):
    data = json.loads(request.body)
    report_id = data.get('reportId')
    type_id = data.get('typeId')
    kind = data.get('kind')

    if kind == 'FOLDER':
        folder = get_object_or_404(Folder, id=type_id)

        if folder.parent is None:
            delete_folder_children(folder)

        folder.is_deleted = True
        folder.save()
        user = folder.created_by
    else:
        document = get_object_or_404(Document, id=type_id)
        document.is_deleted = True
        document.save()

        user = document.created_by

    report = get_object_or_404(Report, id=report_id)
    report.is_verified = True
    report.verified_by = request.user
    report.save()

    reports = Report.objects.filter(type_id=type_id)
    for instance in reports:
        instance.is_verified = True
        instance.verified_by = request.user
        instance.save()

    ActivityLog.objects.create(
        user = request.user,
        kind = 'REPORT',
        type_id = report.id,
        status = 'ACCEPTED',
        text = f'{request.user.user_type} {request.user.id} accepted report {report.id}.'
    )

    # Send Email
    template = 'mail/report.html'
    subject = f'{kind} {type_id} reported at OCRVault'
    app_url = settings.APP_URL
    reason = report.type
    context = {
        'name': user.name,
        'kind': kind,
        'id': type_id,
        'reason': reason,
        'url': app_url
    }
    html_message = render_to_string(template, context)
    from_email = settings.DEFAULT_FROM_EMAIL
    to_email = user.email
    send_mail(subject, message='', from_email=from_email, recipient_list=[to_email], html_message=html_message)

    messages.success(request, 'Report has been accepted.')

    return JsonResponse({'message': 'Report has been accepted.'})

@login_required
@require_POST
def report_ignore(request):
    data = json.loads(request.body)
    report_id = data.get('reportId')
    report = get_object_or_404(Report, id=report_id)
    report.is_verified = True
    report.verified_by = request.user
    report.save()

    ActivityLog.objects.create(
        user = request.user,
        kind = 'REPORT',
        type_id = report.id,
        status = 'IGNORED',
        text = f'{request.user.user_type} {request.user.id} ignored report {report.id}.'
    )

    messages.success(request, 'Report has been ignored.')

    return JsonResponse({'message': 'Report has been ignored.'})

"""

    # SUPERADMIN

"""
@login_required
def download_archive(request):
    directory_path = os.path.join(settings.MEDIA_ROOT, 'archives')
    current_date = timezone.now().strftime('%Y-%m-%d')
    name = f'ocrvault-archives-{current_date}.zip'
    zip_file = zipfile.ZipFile(name, 'w')

    for root, dirs, files in os.walk(directory_path):
        for file in files:
            file_path = os.path.join(root, file)
            zip_file.write(file_path, os.path.relpath(file_path, directory_path))

    zip_file.close()

    with open(name, 'rb') as zip_data:
        response = HttpResponse(zip_data, content_type='application/zip')
        response['Content-Disposition'] = f'attachment; filename="{name}"'
        return response
    
def custom_404(request, exception):
    return render(request, 'error/404.html', {}, status=404)

def custom_405(request, exception):
    return render(request, 'error/405.html', {}, status=405)

def custom_500(request):
    return render(request, 'error/500.html', {}, status=500)