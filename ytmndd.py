#!/usr/bin/env python3

import json
import os
import os.path
import re
import subprocess
import sys
import time
from optparse import OptionParser

import requests
from requests.exceptions import RequestException


class YTMND:
    def __init__(self):
        self.user_mode = False
        self.media_only = False
        self.html_only = False
        self.json_only = False
        self.no_web_audio = False
        self.print_json = False
        self.sleep = 5

    def fetch_user(self, user):
        if user == "":
            print("expecting one ytmnd name, got " + str(sys.argv))
            return

        ytmnd_name = user
        try:
            response = requests.get(
                "http://ytmnd.com/users/" + ytmnd_name + "/sites",
                headers={"User-Agent": "Mozilla/5.0"},
            )
            response.raise_for_status()
            ytmnd_html = response.text.splitlines()
        except RequestException as e:
            print(f"Error fetching user page: {e}")
            return

        domains = []

        for line in ytmnd_html:
            if "profile_link" in line:
                expr = r"site_link\" href=\"http://(\S+).ytmn(d|sfw)?.com\""
                match = re.search(expr, line)
                if match:
                    domain = match.group(1)
                    domains.append(domain)

        if self.json_only:
            if self.media_only:
                os.makedirs(user, exist_ok=True)
                os.chdir(user)
            parsed = []
            for domain in domains:
                result = self.fetch_ytmnd(domain)
                if result:
                    parsed.append(result)
            if self.media_only:
                os.chdir("..")
            self.write_json(ytmnd_name, parsed)

        else:
            print(">> found %d domains" % len(domains))
            os.makedirs(user, exist_ok=True)
            os.chdir(user)
            for domain in domains:
                self.fetch_ytmnd(domain)
            os.chdir("..")

    def fetch_ytmnd(self, domain):
        if domain == "":
            print("expecting one ytmnd name, got " + str(sys.argv))
            return None

        if not self.print_json:
            print("fetching %s" % domain)
        if self.sleep:
            time.sleep(self.sleep)

        ytmnd_name = domain
        try:
            response = requests.get(
                "http://" + domain + ".ytmnd.com", headers={"User-Agent": "Mozilla/5.0"}
            )
            response.raise_for_status()
            ytmnd_html = response.text

            expr = r"ytmnd.site_id = (\d+);"
            match = re.search(expr, ytmnd_html)
            if not match:
                print(f"Could not find site_id for {domain}")
                return None
            ytmnd_id = match.group(1)

            response = requests.get(
                "http://" + domain + ".ytmnd.com/info/" + ytmnd_id + "/json",
                headers={"User-Agent": "Mozilla/5.0"},
            )
            response.raise_for_status()
            ytmnd_info = response.json()

        except RequestException as e:
            print(f"Error fetching {domain}: {e}")
            return None

        if self.print_json:
            print(json.dumps(ytmnd_info, sort_keys=True, indent=4))
        elif self.json_only:
            if self.media_only:
                self.fetch_media(ytmnd_info)
            return self.parse_json(ytmnd_info)
        elif self.media_only:
            self.fetch_media(ytmnd_info)
        elif self.html_only:
            self.write_index(ytmnd_info)
        else:
            self.fetch_media(ytmnd_info)
            self.write_index(ytmnd_info)

        return ytmnd_info

    def fetch_media(self, ytmnd_info):
        domain = ytmnd_info["site"]["domain"]
        original_gif = ytmnd_info["site"]["foreground"]["url"]
        gif_type = original_gif.split(".")[-1]
        original_wav = ytmnd_info["site"]["sound"]["url"]
        wav_type = ytmnd_info["site"]["sound"]["type"]

        if "alternates" in ytmnd_info["site"]["sound"]:
            key = list(ytmnd_info["site"]["sound"]["alternates"].keys())[0]
            value = ytmnd_info["site"]["sound"]["alternates"][key]
            if value["file_type"] != "swf":
                original_wav = value["file_url"]
                wav_type = ytmnd_info["site"]["sound"]["file_type"]

        try:
            gif_response = requests.get(
                original_gif, headers={"User-Agent": "Mozilla/5.0"}
            )
            gif_response.raise_for_status()
            with open(f"{domain}.{gif_type}", "wb") as f:
                f.write(gif_response.content)
        except RequestException as e:
            print(f"Error downloading gif: {e}")

        try:
            wav_response = requests.get(
                original_wav, headers={"User-Agent": "Mozilla/5.0"}
            )
            wav_response.raise_for_status()
            with open(f"{domain}.{wav_type}", "wb") as f:
                f.write(wav_response.content)
        except RequestException as e:
            print(f"Error downloading audio: {e}")

    def write_index(self, ytmnd_info):
        domain = ytmnd_info["site"]["domain"]
        bgcolor = ytmnd_info["site"]["background"]["color"]
        title = ytmnd_info["site"]["description"]
        placement = ytmnd_info["site"]["foreground"]["placement"]

        original_gif = ytmnd_info["site"]["foreground"]["url"]
        gif_type = original_gif.split(".")[-1]
        wav_type = ytmnd_info["site"]["sound"]["type"]

        if "alternates" in ytmnd_info["site"]["sound"]:
            key = list(ytmnd_info["site"]["sound"]["alternates"].keys())[0]
            value = ytmnd_info["site"]["sound"]["alternates"][key]
            if value["file_type"] != "swf":
                original_wav = value["file_url"]
                wav_type = ytmnd_info["site"]["sound"]["file_type"]

        with open(domain + ".html", "w", encoding="utf-8") as fn:
            fn.write("<!DOCTYPE html>\n")
            fn.write("<html>\n")
            fn.write("<head>\n")
            fn.write("<meta charset='utf-8'>\n")
            fn.write(
                "<meta name='viewport' content='width=device-width, initial-scale=1.0'>\n"
            )
            fn.write("<title>%s</title>\n" % title)
            fn.write("<style>\n")
            fn.write("*{margin:0;padding:0;width:100%;height:100%;}\n")
            fn.write(
                "body{font-size:12px;font-weight:normal;font-style:normal;overflow:hidden;"
            )
            fn.write("background-color:%s;" % bgcolor)
            fn.write("background-image:url(%s.%s);" % (domain, gif_type))
            if placement == "mc":
                fn.write(
                    "background-position: center center; background-repeat: no-repeat;}"
                )
            elif placement == "tile":
                fn.write("background-position: top left; background-repeat: repeat;}")
            fn.write("\n")
            fn.write(
                "#zoom_text{position:absolute;left:0;top:0;width:1000px;z-index:10;text-align:center;font-family:Tahoma, sans-serif}\n"
            )
            fn.write("#zoom_text div{position:absolute;width:1000px}\n")
            fn.write("@media (max-width: 768px) {\n")
            fn.write(
                "  #zoom_text{left:50%;top:50%;margin-left:-500px;-webkit-transform:translate(0,-50%) scale(0.55);-ms-transform:translate(0,-50%) scale(0.55);transform:translate(0,-50%) scale(0.55);-webkit-transform-origin:center center;-ms-transform-origin:center center;transform-origin:center center;}\n"
            )
            fn.write("}\n")
            fn.write("@media (max-width: 480px) {\n")
            fn.write(
                "  #zoom_text{-webkit-transform:translate(0,-50%) scale(0.45);-ms-transform:translate(0,-50%) scale(0.45);transform:translate(0,-50%) scale(0.45);}\n"
            )
            fn.write("}\n")
            fn.write(
                "#unmute-overlay{position:fixed;top:0;left:0;width:100%;height:100%;background:rgba(0,0,0,0.9);display:-webkit-box;display:-webkit-flex;display:-ms-flexbox;display:flex;-webkit-box-align:center;-webkit-align-items:center;-ms-flex-align:center;align-items:center;-webkit-box-pack:center;-webkit-justify-content:center;-ms-flex-pack:center;justify-content:center;z-index:99999;cursor:pointer;}\n"
            )
            fn.write(
                "#unmute-btn{width:80px;height:80px;background:rgba(255,255,255,0.1);border:2px solid rgba(255,255,255,0.3);border-radius:50%;display:-webkit-box;display:-webkit-flex;display:-ms-flexbox;display:flex;-webkit-box-align:center;-webkit-align-items:center;-ms-flex-align:center;align-items:center;-webkit-box-pack:center;-webkit-justify-content:center;-ms-flex-pack:center;justify-content:center;font-size:32px;color:rgba(255,255,255,0.9);-webkit-transition:all 0.3s ease;transition:all 0.3s ease;}\n"
            )
            fn.write(
                "#unmute-btn:hover{background:rgba(255,255,255,0.2);border-color:rgba(255,255,255,0.5);-webkit-transform:scale(1.1);-ms-transform:scale(1.1);transform:scale(1.1);}\n"
            )
            fn.write("</style>\n")
            fn.write("</head>\n")

            fn.write("<body>\n")

            fn.write('<div id="unmute-overlay">\n')
            fn.write('  <div id="unmute-btn">▶</div>\n')
            fn.write("</div>\n")

            self.write_zoom_text(fn, ytmnd_info)

            if self.no_web_audio:
                fn.write("<audio src='%s.%s' loop autoplay>\n" % (domain, wav_type))

            fn.write("</body>\n")

            fn.write("<script>\n")
            fn.write("(function() {\n")
            fn.write("  var audioUrl = '%s.%s';\n" % (domain, wav_type))
            fn.write("  var context = null;\n")
            fn.write("  var source = null;\n")
            fn.write("  var audioBuffer = null;\n")
            fn.write("  var isPlaying = false;\n")
            fn.write("  var fallbackAudio = null;\n")
            fn.write("  \n")
            fn.write("  function hasWebAudio() {\n")
            fn.write(
                "    return ('AudioContext' in window) || ('webkitAudioContext' in window);\n"
            )
            fn.write("  }\n")
            fn.write("  \n")
            fn.write("  function createContext() {\n")
            fn.write("    if ('AudioContext' in window) {\n")
            fn.write("      return new AudioContext();\n")
            fn.write("    } else if ('webkitAudioContext' in window) {\n")
            fn.write("      return new webkitAudioContext();\n")
            fn.write("    }\n")
            fn.write("    return null;\n")
            fn.write("  }\n")
            fn.write("  \n")
            fn.write("  function loadAudioWithXHR(callback, errorCallback) {\n")
            fn.write("    var request = new XMLHttpRequest();\n")
            fn.write("    request.open('GET', audioUrl, true);\n")
            fn.write("    request.responseType = 'arraybuffer';\n")
            fn.write("    request.onload = function() {\n")
            fn.write("      if (request.status === 200) {\n")
            fn.write("        callback(request.response);\n")
            fn.write("      } else {\n")
            fn.write(
                "        errorCallback('Request failed with status: ' + request.status);\n"
            )
            fn.write("      }\n")
            fn.write("    };\n")
            fn.write("    request.onerror = function() {\n")
            fn.write("      errorCallback('Network error');\n")
            fn.write("    };\n")
            fn.write("    request.send();\n")
            fn.write("  }\n")
            fn.write("  \n")
            fn.write("  function loopAudio() {\n")
            fn.write("    if (!isPlaying || !audioBuffer) return;\n")
            fn.write("    \n")
            fn.write("    source = context.createBufferSource();\n")
            fn.write("    source.connect(context.destination);\n")
            fn.write("    source.buffer = audioBuffer;\n")
            fn.write("    \n")
            fn.write("    try {\n")
            fn.write("      if (source.start) {\n")
            fn.write("        source.start(0);\n")
            fn.write("      } else if (source.noteOn) {\n")
            fn.write("        source.noteOn(0);\n")
            fn.write("      }\n")
            fn.write("    } catch(e) {\n")
            fn.write("      console.error('Start error:', e);\n")
            fn.write("    }\n")
            fn.write("    \n")
            fn.write("    var duration = audioBuffer.duration * 1000;\n")
            fn.write("    var offset = audioBuffer.duration < 2 ? 0 : 60;\n")
            fn.write("    setTimeout(loopAudio, duration - offset);\n")
            fn.write("  }\n")
            fn.write("  \n")
            fn.write("  function playWebAudio() {\n")
            fn.write("    context = createContext();\n")
            fn.write("    if (!context) {\n")
            fn.write("      fallbackToHTMLAudio();\n")
            fn.write("      return;\n")
            fn.write("    }\n")
            fn.write("    \n")
            fn.write("    if (context.state === 'suspended') {\n")
            fn.write("      try {\n")
            fn.write("        context.resume();\n")
            fn.write("      } catch(e) {\n")
            fn.write("        console.error('Resume error:', e);\n")
            fn.write("      }\n")
            fn.write("    }\n")
            fn.write("    \n")
            fn.write("    loadAudioWithXHR(\n")
            fn.write("      function(arrayBuffer) {\n")
            fn.write("        var decodeSuccess = function(buffer) {\n")
            fn.write("          audioBuffer = buffer;\n")
            fn.write("          isPlaying = true;\n")
            fn.write("          setTimeout(loopAudio, 0);\n")
            fn.write("        };\n")
            fn.write("        var decodeError = function(error) {\n")
            fn.write("          console.error('Decode error:', error);\n")
            fn.write("          fallbackToHTMLAudio();\n")
            fn.write("        };\n")
            fn.write("        try {\n")
            fn.write(
                "          context.decodeAudioData(arrayBuffer, decodeSuccess, decodeError);\n"
            )
            fn.write("        } catch(e) {\n")
            fn.write("          console.error('decodeAudioData exception:', e);\n")
            fn.write("          fallbackToHTMLAudio();\n")
            fn.write("        }\n")
            fn.write("      },\n")
            fn.write("      function(error) {\n")
            fn.write("        console.error('Load error:', error);\n")
            fn.write("        fallbackToHTMLAudio();\n")
            fn.write("      }\n")
            fn.write("    );\n")
            fn.write("  }\n")
            fn.write("  \n")
            fn.write("  function fallbackToHTMLAudio() {\n")
            fn.write("    try {\n")
            fn.write("      fallbackAudio = new Audio(audioUrl);\n")
            fn.write("      fallbackAudio.loop = true;\n")
            fn.write("      var playPromise = fallbackAudio.play();\n")
            fn.write("      if (playPromise && playPromise.catch) {\n")
            fn.write("        playPromise.catch(function(error) {\n")
            fn.write("          console.error('HTML5 audio play failed:', error);\n")
            fn.write("        });\n")
            fn.write("      }\n")
            fn.write("      isPlaying = true;\n")
            fn.write("    } catch(e) {\n")
            fn.write("      console.error('Fallback audio failed:', e);\n")
            fn.write("    }\n")
            fn.write("  }\n")
            fn.write("  \n")
            fn.write("  function startAudio() {\n")
            fn.write("    var overlay = document.getElementById('unmute-overlay');\n")
            fn.write("    if (overlay) {\n")
            fn.write("      overlay.style.display = 'none';\n")
            fn.write("    }\n")
            fn.write("    \n")
            fn.write("    if (hasWebAudio()) {\n")
            fn.write("      try {\n")
            fn.write("        playWebAudio();\n")
            fn.write("      } catch(e) {\n")
            fn.write("        console.error('Web Audio failed:', e);\n")
            fn.write("        fallbackToHTMLAudio();\n")
            fn.write("      }\n")
            fn.write("    } else {\n")
            fn.write("      fallbackToHTMLAudio();\n")
            fn.write("    }\n")
            fn.write("  }\n")
            fn.write("  \n")
            fn.write("  var overlay = document.getElementById('unmute-overlay');\n")
            fn.write("  if (overlay) {\n")
            fn.write("    overlay.addEventListener('click', function(e) {\n")
            fn.write("      e.preventDefault();\n")
            fn.write("      startAudio();\n")
            fn.write("    });\n")
            fn.write("    overlay.addEventListener('touchend', function(e) {\n")
            fn.write("      e.preventDefault();\n")
            fn.write("      startAudio();\n")
            fn.write("    });\n")
            fn.write("  }\n")
            fn.write("  \n")
            fn.write("  document.addEventListener('keydown', function(e) {\n")
            fn.write("    if (overlay && overlay.style.display !== 'none') {\n")
            fn.write("      startAudio();\n")
            fn.write("    }\n")
            fn.write("  });\n")
            fn.write("})();\n")
            fn.write("</script>\n")

            fn.write("<script type='application/json' id='ytmnd-data'>\n")
            fn.write(json.dumps(ytmnd_info, sort_keys=True, indent=2) + "\n")
            fn.write("</script>\n")

            fn.write("</html>")

    def write_zoom_text(self, fn, ytmnd_info):
        if "zoom_text" not in ytmnd_info["site"]:
            return

        zoom_text = ytmnd_info["site"]["zoom_text"]

        fn.write('<div id="zoom_text">')

        offset = 100
        if "line_3" in zoom_text and len(zoom_text["line_3"]) > 0:
            self.write_zoom_layers(fn, zoom_text["line_3"], offset, 269)
            offset += 21
        if "line_2" in zoom_text and len(zoom_text["line_2"]) > 0:
            self.write_zoom_layers(fn, zoom_text["line_2"], offset, 135)
            offset += 21
        if "line_1" in zoom_text and len(zoom_text["line_1"]) > 0:
            self.write_zoom_layers(fn, zoom_text["line_1"], offset, 1)

        fn.write("</div>")

    def write_zoom_layers(self, fn, text, offset, top):
        for i in range(1, 22):
            z_index = offset + i
            row_left = i * 2
            row_top = top + i
            font_size = i * 2
            if i == 21:
                color = 0
            else:
                color = i * 4

            fn.write(
                "<div style='z-index: %d; left: %dpx; top: %dpx; color: rgb(%d, %d, %d); font-size: %dpt;'>%s</div>"
                % (z_index, row_left, row_top, color, color, color, font_size, text)
            )

    def parse_json(self, ytmnd_info):
        domain = ytmnd_info["site"]["domain"]
        bgcolor = ytmnd_info["site"]["background"]["color"]
        title = ytmnd_info["site"]["description"]
        placement = ytmnd_info["site"]["foreground"]["placement"]

        gif_type = ytmnd_info["site"]["foreground"]["url"].split(".")[-1]
        wav_type = ytmnd_info["site"]["sound"]["type"]
        zoom_text = ytmnd_info["site"]["zoom_text"]
        keywords = ytmnd_info["site"]["keywords"]
        username = ytmnd_info["site"]["user"]["user_name"]
        sound_origin = ytmnd_info["site"]["sound_origin"]
        image_origin = ytmnd_info["site"]["fg_image_origin"]
        work_safe = ytmnd_info["site"]["work_safe"]

        if len(zoom_text["line_1"]) == 0:
            zoom_text = ""

        if "alternates" in ytmnd_info["site"]["sound"]:
            key = list(ytmnd_info["site"]["sound"]["alternates"].keys())[0]
            value = ytmnd_info["site"]["sound"]["alternates"][key]
            if value["file_type"] != "swf":
                wav_type = ytmnd_info["site"]["sound"]["file_type"]

        simplified_info = {
            "domain": domain,
            "title": title,
            "username": username,
            "work_safe": work_safe,
            "bgcolor": bgcolor,
            "placement": placement,
            "zoom_text": zoom_text,
            "image": domain + "." + gif_type,
            "sound": domain + "." + wav_type,
            "image_type": gif_type,
            "sound_type": wav_type,
            "image_origin": image_origin,
            "sound_origin": sound_origin,
        }

        return simplified_info

    def write_json(self, domain, data):
        with open(domain + ".json", "w", encoding="utf-8") as fn:
            fn.write(json.dumps(data))


