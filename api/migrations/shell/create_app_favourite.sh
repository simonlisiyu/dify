#!/bin/bash
# 2. create_app_favourite.sh installed_app market
# docker exec -it hz-starry-02-db-1 sh /home/shell/create_app_favourite.sh
## create favourite
psql --command "CREATE TABLE public.installed_apps_favourite (\
	id uuid DEFAULT uuid_generate_v4() NOT NULL,\
	account_id uuid NOT NULL,\
	installed_app_id uuid NOT NULL,\
	is_pinned bool DEFAULT false NOT NULL,\
	last_used_at timestamp NULL,\
	created_at timestamp DEFAULT CURRENT_TIMESTAMP(0) NOT NULL,\
	app_id uuid NOT NULL,\
	CONSTRAINT faverite_app_pkey PRIMARY KEY (id),\
	CONSTRAINT unique_faverite_app UNIQUE (account_id, installed_app_id)\
);\
CREATE INDEX installed_apps_faverite_account_id_idx ON public.installed_apps_favourite USING btree (account_id);" "host=127.0.0.1 hostaddr=127.0.0.1 port=5432 user=postgres password=starryai123456 dbname=starry"