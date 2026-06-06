/* ============================================================
   monograph-icons.js — the iconography layer for The Monograph
   ------------------------------------------------------------
   A small, framework-agnostic icon registry that matches the
   system's engraved-editorial voice: thin 1.6px line work on a
   24px grid, round caps/joins, drawn with fill:none +
   stroke:currentColor so every icon inherits its colour and
   sizes to the surrounding font. Brand/social glyphs are the
   exception — solid currentColor marks, recognisable at a glance.

   PAIRS WITH monograph.css (.bk-icon, .bk-social, .bk-ilink).

   USAGE — three ways, pick per context
   ------------------------------------
   1. Placeholder + auto-hydration (static pages — easiest):
        <i data-bk-icon="mail"></i>
        <i data-bk-icon="github" class="bk-icon--lg"></i>
      On DOMContentLoaded every [data-bk-icon] is swapped for its
      <svg class="bk-icon …">. Call MonographIcons.hydrate(root)
      again after you inject markup yourself.

   2. Inline string (engine content / templating):
        right: "<a class='bk-ilink' href='…'>" +
               MonographIcons.markup("arrow-up-right") + " Read on</a>"
      Use this inside Monograph.mount() content — the book engine
      sets innerHTML, so inline the SVG rather than relying on a
      placeholder that won't be re-hydrated on every page flip.

   3. Element:  el.append(MonographIcons.el("bookmark"))

   Social buttons (circular printer's-mark style):
     <div class="bk-social">
       <a class="bk-social__btn" href="…" aria-label="GitHub"><i data-bk-icon="github"></i></a>
       …
     </div>
   Add .bk-social--invert when the row sits on the dark desk.

   API
   ---
   MonographIcons.names         → all icon names (line + brand)
   MonographIcons.line          → line-icon names only
   MonographIcons.brand         → brand/social names only
   MonographIcons.has(name)     → boolean
   MonographIcons.markup(name[,opts])  → "<svg …>…</svg>" string
   MonographIcons.el(name[,opts])      → SVGElement
   MonographIcons.hydrate(root=document)→ swap [data-bk-icon] in scope
       opts: { size:"1.25em"|number, stroke:1.6, class:"…", label:"…" }
   ============================================================ */
