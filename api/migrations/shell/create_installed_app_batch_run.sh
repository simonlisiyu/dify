#!/bin/bash

# 数据跑批相关sql更新
# 1. create_installed_app_batch_run.sh (new&update)
# docker exec -it hz-starry-02-db-1 sh /home/shell/create_installed_app_batch_run.sh
## create create_installed_app_batch_run
psql --command "CREATE TABLE IF NOT EXISTS public.installed_app_batch_run
(
    id uuid NOT NULL DEFAULT uuid_generate_v4(),
    tenant_id uuid NOT NULL,
    app_id uuid NOT NULL,
    created_by uuid,
    meta text COLLATE pg_catalog."default",
    created_at timestamp without time zone NOT NULL DEFAULT CURRENT_TIMESTAMP(0),
    CONSTRAINT installed_app_batch_run_pkey PRIMARY KEY (id),
    CONSTRAINT installed_app_batch_run_app_idx UNIQUE (tenant_id, app_id)
);" "host=127.0.0.1 hostaddr=127.0.0.1 port=5432 user=postgres password=starryai123456 dbname=starry"

psql --command "CREATE INDEX IF NOT EXISTS installed_app_batch_run_tenant_id_idx
    ON public.installed_app_batch_run USING btree(tenant_id ASC NULLS LAST)" "host=127.0.0.1 hostaddr=127.0.0.1 port=5432 user=postgres password=starryai123456 dbname=starry"

psql --command "CREATE TABLE IF NOT EXISTS public.installed_app_batch_run_record
(
    id uuid NOT NULL DEFAULT uuid_generate_v4(),
    tenant_id uuid NOT NULL,
    app_id uuid NOT NULL,
    app_name character varying(255) COLLATE pg_catalog."default" NOT NULL,
    from_pro character varying(255) COLLATE pg_catalog."default" NOT NULL,
    input_tb_id character varying(255) COLLATE pg_catalog."default" NOT NULL,
    input_tb_name character varying(255) COLLATE pg_catalog."default" NOT NULL,
    output_tb_id character varying(255) COLLATE pg_catalog."default" NOT NULL,
    output_tb_name character varying(255) COLLATE pg_catalog."default" NOT NULL,
    created_at timestamp without time zone NOT NULL DEFAULT CURRENT_TIMESTAMP(0),
    updated_at timestamp without time zone NOT NULL DEFAULT CURRENT_TIMESTAMP(0),
    created_by uuid,
    all_data_count integer NOT NULL DEFAULT 0,
    success_data_count integer NOT NULL DEFAULT 0,
    fail_data_count integer NOT NULL DEFAULT 0,
    meta text COLLATE pg_catalog."default",
    status integer DEFAULT 0,
    error_msg text COLLATE pg_catalog."default",
    folder_from character varying(255) COLLATE pg_catalog."default" NOT NULL DEFAULT ''::character varying,
    CONSTRAINT installed_app_batch_run_record_pkey PRIMARY KEY (id)
);" "host=127.0.0.1 hostaddr=127.0.0.1 port=5432 user=postgres password=starryai123456 dbname=starry"

psql --command "COMMENT ON COLUMN public.installed_app_batch_run_record.status
    IS '状态0新建1进行中2成功3失败';" "host=127.0.0.1 hostaddr=127.0.0.1 port=5432 user=postgres password=starryai123456 dbname=starry"

psql --command "CREATE INDEX IF NOT EXISTS installed_app_batch_run_record_tenant_id_idx
    ON public.installed_app_batch_run_record USING btree
    (tenant_id ASC NULLS LAST);" "host=127.0.0.1 hostaddr=127.0.0.1 port=5432 user=postgres password=starryai123456 dbname=starry"
