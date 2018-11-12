import requests
import csv
import os
import urllib
import json
from string import Template

PINKKAS=[160, 161, 162, 163, 164]

INFO_TEMPLATE = Template("""
  <b>$title</b><br />
  $body
""")

BACK_TEMPLATE = Template("""
  <b>$scientificName</b><br />
  <b>$finnishName</b><br />
  <b>$pinkka</b><br />
  <br />
  <button id="showMore" onclick="document.getElementById('moreInfo').style.display = 'block'">Lisatietoja</button><br /><br />
  <div id="moreInfo" style="display: none;">$info</div>
""")

FRONT_TEMPLATE = Template("""
  <img id="plantImage" style="max-height: 400px" />
  <br />
  <button onclick="changeImage(-1)" id="previousButton">Edellinen</button>
  <button onclick="changeImage(1)" id="nextButton">Seuraava</button>
  <script>
    var images = $imageArray;
    var selected = 0;

    function changeImage(val) {
      selected = selected + val;
      document.getElementById("plantImage").src = images[selected];

      if (selected === 0) {
        document.getElementById("previousButton").disabled = true;
      } else {
        document.getElementById("previousButton").disabled = false;
      }

      if (selected === images.length - 1) {
        document.getElementById("nextButton").disabled = true;
      } else {
        document.getElementById("nextButton").disabled = false;
      }
    }

    function shuffle(a) {
      var j, x, i;
      for (i = a.length - 1; i > 0; i--) {
        j = Math.floor(Math.random() * (i + 1));
        x = a[i];
        a[i] = a[j];
        a[j] = x;
      }
      return a;
    }

    window.addEventListener("load", function() {
      shuffle(images);
      changeImage(0);
    })
  </script>
""")

with open('cards.csv', 'wb') as f:
  writer = csv.writer(f)

  for pinkka in PINKKAS:
    url = "https://fmnh-ws-prod.it.helsinki.fi/pinkka/api/subpinkkas/" + str(pinkka)
    pinkkaData = requests.get(url).json()
    cards = pinkkaData["speciesCards"]

    for card in cards:
      cardData = requests.get("https://fmnh-ws-prod.it.helsinki.fi/pinkka/api/speciescards/" + str(card["id"])).json()
      imageUrls = [image["urls"]["large"] for image in cardData["images"]]
      front = FRONT_TEMPLATE.substitute(imageArray=json.dumps(imageUrls))

      finnishName = card['vernacularName']['fi'] if card['vernacularName'] and 'fi' in card['vernacularName'] else ""
      info = ''.join([INFO_TEMPLATE.substitute(title=description["title"]["fi"], body=description["body"]["fi"]) for description in cardData["description"] if "fi" in description["title"] and "fi" in description["body"]])
      back = BACK_TEMPLATE.substitute(scientificName=card['scientificName'], finnishName=finnishName, pinkka=pinkkaData["name"]["fi"], info=info)

      row = [s.encode("utf-8") for s in [front, back]]
      writer.writerow(row)

