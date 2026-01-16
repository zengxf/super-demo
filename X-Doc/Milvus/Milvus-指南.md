# Milvus-指南


#### Milvus - 使用 mmap
- https://milvus.io/docs/zh/create-collection.md
- https://milvus.io/docs/zh/mmap.md
- **Milvus 默认在所有 Collections 上启用 mmap**，允许 Milvus **将原始字段数据映射到内存中，而不是完全加载它们**。
  - 这样可以**减少内存占用，提高 Collections 的容量**。
- **内存映射（Mmap）可实现对磁盘上大型文件的直接内存访问**，使 Milvus **可以在内存和硬盘中同时存储索引和数据**。
  - 这种方法**有助于根据访问频率优化数据放置策略**，在不明显影响搜索性能的情况下扩大 Collections 的存储容量。


#### Milvus - mmap 概述
- https://milvus.io/docs/zh/mmap.md
- **Milvus 是内存密集型数据库系统，可用内存大小决定了 Collection 的容量**。
  - **如果数据量超过内存容量，就无法将包含大量数据的字段加载到内存中**
- 为了解决此类问题，Milvus **引入 mmap 来平衡 Collections 中冷热数据的加载**。
  - 可以配置 Milvus **对某些字段中的原始数据进行内存映射，而不是将它们完全加载到内存中**。

<img src="https://milvus.io/docs/v2.6.x/assets/mmap-illustrated.png" width="560" height="180"/>

- 通过比较左右两幅图中的数据放置程序，可以发现**左图中的内存使用量要比右图中高得多**。
  - **启用 mmap 后，本应加载到内存中的数据会被卸载到硬盘中，并缓存到操作系统的页面缓存中，从而减少内存占用**。
- ***不过，缓存命中失败可能会导致性能下降***。


#### Milvus - 使用 mmap 示例
- https://milvus.io/docs/zh/mmap.md

**全局 mmap 设置**
```yml
...
queryNode:
  mmap:
    scalarField: false
    scalarIndex: false
    vectorField: false
    vectorIndex: false
    # The following should be a path on a high-performance disk
    mmapDirPath: any/valid/path 
....
```

**特定字段的 mmap 设置**
```py
schema = MilvusClient.create_schema()

# 添加标量字段并启用 mmap
schema.add_field(
    field_name="doc_chunk",
    datatype=DataType.INT64,
    is_primary=True,
    mmap_enabled=True,
)

# 修改特定字段的 mmap 设置
# 以下假设您有一个名为 `my_collection` 的集合
client.alter_collection_field(
    collection_name="my_collection",
    field_name="doc_chunk",
    field_params={"mmap.enabled": True}
)
```

**特定索引的内存映射设置**
```py
index_params = MilvusClient.prepare_index_params()

# 使用 mmap 设置对 varchar 字段创建索引
index_params.add_index(
    field_name="title",
    index_type="AUTOINDEX",
    params={ "mmap.enabled": "false" }
)
```


#### Milvus - 设置 Collections TTL
- https://milvus.io/docs/zh/create-collection.md
- 如果需要**在特定时间段内删除 Collections 中的数据**，可以考虑**以秒为单位设置**其 Time-To-Live (TTL)。
- 一旦 TTL 超时，Milvus 就会删除 Collection 中的实体。
- **删除是异步的，这表明在删除完成之前，搜索和查询仍然可以进行**。
```py
client.create_collection(
    collection_name="customized_setup_5",
    schema=schema,
    # highlight-start
    properties={
        "collection.ttl.seconds": 86400
    }
    # highlight-end
)
```


