document.addEventListener("DOMContentLoaded", function () {
    const sidebar = document.getElementById("mithaqSidebar");
    const toggle = document.getElementById("mithaqMenuToggle");
    const overlay = document.getElementById("mithaqOverlay");

    function openSidebar() {
        sidebar.classList.add("open");
        overlay.classList.add("open");
    }

    function closeSidebar() {
        sidebar.classList.remove("open");
        overlay.classList.remove("open");
    }

    if (sidebar && toggle && overlay) {
        toggle.addEventListener("click", openSidebar);
        overlay.addEventListener("click", closeSidebar);
    }
});