"use strict";

/*
|--------------------------------------------------------------------------
| IXXY VPN — SCRIPT.JS
|--------------------------------------------------------------------------
| Совместим с новым premium HTML-интерфейсом.
| Ссылка подписки берётся из текущего URL:
|
| /s/2ix847xy6312016802
|
| Subscription URL:
| /s/CODE?raw=1
|--------------------------------------------------------------------------
*/


// ============================================================
// ELEMENTS
// ============================================================

const happButton =
    document.getElementById("happButton");

const incyButton =
    document.getElementById("incyButton");

const copyButton =
    document.getElementById("copyButton");

const copyMiniButton =
    document.getElementById("copyMiniButton");

const subscriptionLinkElement =
    document.getElementById("subscriptionLink");

const linkContainer =
    document.getElementById("linkContainer");

const toast =
    document.getElementById("toast");

const toastTitle =
    document.getElementById("toastTitle");

const toastText =
    document.getElementById("toastText");


// ============================================================
// STATE
// ============================================================

let toastTimer = null;


// ============================================================
// GET SUBSCRIPTION CODE
// ============================================================

function getCode() {

    const parts =
        window.location.pathname
            .split("/")
            .filter(Boolean);

    const sIndex =
        parts.indexOf("s");

    if (
        sIndex !== -1 &&
        parts[sIndex + 1]
    ) {
        return parts[sIndex + 1];
    }

    return "";
}


// ============================================================
// GET SUBSCRIPTION URL
// ============================================================

function getSubscriptionUrl() {

    const code =
        getCode();

    if (!code) {
        return "";
    }

    return (
        window.location.origin +
        "/s/" +
        encodeURIComponent(code) +
        "?raw=1"
    );
}


// ============================================================
// TOAST
// ============================================================

function showToast(
    title,
    message
) {

    if (!toast) {
        return;
    }

    if (toastTitle) {
        toastTitle.textContent =
            title;
    }

    if (toastText) {
        toastText.textContent =
            message;
    }

    toast.classList.add("show");

    clearTimeout(toastTimer);

    toastTimer =
        setTimeout(() => {

            toast.classList.remove(
                "show"
            );

        }, 2400);
}


// ============================================================
// UPDATE SUBSCRIPTION LINK
// ============================================================

function updateSubscriptionLink() {

    if (!subscriptionLinkElement) {
        return;
    }

    const link =
        getSubscriptionUrl();

    if (!link) {

        subscriptionLinkElement.textContent =
            "Ссылка недоступна";

        if (linkContainer) {
            linkContainer.classList.add(
                "error"
            );
        }

        return;
    }

    subscriptionLinkElement.textContent =
        link;

    if (linkContainer) {
        linkContainer.classList.remove(
            "error"
        );

        linkContainer.classList.add(
            "ready"
        );
    }
}


// ============================================================
// COPY SUBSCRIPTION
// ============================================================

async function copySubscription() {

    const link =
        getSubscriptionUrl();

    if (!link) {

        showToast(
            "Ошибка",
            "Ссылка недоступна"
        );

        return;
    }

    try {

        await navigator.clipboard.writeText(
            link
        );

        showToast(
            "Готово ✓",
            "Ссылка скопирована"
        );

        animateCopy();

    } catch (error) {

        fallbackCopy(link);
    }
}


// ============================================================
// FALLBACK COPY
// ============================================================

function fallbackCopy(text) {

    const textarea =
        document.createElement(
            "textarea"
        );

    textarea.value =
        text;

    textarea.style.position =
        "fixed";

    textarea.style.left =
        "-9999px";

    textarea.style.top =
        "0";

    textarea.style.opacity =
        "0";

    document.body.appendChild(
        textarea
    );

    textarea.focus();
    textarea.select();

    try {

        const success =
            document.execCommand(
                "copy"
            );

        if (success) {

            showToast(
                "Готово ✓",
                "Ссылка скопирована"
            );

            animateCopy();

        } else {

            showToast(
                "Ошибка",
                "Не удалось скопировать"
            );
        }

    } catch (error) {

        showToast(
            "Ошибка",
            "Не удалось скопировать"
        );

    } finally {

        textarea.remove();
    }
}


