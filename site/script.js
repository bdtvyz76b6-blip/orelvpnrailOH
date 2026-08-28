"use strict";
/*
|--------------------------------------------------------------------------
| IXXY VPN WEBSITE
|--------------------------------------------------------------------------
|
| URL:
| https://ixxyvpn.pages.dev/s/2ix847xyXXXXXXXX
|
| The current page URL is used as the subscription identifier.
|
*/
// ============================================================
// ELEMENTS
// ============================================================
const happButton = document.getElementById("happButton");
const incyButton = document.getElementById("incyButton");
const copyButton = document.getElementById("copyButton");
const subscriptionLinkElement =
    document.getElementById("subscriptionLink");
const toast =
    document.getElementById("toast");
const toastText =
    document.getElementById("toastText");
// ============================================================
// GET CURRENT CODE
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
// SUBSCRIPTION URL
// ============================================================
//
// Пока сайт работает через собственный endpoint:
//
// /s/CODE?raw=1
//
// Позже github_update.py будет использовать именно этот URL.
// Пользователь при этом никогда не увидит RAW GitHub URL.
//
function getSubscriptionUrl() {
    const code = getCode();
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
// SHOW TOAST
// ============================================================
let toastTimer = null;
function showToast(message) {
    if (!toast || !toastText) {
        return;
    }
    toastText.textContent = message;
    toast.classList.add("show");
    clearTimeout(toastTimer);
    toastTimer = setTimeout(() => {
        toast.classList.remove("show");
    }, 2200);
}
// ============================================================
// UPDATE LINK
// ============================================================
function updateSubscriptionLink() {
    const link =
        getSubscriptionUrl();
    if (!subscriptionLinkElement) {
        return;
    }
    if (!link) {
        subscriptionLinkElement.textContent =
            "Ссылка недоступна";
        return;
    }
    subscriptionLinkElement.textContent =
        link;
}
// ============================================================
// COPY
// ============================================================
async function copySubscription() {
    const link =
        getSubscriptionUrl();
    if (!link) {
        showToast(
            "Ссылка недоступна"
        );
        return;
    }
    try {
        await navigator.clipboard.writeText(
            link
        );
        showToast(
            "Ссылка скопирована ✓"
        );
    } catch (error) {
        fallbackCopy(link);
    }
}
// ============================================================
// FALLBACK COPY
// ============================================================
function fallbackCopy(text) {
    const textarea =
        document.createElement("textarea");
    textarea.value = text;
    textarea.style.position = "fixed";
    textarea.style.opacity = "0";
    document.body.appendChild(
        textarea
    );
    textarea.focus();
    textarea.select();
    try {
        document.execCommand("copy");
        showToast(
            "Ссылка скопирована ✓"
        );
    } catch (error) {
        showToast(
            "Не удалось скопировать"
        );
    }
    textarea.remove();
}
// ============================================================
// HAPP
// ============================================================
function openHapp() {
    const link =
        getSubscriptionUrl();
    if (!link) {
        showToast(
            "Ссылка недоступна"
        );
        return;
    }
    /*
     * Happ deeplink.
     *
     * The subscription URL is encoded because it is
     * passed as a URL parameter.
     */
    const encoded =
        encodeURIComponent(link);
    const happUrl =
        "happ://add/" +
        encoded;
    window.location.href =
        happUrl;
}
// ============================================================
// INCY
// ============================================================
function openIncy() {
    const link =
        getSubscriptionUrl();
    if (!link) {
        showToast(
            "Ссылка недоступна"
        );
        return;
    }
    /*
     * INCY officially supports:
     *
     * incy://add/{url}
     *
     * The URL itself must be URI encoded when
     * embedded into the deeplink.
     */
    const encoded =
        encodeURIComponent(link);
    const incyUrl =
        "incy://add/" +
        encoded;
    window.location.href =
        incyUrl;
}
// ============================================================
// EVENTS
// ============================================================
if (copyButton) {
    copyButton.addEventListener(
        "click",
        copySubscription
    );
}
if (happButton) {
    happButton.addEventListener(
        "click",
        openHapp
    );
}
if (incyButton) {
    incyButton.addEventListener(
        "click",
        openIncy
    );
}
// ============================================================
// INIT
// ============================================================
updateSubscriptionLink();