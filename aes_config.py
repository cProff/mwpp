import requests
from jsbeautifier import beautify as bf
from my_web import search_bounds
import subprocess
from binascii import unhexlify
import time


import random, os, string #for tempfiles
import js2py

BAD_PART = '''{
        a: this.options.partner_id,
        b: this.options.domain_id,
        c: e._mw_adb,
        e: this.options.video_token,
        f: navigator.userAgent
    }'''


class Tempfile():
    def __init__(self):
        self.path = ''.join(random.choices(string.ascii_uppercase + string.digits, k=20))
    
    def __enter__(self):
        self.file = open(self.path, 'w')
        return self
        
    def __exit__(self, type, value, traceback):
        try:
            self.file.close()
        except:
            pass
        os.remove(self.path)


def node_run(code):
    with Tempfile() as f:
        f.file.write(code)
        f.file.close()
        process = subprocess.Popen(['node', f.path], stdout=subprocess.PIPE)
        return process.communicate()
        

class TaskTimer():
    __level__ = 0
    def __init__(self, runText, stopText):
        self.runText = runText
        self.stopText = stopText
    def __enter__(self):
        self.t = time.time()
        print('{}{}'.format('\t'*TaskTimer.__level__, self.runText))
        TaskTimer.__level__ += 1
    def __exit__(self, a, b, c):
        TaskTimer.__level__ -= 1
        print('{}{}. It takes {:.3} sec'.format('\t'*TaskTimer.__level__, self.stopText, time.time()-self.t))


def find_func_start(code, pos):
    level = 1
    while(pos > 0 and level != 0):
        if(code[pos] == '}'):
            level+=1
        elif(code[pos] == '{'):
            level-=1
        pos-=1
    return pos+2


def get_aes_config(url):
    with TaskTimer('Corruting AES keys...', 'AES keys are corrupted'):
        #~~~ download js code
        t1 = time.time()
        with TaskTimer('Loading JS code...', 'JS code loaded'):
            jsResponse = requests.get(url)
        jsCode = jsResponse.text
        #~~~ find getVideoManifest function code
        ajaxPos = jsCode.find('t.ajax')
        funcStart = find_func_start(jsCode, ajaxPos)
        funcText = jsCode[funcStart:ajaxPos]
        with TaskTimer('Beautifying JS code...', 'JS code is beauty :)'):
            funcText = bf(str(funcText)+'\n')
        #~~~ hacking(parsing) func text to find aes key and iv'
        implementCode = search_bounds(funcText, False, 'CryptoJS').replace(BAD_PART, '0').replace('JSON.stringify', '')
        #~~~ delete unused last string:
        implementCode = implementCode[:implementCode.rfind(',')] + ';'
        lastVars = [line.split('=')[0].strip() for line in implementCode[implementCode.rfind('var')+3:].split('\n')] # contains names of variables
        initCode = 'function() { var e = Object.create(null);'
        returnCode = '\nreturn [{}, {}];'.format(*lastVars)+'}'
        with TaskTimer('Compilation of JS code...', 'JS code was transformed to python code'):
            res = js2py.eval_js(initCode + implementCode + returnCode)()
        keyData = res[0]
        ivData = res[1]

        #~~~ change default aes values and return results
        AES_DEFAULT_KEY = unhexlify(keyData)
        AES_DEFAULT_IV = unhexlify(ivData)
    return AES_DEFAULT_KEY, AES_DEFAULT_IV

if __name__ == "__main__":
    get_aes_config('https://streamguard.cc/assets/video-9f4475bcc7bc5cd42689a6fca30f9c3847742f11a167070176ab47a913d62579.js')