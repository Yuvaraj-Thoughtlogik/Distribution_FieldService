/** Quote request list: +/- buttons and auto-submit of quantity changes. */
function initQuoteForm(form) {
    if (form.dataset.tlInit) {
        return;
    }
    form.dataset.tlInit = "1";
    const submit = () => {
        const btn = form.querySelector(".tl_quote_update_btn");
        if (btn) {
            btn.click();
        } else {
            form.submit();
        }
    };
    form.querySelectorAll(".tl_qty_group").forEach((group) => {
        const input = group.querySelector(".tl_qty_input");
        if (!input) {
            return;
        }
        const step = (delta) => {
            const value = Math.max(0, (parseInt(input.value, 10) || 0) + delta);
            input.value = value;
            submit();
        };
        group.querySelector(".tl_qty_minus")?.addEventListener("click", () => step(-1));
        group.querySelector(".tl_qty_plus")?.addEventListener("click", () => step(1));
        input.addEventListener("change", submit);
    });
}

function initAll() {
    document.querySelectorAll("form.tl_quote_form").forEach(initQuoteForm);
}

if (document.readyState === "loading") {
    document.addEventListener("DOMContentLoaded", initAll);
} else {
    initAll();
}