// ============================================================
// COPY BUTTON ANIMATION
// ============================================================

function animateCopy() {

    const buttons = [
        copyButton,
        copyMiniButton
    ];

    buttons.forEach(
        (button) => {

            if (!button) {
                return;
            }

            const original =
                button.innerHTML;

            button.classList.add(
                "copied"
            );

            if (
                button === copyButton
            ) {

                button.innerHTML = `
                    <span class="copy-symbol">✓</span>
                    <span>Скопировано</span>
                    <span class="copy-arrow">✓</span>
                `;
            }

            if (
                button === copyMiniButton
            ) {

                button.textContent =
                    "✓";
            }

            setTimeout(
                () => {

                    button.classList.remove(
                        "copied"
                    );

                    if (
                        button === copyButton
                    ) {

                        button.innerHTML =
                            original;
                    }

                    if (
                        button === copyMiniButton
                    ) {

                        button.textContent =
                            "⧉";
                    }

                },
                1400
            );
        }
    );
}


// ============================================================
// HAPP
// ============================================================

function openHapp() {

    const link =
        getSubscriptionUrl();

    if (!link) {

        showToast(
            "Ошибка",
            "Ссылка недоступна"
        );

        return;
    }

    const encoded =
        encodeURIComponent(link);

    const happUrl =
        "happ://add/" +
        encoded;

    showToast(
        "Открываем Happ",
        "Добавляем вашу подписку..."
    );

    setTimeout(
        () => {

            window.location.href =
                happUrl;

        },
        120
    );
}


// ============================================================
// INCY
// ============================================================

function openIncy() {

    const link =
        getSubscriptionUrl();

    if (!link) {

        showToast(
            "Ошибка",
            "Ссылка недоступна"
        );

        return;
    }

    const encoded =
        encodeURIComponent(link);

    const incyUrl =
        "incy://add/" +
        encoded;

    showToast(
        "Открываем INCY",
        "Добавляем вашу подписку..."
    );

    setTimeout(
        () => {

            window.location.href =
                incyUrl;

        },
        120
    );
}


// ============================================================
// BUTTON RIPPLE
// ============================================================

function addRipple(button) {

    if (!button) {
        return;
    }

    button.addEventListener(
        "pointerdown",
        function (event) {

            const rect =
                button.getBoundingClientRect();

            const ripple =
                document.createElement(
                    "span"
                );

            ripple.className =
                "ripple";

            const size =
                Math.max(
                    rect.width,
                    rect.height
                );

            ripple.style.width =
                size + "px";

            ripple.style.height =
                size + "px";

            ripple.style.left =
                (
                    event.clientX -
                    rect.left -
                    size / 2
                ) + "px";

            ripple.style.top =
                (
                    event.clientY -
                    rect.top -
                    size / 2
                ) + "px";

            button.appendChild(
                ripple
            );

            setTimeout(
                () => {
                    ripple.remove();
                },
                600
            );
        }
    );
}


// ============================================================
// EVENTS
// ============================================================

if (copyButton) {

    copyButton.addEventListener(
        "click",
        copySubscription
    );

    addRipple(copyButton);
}


if (copyMiniButton) {

    copyMiniButton.addEventListener(
        "click",
        copySubscription
    );

    addRipple(copyMiniButton);
}


if (happButton) {

    happButton.addEventListener(
        "click",
        openHapp
    );

    addRipple(happButton);
}


if (incyButton) {

    incyButton.addEventListener(
        "click",
        openIncy
    );

    addRipple(incyButton);
}


// ============================================================
// PREVENT DOUBLE TAP ZOOM ON BUTTONS
// ============================================================

document
    .querySelectorAll("button")
    .forEach(
        (button) => {

            button.addEventListener(
                "dblclick",
                (event) => {
                    event.preventDefault();
                }
            );
        }
    );


// ============================================================
// INITIALIZATION
// ============================================================

function init() {

    updateSubscriptionLink();

    document.body.classList.add(
        "loaded"
    );
}


// ============================================================
// START
// ============================================================

if (
    document.readyState ===
    "loading"
) {

    document.addEventListener(
        "DOMContentLoaded",
        init
    );

} else {

    init();
}