import requests
import genanki
import os
import json
import sys
from string import Template

# generated with random.randrange(1 << 30, 1 << 31)
BASE_UNIQUE_MODEL_ID = 1513242769
BASE_UNIQUE_DECK_ID = 1646188680

INFO_TEMPLATE = Template("""
  <b>$title</b><br />
  $body
""")

BACK_TEMPLATE = """
  {{FrontSide}}
  <div style="text-align: center">
    <hr id="answer">
    <b>{{ScientificName}}</b><br />
    <b>{{FinnishName}}</b><br />
    {{Pinkka}}<br />
    <br />
    <button id="showMore" onclick="document.getElementById('moreInfo').style.display = 'block'">Lisatietoja</button><br /><br />
  </div>
  <div id="moreInfo" style="display: none;">{{Info}}</div>
"""

FRONT_TEMPLATE = """
  <div style="text-align: center">
    <div style="height: 450px">
      <img id="plantImage" style="max-height: 400px;" />
    </div>
    <hr />
    <button onclick="changeImage(-1)" id="previousButton">Edellinen</button>
    <button onclick="changeImage(1)" id="nextButton">Seuraava</button>
  </div>
  <script>
    var images = {{Images}};
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
"""

class PinkkaNote(genanki.Note):
  @property
  def guid(self):
    return genanki.guid_for(self.fields[0], self.model.model_id)

if __name__ == '__main__':
  pinkkaId = int(sys.argv[1])
  filename = sys.argv[2]
  pinkkaData = requests.get("https://fmnh-ws-prod.it.helsinki.fi/pinkka/api/pinkkas/" + str(pinkkaId)).json()
  pinkkaName = pinkkaData["name"]["fi"]

  print("Found pinkka with name", pinkkaName)

  ankiModel = genanki.Model(
    BASE_UNIQUE_MODEL_ID + pinkkaId,
    'Model for ' + pinkkaName,
    fields=[
      {'name': 'ID'},
      {'name': 'ScientificName'},
      {'name': 'FinnishName'},
      {'name': 'Pinkka'},
      {'name': 'Images'},
      {'name': 'Info'},
    ],
    templates=[
      {
        'name': 'Pinkka Card',
        'qfmt': FRONT_TEMPLATE,
        'afmt': BACK_TEMPLATE,
      },
    ])

  ankiDeck = genanki.Deck(
    BASE_UNIQUE_DECK_ID + pinkkaId,
    pinkkaName
  )

  subPinkkaIds = [subPinkka["id"] for subPinkka in pinkkaData["subPinkkas"]]

  for subPinkkaId in subPinkkaIds:
    url = "https://fmnh-ws-prod.it.helsinki.fi/pinkka/api/subpinkkas/" + str(subPinkkaId)
    subPinkkaData = requests.get(url).json()
    cards = subPinkkaData["speciesCards"]
    subPinkkaName = subPinkkaData["name"]["fi"]
    print("Found sub-pinkka", subPinkkaName, "with", len(cards), "cards")

    for card in cards:
      cardData = requests.get("https://fmnh-ws-prod.it.helsinki.fi/pinkka/api/speciescards/" + str(card["id"])).json()
      imageUrls = [image["urls"]["large"] for image in cardData["images"]]
      finnishName = card['vernacularName']['fi'] if card['vernacularName'] and 'fi' in card['vernacularName'] else ""
      info = ''.join([INFO_TEMPLATE.substitute(title=description["title"]["fi"], body=description["body"]["fi"]) for description in cardData["description"] if "fi" in description["title"] and "fi" in description["body"]])
      

      note = PinkkaNote(
        model=ankiModel,
        fields=[cardData["taxonId"], card['scientificName'], finnishName, subPinkkaName, json.dumps(imageUrls), info],
        sort_field='FinnishName',
        tags=[subPinkkaName]
      )

      ankiDeck.add_note(note)

  print("Writing to file", sys.argv[2])
  genanki.Package(ankiDeck).write_to_file(sys.argv[2])