#### Milvus - 设置一致性级别
- https://milvus.io/docs/zh/create-collection.md
- https://milvus.io/docs/zh/tune_consistency.md
- Milvus 提供了多种一致性级别，**以确保每个节点或副本在读写操作期间都能访问相同的数据**。
- **创建 Collections 时**，可以为集合中的搜索和查询设置一致性级别。
```py
client.create_collection(
    collection_name="customized_setup_6",
    schema=schema,
    # highlight-next-line
    consistency_level="Bounded",
)
```
- 支持的一致性级别包括`强、有限制、最终 和 会话`，**其中`有限制`是默认**使用的一致性级别。
  - `consistency_level` 参数的可能值是 `Strong, Bounded, Eventually, Session`。
- **在查询中设置一致性级别**
```py
res = client.query(
    collection_name="my_collection",
    filter="color like \"red%\"",
    output_fields=["vector", "color"],
    limit=3，
    # highlight-start
    consistency_level="Eventually",
    # highlight-next-line
)
```


#### Milvus - 动态字段
- https://milvus.io/docs/zh/enable-dynamic-field.md
- Milvus 允许你**通过动态字段这一特殊功能，插入结构灵活、不断变化的实体**。
  - 该字段**以名为 `$meta` 的隐藏 JSON 字段实现**，它会**自动存储数据中任何未在 Collections Schema 中明确定义的字段**。
- 例如，如果您的 Collections Schema 只定义了`id`和`vector`，而您**插入以下实体**：
```js
{
  "id": 1,
  "vector": [0.1, 0.2, 0.3],
  "name": "Item A",    // Not in schema
  "category": "books"  // Not in schema
}
```
- 启用动态字段功能后，Milvus 将其**内部存储为**：
```js
{
  "id": 1,
  "vector": [0.1, 0.2, 0.3],
  // highlight-start
  "$meta": {
    "name": "Item A",
    "category": "books"
  }
  // highlight-end
}
```
- **要使用动态字段功能，请在创建 Collections Schema 时设置 `enable_dynamic_field=True`**：
```py
# 创建启用动态字段的模式
schema = client.create_schema(
    auto_id=False,
    enable_dynamic_field=True,
)
```


#### Milvus - 修改 Collections
- https://milvus.io/docs/zh/modify-collection.md
```py
# 重命名 Collection
client.rename_collection(
    old_name="my_collection",
    new_name="my_new_collection"
)

# 设置集合属性
client.alter_collection_properties(
    collection_name="my_collection",
    properties={
      "collection.ttl.seconds": 60, # 设置 TTL
      "mmap.enabled": True, # 启用 mmap
      "dynamicfield.enabled": True, # 启用动态字段
      "timezone": "Asia/Shanghai", # 设置时区
    }
)

# 删除 Collection 属性
client.drop_collection_properties(
    collection_name="my_collection",
    property_keys=[
        "collection.ttl.seconds"
    ]
)
```


#### Milvus - 集合 - 加载和释放
- https://milvus.io/docs/zh/load-and-release.md
- **加载集合是在集合中进行相似性搜索和查询的前提**。
- **加载时，会将索引文件和所有字段的原始数据加载到内存中，以便快速响应搜索和查询**。
```py
client.load_collection(collection_name="my_collection")
res = client.get_load_state(collection_name="my_collection")
print(res)
# Output
# { "state": "<LoadState: Loaded>" }
```
- **可以只加载搜索和查询所涉及的字段，从而减少内存使用并提高搜索性能**
```py
# 应始终在 load_fields 中包含主字段和至少一个向量字段的名称
client.load_collection(
    collection_name="my_collection",
    load_fields=["my_id", "my_vector"] # 只加载指定的字段
    skip_load_dynamic_field=True # 跳过加载动态字段
)
```
- ***要在加载后加载更多字段，需要先释放***
- **搜索和查询是内存密集型操作。为节约成本，建议释放当前不使用的 Collection**
```py
client.release_collection(collection_name="my_collection")
```


#### Milvus - 集合 - 管理分区
- https://milvus.io/docs/zh/manage-partitions.md
- **创建 Collection 时，会创建 `_default` 分区**。
  - **所有插入、搜索和查询也都在默认分区内进行**。
