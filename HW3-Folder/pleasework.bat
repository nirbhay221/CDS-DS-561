gcloud functions deploy python-http-function ^
--gen2 ^
--runtime=python311 ^
--region=us-east1 ^
--source=. ^
--entry-point=get_file ^
--trigger-http ^
--allow-unauthenticated ^
--memory 200MB
