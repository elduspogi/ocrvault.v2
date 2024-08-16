$(document).ready(function () {
    // Sidebar Toggle
    const sidebarToggle = $('#sidebarToggle');
    if (sidebarToggle.length) {
        if (localStorage.getItem('sb|sidebar-toggle') === 'true') {
            $('body').toggleClass('sb-sidenav-toggled');
        }
        sidebarToggle.on('click', function (event) {
            event.preventDefault();
            $('body').toggleClass('sb-sidenav-toggled');
            localStorage.setItem('sb|sidebar-toggle', $('body').hasClass('sb-sidenav-toggled'));
        });
    };

    $('#logoutForm').on('submit', function () {
        $('#logoutBtn').prop('disabled', true);
    });

    applyTheme();

    $('#setTheme').click(function() {
        var html = $('html');
        var isDarkTheme = localStorage.getItem('theme') === 'dark';

        if (isDarkTheme) {
            html.removeClass('dark-mode');
            $('#themeText').text('Set Dark');
            $('#themeIcon').removeClass('bi-lightbulb-fill').addClass('bi-lightbulb');
            localStorage.setItem('theme', 'light');
            $('#jqueryUI').attr('href', 'https://ajax.aspnetcdn.com/ajax/jquery.ui/1.10.4/themes/le-frog/jquery-ui.css');
        } else {
            html.addClass('dark-mode');
            $('#themeText').text('Set Light');
            $('#themeIcon').removeClass('bi-lightbulb').addClass('bi-lightbulb-fill');
            localStorage.setItem('theme', 'dark');
            $('#jqueryUI').attr('href', 'https://ajax.aspnetcdn.com/ajax/jquery.ui/1.10.4/themes/dark-hive/jquery-ui.css');
        }
    });
});