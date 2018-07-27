# coding=utf-8
import jinja2

env = jinja2.Environment(autoescape=False)
env.filters['append_spaces'] = lambda s, n: s and ('\n' + ' ' * n).join(s.splitlines())

CONF_TMPL = env.from_string(u'''\
user nginx;
worker_processes  1;

error_log  /var/log/nginx-error.log;
pid              /var/run/nginx.pid;

events {
    worker_connections  1024;
}

http {
	charset  utf-8;

	server_names_hash_bucket_size 128;
	client_header_buffer_size      4k;
	large_client_header_buffers 4 32k;
	client_max_body_size         300m;

	sendfile    on;
	tcp_nopush  on;
	tcp_nodelay on;
	   
	keepalive_timeout 60;
	   
	client_body_buffer_size  512k;
	 
	proxy_connect_timeout         5;
	proxy_read_timeout           60;
	proxy_send_timeout            5;
	proxy_buffer_size           16k;
	proxy_buffers             4 64k;
	proxy_busy_buffers_size    128k;
	proxy_temp_file_write_size 128k;
	   
	# gzip on;
	# gzip_min_length  1k;
	# gzip_buffers     4 16k;
	# gzip_http_version 1.1;
	# gzip_comp_level 2;
	# gzip_types text/plain application/x-javascript text/css application/xml;
	# gzip_vary on;

	server_tokens off;	  

	log_format  main  '$http_x_forwarded_for - $remote_user [$time_local] "$request" '
                '$status $body_bytes_sent "$http_referer" '
                '"$http_user_agent" "$upstream_cache_status" $remote_addr';
	
	
	map $http_upgrade $connection_upgrade {
        default upgrade;
        ''      close;
    }
	    
    {% for host in config.hosts.values() %}
    {% set cache_name = 'cache-' + host.normalized_name %}
    
	# 缓存配置1:2表示第一级目录1个字符，第二级目录2个字符；cache1:20m表示每个缓存区域20M空间；
	# 3d表示3天后缓存过期
	proxy_cache_path  {{config.cache_path}}/{{cache_name}}  levels=1:2 keys_zone={{cache_name}}:20m inactive={{host.cache_expire}} max_size={{host.cache_size_limit}};			   

    server {
        resolver 114.114.114.114;
        listen      80;
        server_name {{host.name}};
         
        # cache purge 
		# location ~ /purge(/.*) {
		# 	allow all;
		# 	proxy_cache_purge cache1 $host$1$is_args$args;
		# 	}

		add_header  X-Qequest-Time '$request_time';
		
		location \ {
				proxy_pass http://$host:$server_port;
				proxy_http_version 1.1;
				proxy_set_header Upgrade $http_upgrade;
				proxy_set_header Connection "upgrade";
		}
		
		# proxy config
        location ~ \.({{ host.extensions_reg }}) {
                proxy_pass http://$host:$server_port;
                # proxy_next_upstream http_502 http_504 error timeout invalid_header;
                proxy_set_header Host $host;
                proxy_set_header User-Agent $http_user_agent;
                proxy_set_header Accept-Encoding "";
                proxy_set_header X-Real-IP $remote_addr; 
                proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for; 
                proxy_set_header X-Forwarded-Proto $scheme;

				proxy_http_version 1.1;
				proxy_set_header Upgrade $http_upgrade;
				proxy_set_header Connection "upgrade";

                add_header Nginx-Cache $upstream_cache_status;
                proxy_cache                    {{cache_name}};
                proxy_cache_key            {{host.cache_key}};
                proxy_cache_valid                 200 304 30m;
                expires                 {{host.cache_expire}};
        }
	}
	{% endfor %}
}
''')


def get_nginx_conf(config):
    return CONF_TMPL.render(config=config)
