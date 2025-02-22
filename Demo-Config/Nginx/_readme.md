## Nginx 配置
```conf
# 在 `http { }` 里面添加
http {
    # 引入文件夹
    include D:/MyData/pub-project/super-demo/Demo-Config/Nginx/*.conf;          # OK
    # include "D:/MyData/pub-project/super-demo/Demo-Config/Nginx/*.conf";      # OK
    # include D:\\MyData\\pub-project\\super-demo\\Demo-Config\\Nginx\\*.conf;  # ERR
}
```
- 具体参考：[nginx.conf.ref.cfg](./nginx.conf.ref.cfg)
- 上游服务：[for-nginx-test](https://github.com/zengxf/spring-demo/tree/master/web/for-nginx-test/readme.md)