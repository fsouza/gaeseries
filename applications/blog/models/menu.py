# -*- coding: utf-8 -*- 

#########################################################################
## Customize your APP title, subtitle and menus here
#########################################################################

response.title = request.application.capitalize()
response.subtitle = T('customize me!')

##########################################
## this is the main application menu
## add/remove items as required
##########################################

response.menu = [
    (T('Index'), False, URL(request.application,'default','index'), []),
    (T('Posts'), False, URL(request.application,'posts','index'), []),
    (T('New post'), False, URL(request.application,'posts','new'), []),
    ]

response.menu += [
]

##########################################
## this is here to provide shortcuts
## during development. remove in production 
##
## mind that plugins may also affect menu
##########################################
