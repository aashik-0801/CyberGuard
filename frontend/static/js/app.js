(() => {
    const toggle = document.querySelector("[data-menu-toggle]");
    const sidebar = document.querySelector(".sidebar");
    const backdrop = document.querySelector("[data-menu-backdrop]");

    if (!toggle || !sidebar || !backdrop) return;

    const setOpen = (open) => {
        sidebar.classList.toggle("is-open", open);
        backdrop.classList.toggle("is-visible", open);
        toggle.setAttribute("aria-expanded", String(open));
        document.body.classList.toggle("nav-open", open);
    };

    toggle.addEventListener("click", () => {
        setOpen(toggle.getAttribute("aria-expanded") !== "true");
    });
    backdrop.addEventListener("click", () => setOpen(false));
    sidebar.querySelectorAll("a").forEach((link) => {
        link.addEventListener("click", () => setOpen(false));
    });
    document.addEventListener("keydown", (event) => {
        if (event.key === "Escape") setOpen(false);
    });
})();
