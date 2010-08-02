


def index():
    form = SQLFORM(db.image)

    # if form.accepts(request.vars,session): response.flash='image uploaded'

    if FORM.accepts(form, request.vars, session):
        response.flash = 'image uploaded'
    return dict(form=form)


