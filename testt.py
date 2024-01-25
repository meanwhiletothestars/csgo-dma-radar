import random
import os
import re
import math
import time
import json


def main():
    with open('csgo.min.json', 'r') as f:
        data = json.load(f)
    signatures = {key: hex(value) for key, value in data['signatures'].items()}
    netvars = {key: hex(value) for key, value in data['netvars'].items()}
 
    dwLocalPlayer = int(signatures['dwLocalPlayer'], 16)
    m_vecOrigin = int(netvars['m_vecOrigin'], 16)
    print(f'{dwLocalPlayer},{m_vecOrigin}')
if __name__ == "__main__":
    main()