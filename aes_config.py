import requests
from jsbeautifier import beautify
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
        


def get_aes_config(url):
    #~~~ download js code
    print('Corrupting AES keys...')
    t1 = time.time()
    
    jsResponse = requests.get(url)
    jsCode = beautify(jsResponse.text)
    #~~~ find getVideoManifest function code
    funcText = search_bounds(jsCode, 
                        'getVideoManifests: function() {', 'onGetManifestSuccess') 
    #~~~ hacking(parsing) func text to find aes key and iv'
    ## was deleted on 08.11
    # implementCode = 'r=[' + search_bounds(funcText, 'r = [', 'l = ').rstrip('\n ,')+';' 
    # implementCode1 = 'function add(){var e = Object.create(null);' + implementCode+'return l;}'
    # implementCode2 = 'function add(){var e = Object.create(null);' + implementCode+'return c;}'
    # a = js2py.eval_js(implementCode1)
    # s = js2py.eval_js(implementCode2)
    # keyData = s()
    # ivData = a()
    ## was added on 08.11
    ## was deleted on 14.11
    # implementCode = search_bounds(funcText, False, 'u =').replace(BAD_PART, 'var').strip().rstrip(',') + ';'
    # implementCode1 = 'var e = Object.create(null);' + implementCode+'console.log(l);'
    # implementCode2 = 'var e = Object.create(null);' + implementCode+'console.log(c);'
    # out, err = node_run(implementCode1)
    # keyData = out.strip()
    # out, err = node_run(implementCode2)
    # ivData = out.strip()
    ## was added on 14.11
    implementCode = search_bounds(funcText, False, 'CryptoJS').replace(BAD_PART, '0').replace('JSON.stringify', '')
    #    #~~~ delete unused last string:
    implementCode = implementCode[:implementCode.rfind(',')] + ';'
    lastVars = [line.split('=')[0].strip() for line in implementCode[implementCode.rfind('var')+3:].split('\n')] # contains names of variables
    # input(str(lastVars))
    initCode = 'function() { var e = Object.create(null);'
    returnCode = '\nreturn [{}, {}];'.format(*lastVars)+'}'
    print('JS decoding...')
    res = js2py.eval_js(initCode + implementCode + returnCode)()
    print(res)
    print('JS compilation ended.')
    keyData = res[0]
    ivData = res[1]
    
    #~~~ change default aes values and return results
    AES_DEFAULT_KEY = unhexlify(keyData)
    AES_DEFAULT_IV = unhexlify(ivData)
    print('AES keys corrupted. It takes {:.2} sec'.format(time.time()-t1))
    return AES_DEFAULT_KEY, AES_DEFAULT_IV
