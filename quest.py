import json
class questdt:
  title = "A quest"
  desc = "A basic Expedition"
  adventurers = []
  reward = ""
  requirements = ""
  img = ""
  def __init__(self, title):
    self.title = title
  
  def toJson(self):
          return json.dumps(self, default=lambda o: o.__dict__)
  
  