/**
 * AapdaSetu - Language Utility Bridge
 * Synchronizes with translations.js and app.js
 */

function changeLanguage(lang) {
    if (!lang) lang = "en";
    localStorage.setItem("aapdaLanguage", lang);
    localStorage.setItem("aapda_language", lang);

    if (typeof setLanguage === "function") {
        setLanguage(lang);
        return;
    }

    const dict = (typeof translations !== "undefined" && translations[lang]) 
        ? translations[lang] 
        : ((typeof translations !== "undefined" && translations.en) ? translations.en : {});

    document.documentElement.lang = lang;

    document.querySelectorAll("[data-i18n]").forEach(element => {
        const key = element.getAttribute("data-i18n");
        if (dict[key]) {
            if (element.tagName === "INPUT" || element.tagName === "TEXTAREA") {
                element.placeholder = dict[key];
            } else {
                element.textContent = dict[key];
            }
        }
    });

    document.querySelectorAll("[data-i18n-placeholder]").forEach(element => {
        const key = element.getAttribute("data-i18n-placeholder");
        if (dict[key]) {
            element.placeholder = dict[key];
        }
    });

    document.querySelectorAll("#languageSelector").forEach(selector => {
        selector.value = lang;
    });
}

function initLanguage() {
    const savedLanguage =
        localStorage.getItem("aapda_language") ||
        localStorage.getItem("aapdaLanguage") || "en";

    changeLanguage(savedLanguage);
}

document.addEventListener("DOMContentLoaded", initLanguage);
