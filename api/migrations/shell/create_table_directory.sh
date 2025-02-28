#!/bin/bash

# 1. create_table_directory.sh (new&update)
# docker exec -it hz-starry-02-db-1 sh /home/shell/create_table_directory.sh
## create directory
psql --command "CREATE TABLE public.directory (	id uuid DEFAULT uuid_generate_v4() NOT NULL,	tenant_id uuid NOT NULL,	"name" varchar(255) NOT NULL,	"type" varchar(16) NOT NULL,	"level" int4 DEFAULT 0 NULL,	parent_id uuid NULL,	last_used_at timestamp NULL,	created_at timestamp DEFAULT CURRENT_TIMESTAMP(0) NOT NULL,	CONSTRAINT directory_pkey PRIMARY KEY (id),	CONSTRAINT unique_directory_name UNIQUE (name, parent_id),	CONSTRAINT directory_parent_id_fkey FOREIGN KEY (parent_id) REFERENCES public.directory(id));" "host=127.0.0.1 hostaddr=127.0.0.1 port=5432 user=postgres password=starryai123456 dbname=starry"

## insert default directory (new&update)
psql --command "INSERT INTO public.directory (id,tenant_id,"name","type","level",parent_id,last_used_at,created_at) VALUES	 ('bb7da09d-09b8-419a-b6fc-8e44a4877100'::uuid,'602d2a42-a882-4ca4-b612-445b5758097c'::uuid,'根目录','app',0,NULL,'2024-10-01 14:53:34','2024-10-01 14:53:34'),	 ('bb7da09d-09b8-419a-b6fc-8e44a4877300'::uuid,'602d2a42-a882-4ca4-b612-445b5758097c'::uuid,'根目录','tool',0,NULL,'2024-10-01 14:54:03','2024-10-01 14:54:03'),	 ('bb7da09d-09b8-419a-b6fc-8e44a4877200'::uuid,'602d2a42-a882-4ca4-b612-445b5758097c'::uuid,'根目录','knowledge',0,NULL,'2024-10-01 14:54:03','2024-10-01 14:54:03'),	 ('bb7da09d-09b8-419a-b6fc-8e44a4877101'::uuid,'602d2a42-a882-4ca4-b612-445b5758097c'::uuid,'根目录','app',NULL,'bb7da09d-09b8-419a-b6fc-8e44a4877100'::uuid,'2024-10-01 14:53:34','2024-10-01 14:53:34'),	 ('bb7da09d-09b8-419a-b6fc-8e44a4877301'::uuid,'602d2a42-a882-4ca4-b612-445b5758097c'::uuid,'根目录','tool',NULL,'bb7da09d-09b8-419a-b6fc-8e44a4877300'::uuid,'2024-10-01 14:54:03','2024-10-01 14:54:03'),	 ('bb7da09d-09b8-419a-b6fc-8e44a4877201'::uuid,'602d2a42-a882-4ca4-b612-445b5758097c'::uuid,'根目录','knowledge',NULL,'bb7da09d-09b8-419a-b6fc-8e44a4877200'::uuid,'2024-10-01 14:54:03','2024-10-01 14:54:03');" "host=127.0.0.1 hostaddr=127.0.0.1 port=5432 user=postgres password=starryai123456 dbname=starry"

## create directory binding
psql --command "CREATE TABLE public.directory_bindings (	id uuid DEFAULT uuid_generate_v4() NOT NULL,	tenant_id uuid NULL,	directory_id uuid NULL,	target_id uuid NULL,	created_by uuid NOT NULL,	created_at timestamp DEFAULT CURRENT_TIMESTAMP(0) NOT NULL,	CONSTRAINT directory_binding_pkey PRIMARY KEY (id));CREATE INDEX directory_bind_id_idx ON public.directory_bindings USING btree (directory_id);CREATE INDEX directory_bind_target_id_idx ON public.directory_bindings USING btree (target_id);" "host=127.0.0.1 hostaddr=127.0.0.1 port=5432 user=postgres password=starryai123456 dbname=starry"
psql --command "CREATE INDEX directory_bind_id_idx ON directory_bindings (directory_id);" "host=127.0.0.1 hostaddr=127.0.0.1 port=5432 user=postgres password=starryai123456 dbname=starry"
psql --command "CREATE INDEX directory_bind_target_id_idx ON directory_bindings (target_id);" "host=127.0.0.1 hostaddr=127.0.0.1 port=5432 user=postgres password=starryai123456 dbname=starry"

