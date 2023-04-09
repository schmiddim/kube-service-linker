import json
import logging as log
from modules.kube import *
from modules.logic import analyze_requirements

log.getLogger().setLevel(log.INFO)

with open('tests/fixtures/post.json') as f:
    data = json.load(f)
    analyze_requirements(data)
