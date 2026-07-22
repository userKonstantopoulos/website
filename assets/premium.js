(function () {
  "use strict";

  var year = document.getElementById("year");
  if (year) year.textContent = new Date().getFullYear();

  var progress = document.getElementById("progress");
  var topbar = document.getElementById("topbar");
  function onScroll() {
    var scrollTop = window.scrollY || document.documentElement.scrollTop;
    var height = document.documentElement.scrollHeight - window.innerHeight;
    if (progress) progress.style.width = (height > 0 ? (scrollTop / height) * 100 : 0) + "%";
    if (topbar) topbar.classList.toggle("scrolled", scrollTop > 24);
  }
  window.addEventListener("scroll", onScroll, { passive: true });
  onScroll();

  var hamburger = document.getElementById("hamburger");
  var overlay = document.getElementById("overlay");
  function closeMenu() {
    document.body.classList.remove("menu-open");
  }
  if (hamburger) {
    hamburger.addEventListener("click", function () {
      document.body.classList.toggle("menu-open");
    });
  }
  if (overlay) overlay.addEventListener("click", closeMenu);
  document.querySelectorAll(".drawer a").forEach(function (link) {
    link.addEventListener("click", closeMenu);
  });

  document.querySelectorAll("#svcList .svc-head").forEach(function (head) {
    head.addEventListener("click", function () {
      var row = head.closest(".svc-row");
      var wasOpen = row.classList.contains("open");
      document.querySelectorAll("#svcList .svc-row").forEach(function (item) {
        item.classList.remove("open");
      });
      if (!wasOpen) row.classList.add("open");
    });
  });

  var revealObserver = new IntersectionObserver(function (entries) {
    entries.forEach(function (entry) {
      if (entry.isIntersecting) {
        entry.target.classList.add("in");
        revealObserver.unobserve(entry.target);
      }
    });
  }, { threshold: 0.14, rootMargin: "0px 0px -8% 0px" });
  document.querySelectorAll(".reveal").forEach(function (el) {
    revealObserver.observe(el);
  });

  var navLinks = Array.prototype.slice.call(document.querySelectorAll(".nav-links a"));
  var sections = navLinks.filter(function (link) {
    return (link.getAttribute("href") || "").charAt(0) === "#";
  }).map(function (link) {
    return { link: link, section: document.querySelector(link.getAttribute("href")) };
  }).filter(function (item) {
    return item.section;
  });
  var spy = new IntersectionObserver(function (entries) {
    entries.forEach(function (entry) {
      if (!entry.isIntersecting) return;
      navLinks.forEach(function (link) { link.classList.remove("active"); });
      var current = sections.find(function (item) { return item.section === entry.target; });
      if (current) current.link.classList.add("active");
    });
  }, { rootMargin: "-42% 0px -52% 0px" });
  sections.forEach(function (item) { spy.observe(item.section); });

  var marquee = document.querySelector(".marquee-track");
  if (marquee) marquee.innerHTML = marquee.innerHTML + marquee.innerHTML;

  var consentKey = "mnimiLogosCookieConsent";
  var hasConsent = false;
  try {
    hasConsent = Boolean(window.localStorage.getItem(consentKey));
  } catch (error) {
    hasConsent = false;
  }

  if (!hasConsent) {
    var pathname = window.location.pathname;
    var inLegal = pathname.indexOf("/legal/") !== -1;
    var inEn = pathname.indexOf("/en/") !== -1;
    var cookiesHref = inLegal ? "cookies.html" : (inEn ? "../legal/cookies.html" : "legal/cookies.html");
    var isEn = (document.documentElement.lang || "").toLowerCase().indexOf("en") === 0;
    var t = isEn ? {
      aria: "Cookie notice",
      title: "Cookies",
      body: "We use essential cookies for the operation of the website. Non-essential cookies are enabled only with consent.",
      link: "Cookie Policy",
      necessary: "Essential only",
      accept: "Accept"
    } : {
      aria: "Ενημέρωση cookies",
      title: "Cookies",
      body: "Χρησιμοποιούμε απαραίτητα cookies για τη λειτουργία του ιστοτόπου. Τα μη αναγκαία cookies ενεργοποιούνται μόνο με συγκατάθεση.",
      link: "Πολιτική Cookies",
      necessary: "Μόνο απαραίτητα",
      accept: "Αποδοχή"
    };
    var banner = document.createElement("div");
    banner.className = "cookie-banner";
    banner.setAttribute("role", "dialog");
    banner.setAttribute("aria-label", t.aria);
    banner.innerHTML = [
      '<div class="cookie-copy">',
      "<strong>" + t.title + "</strong>",
      "<p>" + t.body + "</p>",
      '<a href="' + cookiesHref + '">' + t.link + "</a>",
      "</div>",
      '<div class="cookie-actions">',
      '<button type="button" class="btn secondary" data-cookie-choice="necessary">' + t.necessary + "</button>",
      '<button type="button" class="btn primary" data-cookie-choice="accepted">' + t.accept + "</button>",
      "</div>"
    ].join("");
    document.body.appendChild(banner);

    requestAnimationFrame(function () {
      banner.classList.add("show");
    });

    banner.querySelectorAll("[data-cookie-choice]").forEach(function (button) {
      button.addEventListener("click", function () {
        try {
          window.localStorage.setItem(consentKey, button.getAttribute("data-cookie-choice"));
        } catch (error) {}
        banner.classList.remove("show");
        window.setTimeout(function () {
          banner.remove();
        }, 240);
      });
    });
  }
})();