## alter apps/dataset/tool
psql --command "ALTER TABLE public.apps ADD COLUMN account_id uuid NULL,ADD COLUMN directory_id uuid NULL;" "host=127.0.0.1 hostaddr=127.0.0.1 port=5432 user=postgres password=starryai123456 dbname=starry"
psql --command "ALTER TABLE public.datasets ADD COLUMN account_id uuid NULL,ADD COLUMN directory_id uuid NULL;" "host=127.0.0.1 hostaddr=127.0.0.1 port=5432 user=postgres password=starryai123456 dbname=starry"
psql --command "ALTER TABLE public.tool_api_providers ADD COLUMN account_id uuid NULL,ADD COLUMN directory_id uuid NULL;" "host=127.0.0.1 hostaddr=127.0.0.1 port=5432 user=postgres password=starryai123456 dbname=starry"
psql --command "ALTER TABLE public.tool_workflow_providers ADD COLUMN account_id uuid NULL,ADD COLUMN directory_id uuid NULL;" "host=127.0.0.1 hostaddr=127.0.0.1 port=5432 user=postgres password=starryai123456 dbname=starry"

## update apps/dataset/tool data
psql --command "UPDATE apps \
SET account_id = ( \
    SELECT account_id \
    FROM tenant_account_joins \
    WHERE role = 'owner' \
    LIMIT 1 \
), directory_id = 'bb7da09d-09b8-419a-b6fc-8e44a4877101' WHERE account_id IS null;	\
UPDATE datasets \
SET account_id = ( \
    SELECT account_id \
    FROM tenant_account_joins \
    WHERE role = 'owner' \
    LIMIT 1 \
), directory_id = 'bb7da09d-09b8-419a-b6fc-8e44a4877201' WHERE account_id IS null;	\
UPDATE tool_api_providers \
SET account_id = ( \
    SELECT account_id \
    FROM tenant_account_joins \
    WHERE role = 'owner' \
    LIMIT 1 \
), directory_id = 'bb7da09d-09b8-419a-b6fc-8e44a4877301' WHERE account_id IS null;	\
UPDATE tool_workflow_providers \
SET account_id = ( \
    SELECT account_id \
    FROM tenant_account_joins \
    WHERE role = 'owner' \
    LIMIT 1 \
), directory_id = 'bb7da09d-09b8-419a-b6fc-8e44a4877301' WHERE account_id IS null;" "host=127.0.0.1 hostaddr=127.0.0.1 port=5432 user=postgres password=starryai123456 dbname=starry"

## reinsert binding data
psql --command "TRUNCATE TABLE directory_bindings;" "host=127.0.0.1 hostaddr=127.0.0.1 port=5432 user=postgres password=starryai123456 dbname=starry"
psql --command "WITH id_list AS (	    SELECT id, tenant_id, account_id, directory_id	    FROM apps	) INSERT INTO directory_bindings (id, tenant_id, directory_id, target_id, created_by, created_at)	SELECT id, tenant_id, directory_id, id, account_id, CURRENT_TIMESTAMP	FROM id_list;" "host=127.0.0.1 hostaddr=127.0.0.1 port=5432 user=postgres password=starryai123456 dbname=starry"
psql --command "WITH id_list AS (	    SELECT id, tenant_id, account_id, directory_id	    FROM datasets	)	INSERT INTO directory_bindings (id, tenant_id, directory_id, target_id, created_by, created_at)	SELECT id, tenant_id, directory_id, id, account_id, CURRENT_TIMESTAMP	FROM id_list;" "host=127.0.0.1 hostaddr=127.0.0.1 port=5432 user=postgres password=starryai123456 dbname=starry"
psql --command "WITH id_list AS (	    SELECT id, tenant_id, account_id, directory_id	    FROM tool_api_providers	)	INSERT INTO directory_bindings (id, tenant_id, directory_id, target_id, created_by, created_at)	SELECT id, tenant_id, directory_id, id, account_id, CURRENT_TIMESTAMP	FROM id_list;" "host=127.0.0.1 hostaddr=127.0.0.1 port=5432 user=postgres password=starryai123456 dbname=starry"
psql --command "WITH id_list AS (	    SELECT id, tenant_id, account_id, directory_id	    FROM tool_workflow_providers	)	INSERT INTO directory_bindings (id, tenant_id, directory_id, target_id, created_by, created_at)	SELECT id, tenant_id, directory_id, id, account_id, CURRENT_TIMESTAMP	FROM id_list;" "host=127.0.0.1 hostaddr=127.0.0.1 port=5432 user=postgres password=starryai123456 dbname=starry"
