(function () {
  var toggle = document.querySelector(".nav-toggle");
  var nav = document.getElementById("nav");
  if (toggle && nav) {
    toggle.addEventListener("click", function () {
      var open = nav.classList.toggle("open");
      toggle.setAttribute("aria-expanded", open ? "true" : "false");
    });
  }
  document.addEventListener("click", function (ev) {
    var btn = ev.target.closest && ev.target.closest(".yt-facade");
    if (!btn) return;
    var id = btn.getAttribute("data-yt") || "";
    if (!/^[\w-]{6,}$/.test(id)) return;
    var frame = document.createElement("iframe");
    frame.src = "https://www.youtube-nocookie.com/embed/" + id + "?autoplay=1";
    frame.title = btn.getAttribute("data-title") || "YouTube Short";
    frame.setAttribute("allow", "accelerometer; autoplay; clipboard-write; encrypted-media; gyroscope; picture-in-picture; web-share");
    frame.allowFullscreen = true;
    var box = document.createElement("div");
    box.className = "yt";
    box.appendChild(frame);
    btn.replaceWith(box);
  });
})();