- **可以添加更多分区，并根据特定条件将实体插入其中**。
  - **这样就可以限制在某些分区内进行搜索和查询，从而提高搜索性能**。
- 一个 Collections **最多 `1024` 个分区**。
```py
# --------- 查看分区 ---------
res = client.list_partitions(collection_name="my_collection")
print(res)

# --------- 创建分区 ---------
client.create_partition(collection_name="my_collection", partition_name="partitionA")
res = client.list_partitions(collection_name="my_collection")
print(res)

# --------- 加载分区 ---------
client.load_partitions(collection_name="my_collection", partition_names=["partitionA"])
res = client.get_load_state(collection_name="my_collection", partition_name="partitionA")
print(res)

# --------- 释放分区 ---------
client.release_partitions(collection_name="my_collection", partition_names=["partitionA"])
res = client.get_load_state(collection_name="my_collection", partition_name="partitionA")
print(res)

# --------- 删除分区 ---------
client.drop_partition(collection_name="my_collection", partition_name="partitionA")
res = client.list_partitions(collection_name="my_collection")
print(res)

"""
输出：
['_default']
['_default', 'partitionA']
{'state': <LoadState: Loaded>}
{'state': <LoadState: NotLoad>}
['_default']
"""
```


#### Milvus - 集合 - 管理别名
- https://milvus.io/docs/zh/manage-aliases.md
```py
# --------- 删除别名 ---------
client.drop_alias(alias="bob")
client.drop_alias(alias="alice")

# --------- 创建别名 ---------
client.create_alias(collection_name="my_collection_1", alias="bob")
client.create_alias(collection_name="my_collection_1", alias="alice")

# --------- 列出别名 ---------
res = client.list_aliases(collection_name="my_collection_1")
print("coll 1 alias: ", res)

# --------- 描述别名 ---------
res = client.describe_alias(alias="bob")
print("alias 'bob' desc: ",res)

# --------- 更改别名 ---------
# 将已分配给特定集合的别名重新分配给另一个集合
client.alter_alias(collection_name="my_collection_2", alias="alice")
res = client.list_aliases(collection_name="my_collection_1")
print("coll 1 alias: ", res)
res = client.list_aliases(collection_name="my_collection_2")
print("coll 2 alias: ", res)

"""
Output:
coll 1 alias:  {'aliases': ['bob', 'alice'], 'collection_name': 'my_collection_1', 'db_name': 'default'}
alias 'bob' desc:  {'alias': 'bob', 'collection_name': 'my_collection_1', 'db_name': 'default'}
coll 1 alias:  {'aliases': ['bob'], 'collection_name': 'my_collection_1', 'db_name': 'default'}
coll 2 alias:  {'aliases': ['alice'], 'collection_name': 'my_collection_2', 'db_name': 'default'}
"""
```


#### Milvus - 插入实体
- https://milvus.io/docs/zh/insert-update-delete.md
```py
# ---------- 插入实体 ----------
data = [
    {"my_id": 110, "my_vector": [0.35, -0.60, 0.18, 1, 1], "my_varchar": "pink_8682"}
]
res = client.insert(collection_name="quick_setup", data=data)
print(res)

# ---------- 插入实体 (指定分区) ----------
data = [
    {"my_id": 120, "my_vector": [0.35, -0.60, 0.18, 1, 1], "my_varchar": "pink_8682"}
]
res = client.insert(collection_name="quick_setup", partition_name="partitionA", data=data)
print(res)

# ---------- 插入实体 (带动态字段) ----------
data = [{
    "my_id": 130, "my_vector": [0.35, -0.60, 0.18, 1, 2], "my_varchar": "pink_8682",
    "z_test1": 122, "z_test2": "aaa", "z-test-3": True  # 动态字段
}]
res = client.insert(collection_name="quick_setup", data=data)
print(res)

"""
Output:
{'insert_count': 1, 'ids': [110]}
{'insert_count': 1, 'ids': [120]}
{'insert_count': 1, 'ids': [130]}
"""
```
- **支持重复插入，相当于根据 id 进行修改**
- ***不支持部分字段修改，可直接 insert 修改***


