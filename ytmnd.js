(function () {
  var AudioContext = window.AudioContext || window.webkitAudioContext;
  var context = new AudioContext();
  var request = new XMLHttpRequest();
  var source;
  var buffer;

  request.open("GET", url, true);
  request.responseType = "arraybuffer";

  request.onload = function () {
    context.decodeAudioData(
      request.response,
      function (response) {
        buffer = response;

        function playBuffer() {
          source = context.createBufferSource();
          source.buffer = buffer;
          source.connect(context.destination);

          source.onended = function () {
            playBuffer();
          };

          source.start(0);
        }

        playBuffer();
      },
      function (error) {
        console.error("Audio decoding failed:", error);
      },
    );
  };

  request.onerror = function () {
    console.error("Failed to load audio file");
  };

  request.send();
})();