if __name__ == "__main__":
    parser = OptionParser()

    parser.add_option("-u", "--user", action="store_true")
    parser.add_option("-m", "--media-only", action="store_true")
    parser.add_option("-f", "--html-only", action="store_true")
    parser.add_option("-j", "--json-only", action="store_true")
    parser.add_option("-w", "--no-web-audio", action="store_true")
    parser.add_option("-p", "--print-json", action="store_true")
    parser.add_option(
        "-s", "--sleep", action="store", type="int", dest="sleep", default=5
    )

    (options, args) = parser.parse_args()

    if len(args) == 0:
        parser.error("incorrect number of arguments")
        sys.exit(1)

    ytmnd = YTMND()
    ytmnd.user_mode = options.user
    ytmnd.media_only = options.media_only
    ytmnd.html_only = options.html_only
    ytmnd.json_only = options.json_only
    ytmnd.no_web_audio = options.no_web_audio
    ytmnd.print_json = options.print_json
    ytmnd.sleep = options.sleep

    if options.user:
        user = args[0]
        ytmnd.fetch_user(user)

    else:
        name = (
            args[0]
            .replace("http://", "")
            .replace(".ytmnsfw.com", "")
            .replace(".ytmnd.com", "")
            .replace("/", "")
        )
        ytmnd.fetch_ytmnd(name)
