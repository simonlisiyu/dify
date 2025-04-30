#!/bin/bash

# no need
# 0. init_tenant_account.sh (new)
```
curl -XPOST 'http://127.0.0.1/console/api/setup' \
  -H 'content-type: application/json' \
  -d '{"email":"superadmin","name":"超级管理员","password":"haizhi1234"}'
```
# docker exec -it hz-starry-02-db-1 sh /home/shell/init_tenant_account.sh
## tenant
psql --command "INSERT INTO public.tenants (id,"name",encrypt_public_key,plan,status,created_at,updated_at,custom_config) VALUES	 ('44586050-c296-48a6-af06-a3d75016e3e8'::uuid,'haizhi''s Workspace','-----BEGIN PUBLIC KEY-----MIIBIjANBgkqhkiG9w0BAQEFAAOCAQ8AMIIBCgKCAQEA9p2gXDJfiuD0jm7MCVqJpHKNCARH+FZEpKMs/gJoQu1UX7bd8ZoOQ5AWJrUtmEqYBojpz2OHCPaAa1cN5YzBRvzWChutdxbvCzwcEMbzUXysHLsjvZ3iDqVcwwxMJqhisdxdI0lYi1Tzv4sWfUiJH0/dbkMIqd4WHkBIuapksc36UFMnEalKrhpI9UUTAgvLE2nN3hOw9IXOwCDrWDkOMUa+v3hqKv2Jig7TVHQw/cr/nKShAbPq5k2C8MaXK/ZsF8kpY1h8FQzdQ8f7ZXFqNZIFqsWOhqa8KwT1O+MaXCiv819jLCI7S+Y6lQNP+r/j24zDMpKr9POcy7W7HhjDIQIDAQAB-----END PUBLIC KEY-----','basic','normal','2024-10-01 07:13:11','2024-10-01 07:13:11',NULL);" "host=127.0.0.1 hostaddr=127.0.0.1 port=5432 user=postgres password=starryai123456 dbname=starry"

## account
psql --command "INSERT INTO public.accounts (id,"name",email,"password",password_salt,avatar,interface_language,interface_theme,timezone,last_login_at,last_login_ip,status,initialized_at,created_at,updated_at,last_active_at) VALUES	 ('5a1c8a51-1b06-473d-b4f0-f894d3b96f2f'::uuid,'超级管理员','superadmin','NjRlZGZjNDNjMmY2NDRjY2U5YjQxNWJmOTQ1M2M3NTVlOWViYWQ0ODUyZTc2YWFmNTBmMDNiNDY0YTM0NjdkZA==','WZiInUrb39Yyk1Q3H3E85g==',NULL,'zh-Hans','light','Asia/Shanghai',NULL,NULL,'active','2024-10-01 12:21:28.683993','2024-10-01 12:21:29','2024-10-01 12:21:29','2024-10-01 01:57:50.092072');" "host=127.0.0.1 hostaddr=127.0.0.1 port=5432 user=postgres password=starryai123456 dbname=starry"

## role
psql --command "INSERT INTO public.tenant_account_joins (id,tenant_id,account_id,"role",invited_by,created_at,updated_at,"current") VALUES	 ('ae1cefeb-908b-4c3c-a9d6-05203386c8fb'::uuid,'44586050-c296-48a6-af06-a3d75016e3e8'::uuid,'5a1c8a51-1b06-473d-b4f0-f894d3b96f2f'::uuid,'owner',NULL,'2024-10-01 12:21:29','2024-10-01 12:21:29',true);" "host=127.0.0.1 hostaddr=127.0.0.1 port=5432 user=postgres password=starryai123456 dbname=starry"
