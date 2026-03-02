/**
 * Переключатель темы день/ночь. Сохраняет выбор в localStorage, применяет ко всем страницам (включая админку).
 */
(function () {
    const STORAGE_KEY = "site-theme";

    function getStoredTheme() {
        return localStorage.getItem(STORAGE_KEY);
    }

    function setStoredTheme(theme) {
        if (theme) {
            localStorage.setItem(STORAGE_KEY, theme);
        } else {
            localStorage.removeItem(STORAGE_KEY);
        }
    }

    function getPreferredTheme() {
        const stored = getStoredTheme();
        if (stored) return stored;
        if (window.matchMedia && window.matchMedia("(prefers-color-scheme: dark)").matches) {
            return "dark";
        }
        return "light";
    }

    function applyTheme(theme) {
        const html = document.documentElement;
        if (theme === "dark") {
            html.setAttribute("data-theme", "dark");
        } else {
            html.removeAttribute("data-theme");
        }
        updateToggleButton(theme);
    }

    function updateToggleButton(theme) {
        const btn = document.getElementById("themeToggle");
        if (!btn) return;
        const iconLight = btn.querySelector(".theme-icon-light");
        const iconDark = btn.querySelector(".theme-icon-dark");
        const label = btn.querySelector(".theme-toggle-label");
        if (iconLight && iconDark) {
            if (theme === "dark") {
                iconLight.classList.add("d-none");
                iconDark.classList.remove("d-none");
                if (label) label.textContent = "Ночь";
            } else {
                iconLight.classList.remove("d-none");
                iconDark.classList.add("d-none");
                if (label) label.textContent = "День";
            }
        }
    }

    function toggleTheme() {
        const current = document.documentElement.getAttribute("data-theme");
        const next = current === "dark" ? "light" : "dark";
        setStoredTheme(next);
        applyTheme(next);
    }

    function init() {
        const theme = getPreferredTheme();
        applyTheme(theme);

        const btn = document.getElementById("themeToggle");
        if (btn) {
            btn.addEventListener("click", toggleTheme);
        }
    }

    if (document.readyState === "loading") {
        document.addEventListener("DOMContentLoaded", init);
    } else {
        init();
    }
})();
