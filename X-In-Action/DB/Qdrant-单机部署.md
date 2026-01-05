# Qdrant-单机部署


## 下载
**Qdrant 服务**
- 版本：`1.16.3` 示例
- 入口：https://github.com/qdrant/qdrant/releases/tag/v1.16.3
- 点击 `qdrant-x86_64-pc-windows-msvc.zip`
- 最终：https://github.com/qdrant/qdrant/releases/download/v1.16.3/qdrant-x86_64-pc-windows-msvc.zip

**Qdrant Web UI**
- 版本：`0.2.5` 示例
- 入口：https://github.com/qdrant/qdrant-web-ui/releases/tag/v0.2.5
- 点击 `dist-qdrant.zip`
- 最终：https://github.com/qdrant/qdrant-web-ui/releases/download/v0.2.5/dist-qdrant.zip


## 启动
- 解压之后，添加到 `Path` 直接运行
```bat
cd /d %qdrant%

qdrant
```


## Web-UI 配置
- 解压后将 `dist` 改名为 `qdrant-web-ui-0.2`

**修改 `index.html`**
```html
<!-- 将 /dashboard 全删除 -->
<!-- 如："/dashboard/favicon.ico" 改为 "/favicon.ico" -->
<!-- 下面这 2 行是关键 -->
<script type="module" crossorigin src="/assets/index-BLw1FxSh.js"></script>
<link rel="stylesheet" crossorigin href="/assets/index-BG9q9yEd.css">
```

**Nginx 配置**
```conf
    # http://localhost:8088/
    server {
        listen          8088;            
        server_name     localhost;     
        
        root  D:/Install/DB/qdrant-web-ui-0.2;  # 绝对路径
		index index.html;

        location / {
			try_files $uri $uri/ /index.html;
        }
			
		# 反向代理 Qdrant API
		# 转发所有以 /collections /points 等开头的路径到 qdrant
		location ~ ^/(collections|aliases|points|cluster|telemetry|locks|snapshots|metrics|service) {
			proxy_pass http://127.0.0.1:6333;
			proxy_set_header Host $host;
			proxy_set_header X-Real-IP $remote_addr;
			proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
		}
    }
```
- `nginx -s reload` 之后，浏览器要 `Ctrl + F5` 刷新
- 访问：http://localhost:8088/


## CURL 请求

### 查看基本信息
```shell
# 查看基本信息 (包括版本)
curl http://localhost:6333/
```

### 集合-创建、查询
```shell
# 创建指定向量大小与距离度量的集合
curl -X PUT "http://localhost:6333/collections/my_collection" \
     -H "Content-Type: application/json" \
     -d '{
           "vectors": {
             "size": 768,
             "distance": "Cosine"
           }
         }'

# 查看已创建的集合
curl http://localhost:6333/collections

# 查看集合详情
curl http://localhost:6333/collections/my_collection
```

### 别名
```shell
# 给 `my_collection` 集合创建别名
curl -X POST "http://localhost:6333/collections/aliases" \
     -H "Content-Type: application/json" \
     -d '{
           "actions": [
             {
               "create_alias": {
                 "collection_name": "my_collection",
                 "alias_name": "my_alias"
               }
             }
           ]
         }'

# 切换别名（无缝迁移数据）
curl -X POST http://localhost:6333/collections/aliases \
-H 'Content-Type: application/json' \
-d '{
    "actions": [
        {
            "delete_alias": { "alias_name": "production_alias" }
        },
        {
            "create_alias": { 
                "collection_name": "new_collection_v2", 
                "alias_name": "production_alias" 
            }
        }
    ]
}'

# 没有 upsert_alias 操作
# 通过"原子操作"中同时组合 delete_alias 和 create_alias 来达到“替换”的效果

# 查看当前所有别名
curl http://localhost:6333/aliases

# 查看 `my_collection` 集合的别名
curl http://localhost:6333/collections/my_collection/aliases

# 使用别名访问集合 (结果是一样的)
curl -X POST "http://localhost:6333/collections/aliases" \
     -H "Content-Type: application/json" \
     -d '{
           "actions": [
             {
               "create_alias": {
                 "collection_name": "test001",
                 "alias_name": "alias001"
               }
             }
           ]
         }'
curl http://localhost:6333/collections/test001/points/1
curl http://localhost:6333/collections/alias001/points/1
```