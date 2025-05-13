import os
import down
import ren

def run(a, b, c):
    if not os.path.exists('cache.json'):
        with open('cache.json', 'w') as f:
            f.write('{}')
    down.run(a, b, c)
    os.system('./bin')
    ren.run()

# run(3932620, 3933050)