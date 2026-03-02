// Mobile Menu Script
document.addEventListener('DOMContentLoaded', function() {
    const menuToggle = document.getElementById('mobileMenuToggle');
    const sidebarNav = document.querySelector('.sidebar-nav');
    const overlay = document.getElementById('mobileMenuOverlay');
    const navLinks = document.querySelectorAll('.sidebar-nav .nav-link');

    function openMenu() {
        sidebarNav.classList.add('mobile-open');
        overlay.classList.add('active');
        document.body.style.overflow = 'hidden';
    }

    function closeMenu() {
        sidebarNav.classList.remove('mobile-open');
        overlay.classList.remove('active');
        document.body.style.overflow = '';
    }

    menuToggle.addEventListener('click', function() {
        if (sidebarNav.classList.contains('mobile-open')) {
            closeMenu();
        } else {
            openMenu();
        }
    });

    overlay.addEventListener('click', closeMenu);

    navLinks.forEach(link => {
        link.addEventListener('click', closeMenu);
    });

    // Close menu on window resize if screen becomes larger
    window.addEventListener('resize', function() {
        if (window.innerWidth > 768) {
            closeMenu();
        }
    });
});

// User Menu Script
document.addEventListener('DOMContentLoaded', function() {
    const userMenuToggle = document.getElementById('userMenuToggle');
    const userMenuDropdown = document.getElementById('userMenuDropdown');
    const userMenuArrow = document.getElementById('userMenuArrow');
    const userMenuWrapper = document.querySelector('.user-menu-wrapper');

    if (userMenuToggle && userMenuDropdown && userMenuArrow && userMenuWrapper) {
        function toggleUserMenu() {
            const isActive = userMenuDropdown.classList.contains('active');
            
            if (isActive) {
                userMenuDropdown.classList.remove('active');
                userMenuArrow.classList.remove('rotated');
            } else {
                userMenuDropdown.classList.add('active');
                userMenuArrow.classList.add('rotated');
            }
        }

        function closeUserMenu() {
            userMenuDropdown.classList.remove('active');
            userMenuArrow.classList.remove('rotated');
        }

        userMenuToggle.addEventListener('click', function(e) {
            e.preventDefault();
            toggleUserMenu();
        });

        // Close menu when clicking outside
        document.addEventListener('click', function(e) {
            if (userMenuDropdown && userMenuWrapper) {
                const isClickInside = userMenuWrapper.contains(e.target);
                if (!isClickInside && userMenuDropdown.classList.contains('active')) {
                    closeUserMenu();
                }
            }
        });

        // Close menu when clicking on menu items
        const userMenuItems = userMenuDropdown.querySelectorAll('.user-menu-item');
        userMenuItems.forEach(item => {
            item.addEventListener('click', function(e) {
                // Можно добавить логику обработки клика на пункты меню
                // closeUserMenu();
            });
        });
    }
});
