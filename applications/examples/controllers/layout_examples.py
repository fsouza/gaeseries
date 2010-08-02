


def civilized():
    response.menu = [['civilized', True, URL(r=request, f='civilized'
                     )], ['slick', False, URL(r=request, f='slick')],
                     ['basic', False, URL(r=request, f='basic')]]
    response.flash = 'you clicked on civilized'
    return dict(message='you clicked on civilized')


def slick():
    response.menu = [['civilized', False, URL(r=request, f='civilized'
                     )], ['slick', True, URL(r=request, f='slick')],
                     ['basic', False, URL(r=request, f='basic')]]
    response.flash = 'you clicked on slick'
    return dict(message='you clicked on slick')


def basic():
    response.menu = [['civilized', False, URL(r=request, f='civilized'
                     )], ['slick', False, URL(r=request, f='slick')],
                     ['basic', True, URL(r=request, f='basic')]]
    response.flash = 'you clicked on basic'
    return dict(message='you clicked on basic')


