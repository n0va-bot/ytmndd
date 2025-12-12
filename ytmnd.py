#!/usr/bin/env python3

import sys
import os
import os.path
import re
import time
import json
import subprocess
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
      response = requests.get("http://ytmnd.com/users/" + ytmnd_name + "/sites",
                              headers={'User-Agent': 'Mozilla/5.0'})
      response.raise_for_status()
      ytmnd_html = response.text.splitlines()
    except RequestException as e:
      print(f"Error fetching user page: {e}")
      return

    domains = []

    for line in ytmnd_html:
      if 'profile_link' in line:
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
      if not self.no_web_audio:
        self.copy_ytmnd_js()
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
      response = requests.get("http://" + domain + ".ytmnd.com",
                              headers={'User-Agent': 'Mozilla/5.0'})
      response.raise_for_status()
      ytmnd_html = response.text

      expr = r"ytmnd.site_id = (\d+);"
      match = re.search(expr, ytmnd_html)
      if not match:
        print(f"Could not find site_id for {domain}")
        return None
      ytmnd_id = match.group(1)

      response = requests.get("http://" + domain + ".ytmnd.com/info/" + ytmnd_id + "/json",
                              headers={'User-Agent': 'Mozilla/5.0'})
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
    domain = ytmnd_info['site']['domain']
    original_gif = ytmnd_info['site']['foreground']['url']
    gif_type = original_gif.split(".")[-1]
    original_wav = ytmnd_info['site']['sound']['url']
    wav_type = ytmnd_info['site']['sound']['type']

    if 'alternates' in ytmnd_info['site']['sound']:
      key = list(ytmnd_info['site']['sound']['alternates'].keys())[0]
      value = ytmnd_info['site']['sound']['alternates'][key]
      if value['file_type'] != 'swf':
        original_wav = value['file_url']
        wav_type = ytmnd_info['site']['sound']['file_type']

    subprocess.run(["wget", "--quiet", "-O", f"{domain}.{gif_type}", original_gif])
    subprocess.run(["wget", "--quiet", "-O", f"{domain}.{wav_type}", original_wav])

  def write_index(self, ytmnd_info):

    domain = ytmnd_info['site']['domain']
    bgcolor = ytmnd_info['site']['background']['color']
    title = ytmnd_info['site']['description']
    placement = ytmnd_info['site']['foreground']['placement']

    original_gif = ytmnd_info['site']['foreground']['url']
    gif_type = original_gif.split(".")[-1]
    wav_type = ytmnd_info['site']['sound']['type']

    if 'alternates' in ytmnd_info['site']['sound']:
      key = list(ytmnd_info['site']['sound']['alternates'].keys())[0]
      value = ytmnd_info['site']['sound']['alternates'][key]
      if value['file_type'] != 'swf':
        original_wav = value['file_url']
        wav_type = ytmnd_info['site']['sound']['file_type']

    with open(domain + ".html", 'w', encoding='utf-8') as fn:
      fn.write("<html>\n")
      fn.write("<head>\n")
      fn.write("<title>%s</title>\n" % title)
      fn.write("<style>\n")
      fn.write("*{margin:0;padding:0;width:100%;height:100%;}\n")
      fn.write("body{font-size:12px;font-weight:normal;font-style:normal;overflow:hidden;")
      fn.write("background-color:%s;" % bgcolor)
      fn.write("background-image:url(%s.%s);" % (domain, gif_type))
      if placement == "mc":
        fn.write("background-position: center center; background-repeat: no-repeat;}")
      elif placement == "tile":
        fn.write("background-position: top left; background-repeat: repeat;}")
      fn.write("\n")
      fn.write("#zoom_text{position:absolute;left:0;top:0;width:1000px;z-index:10;text-align:center;font-family:Tahoma, sans-serif}")
      fn.write("#zoom_text div{position:absolute;width:1000px}")
      fn.write("</style>\n")
      fn.write("</head>\n")

      fn.write("<body>\n")
      self.write_zoom_text(fn, ytmnd_info)

      if self.no_web_audio:
        fn.write("<audio src='%s.%s' loop autoplay>\n" % (domain, wav_type))
        fn.write("</body>\n")
      else:
        fn.write("</body>\n")
        fn.write("<script>var url = '%s.%s'</script>\n" % (domain, wav_type))
        fn.write("<script src='ytmnd.js'></script>\n")
        fn.write("<script type='application/json'>\n")
        fn.write(json.dumps(ytmnd_info, sort_keys=True, indent=4) + "\n")
        fn.write("</script>\n")
      fn.write("</html>")

  def write_zoom_text(self, fn, ytmnd_info):
    if 'zoom_text' not in ytmnd_info['site']:
      return

    zoom_text = ytmnd_info['site']['zoom_text']

    fn.write('<div id="zoom_text">')

    offset = 100
    if "line_3" in zoom_text and len(zoom_text["line_3"]) > 0:
      self.write_zoom_layers(fn, zoom_text['line_3'], offset, 269)
      offset += 21
    if "line_2" in zoom_text and len(zoom_text["line_2"]) > 0:
      self.write_zoom_layers(fn, zoom_text['line_2'], offset, 135)
      offset += 21
    if "line_1" in zoom_text and len(zoom_text["line_1"]) > 0:
      self.write_zoom_layers(fn, zoom_text['line_1'], offset, 1)

    fn.write('</div>')

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

      fn.write("<div style='z-index: %d; left: %dpx; top: %dpx; color: rgb(%d, %d, %d); font-size: %dpt;'>%s</div>"
        % (z_index, row_left, row_top, color, color, color, font_size, text))

  def copy_ytmnd_js(self):
    if not os.path.isfile("ytmnd.js"):
      parent_js = os.path.join("..", "ytmnd.js")
      if os.path.isfile(parent_js):
        subprocess.run(["cp", parent_js, "."])

  def parse_json(self, ytmnd_info):
    domain = ytmnd_info['site']['domain']
    bgcolor = ytmnd_info['site']['background']['color']
    title = ytmnd_info['site']['description']
    placement = ytmnd_info['site']['foreground']['placement']

    gif_type = ytmnd_info['site']['foreground']['url'].split(".")[-1]
    wav_type = ytmnd_info['site']['sound']['type']
    zoom_text = ytmnd_info['site']['zoom_text']
    keywords = ytmnd_info['site']['keywords']
    username = ytmnd_info['site']['user']['user_name']
    sound_origin = ytmnd_info['site']['sound_origin']
    image_origin = ytmnd_info['site']['fg_image_origin']
    work_safe = ytmnd_info['site']['work_safe']

    if len(zoom_text['line_1']) == 0:
      zoom_text = ""

    if 'alternates' in ytmnd_info['site']['sound']:
      key = list(ytmnd_info['site']['sound']['alternates'].keys())[0]
      value = ytmnd_info['site']['sound']['alternates'][key]
      if value['file_type'] != 'swf':
        wav_type = ytmnd_info['site']['sound']['file_type']

    simplified_info = {
      'domain': domain,
      'title': title,
      'username': username,
      'work_safe': work_safe,
      'bgcolor': bgcolor,
      'placement': placement,
      'zoom_text': zoom_text,
      'image': domain + "." + gif_type,
      'sound': domain + "." + wav_type,
      'image_type': gif_type,
      'sound_type': wav_type,
      'image_origin': image_origin,
      'sound_origin': sound_origin,
    }

    return simplified_info

  def write_json(self, domain, data):
    with open(domain + '.json', 'w', encoding='utf-8') as fn:
      fn.write(json.dumps(data))

if __name__ == '__main__':

  parser = OptionParser()

  parser.add_option("-u", "--user", action="store_true")
  parser.add_option("-m", "--media-only", action="store_true")
  parser.add_option("-f", "--html-only", action="store_true")
  parser.add_option("-j", "--json-only", action="store_true")
  parser.add_option("-w", "--no-web-audio", action="store_true")
  parser.add_option("-p", "--print-json", action="store_true")
  parser.add_option("-s", "--sleep", action="store", type="int", dest="sleep", default=5)

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
    name = args[0].replace("http://","").replace(".ytmnsfw.com","").replace(".ytmnd.com","").replace("/","")
    ytmnd.fetch_ytmnd(name)
