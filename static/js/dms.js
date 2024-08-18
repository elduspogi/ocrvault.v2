$(document).ready(function () {
    // CSRF_TOKEN
    var csrfToken = $('meta[name=csrf-token]').attr('content');
    // GLOBAL VARIABLES
    const url = `${window.location.protocol}//${window.location.host}`;

    // GLOBAL FUNCTIONS
    function reloadPage() {
        window.location.reload();
    }

    function getId(target) {
        var id = $(target).closest('.col-lg-3').data('id');
        return id;
    }

    function updateSelectedCount(count) {
        $('#selectedCount').text(count);
    }

    function toggleSettings(selected) {
        if (selected > 0) {
            $('.sort-settings').addClass('hide');
            $('.select-settings').removeClass('hide');
        } else {
            $('.sort-settings').removeClass('hide');
            $('.select-settings').addClass('hide');
        }
    }

    function isAllSelected() {
        var allFiles = $('.folder-item');
        var isTrue = allFiles.length === selected;

        if (isTrue) {
            $('#selectAllBtn').addClass('file-selected');
        } else {
            $('#selectAllBtn').removeClass('file-selected');
        }
    }

    function toggleSelectAll() {
        var allFiles = $('.folder-item');
        var isTrue = allFiles.length === selected;

        if (isTrue) {
            allFiles.removeClass('file-selected');
            $(this).removeClass('file-selected');
            selected = 0;
        } else {
            allFiles.addClass('file-selected');
            $(this).addClass('file-selected');
            selected = allFiles.length;
        }

        updateSelectedCount(selected);
    }

    function getFolders() {
        var folders = [];

        $('.folder-entity .folder-item.file-selected').each(function () {
            var kind = $(this).closest('.folder-entity').data('kind');
            if (kind === 'FOLDER') {
                var id = $(this).closest('.folder-entity').data('id');
                folders.push(id);
            }
        });

        return folders;
    }


    function getDocuments() {
        var documents = [];

        $('.document-entity .folder-item.file-selected').each(function () {
            var kind = $(this).closest('.document-entity').data('kind');

            if (kind === 'DOCUMENT') {
                var id = $(this).closest('.document-entity').data('id');
                documents.push(id);
            }
        });

        return documents;
    }

    // FORMS
        // Add Folder
    $('#createFolder').on('submit', function (e) {
        e.preventDefault();

        $('#createBtn').prop('disabled', true).text('PLEASE WAIT...');

        $.ajax({
            url: '/add/folder',
            method: 'POST',
            data: $(this).serialize(),
            success: function () {
                reloadPage();
            }
        });
    });

        // Delete Items
    $('#deleteSelectedBtn').on('click', function () {
        var folders = getFolders();
        var documents = getDocuments();

        var idForDeletion = {
            'folders': folders,
            'documents': documents
        }

        $.ajax({
            url: '/delete/all',
            method: 'POST',
            headers: {
                'X-CSRFToken': csrfToken
            },
            data: JSON.stringify(idForDeletion),
            contentType: 'application/json',
            success: function (response) {
                reloadPage();
            }
        })
    });

    $('#extractBtn').on('click', function () {
        $('.main-container').addClass('hide');
        $('.spin-container').removeClass('hide');

        var folders = getFolders();
        var documents = getDocuments();

        var idForExtraction = {
            'folders': folders,
            'documents': documents
        }

        $.ajax({
            url: '/extract-text/document',
            method: 'POST',
            headers: {
                'X-CSRFToken': csrfToken
            },
            data: JSON.stringify(idForExtraction),
            contentType: 'application/json',
            success: function (response) {
                reloadPage();
            }

        });
    })

    $('.bi-three-dots-vertical').on('click', function () {
        var id = $(this).closest('.col-lg-3').data('id');
        var kind = $(this).closest('.col-lg-3').data('kind');

        if (kind === 'FOLDER') {
            window.location.href = `${url}/edit/folder/${id}`;    
        } else {
            window.location.href = `${url}/edit/document/${id}`;
        }
    });

    $('.folder-item').on('dblclick', function () {
        var id = getId(this);
        var kind = $(this).closest('.col-lg-3').data('kind');
        var path = $(this).closest('.col-lg-3').data('path');
        
        if (kind === 'FOLDER') {
            window.location.href = `${url}/folder/${id}`;    
        } else {
            window.location.href = `${url}${path}`;
        }
    });

    var selected = 0;

    $('.folder-item').on('click', function () {
        if ($(this).hasClass('file-selected')) {
            $(this).removeClass('file-selected');
            selected--;
        } else {
            $(this).addClass('file-selected');
            selected++;
        }

        updateSelectedCount(selected);
        toggleSettings(selected);
        isAllSelected(selected);
    });

    $('#selectAllBtn').on('click', function () {
        $(this).toggleClass('file-selected');
        toggleSelectAll();
        toggleSettings(selected);
    })

    $('#settingBtn').on('click', function () {
        selected = 0;
        $('.folder-item').removeClass('file-selected');
        toggleSettings();
    })



    $('.document').on('click', function () {
        $(this).addClass('folder-label-select');
        $('.document .bi').removeClass('bi-file-text-fill').addClass('bi-check-lg');
        $('.folder').removeClass('folder-label-select');
        $('.folder .bi').removeClass('bi-check-lg').addClass('bi-folder-fill');

        $('#createFolder').addClass('hide');
        $('.document-form').removeClass('hide');
        $('.alert-text').removeClass('hide');
    });

    $('.folder').on('click', function () {
        if (!$(this).hasClass('folder-label-select')) {
            $(this).addClass('folder-label-select');
        };
        $('.document .bi').removeClass('bi-check-lg').addClass('bi-file-text-fill');
        $('.document').removeClass('folder-label-select');
        $('.folder .bi').removeClass('bi-folder-fill').addClass('bi-check-lg');

        $('#createFolder').removeClass('hide');
        $('.document-form').addClass('hide');
        $('.alert-text').addClass('hide');
    });

    function sortByType() {
        $('#folderLabel').on('click', function () {
            $('#allLabel').removeClass('folder-label-select');
            $('.eye-label-icon').removeClass('bi-check-lg').addClass('bi-eye-fill');
            $(this).addClass('folder-label-select')
            $('.folder-label-icon').removeClass('bi-folder-fill').addClass('bi-check-lg');
            $('.document-label-icon').removeClass('bi-check-lg').addClass('bi-file-text-fill');
            $('#documentLabel').removeClass('folder-label-select');
            $('.folder-entity').show();
            $('.document-entity').hide();
        });
    
        $('#documentLabel').on('click', function () {
            $('#allLabel').removeClass('folder-label-select');
            $('.eye-label-icon').removeClass('bi-check-lg').addClass('bi-eye-fill');
            $(this).addClass('folder-label-select')
            $('.folder-label-icon').removeClass('bi-check-lg').addClass('bi-folder-fill');
            $('.document-label-icon').removeClass('bi-file-text-fill').addClass('bi-check-lg');
            $('#folderLabel').removeClass('folder-label-select');
            $('.document-entity').show();
            $('.folder-entity').hide();
        });
    
        $('#allLabel').on('click', function () {
            $('#folderLabel').removeClass('folder-label-select');
            $('.folder-label-icon').removeClass('bi-check-lg').addClass('bi-folder-fill');
            $(this).addClass('folder-label-select')
            $('.eye-label-icon').removeClass('bi-eye-fill').addClass('bi-check-lg');
            $('.document-label-icon').removeClass('bi-check-lg').addClass('bi-file-text-fill');
            $('#documentLabel').removeClass('folder-label-select');
            $('.document-entity, .folder-entity').show();
        });
    }

    sortByType();

    function sortByOrder() {
        var $container = $('#isoContainer').isotope({
            itemSelector: '.document-link, .folder-link',
            layoutMode: 'fitRows',
            getSortData: {
                title: function (itemEl) {
                    var titleEl = $(itemEl).find('.document-link h6, .folder-link h6');
                    return titleEl.text();
                }
            }
        });


        if ($('#ascIcon').hasClass('bi-chevron-double-up')) {
            $('#ascIcon').removeClass('bi-chevron-double-up').addClass('bi-chevron-double-down');
            $('#ascText').text('Desc');
            $container.isotope({sortBy: 'original-order', sortAscending: false,});
        } else {
            $('#ascIcon').removeClass('bi-chevron-double-down').addClass('bi-chevron-double-up');
            $('#ascText').text('Asc');
            $container.isotope({sortBy: 'original-order', sortAscending: true,});
        }
    }
    $('#ascLabel').on('click', function () {
        sortByOrder();
    })

    $('.search-form').on('input', function () {
        var input = $('#keyword').val();
        var id = $('#id').val();
        data = {
            'input': input,
            'id': id
        }

        $.ajax({
            url: '/search',
            method: 'POST',
            headers: {
                'X-CSRFToken': csrfToken,
            },
            data: JSON.stringify(data),
            success: function (data) {
                $('.document-link, .folder-link').addClass('hide');
                $('.root-folder').addClass('hide');

                $(data.documents).each(function () {
                    $('.global-document[data-id="' + this.id  + '"]').removeClass('hide');
                });

                $(data.folders).each(function () {
                    $('.global-folder[data-id="' + this.id  + '"]').removeClass('hide');
                })
            }
        });
    });

    // Init DataTables
    $('#myTable, #docTable, #folTable').DataTable({
        layout: {
            topStart: {
                buttons: ['pdf', 'excel', 'print']
            }
        },
        aLengthMenu: [
            [25, 50, 100, 200, -1],
            [25, 50, 100, 200, "All"]
        ],
        iDisplayLength: -1,
        paging: false,
        info: false,
        order: [[ 0, 'desc']]
    });

    $('#moveBtn').on('click', function () {
        $('#moveModal').modal('show');

        removeExcludedFolders();

    });

    $('.bi-x-lg').on('click', function () {
        $('.modal').modal('hide');
    });

    function getExcludedFolders() {
        var currentFolder = $('#moveBtn').data('current-id');
        var foldersToExclude = [currentFolder];

        $('.folder-entity .folder-item.file-selected').each(function () {
            var id = $(this).data('id');
            foldersToExclude.push(id);
        });

        return foldersToExclude;
    }

    function removeExcludedFolders() {
        var foldersToExclude = getExcludedFolders();

        for (var i = 0; i < foldersToExclude.length; i++) {
            var folderId = foldersToExclude[i];
            $('.version-row').each(function () {
                var id = $(this).data('id');
                if (id === folderId) {
                    $(this).addClass('hide');
                }
            });
        }
    }

    $('.version-row').on('click', function () {
        $(this).toggleClass('file-selected');
        var id = $(this).data('id');
        var documents = getDocuments();
        var folders = getFolders();
        var data = {
            'folderId': id,
            'documents': documents,
            'folders': folders
        }
        
        $.ajax({
            url: '/move/files',
            method: 'POST',
            headers: {
                'X-CSRFToken': csrfToken
            },
            data: JSON.stringify(data),
            success: function (response) {
                reloadPage();
            }
        })

        $('.version-row').not(this).removeClass('file-selected');

    });

    $('#changePass').on('click', function () {
        window.location.href = `${url}/change-password`;
    });
    
    $('#refreshPage').click(function () {
        location.reload();
    });
});