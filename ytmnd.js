(function () {
  var audio = new Audio(url);
  audio.loop = true;
  audio.muted = true;
  audio
    .play()
    .then(function () {
      console.log("Audio started (muted). Click/tap to unmute!");
      var unmuteMsg = document.createElement("div");
      unmuteMsg.textContent = "Click to unmute";
      unmuteMsg.style.cssText =
        "position:fixed;top:10px;right:10px;background:rgba(0,0,0,0.8);color:#fff;padding:10px 20px;border-radius:5px;font-family:sans-serif;z-index:9999;cursor:pointer;";
      document.body.appendChild(unmuteMsg);
      function unmute() {
        audio.muted = false;
        unmuteMsg.remove();
        console.log("Audio unmuted!");
      }
      document.addEventListener("click", unmute, { once: true });
      document.addEventListener("keydown", unmute, { once: true });
      document.addEventListener("touchstart", unmute, { once: true });
      unmuteMsg.addEventListener("click", unmute, { once: true });
    })
    .catch(function (error) {
      console.error("Autoplay failed even when muted:", error);
      function playOnInteraction() {
        audio.muted = false;
        audio
          .play()
          .then(function () {
            console.log("Audio started after user interaction");
          })
          .catch(function (err) {
            console.error("Still couldn't play:", err);
          });
      }
      document.addEventListener("click", playOnInteraction, { once: true });
      document.addEventListener("keydown", playOnInteraction, { once: true });
      document.addEventListener("touchstart", playOnInteraction, {
        once: true,
      });
    });
})();
