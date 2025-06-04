import os
import down
import ren
import anal
import config

def run(a, b, c):
    if not os.path.exists(config.general.cache_file):
        with open(config.general.cache_file, 'w') as f:
            f.write('{}')
    down.run(a, b, c)
    anal.run()
    ren.run() 

# run(3932620, 3933050) 