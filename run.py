import os
import down
import ren
import anal

def run(a, b, c):
    if not os.path.exists('cache.json'):
        with open('cache.json', 'w') as f:
            f.write('{}')
    down.run(a, b, c)
    anal.run()
    ren.run() 

# run(3932620, 3933050) 