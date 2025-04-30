## 1. update_recommended_app.sh (new&update)
## docker exec -it hz-starry-02-db-1 sh /home/shell/update_recommended_app.sh
### alter recommended_app
#psql --command "ALTER TABLE public.recommended_apps \
#  ADD COLUMN \"name\" varchar(255) NOT NULL, \
#  ADD COLUMN \"mode\" varchar(255) NOT NULL, \
#  ADD COLUMN icon varchar(255) NULL, \
#  ADD COLUMN icon_background varchar(255) NULL, \
#  ADD COLUMN export_data text NOT NULL; " "host=127.0.0.1 hostaddr=127.0.0.1 port=5432 user=postgres password=starryai123456 dbname=starry"
#
### create directory
#psql --command "CREATE TABLE public.directory (	id uuid DEFAULT uuid_generate_v4() NOT NULL,	tenant_id uuid NOT NULL,	"name" varchar(255) NOT NULL,	"type" varchar(16) NOT NULL,	"level" int4 DEFAULT 0 NULL,	parent_id uuid NULL,	last_used_at timestamp NULL,	created_at timestamp DEFAULT CURRENT_TIMESTAMP(0) NOT NULL,	CONSTRAINT directory_pkey PRIMARY KEY (id),	CONSTRAINT unique_directory_name UNIQUE (name, parent_id),	CONSTRAINT directory_parent_id_fkey FOREIGN KEY (parent_id) REFERENCES public.directory(id));" "host=127.0.0.1 hostaddr=127.0.0.1 port=5432 user=postgres password=starryai123456 dbname=starry"
