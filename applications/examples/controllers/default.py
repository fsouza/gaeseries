
response.title = 'web2py Enterprise Web Framework'
response.keywords = 'web2py, Python, Enterprise Web Framework'
response.description = 'web2py Enterprise Web Framework'

session.forget()


def index():
    return response.render(dict())

def what():
    return response.render(dict())

def who():
    return dict()

def download():
    return response.render(dict())

def docs():
    return response.render(dict())

def support():
    return dict()

def api():
    return dict()

def dal():
    return response.render(dict())

def license():
    return response.render(dict())

def version():
   return request.env.web2py_version

def security():
   return response.render(dict())

def examples():
    return response.render(dict())

def tools():
    return response.render(dict())

def cron():
   return response.render(dict())

def changelog():
    log=[]
    code=False
    for line in open('README','r').readlines():
        if line.strip()=='': continue
        elif line[0]=='#':
            log.append(TABLE())
            log.append(H2(line[1:]))
            code=False        
        elif line[0] in [' ','\t']:
            if not code:
                code=PRE()
                log[-2].append(TR(TD(code)))
            code.append(line)
        else:
            log[-2].append(TR(TD('> '+line)))
            code=False
    log.reverse()
    log=log[-2:]+log[:-2]
    return dict(changelog=DIV(*log))
    
