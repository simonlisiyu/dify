# 1. update_app.sh (new&update)
# docker exec -it hz-starry-02-db-1 sh /home/shell/update_app.sh
## alter app
psql --command "ALTER TABLE public.apps ALTER COLUMN icon TYPE varchar(40960) USING icon::varchar(40960); " "host=127.0.0.1 hostaddr=127.0.0.1 port=5432 user=postgres password=starryai123456 dbname=starry"
psql --command "ALTER TABLE public.tool_workflow_providers ALTER COLUMN icon TYPE varchar(40960) USING icon::varchar(40960); " "host=127.0.0.1 hostaddr=127.0.0.1 port=5432 user=postgres password=starryai123456 dbname=starry"
psql --command "ALTER TABLE public.sites ALTER COLUMN icon TYPE varchar(40960) USING icon::varchar(40960); " "host=127.0.0.1 hostaddr=127.0.0.1 port=5432 user=postgres password=starryai123456 dbname=starry"
