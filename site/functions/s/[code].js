/*
|--------------------------------------------------------------------------
| IXXY VPN — SUBSCRIPTION ROUTE
|--------------------------------------------------------------------------
|
| URL:
|
| https://ixxyvpn.pages.dev/s/2ix847xyXXXXXX
|
| Browser:
|     /s/CODE
|     → beautiful website
|
| VPN client:
|     /s/CODE?raw=1
|     → subscription content
|
|--------------------------------------------------------------------------
*/
// ============================================================
// CONFIG
// ============================================================
const GITHUB_OWNER =
    "bdtvyz76b6-blip";
const GITHUB_REPO =
    "vpn-sub";
const GITHUB_BRANCH =
    "main";
// ============================================================
// RESPONSE HEADERS
// ============================================================
function htmlHeaders() {
    return {
        "Content-Type":
            "text/html; charset=UTF-8",
        "Cache-Control":
            "no-store",
        "X-Content-Type-Options":
            "nosniff",
        "Referrer-Policy":
            "no-referrer"
    };
}
function subscriptionHeaders() {
    return {
        "Content-Type":
            "text/plain; charset=UTF-8",
        "Cache-Control":
            "no-store, no-cache, must-revalidate",
        "Pragma":
            "no-cache"
    };
}
// ============================================================
// ERROR PAGE
// ============================================================
function errorPage(title, message) {
    return `
<!DOCTYPE html>
<html lang="ru">
<head>
<meta charset="UTF-8">
<meta
    name="viewport"
    content="width=device-width, initial-scale=1.0"
>
<meta
    name="theme-color"
    content="#08090d"
>
<title>${escapeHtml(title)}</title>
<style>
* {
    box-sizing: border-box;
}
body {
    margin: 0;
    min-height: 100vh;
    display: flex;
    align-items: center;
    justify-content: center;
    padding: 20px;
    background: #08090d;
    color: white;
    font-family:
        -apple-system,
        BlinkMacSystemFont,
        "SF Pro Display",
        Arial,
        sans-serif;
    text-align: center;
}
.card {
    width: 100%;
    max-width: 420px;
    padding: 35px 25px;
    border-radius: 28px;
    background: rgba(25, 27, 35, 0.9);
    border: 1px solid rgba(255,255,255,.08);
    box-shadow:
        0 30px 80px rgba(0,0,0,.45);
}
.icon {
    font-size: 50px;
    margin-bottom: 15px;
}
h1 {
    margin: 0;
    font-size: 25px;
}
p {
    margin-top: 10px;
    color: #9699a5;
    line-height: 1.5;
    font-size: 14px;
}
</style>
</head>
<body>
<div class="card">
    <div class="icon">☂️</div>
    <h1>${escapeHtml(title)}</h1>
    <p>${escapeHtml(message)}</p>
</div>
</body>
</html>
`;
}
// ============================================================
// HTML ESCAPE
// ============================================================
function escapeHtml(value) {
    return String(value)
        .replaceAll("&", "&amp;")
        .replaceAll("<", "&lt;")
        .replaceAll(">", "&gt;")
        .replaceAll('"', "&quot;")
        .replaceAll("'", "&#039;");
}
// ============================================================
// GET OLD GITHUB SUBSCRIPTION
// ============================================================
//
// FIRST VERSION:
//
// The code:
//     2ix847xy6312016802
//
// contains the user ID at the end.
//
// This lets us migrate the old files without changing
// the whole subscription system in one step.
//
// Later github_update.py will generate the new storage
// directly.
//
function getUserIdFromCode(code) {
    const prefix =
        "2ix847xy";
    if (!code.startsWith(prefix)) {
        return null;
    }
    const userId =
        code.slice(prefix.length);
    if (!/^\d+$/.test(userId)) {
        return null;
    }
    return userId;
}
// ============================================================
// OLD GITHUB URL
// ============================================================
function getGithubSubscriptionUrl(userId) {
    return (
        "https://raw.githubusercontent.com/" +
        GITHUB_OWNER +
        "/" +
        GITHUB_REPO +
        "/" +
        GITHUB_BRANCH +
        "/users/" +
        encodeURIComponent(userId) +
        ".txt"
    );
}
// ============================================================
// LOAD SUBSCRIPTION
// ============================================================
async function loadSubscription(userId) {
    const url =
        getGithubSubscriptionUrl(
            userId
        );
    const response =
        await fetch(
            url,
            {
                method: "GET",
                headers: {
                    "Accept":
                        "text/plain"
                },
                cf: {
                    cacheTtl: 0
                }
            }
        );
    if (!response.ok) {
        throw new Error(
            "Subscription not found"
        );
    }
    const text =
        await response.text();
    if (!text.trim()) {
        throw new Error(
            "Subscription is empty"
        );
    }
    return text;
}
// ============================================================
// HTML PAGE
// ============================================================
function renderPage(code) {
    return `<!DOCTYPE html>
<html lang="ru">
<head>
<meta charset="UTF-8">
<meta
    name="viewport"
    content="width=device-width, initial-scale=1.0, viewport-fit=cover"
>
<meta
    name="theme-color"
    content="#08090d"
>
<meta
    name="description"
    content="ixxy VPN — безопасное подключение"
>
<title>ixxy VPN</title>
<link
    rel="stylesheet"
    href="/style.css"
>
</head>
<body>
<div class="background">
    <div class="glow glow-one"></div>
    <div class="glow glow-two"></div>
</div>
<main class="page">
<section class="card">
    <div class="logo">
        <span>☂️</span>
    </div>
    <div class="brand">
        <h1>ixxy VPN</h1>
        <p>
            Безопасное подключение в один тап
        </p>
    </div>
    <div class="status">
        <span class="status-dot"></span>
        <span>
            Подписка готова
        </span>
    </div>
    <div class="divider"></div>
    <h2>
        Добавьте VPN
    </h2>
    <p class="subtitle">
        Выберите приложение,
        в которое хотите добавить подписку.
    </p>
    <div class="buttons">
        <button
            class="app-button happ"
            id="happButton"
            type="button"
        >
            <span class="button-icon">
                🚀
            </span>
            <span class="button-text">
                <strong>
                    Добавить в Happ
                </strong>
                <small>
                    Открыть приложение
                </small>
            </span>
            <span class="arrow">
                ›
            </span>
        </button>
        <button
            class="app-button incy"
            id="incyButton"
            type="button"
        >
            <span class="button-icon">
                ⚡
            </span>
            <span class="button-text">
                <strong>
                    Добавить в INCY
                </strong>
                <small>
                    Открыть приложение
                </small>
            </span>
            <span class="arrow">
                ›
            </span>
        </button>
    </div>
    <div class="copy-section">
        <div class="copy-title">
            <span>🔗</span>
            <span>
                Ссылка подписки
            </span>
        </div>
        <div class="link-box">
            <span id="subscriptionLink">
                Подготовка ссылки...
            </span>
        </div>
        <button
            class="copy-button"
            id="copyButton"
            type="button"
        >
            📋 Скопировать ссылку
        </button>
    </div>
    <div class="instruction">
        <div class="instruction-title">
            <span>💡</span>
            <span>
                Как подключить
            </span>
        </div>
        <div class="steps">
            <div class="step">
                <span class="step-number">
                    1
                </span>
                <div>
                    <strong>
                        Выберите приложение
                    </strong>
                    <p>
                        Happ или INCY
                    </p>
                </div>
            </div>
            <div class="step">
                <span class="step-number">
                    2
                </span>
                <div>
                    <strong>
                        Добавьте подписку
                    </strong>
                    <p>
                        Нажмите кнопку выше
                    </p>
                </div>
            </div>
            <div class="step">
                <span class="step-number">
                    3
                </span>
                <div>
                    <strong>
                        Подключитесь
                    </strong>
                    <p>
                        Откройте приложение и включите VPN
                    </p>
                </div>
            </div>
        </div>
    </div>
    <footer>
        <span>☂️</span>
        <span>
            ixxy VPN
        </span>
        <span>
            •
        </span>
        <span>
            Secure connection
        </span>
    </footer>
</section>
</main>
<div
    class="toast"
    id="toast"
>
    <span>✓</span>
    <span id="toastText">
        Ссылка скопирована
    </span>
</div>
<script>
const CODE =
    ${JSON.stringify(code)};
function subscriptionUrl() {
    return (
        window.location.origin +
        "/s/" +
        encodeURIComponent(CODE) +
        "?raw=1"
    );
}
function showToast(text) {
    const toast =
        document.getElementById("toast");
    const toastText =
        document.getElementById("toastText");
    toastText.textContent = text;
    toast.classList.add("show");
    setTimeout(() => {
        toast.classList.remove("show");
    }, 2200);
}
async function copyLink() {
    const link =
        subscriptionUrl();
    try {
        await navigator.clipboard.writeText(
            link
        );
        showToast(
            "Ссылка скопирована ✓"
        );
    } catch {
        showToast(
            "Скопируйте ссылку вручную"
        );
    }
}
function openHapp() {
    const link =
        subscriptionUrl();
    window.location.href =
        "happ://add/" +
        encodeURIComponent(link);
}
function openIncy() {
    const link =
        subscriptionUrl();
    window.location.href =
        "incy://add/" +
        encodeURIComponent(link);
}
document
    .getElementById("subscriptionLink")
    .textContent =
    subscriptionUrl();
document
    .getElementById("copyButton")
    .addEventListener(
        "click",
        copyLink
    );
document
    .getElementById("happButton")
    .addEventListener(
        "click",
        openHapp
    );
document
    .getElementById("incyButton")
    .addEventListener(
        "click",
        openIncy
    );
</script>
</body>
</html>`;
}
// ============================================================
// REQUEST HANDLER
// ============================================================
export async function onRequest(context) {
    const code =
        String(
            context.params.code || ""
        );
    if (!code) {
        return new Response(
            errorPage(
                "Ссылка недействительна",
                "Не удалось определить код подписки."
            ),
            {
                status: 404,
                headers: htmlHeaders()
            }
        );
    }
    // ========================================================
    // RAW MODE
    // ========================================================
    const url =
        new URL(
            context.request.url
        );
    if (
        url.searchParams.get("raw") === "1"
    ) {
        const userId =
            getUserIdFromCode(code);
        if (!userId) {
            return new Response(
                "Invalid subscription",
                {
                    status: 404,
                    headers:
                        subscriptionHeaders()
                }
            );
        }
        try {
            const subscription =
                await loadSubscription(
                    userId
                );
            return new Response(
                subscription,
                {
                    status: 200,
                    headers:
                        subscriptionHeaders()
                }
            );
        } catch (error) {
            return new Response(
                "Subscription not found",
                {
                    status: 404,
                    headers:
                        subscriptionHeaders()
                }
            );
        }
    }
    // ========================================================
    // WEBSITE
    // ========================================================
    return new Response(
        renderPage(code),
        {
            status: 200,
            headers:
                htmlHeaders()
        }
    );
}