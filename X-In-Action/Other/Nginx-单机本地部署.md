# Nginx-单机本地部署
- 参考: https://nginx.org/en/docs/windows.html


## 下载
- 访问: https://nginx.org/en/download.html
- 点击 `nginx/Windows-$version` 链接
  - 下载，如: https://nginx.org/download/nginx-1.26.2.zip
  - 解压


## 初始配置
- 进入 `./conf` 目录
  - 修改 `nginx.conf`
```conf
worker_processes        1;

events {
    worker_connections  64;
}

http {
    include       mime.types;
    default_type  application/octet-stream;

    sendfile            on;
    keepalive_timeout   65;
    #gzip  on;

    # http://localhost/  或  http://zxf68.fa:888/ 
    server {
        listen       80;            # 888
        server_name  localhost;     # zxf68.fa
        
        root  html;
        # root  D:/Install/Web/nginx-1.26.2/html/dist;

        location / {
            try_files $uri /index.html; # 支持 React 路由，否则会出错 404
        }
    }
} # http end
```


## 启动
```js
// 配置环境变量
nginx1 = D:\Install\Web\nginx-1.26.2

// 启动 (Windows 需进入到安装目录)
C:\..> cd %nginx1%
D:\..> start nginx      // 启动

// 重载和退出
D:\..> nginx -s reload  // 重新加载配置 (还是需要在安装目录下执行)
D:\..> nginx -s quit    // 退出
```


## 测试
- 访问: http://localhost/