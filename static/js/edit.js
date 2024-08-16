$(document).ready(function () {
    var csrfToken = $('meta[name=csrf-token]').attr('content');
    const url = `${window.location.protocol}//${window.location.host}`;
    var isPrivate = '{{ folder.type }}' === 'PRIVATE';
    var folderId = '{{ folder.id }}';
    var parentId = '{{ folder.parent.id }}';
    
    if (isPrivate) {
        $('#folderCheckbox').attr('checked', 'checked');
        $('#folderValue').val('PRIVATE');
    }

    $('#newFolderFormInput').on('input', function () {
        var value = $(this).val();
        $('#folderName').text(value);
    });

    $('#folderCheckbox').on('change', function () {
        if ($(this).is(':checked')) {
            $('#folderType').text('PRIVATE');
            $('#folderValue').val('PRIVATE');
        } else {
            $('#folderType').text('PUBLIC');
            $('#folderValue').val('PUBLIC');
        }
    });

    $('.edit-send-form').on('submit', function (event) {
        event.preventDefault();

        $.ajax({
            url: '/edit/folder/' + folderId,
            type: 'POST',
            data: $(this).serialize(),
            success: function (response) {
                location.reload();
            }
        });
    });

    $('.btn-danger').on('click', function () {
        $.ajax({
            url: '/delete/folder/' + folderId,
            type: 'POST',
            headers: {
                'X-CSRFToken': csrfToken
            },
            success: function (response) {
                if (parentId === '') {
                    window.location.href = `${url}/home`;
                } else {
                    window.location.href = `${url}/folder/` + parentId;
                }
            }
        });
    });
    $('.go-back').on('click', function () {
        if (parentId === '') {
            window.location.href = `${url}/home`;
        } else {
            window.location.href = `${url}/folder/${parentId}`;
        }
    });
});