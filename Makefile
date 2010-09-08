run:
	@echo 'Running the development server...'
	@/usr/local/google_appengine/dev_appserver.py app

deploy:
	@echo 'Deploying the application'
	@/usr/local/google_appengine/appcfg.py update app
	@echo 'Done.'
