
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


#### Milvus - xx
- https://milvus.io/docs/zh/create-collection.md


#### Milvus - xx
- https://milvus.io/docs/zh/create-collection.md


#### Milvus - xx
- https://milvus.io/docs/zh/create-collection.md


#### Milvus - xx
- https://milvus.io/docs/zh/create-collection.md