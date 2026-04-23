/** @odoo-module **/
/**
 * website_google_consent_mode – Consent Update Integration
 * Valryx (https://valryx.tech)
 *
 * Production hardened:
 *   ✅ Fix 1 – WeakSet guard prevents duplicate listeners on the same button
 *   ✅ Fix 2 – gtag safety: queues calls if gtag not yet ready, retries up to 3s
 *   ✅ Fix 3 – Tag ID validation lives in Python (@api.constrains), surfaced via logs here
 *   ✅ Fix 4 – Fallback defaults always applied server-side; JS trusts that layer
 */

/** @type {WeakSet<Element>} Tracks buttons that already have our listener attached */
const _hooked = new WeakSet();

const CONSENT_COOKIE = "odoo_cookie_accepted";

// ─────────────────────────────────────────────────────────────────────────────
// FIX 2 — Safe gtag wrapper with retry queue
// If gtag() hasn't been defined yet (async load still in flight), we queue
// the call and drain the queue once gtag becomes available (up to 3 s).
// ─────────────────────────────────────────────────────────────────────────────
const _gtagQueue = [];
let _gtagReady = false;

function _safeGtag(...args) {
    if (typeof window.gtag === "function") {
        _gtagReady = true;
        window.gtag(...args);
    } else {
        // Queue and start polling
        _gtagQueue.push(args);
        _startGtagPoller();
    }
}

let _pollerStarted = false;
function _startGtagPoller() {
    if (_pollerStarted) return;
    _pollerStarted = true;
    const start = Date.now();
    const interval = setInterval(() => {
        if (typeof window.gtag === "function") {
            _gtagReady = true;
            clearInterval(interval);
            _gtagQueue.splice(0).forEach((args) => window.gtag(...args));
        } else if (Date.now() - start > 3000) {
            // Give up after 3 s — log a warning but don't throw
            clearInterval(interval);
            if (window.location.hostname !== "localhost") {
                console.warn(
                    "[Valryx] Google Consent Mode: gtag() did not become available " +
                    "within 3 s. Check that your Google Tag ID is correct and " +
                    "gtag.js loaded successfully."
                );
            }
            _gtagQueue.length = 0;
        }
    }, 100);
}

// ─────────────────────────────────────────────────────────────────────────────
// Cookie helper
// ─────────────────────────────────────────────────────────────────────────────
function _getCookie(name) {
    const match = document.cookie.match(
        new RegExp("(?:^|; )" + name.replace(/([.*+?^=!:${}()|[\]\\])/g, "\\$1") + "=([^;]*)")
    );
    return match ? decodeURIComponent(match[1]) : null;
}

// ─────────────────────────────────────────────────────────────────────────────
// Public consent API — delegates through _safeGtag
// ─────────────────────────────────────────────────────────────────────────────
window.valryxGoogleConsent = {
    update(params) {
        _safeGtag("consent", "update", params);
    },
    grantAll() {
        this.update({
            ad_storage: "granted",
            ad_user_data: "granted",
            ad_personalization: "granted",
            analytics_storage: "granted",
            functionality_storage: "granted",
            personalization_storage: "granted",
            security_storage: "granted",
        });
    },
    denyAll() {
        this.update({
            ad_storage: "denied",
            ad_user_data: "denied",
            ad_personalization: "denied",
            analytics_storage: "denied",
            functionality_storage: "granted",
            personalization_storage: "denied",
            security_storage: "granted",
        });
    },
};

// ─────────────────────────────────────────────────────────────────────────────
// Apply consent from existing cookie (page load / SPA navigation)
// ─────────────────────────────────────────────────────────────────────────────
function _applyConsentFromCookie() {
    if (!window.valryxConsentModeEnabled) return;
    if (window.valryxConsentManager !== "odoo_cookie_bar") return;

    const val = _getCookie(CONSENT_COOKIE);
    if (val === "1" || val === "true") {
        window.valryxGoogleConsent.grantAll();
    } else if (val === "0" || val === "false") {
        window.valryxGoogleConsent.denyAll();
    }
    // No cookie yet → server-side defaults already applied. Nothing to do.
}

// ─────────────────────────────────────────────────────────────────────────────
// FIX 1 — Hook cookie bar buttons, guarded by WeakSet to prevent duplicates
// ─────────────────────────────────────────────────────────────────────────────
function _hookCookieBar() {
    if (!window.valryxConsentModeEnabled) return;
    if (window.valryxConsentManager !== "odoo_cookie_bar") return;

    const ACCEPT_SEL = [
        ".o_cookies_bar_consent_accept",
        "[data-action='accept_all']",
        ".btn-accept-cookies",
        ".accept-cookies",
    ].join(", ");

    const DENY_SEL = [
        ".o_cookies_bar_consent_reject",
        ".o_cookies_bar_consent_essential",
        "[data-action='reject_all']",
        ".btn-reject-cookies",
        ".reject-cookies",
    ].join(", ");

    document.querySelectorAll(ACCEPT_SEL).forEach((btn) => {
        if (_hooked.has(btn)) return;           // ← FIX 1: skip if already hooked
        _hooked.add(btn);
        btn.addEventListener("click", () => window.valryxGoogleConsent.grantAll());
    });

    document.querySelectorAll(DENY_SEL).forEach((btn) => {
        if (_hooked.has(btn)) return;           // ← FIX 1: skip if already hooked
        _hooked.add(btn);
        btn.addEventListener("click", () => window.valryxGoogleConsent.denyAll());
    });
}

// ─────────────────────────────────────────────────────────────────────────────
// MutationObserver — watches for cookie bar injected dynamically by Odoo
// Observer fires _hookCookieBar which is now idempotent thanks to WeakSet.
// ─────────────────────────────────────────────────────────────────────────────
function _startObserver() {
    const observer = new MutationObserver(_hookCookieBar);
    observer.observe(document.body || document.documentElement, {
        childList: true,
        subtree: true,
    });
    // Disconnect after 15 s — cookie bar is always rendered within page load
    setTimeout(() => observer.disconnect(), 15000);
}

// ─────────────────────────────────────────────────────────────────────────────
// Initialisation
// ─────────────────────────────────────────────────────────────────────────────
function _init() {
    _applyConsentFromCookie();
    _hookCookieBar();
    _startObserver();
}

if (document.readyState === "loading") {
    document.addEventListener("DOMContentLoaded", _init);
} else {
    _init();
}

// SPA / Turbo page navigations
document.addEventListener("page:load", () => {
    _applyConsentFromCookie();
    _hookCookieBar();
});
