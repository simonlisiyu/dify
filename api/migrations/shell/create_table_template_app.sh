#!/bin/bash

# 1. update_template_app.sh (new&update)
# docker exec -it hz-starry-02-db-1 sh /home/shell/create_table_template_app.sh
## create template_apps
psql --command "CREATE TABLE public.template_apps ( \
	id uuid DEFAULT uuid_generate_v4() NOT NULL,	\
	tenant_id uuid NOT NULL,	\
	\"name\" varchar(255) NOT NULL, \
	\"mode\" varchar(16) NOT NULL,	\
	category varchar(255) NOT NULL,	\
	description varchar(4096) NOT NULL, \
	icon varchar(255) NOT NULL, \
  icon_background varchar(255) NOT NULL, \
  export_data text NOT NULL, \
	copyright varchar(255) NULL, \
  privacy_policy varchar(255) NULL, \
  "position" int4 NOT NULL, \
  is_listed bool NOT NULL, \
  install_count int4 NOT NULL, \
  "language" varchar(255) DEFAULT 'zh-Hans'::character varying NOT NULL, \
  created_at timestamp DEFAULT CURRENT_TIMESTAMP(0) NOT NULL, \
  updated_at timestamp DEFAULT CURRENT_TIMESTAMP(0) NOT NULL, \
	CONSTRAINT template_apps_pkey PRIMARY KEY (id),	\
	CONSTRAINT unique_tenant_name UNIQUE (tenant_id, name));" "host=127.0.0.1 hostaddr=127.0.0.1 port=5432 user=postgres password=starryai123456 dbname=starry"

psql --command "CREATE INDEX template_app_is_listed_idx ON public.template_apps \
  USING btree (is_listed, language);" "host=127.0.0.1 hostaddr=127.0.0.1 port=5432 user=postgres password=starryai123456 dbname=starry"