#### Milvus - 删除实体
- https://milvus.io/docs/zh/delete-entities.md
```py
# -------- 通过筛选条件删除实体 --------
res = client.delete(collection_name="quick_setup", filter="my_varchar in ['red_7025', 'purple_4976']")
print(res)

# -------- 通过主键删除实体 --------
res = client.delete(collection_name="quick_setup", ids=[18, 19])
print(res)

# -------- 从分区中删除实体 --------
res = client.delete(collection_name="quick_setup", ids=[18, 19], partition_name="partitionA")
print(res)

# -------- 删除所有 --------
res = client.delete(collection_name="quick_setup", filter="my_id > 0")
print(res)

"""
Output:
{}
{'delete_count': 2}
{'delete_count': 2}
{}
```


#### Milvus - 集合统计
```py
# -------- 查看集合数据量 --------
stats = client.get_collection_stats(collection_name="quick_setup")
print(stats)  # 统计不准

# -------- 查看集合准确行数 --------
res = client.query(collection_name="quick_setup", output_fields=["count(*)"])
print(f"准确行数: {res}")
print(f"准确行数: {res[0]['count(*)']}")

"""
Output:
{'row_count': 45}
准确行数: data: ["{'count(*)': 10}"], extra_info: {}
准确行数: 10
"""
```


#### Milvus - 单向量搜索
- https://milvus.io/docs/zh/single-vector-search.md#Single-Vector-Search
```py
# ---------- 单向量搜索 ----------
query_vector = [0.35, -0.60, 0.18, 1, 1.56]
res = client.search(
    collection_name="quick_setup",
    # anns_field="my_vector",                   # 可以省略
    data=[query_vector],
    limit=3,
    output_fields=["my_varchar", "$meta"],
    # search_params={"metric_type": "IP"}       # 不能随意指定
    # search_params={"metric_type": "COSINE"}   # 默认就是 COSINE，因此可以省略
)

for hits in res:
    print("----------------------")
    for hit in hits:
        print(hit)

"""
----------------------
{'my_id': 130, 'distance': 0.9932429194450378, 'entity': {'my_varchar': 'pink_8682', 'z_test1': 122, 'z_test2': 'bbb', 'z-test-3': True}}
{'my_id': 110, 'distance': 0.975786030292511, 'entity': {'my_varchar': 'pink_8682'}}
{'my_id': 120, 'distance': 0.975786030292511, 'entity': {'my_varchar': 'pink_8682'}}
"""
```


#### Milvus - HNSW 测试
```py
# --------- 创建集合 ---------
schema = MilvusClient.create_schema(auto_id=False, enable_dynamic_field=True)
schema.add_field(field_name="my_id", datatype=DataType.INT64, is_primary=True)
schema.add_field(field_name="my_vector", datatype=DataType.FLOAT_VECTOR, dim=5)

index_params = client.prepare_index_params()
index_params.add_index(field_name="my_id", index_type="AUTOINDEX")
index_params.add_index(
    index_name="idx_vector",  # 要创建的索引的名称
    field_name="my_vector",  # 要索引的向量字段的名称
    index_type="HNSW",  # 要创建的索引类型
    metric_type="COSINE",  # 用于度量相似性的度量类型
    params={
        "M": 64,  # 每个节点可连接的最大邻居数量。
        "efConstruction": 100  # 索引构建过程中考虑连接的候选邻居数量。
    }  # 索引构建参数
)

res = client.create_collection(collection_name=coll_name, schema=schema, index_params=index_params)


# --------- 搜索 ---------
query_vector = [2, 2, 2, 2, 2]
results = client.search(
    collection_name=coll_name,
    data=[query_vector],
    params={"ef": 10},  # ef: 搜索时要考虑的邻居数量。
    limit=5,
)
for r in results[0]:
    print(r.id, r.distance)
```