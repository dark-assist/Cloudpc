pipelines:
  default:
    - step:
        name: Run Python Script
        image: python:3.10
        size: 2x
        script:
          - pip install telebot pymongo aiohttp
          - git clone https://github.com/kingfather09090/--SOULCRACKS
          - ls
          - mv soul.py -- ./--SOULCRACKS/soul.py
          - cd ./--SOULCRACKS
          - lscpu
          - chmod +x *
          - python3 soul.py