(function (global) {
  "use strict";

  /* ---- LINE ICONS — inner markup; rendered fill:none stroke:currentColor ---- */
  var LINE = {
    /* navigation & UI */
    "arrow-left":  '<line x1="19" y1="12" x2="5" y2="12"/><polyline points="12 5 5 12 12 19"/>',
    "arrow-right": '<line x1="5" y1="12" x2="19" y2="12"/><polyline points="12 5 19 12 12 19"/>',
    "arrow-up":    '<line x1="12" y1="19" x2="12" y2="5"/><polyline points="5 12 12 5 19 12"/>',
    "arrow-down":  '<line x1="12" y1="5" x2="12" y2="19"/><polyline points="5 12 12 19 19 12"/>',
    "arrow-up-right": '<line x1="7" y1="17" x2="17" y2="7"/><polyline points="8 7 17 7 17 16"/>',
    "chevron-left":  '<polyline points="15 6 9 12 15 18"/>',
    "chevron-right": '<polyline points="9 6 15 12 9 18"/>',
    "chevron-up":    '<polyline points="6 15 12 9 18 15"/>',
    "chevron-down":  '<polyline points="6 9 12 15 18 9"/>',
    "close":   '<line x1="6" y1="6" x2="18" y2="18"/><line x1="18" y1="6" x2="6" y2="18"/>',
    "menu":    '<line x1="4" y1="7" x2="20" y2="7"/><line x1="4" y1="12" x2="20" y2="12"/><line x1="4" y1="17" x2="20" y2="17"/>',
    "plus":    '<line x1="12" y1="5" x2="12" y2="19"/><line x1="5" y1="12" x2="19" y2="12"/>',
    "minus":   '<line x1="5" y1="12" x2="19" y2="12"/>',
    "check":   '<polyline points="4 12.5 9.5 18 20 6.5"/>',
    "search":  '<circle cx="11" cy="11" r="7"/><line x1="16.2" y1="16.2" x2="21" y2="21"/>',
    "more-horizontal": '<circle cx="5.5" cy="12" r="1.1"/><circle cx="12" cy="12" r="1.1"/><circle cx="18.5" cy="12" r="1.1"/>',
    "filter":  '<polygon points="3 5 21 5 14 13 14 19 10 21 10 13 3 5"/>',

    /* editorial & content */
    "book-open": '<path d="M12 6.2C10.3 5 7.2 4.4 4.5 5v13.2c2.7-.6 5.8 0 7.5 1.2 1.7-1.2 4.8-1.8 7.5-1.2V5C16.8 4.4 13.7 5 12 6.2Z"/><line x1="12" y1="6.2" x2="12" y2="19.4"/>',
    "bookmark":  '<path d="M7 4.5h10a0 0 0 0 1 0 0v15l-5-3.8-5 3.8v-15a0 0 0 0 1 0 0Z"/>',
    "quote":     '<path d="M9.5 7C7 7 5.5 8.9 5.5 11.3c0 2 1.4 3.4 3.3 3.4.4 0 .7 0 1-.1-.4 1.7-1.8 2.8-3.5 3l.4 1.4C9.9 19.5 12 16.8 12 13.2V11C12 8.6 11.5 7 9.5 7Z"/><path d="M18 7c-2.5 0-4 1.9-4 4.3 0 2 1.4 3.4 3.3 3.4.4 0 .7 0 1-.1-.4 1.7-1.8 2.8-3.5 3l.4 1.4c2.7-.5 4.8-3.2 4.8-6.8V11C20.5 8.6 20 7 18 7Z"/>',
    "pen":       '<path d="M15.5 4.5l4 4L9 19l-5.2 1.2L5 15Z"/><line x1="13.5" y1="6.5" x2="17.5" y2="10.5"/>',
    "feather":   '<path d="M20 4C12.5 4 6.5 9.5 6.5 17l.1 1.4M20 4c0 6-3.6 9.4-9.5 10M20 4c-1.2 5.6-4.4 8.4-9.5 10M4 20l3.2-3.2"/><line x1="9" y1="15" x2="14.5" y2="15"/>',
    "document":  '<path d="M7 3.5h7l4 4V20.5H7Z"/><polyline points="13.5 3.5 13.5 8 18 8"/><line x1="9.5" y1="12" x2="15.5" y2="12"/><line x1="9.5" y1="15.5" x2="15.5" y2="15.5"/>',
    "image":     '<rect x="3.5" y="5" width="17" height="14" rx="1.6"/><circle cx="9" cy="10" r="1.6"/><polyline points="5 17.5 10.5 12 14 15.5 17 12.5 19.5 15"/>',
    "link":      '<path d="M10.2 13.8l3.6-3.6"/><path d="M11.4 7.6l1.6-1.6a3.6 3.6 0 0 1 5.1 5.1l-2.2 2.2"/><path d="M12.6 16.4l-1.6 1.6a3.6 3.6 0 0 1-5.1-5.1l2.2-2.2"/>',
    "list":      '<circle cx="5" cy="7" r="1.1"/><circle cx="5" cy="12" r="1.1"/><circle cx="5" cy="17" r="1.1"/><line x1="9" y1="7" x2="20" y2="7"/><line x1="9" y1="12" x2="20" y2="12"/><line x1="9" y1="17" x2="20" y2="17"/>',
    "grid":      '<rect x="4" y="4" width="7" height="7" rx="1"/><rect x="13" y="4" width="7" height="7" rx="1"/><rect x="4" y="13" width="7" height="7" rx="1"/><rect x="13" y="13" width="7" height="7" rx="1"/>',
    "type":      '<polyline points="5 8 5 5.5 19 5.5 19 8"/><line x1="12" y1="5.5" x2="12" y2="19"/><line x1="9" y1="19" x2="15" y2="19"/>',
    "hash":      '<line x1="6" y1="9" x2="20" y2="9"/><line x1="4" y1="15" x2="18" y2="15"/><line x1="10" y1="4" x2="8" y2="20"/><line x1="16" y1="4" x2="14" y2="20"/>',
    "asterisk":  '<line x1="12" y1="4.5" x2="12" y2="19.5"/><line x1="5.5" y1="8.25" x2="18.5" y2="15.75"/><line x1="18.5" y1="8.25" x2="5.5" y2="15.75"/>',

    /* contact & colophon */
    "mail":     '<rect x="3.5" y="5.5" width="17" height="13" rx="1.8"/><polyline points="4 7.5 12 13 20 7.5"/>',
    "phone":    '<path d="M6.5 4.5H10l1.5 4-2 1.4a11 11 0 0 0 4.6 4.6l1.4-2 4 1.5V18a1.5 1.5 0 0 1-1.6 1.5C11.8 19 5 12.2 5 6.1A1.5 1.5 0 0 1 6.5 4.5Z"/>',
    "map-pin":  '<path d="M12 21s7-6.2 7-11a7 7 0 1 0-14 0c0 4.8 7 11 7 11Z"/><circle cx="12" cy="10" r="2.6"/>',
    "calendar": '<rect x="4" y="5.5" width="16" height="15" rx="1.8"/><line x1="4" y1="9.5" x2="20" y2="9.5"/><line x1="9" y1="3" x2="9" y2="6.5"/><line x1="15" y1="3" x2="15" y2="6.5"/>',
    "clock":    '<circle cx="12" cy="12" r="8"/><polyline points="12 7.5 12 12 15.5 13.8"/>',
    "globe":    '<circle cx="12" cy="12" r="8"/><line x1="4" y1="12" x2="20" y2="12"/><path d="M12 4c2.5 2.2 3.8 5 3.8 8S14.5 17.8 12 20c-2.5-2.2-3.8-5-3.8-8S9.5 6.2 12 4Z"/>',
    "send":     '<path d="M21 4 3.5 11l6.2 2.3L12 20l3.2-5.6L21 4Z"/><line x1="9.7" y1="13.3" x2="21" y2="4"/>',
    "at-sign":  '<circle cx="12" cy="12" r="3.4"/><path d="M15.4 12v1.3a2.4 2.4 0 0 0 4.8 0V12a8 8 0 1 0-3.2 6.4"/>',

    /* actions */
    "download": '<line x1="12" y1="4" x2="12" y2="15"/><polyline points="7 10.5 12 15.5 17 10.5"/><path d="M5 19.5h14"/>',
    "upload":   '<line x1="12" y1="16" x2="12" y2="5"/><polyline points="7 9.5 12 4.5 17 9.5"/><path d="M5 19.5h14"/>',
    "share":    '<circle cx="6" cy="12" r="2.6"/><circle cx="17.5" cy="6" r="2.6"/><circle cx="17.5" cy="18" r="2.6"/><line x1="8.3" y1="10.8" x2="15.2" y2="7.2"/><line x1="8.3" y1="13.2" x2="15.2" y2="16.8"/>',
    "copy":     '<rect x="8" y="8" width="12" height="12" rx="1.8"/><path d="M16 8V5.5A1.5 1.5 0 0 0 14.5 4h-9A1.5 1.5 0 0 0 4 5.5v9A1.5 1.5 0 0 0 5.5 16H8"/>',
    "print":    '<path d="M7 9V4h10v5"/><rect x="4.5" y="9" width="15" height="7" rx="1.6"/><rect x="7" y="14" width="10" height="6" rx="0.6"/>',
    "external": '<path d="M14 5h5v5"/><line x1="19" y1="5" x2="11" y2="13"/><path d="M18.5 14v4A1.5 1.5 0 0 1 17 19.5H6.5A1.5 1.5 0 0 1 5 18V7.5A1.5 1.5 0 0 1 6.5 6H11"/>',
    "play":     '<path d="M7 4.8 19 12 7 19.2Z"/>',
    "pause":    '<line x1="9" y1="5" x2="9" y2="19"/><line x1="15" y1="5" x2="15" y2="19"/>',
    "eye":      '<path d="M2.5 12S6 5.5 12 5.5 21.5 12 21.5 12 18 18.5 12 18.5 2.5 12 2.5 12Z"/><circle cx="12" cy="12" r="3"/>',
    "star":     '<polygon points="12 4 14.6 9.3 20.5 10.1 16.2 14.2 17.3 20 12 17.2 6.7 20 7.8 14.2 3.5 10.1 9.4 9.3"/>',
    "heart":    '<path d="M12 20.3S4.5 15.6 4.5 10.4A3.8 3.8 0 0 1 12 7.6a3.8 3.8 0 0 1 7.5 2.8c0 5.2-7.5 9.9-7.5 9.9Z"/>',
    "info":     '<circle cx="12" cy="12" r="8.2"/><line x1="12" y1="11" x2="12" y2="16.2"/><circle cx="12" cy="7.8" r="0.6"/>',
    "alert":    '<path d="M12 3.5 21.5 20H2.5Z"/><line x1="12" y1="9.5" x2="12" y2="14"/><circle cx="12" cy="17" r="0.6"/>'
  };

  /* ---- BRAND / SOCIAL — recognisable solid (or self-described) marks ---- */
  var BRAND = {
    "x": { fill: true, p: '<path d="M18.24 2.25h3.31l-7.23 8.26L22.84 21.75h-6.66l-5.22-6.82-5.96 6.82H1.68l7.73-8.84L1.16 2.25h6.83l4.71 6.23 5.54-6.23Zm-1.16 17.52h1.83L7.01 4.13H5.04L17.08 19.77Z"/>' },
    "linkedin": { fill: true, p: '<path d="M20.45 20.45h-3.56v-5.57c0-1.33-.03-3.04-1.85-3.04-1.86 0-2.14 1.45-2.14 2.94v5.67H9.35V9.0h3.41v1.56h.05c.48-.9 1.64-1.85 3.37-1.85 3.6 0 4.27 2.37 4.27 5.45v6.29ZM5.34 7.43a2.07 2.07 0 1 1 0-4.13 2.07 2.07 0 0 1 0 4.13ZM7.12 20.45H3.56V9.0h3.56v11.45ZM22.22 0H1.78C.8 0 0 .77 0 1.73v20.54C0 23.22.8 24 1.78 24h20.44c.98 0 1.78-.78 1.78-1.73V1.73C24 .77 23.2 0 22.22 0Z"/>' },
    "github": { fill: true, p: '<path d="M12 .5C5.37.5 0 5.87 0 12.5c0 5.3 3.44 9.8 8.21 11.39.6.11.82-.26.82-.58 0-.28-.01-1.03-.02-2.04-3.34.73-4.04-1.61-4.04-1.61-.55-1.39-1.34-1.76-1.34-1.76-1.09-.75.08-.73.08-.73 1.2.09 1.84 1.24 1.84 1.24 1.07 1.84 2.81 1.31 3.5 1 .11-.78.42-1.31.76-1.61-2.67-.3-5.47-1.34-5.47-5.95 0-1.32.47-2.39 1.24-3.23-.13-.3-.54-1.52.12-3.18 0 0 1.01-.32 3.3 1.23a11.5 11.5 0 0 1 6.01 0c2.29-1.55 3.3-1.23 3.3-1.23.66 1.66.25 2.88.12 3.18.77.84 1.24 1.91 1.24 3.23 0 4.62-2.81 5.64-5.49 5.94.43.37.81 1.1.81 2.22 0 1.6-.01 2.9-.01 3.29 0 .32.22.7.83.58A12 12 0 0 0 24 12.5C24 5.87 18.63.5 12 .5Z"/>' },
    "instagram": { fill: false, p: '<rect x="2.7" y="2.7" width="18.6" height="18.6" rx="5.3"/><circle cx="12" cy="12" r="4.4"/><circle cx="17.25" cy="6.75" r="1.15" fill="currentColor" stroke="none"/>' },
    "dribbble": { fill: false, p: '<circle cx="12" cy="12" r="9.2"/><path d="M4.6 6.8c3.7 4.2 9 6.3 14.8 6.5M3.1 13.7c5.2-1.4 10.3-.3 13.6 3.9M8.7 3.4C12.3 7.7 15 13.2 16 20.4"/>' },
    "behance": { fill: true, p: '<path d="M8.3 11.4c.8-.4 1.3-1.1 1.3-2.1 0-2-1.5-2.7-3.3-2.7H1v10.8h5.5c1.9 0 3.7-.9 3.7-3.1 0-1.4-.6-2.4-1.9-2.9ZM3.4 8.5h2.2c.8 0 1.5.2 1.5 1.1 0 .9-.6 1.2-1.4 1.2H3.4V8.5Zm2.5 7H3.4v-2.8h2.6c1 0 1.6.4 1.6 1.4 0 1-.8 1.4-1.7 1.4ZM23 13.7c0-2.4-1.4-4.4-3.9-4.4-2.5 0-4.2 1.9-4.2 4.3 0 2.5 1.6 4.3 4.2 4.3 2 0 3.3-.9 3.8-2.8h-2c-.2.6-.9.9-1.6.9-1.1 0-1.8-.7-1.8-1.8H23c0-.3 0-.5 0-.8Zm-5.5-.9c.1-.9.7-1.5 1.6-1.5.9 0 1.4.5 1.5 1.5h-3.1ZM15.5 7.5h4.8V6.3h-4.8v1.2Z"/>' },
    "bluesky": { fill: true, p: '<path d="M6.3 4.6c2.6 1.95 5.4 5.9 6.4 8 1-2.1 3.8-6.05 6.4-8 1.9-1.4 5-2.5 5 1.05 0 .7-.4 5.95-.65 6.8-.85 2.95-3.85 3.7-6.5 3.25 4.65.8 5.85 3.45 3.3 6.1-4.85 5.05-6.95-1.25-7.5-2.85-.1-.3-.15-.45-.15-.35 0-.1-.05.05-.15.35-.55 1.6-2.65 7.9-7.5 2.85-2.55-2.65-1.35-5.3 3.3-6.1-2.65.45-5.65-.3-6.5-3.25C1.3 11.6.9 6.35.9 5.65c0-3.55 3.1-2.45 5-1.05Z"/>' },
    "youtube": { fill: true, p: '<path d="M23.5 6.5a3 3 0 0 0-2.12-2.12C19.5 3.9 12 3.9 12 3.9s-7.5 0-9.38.48A3 3 0 0 0 .5 6.5 31.3 31.3 0 0 0 0 12a31.3 31.3 0 0 0 .5 5.5 3 3 0 0 0 2.12 2.12C4.5 20.1 12 20.1 12 20.1s7.5 0 9.38-.48A3 3 0 0 0 23.5 17.5 31.3 31.3 0 0 0 24 12a31.3 31.3 0 0 0-.5-5.5ZM9.6 15.5v-7l6.1 3.5-6.1 3.5Z"/>' },
    "medium": { fill: true, p: '<path d="M3.4 7.6a.9.9 0 0 0-.3-.76L1 4.36V4h6.4l4.95 10.85L16.7 4H22v.36l-1.8 1.73a.5.5 0 0 0-.2.5v12.82a.5.5 0 0 0 .2.5L22 21.64V22h-9v-.36l1.86-1.8c.18-.18.18-.24.18-.5V9.1l-5.2 12.86h-.7L3.3 9.1v8.62a1.2 1.2 0 0 0 .33 1l2.42 2.92V22H0v-.36l2.42-2.92a1.16 1.16 0 0 0 .98-1V7.6Z"/>' },
    "rss": { fill: true, p: '<circle cx="5.4" cy="18.6" r="2.4" stroke="none"/><path stroke="none" d="M3 11.6v3a6.4 6.4 0 0 1 6.4 6.4h3A9.4 9.4 0 0 0 3 11.6Z"/><path stroke="none" d="M3 5.6v3A12.4 12.4 0 0 1 15.4 21h3A15.4 15.4 0 0 0 3 5.6Z"/>' },
    "mastodon": { fill: true, p: '<path d="M21.6 8.6c0-4-2.6-5.2-2.6-5.2C17.7 2.8 15.5 2.5 13.2 2.5h-.05C10.8 2.5 8.6 2.8 7.3 3.4c0 0-2.6 1.2-2.6 5.2 0 .9 0 2 .05 3.16.15 3.9.78 7.74 4.4 8.7 1.66.44 3.1.53 4.25.47 2.1-.12 3.27-.75 3.27-.75l-.07-1.52s-1.5.47-3.17.42c-1.66-.06-3.4-.18-3.68-2.2a4 4 0 0 1-.04-.57s1.63.4 3.7.5c1.26.05 2.45-.08 3.65-.22 2.3-.28 4.3-1.7 4.55-3 .4-2.05.37-5 .37-5Zm-3.2 5.32h-2V9.04c0-1.02-.43-1.54-1.3-1.54-.95 0-1.43.62-1.43 1.84v2.66h-1.98V9.34c0-1.22-.48-1.84-1.44-1.84-.86 0-1.3.52-1.3 1.54v4.88h-2V8.9c0-1.02.26-1.83.78-2.43.54-.6 1.24-.9 2.12-.9 1.02 0 1.79.39 2.29 1.17l.5.83.5-.83c.5-.78 1.27-1.17 2.29-1.17.88 0 1.58.3 2.12.9.52.6.78 1.41.78 2.43v5.02Z"/>' }
  };

  function toSize(s) {
    if (s == null) return null;
    return typeof s === "number" ? s + "px" : String(s);
  }

  function buildSVG(name, opts) {
    opts = opts || {};
    var line = LINE[name], brand = BRAND[name];
    if (!line && !brand) return "";
    var cls = "bk-icon" + (opts["class"] ? " " + opts["class"] : "");
    var attrs = 'class="' + cls + '" viewBox="0 0 24 24" ';
    var sz = toSize(opts.size);
    if (sz) attrs += 'style="width:' + sz + ';height:' + sz + '" ';
    if (opts.label) attrs += 'role="img" aria-label="' + opts.label + '" ';
    else attrs += 'aria-hidden="true" focusable="false" ';

    var inner, paint;
    if (line) {
      var sw = opts.stroke != null ? opts.stroke : 1.6;
      paint = 'fill="none" stroke="currentColor" stroke-width="' + sw + '" stroke-linecap="round" stroke-linejoin="round"';
      inner = line;
    } else if (brand.fill) {
      paint = 'fill="currentColor"';
      inner = brand.p;
    } else {
      // self-described brand mark: outline by default, explicit fill where set
      paint = 'fill="none" stroke="currentColor" stroke-width="1.7" stroke-linecap="round" stroke-linejoin="round"';
      inner = brand.p;
    }
    return '<svg ' + attrs + paint + '>' + inner + '</svg>';
  }

  function buildEl(name, opts) {
    var tmp = document.createElement("span");
    tmp.innerHTML = buildSVG(name, opts);
    return tmp.firstChild;
  }

  function hydrate(root) {
    root = root || document;
    var nodes = root.querySelectorAll ? root.querySelectorAll("[data-bk-icon]") : [];
    for (var i = 0; i < nodes.length; i++) {
      var node = nodes[i];
      var name = node.getAttribute("data-bk-icon");
      var markup = buildSVG(name, {
        size: node.getAttribute("data-size") || null,
        stroke: node.getAttribute("data-stroke") || null,
        label: node.getAttribute("aria-label") || null
      });
      if (!markup) continue;
      var tmp = document.createElement("span");
      tmp.innerHTML = markup;
      var svg = tmp.firstChild;
      // carry over any extra classes the author put on the placeholder
      if (node.className) {
        node.className.split(/\s+/).forEach(function (c) { if (c) svg.classList.add(c); });
      }
      node.parentNode.replaceChild(svg, node);
    }
  }

  global.MonographIcons = {
    names: Object.keys(LINE).concat(Object.keys(BRAND)),
    line: Object.keys(LINE),
    brand: Object.keys(BRAND),
    has: function (n) { return !!(LINE[n] || BRAND[n]); },
    markup: buildSVG,
    el: buildEl,
    hydrate: hydrate
  };

  if (document.readyState === "loading") {
    document.addEventListener("DOMContentLoaded", function () { hydrate(document); });
  } else {
    hydrate(document);
  }

})(window);
