#!/bin/bash

# 数据跑批相关sql更新
# 1. create_installed_app_batch_run.sh (new&update)
# docker exec -it hz-starry-02-db-1 sh /home/shell/create_installed_app_batch_run.sh
## create create_installed_app_batch_run
psql --command "ALTER TABLE IF EXISTS public.accounts ADD COLUMN dmc_user_id character varying(255) DEFAULT '';" "host=127.0.0.1 hostaddr=127.0.0.1 port=5432 user=postgres password=starryai123456 dbname=starry"
psql --command "ALTER TABLE IF EXISTS public.accounts ADD COLUMN dmc_user_name character varying(255) DEFAULT '';" "host=127.0.0.1 hostaddr=127.0.0.1 port=5432 user=postgres password=starryai123456 dbname=starry"