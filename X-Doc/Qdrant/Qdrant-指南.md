
#### HNSW 索引指的是什么
- https://chatgpt.com/c/6964b2c6-11a4-832c-842b-52acb85d897a
- 它是 Qdrant、Milvus、FAISS、Weaviate 等向量数据库的核心算法之一。

- --
🧠 **一、HNSW 是什么**？
- **HNSW** 全称是 **Hierarchical Navigable Small World graph**（分层可导航小世界图）。
- 是一种用 **图结构（graph）** 来加速**高维向量相似搜索**的算法。
- 目标是：**让你在上亿个向量中，快速找到最相似的向量，而不用一个个去比**。

- --
🏗️ **二、核心思想（直观理解）**
- 可以把 HNSW 想成一个“分层导航图”：

* 每个节点是一条向量；
* 节点之间根据相似度（距离小）建立连边；
* 顶层层数少，连接稀疏；底层层数多，连接密；
* 搜索时从顶层开始，逐层往下走，每层都往相似的方向跳；
* 最终在底层找到最接近的几个向量。

**类比**
- **就像在地图上找一个城市**：
- **先从“世界地图”找到国家 → 再看“国家地图”找省份 → 再看“城市地图”精确定位**。
- 这样能极大减少比较次数（不用全量扫描）。


#### Qdrant 中的 HNSW 索引
- https://chatgpt.com/c/6964b2c6-11a4-832c-842b-52acb85d897a
- 在 Qdrant 里，每个 collection 都会默认使用 **HNSW 索引** 来加速相似搜索。

- --
⚙️ **结构**
- 它有一些关键参数可以配置：
```json
"hnsw_config": {
  "m": 16,
  "ef_construct": 100,
  "ef": 100
}
```

| 参数名 | 含义 | 影响 |
| -- | -- | -- |
| `m`            | 每个点的最大邻居数（图的稀疏度） | 越大 → 精度高但内存占用大   |
| `ef_construct` | 建索引时的搜索宽度        | 越大 → 建索引慢但查询精度更高 |
| `ef`           | 查询时的搜索宽度（可动态调整）  | 越大 → 查询更准但更慢     |

- --
📈 **性能特点**

| 特性 | 说明 |
| -- | -- |
| 🔥 **速度快**    | 通常只需几百次比较即可从百万数据中找到最相似向量      |
| 📦 **内存效率高**  | 图结构压缩存储相邻关系                   |
| 🎯 **近似搜索**   | 非精确匹配，但结果非常接近（通常 >99% recall） |
| 🧩 **支持动态更新** | 可插入、删除数据（不像某些静态索引）            |

- **召回率高：在参数调优得当的情况下，其搜索结果可以非常接近精确最近邻搜索，满足绝大多数业务需求**。

- --
🧠 **与其他索引算法的对比**

| 算法 | 核心思想 | 特点 | 适用场景 |
| -- | -- | -- | -- |
| **HNSW**               | 分层图搜索     | 高精度、高速、动态更新 | 通用场景首选      |
| **IVF+PQ**             | 向量分桶 + 压缩 | 快速但有量化误差    | 大规模数据（>10亿） |
| **Flat (Brute Force)** | 全量比较      | 精确但慢        | 小数据集或测试     |


#### HNSW 关键参数
- https://chatglm.cn/main/alltoolsdetail?lang=zh&cid=6964af876e5cd314d2a3726d
- HNSW 的性能和准确性主要由两个超参数控制，理解它们是调优 HNSW 索引的关键。

| 参数 | 含义与作用 | 调优建议 |
| :-- | :-- | :-- |
| **`M` (Max Connections)** | **每个节点在各层中拥有的最大邻居数（连接数）**。它决定了图的**连通性**和**密度**。<br> • **`M` 越大**：图的连接越紧密，搜索路径更优，**召回率（准确性）越高**，但索引构建时间变长，**内存占用和索引大小也会增加**。<br> • **`M` 越小**：图更稀疏，构建更快、内存更省，但可能错过一些更优路径，召回率下降。 | **通常在 16 到 64 之间**。<br> • **低延迟/实时系统**（如聊天机器人）：尝试 **M=8-12**<br> • **高吞吐/批量分析**（如后台推荐）：尝试 **M=32-48**<br> • **默认值**（如16）是很好的起点。 |
| **`ef` (entry factor)** | **查询时，在每层（尤其是最底层）搜索的**动态**候选队列大小**。它控制了搜索的**广度**和**探索范围**。<br> • **`ef` 越大**：搜索时考察的节点越多，**召回率越高**，但**查询延迟（Latency）也越高**（需要计算更多距离）。<br> • **`ef` 越小**：搜索更快，但可能因探索范围不足而错过最近邻，召回率下降。 | **通常在 10 到 1000 之间，远大于 M**。<br> • **在线搜索参数**，**可动态调整**以满足不同场景需求。<br> • **低延迟优先**：尝试 **ef=32-64**<br> • **高召回优先**：尝试 **ef=200-400**<br> • **许多系统默认 `ef = top_k`**（例如，查询Top10，`ef`也设为10），但通常需要调大以获得更好效果。 |

还有一个与索引构建相关的参数：
| 参数 |  含义与作用 | 调优建议 |
| :-- |  :-- | :-- |
| **`ef_construction`** | **构建索引时，在每层搜索的候选队列大小**。它只影响**索引构建阶段**，**不影响查询阶段**。<br> • **`ef_construction` 越大**：构建索引时花费更多时间探索，能构建出**质量更高、结构更优的图**，通常能获得更好的查询性能和召回率。<br> • **`ef_construction` 越小**：索引构建更快，但图的质量可能稍逊。 | **通常在 200 到 800 之间，默认值 400 是很好的起点**。<br> • 如果你有大量数据和充足时间进行索引构建，可以尝试增大此值（如500-800）来换取更好的在线查询性能。 |

- --
📊 **参数调优建议**

| 目标 | 建议参数 | 说明 |
| -- | -- | -- |
| 🚀 极致速度    | `m=8`, `ef_construct=50`, `ef=64`    | 较快但召回率略低 |
| ⚖️ 平衡型（默认） | `m=16`, `ef_construct=100`, `ef=128` | 通用推荐     |
| 🎯 高精度搜索   | `m=32`, `ef_construct=300`, `ef=512` | 慢一些但更准   |

- --
🧠 **总结**

| 参数 | 阶段 | 控制内容 | 取值越大效果 |
| -- | -- | -- | -- |
| `m`            | 索引结构 | 每个点的连边数量 | 图更密、更准，但占内存 |
| `ef_construct` | 构建阶段 | 建索引时搜索范围 | 索引更准但建得慢    |
| `ef`           | 查询阶段 | 查询时搜索范围  | 搜索更准但速度慢    |


#### Qdrant - distance 选项及举例
- https://chatgpt.com/c/6964c67d-5648-8328-8c69-c084cbf7b376
- https://chat.qwen.ai/c/70e267e1-3aa0-44ca-8669-70f690d9c6ad

- --
- **假设有两个向量**：
```js
A = [1, 2, 3]
B = [2, 3, 4]
```

- --
1️⃣ **Cosine（余弦相似度）**
- **衡量两个非零向量在方向上的相似程度，不考虑它们的大小（模长），只关注夹角**

**公式：**
$$
\text{Cosine Distance} = 1 - \frac{A \cdot B}{||A|| \times ||B||}
$$

**计算步骤：**

* 点积 ($ A \cdot B = 1×2 + 2×3 + 3×4 = 20 $)
* 向量模长：
  * ($ ||A|| = \sqrt{1^2 + 2^2 + 3^2} = 3.742 $)
  * ($ ||B|| = \sqrt{2^2 + 3^2 + 4^2} = 5.385 $)
* 余弦相似度 = 20 / (3.742 × 5.385) = **0.9746**
* 余弦距离 = 1 - 0.9746 = **0.0254**

✅ 越小表示越相似。
→ 两个方向几乎一致。

- --
2️⃣ **Euclid（欧氏距离 / L2）**
- 距离越小，表示两个向量越“接近”。

**公式：**
$$
d(\mathbf{a}, \mathbf{b}) = \sqrt{\sum_{i=1}^{n} (a_i - b_i)^2}
$$

$$
\text{Euclidean Distance} = \sqrt{(1-2)^2 + (2-3)^2 + (3-4)^2}
$$

**计算：**
$$
= \sqrt{1 + 1 + 1} = \sqrt{3} = 1.732
$$

✅ 越小表示越相似。

- --
3️⃣ **Dot（点积）**

**公式：**
$$
\text{Dot Product} = \sum A_i \times B_i
$$

**计算：**
$$
= 1×2 + 2×3 + 3×4 = 20
$$

✅ 越大表示越相似（与前两种相反）。

- --
4️ **Manhattan（曼哈顿距离，L1 距离）**
- 对于两个 n 维向量  
$$
\mathbf{a} = [a_1, a_2, \dots, a_n], \quad \mathbf{b} = [b_1, b_2, \dots, b_n]
$$  
- **曼哈顿距离**：
$$
d_{\text{manhattan}}(\mathbf{a}, \mathbf{b}) = \sum_{i=1}^{n} |a_i - b_i|
$$
**示例**：
$$
\text{Manhattan Distance} = |1-2| + |2-3| + |3-4| = 3
$$

✅ 越小表示越相似。

- --
📊 **总结对比表**

| 距离类型 | 结果 | 越小越相似？ | 特点 |
| -- | -- | -- | -- |
| Cosine    | 0.025 | ✅        | 只看方向（常用于文本）  |
| Euclid    | 1.732 | ✅        | 看绝对差值（数值/几何） |
| Dot       | 20    | ❌（越大越相似） | 常用于归一化或推荐场景  |
| Manhattan | 3     | ✅        | 对离群点更鲁棒      |


#### Qdrant - 集合示例
- https://qdrant.tech/documentation/concepts/collections/
- **创建集合**
```shell
curl -X PUT http://localhost:6333/collections/my_test \
-H "Content-Type: application/json" \
-d \
'{
    "vectors": {
        "size": 300,
        "distance": "Cosine",
        "datatype": "uint8"
    }
}'
```
- **参考解释**：
  - `size` **指定向量长度**，必须是数字，不能是数组，相当于向量只能是一维的，多维的要打平
    - `matrix.flatten().tolist() # numpy 示例` 
  - `distance` **计算两向量之间的距离方式**
  - `datatype` **指定向量数据类型**
    - `uint8` 以更紧凑的格式存储，节省内存并提高搜索速度，但牺牲一些精度
- **包含多个向量的集合**
```shell
curl -X PUT http://localhost:6333/collections/my_test2 \
-H "Content-Type: application/json" \
-d \
'{
    "vectors": {
        "image": {
            "size": 4,
            "distance": "Dot"
        },
        "text": {
            "size": 8,
            "distance": "Cosine"
        }
    }
}'
```
- **检查集合情况**
```shell
curl -X GET http://localhost:6333/collections/my_test/exists
```
- **删除集合**
```shell
curl -X DELETE http://localhost:6333/collections/my_test
```

#### Qdrant - 理解 distance (距离度量) 🧮
- `distance` 参数决定了 Qdrant 计算两个向量之间**相似度**的**数学方法**。它定义了在这个向量空间中“距离”和“方向”的含义。
```json
"vectors": {
  "distance": "Cosine"
}
```
*   **含义**：当你在搜索时，Qdrant 会用这个公式计算你的查询向量与集合中每个向量之间的距离/相似度分数，并按分数排序返回最相似的向量。
*   **常见度量方式**：

| 度量方式 | 计算方式 (公式) | 核心特点 | 典型应用场景 | 影响因素 |
| :-- | :-- | :-- | :-- | :-- |
| **`Cosine` (余弦相似度)** | 计算两个向量**夹角的余弦值**。<br>范围: **[-1, 1]**，**1 表示完全同向**，最相似。 | **忽略向量长度（模长），只关注方向**。对向量归一化后，等同于**点积**。 | **文本检索、语义搜索、推荐系统**（文本词频向量长度差异大，但方向相似更重要）。 | **向量方向** |
| **`Dot` (点积)** | 计算两个向量的**对应元素乘积之和**。<br>范围: **无界**，值越大越相似。 | **同时考虑向量的方向和长度**。计算简单高效。 | **向量已预先归一化为单位长度**时，等同于余弦相似度。常用于**图像检索**、**某些神经网络输出**。 | **向量方向和长度** |
| **`Euclid` (欧氏距离)** | 计算两个向量在空间中的**直线距离**（L2范数）。<br>范围: **[0, ∞)**，**0 表示重合**，距离越小越相似。 | **最直观的“距离”概念**。**对向量的长度和方向都敏感**。 | **图像检索、低维数据**、**物理空间距离模拟**。在高维空间中，其区分能力可能下降。 | **向量方向和长度** |
| **`Manhattan` (曼哈顿距离)** | 计算两个向量在**每个维度上绝对差值之和**（L1范数）。<br>范围: **[0, ∞)**。 | **计算方式简单，对高维数据更鲁棒**。在某些高维场景下可能比欧氏距离表现更好。 | **某些高维稀疏数据**、**具有网格结构的数据**（如城市街区距离）。 | **向量在各个维度上的差异** |

* **如何选择？**
    *   **对于文本数据（NLP）**：**首选 `Cosine`**。因为文本向量（如 TF-IDF, Word2Vec）的长度（模长）通常与文档长度或词频相关，而**语义相似性更多体现在方向上**。使用 `Cosine` 可以消除长度差异的影响，专注于内容相似性。
    *   **对于图像数据或已归一化的向量**：**`Dot` 或 `Euclid` 都是常见选择**。如果确保向量已归一化，`Dot` 计算更高效。
    *   **不确定时**：**`Cosine` 是一个安全且广泛适用的默认选择**，尤其是在处理自然语言文本时。你可以先用 `Cosine` 进行实验，再根据效果尝试其他度量。
- 💡 **重要提示**：**距离度量方式一旦创建集合后通常无法更改**。如果之后想换一种度量方式，你需要**删除旧集合并使用新参数重新创建一个新集合**，然后重新写入所有数据。因此，初期选择很重要。


#### Qdrant - 多向量集合操作示例
- 多向量：也就是每个点（point）可以同时包含多个向量（这里是 `image` 和 `text`）。

- --
✅ **一、Collection 定义**
```bash
curl -X PUT "http://localhost:6333/collections/my_test2" \
-H "Content-Type: application/json" \
-d '{
    "vectors": {
        "image": {
            "size": 4,
            "distance": "Dot"
        },
        "text": {
            "size": 8,
            "distance": "Cosine"
        }
    }
}'
```

- --
✅ **二、插入多向量数据**
- **用 put 新增或覆盖**
```bash
curl -X PUT "http://localhost:6333/collections/my_test2/points" \
-H "Content-Type: application/json" \
-d '{
    "points": [
        {
            "id": 1,
            "vector": {
                "image": [0.1, 0.2, 0.3, 0.4],
                "text":  [0.9, 0.8, 0.7, 0.6, 0.5, 0.4, 0.3, 0.2]
            },
            "payload": {
                "category": "cat",
                "desc": "A cute kitten image"
            }
        },
        {
            "id": 2,
            "vector": {
                "image": [0.2, 0.1, 0.0, 0.5],
                "text":  [0.8, 0.6, 0.4, 0.2, 0.9, 0.7, 0.5, 0.3]
            },
            "payload": {
                "category": "dog",
                "desc": "A dog image"
            }
        }
    ]
}'
```

* `id`：唯一标识；
* `vector`：这里是个 **对象（object）**，每个键名对应 collection 中定义的子向量；
* `payload`：可选，附带元信息。

- --
✅ **三、查询（Search）示例**
- 可以选择按某一个向量空间检索（如 `image` 或 `text`）：
- **搜索相似图片向量**：
```bash
curl -X POST "http://localhost:6333/collections/my_test2/points/search" \
-H "Content-Type: application/json" \
-d '{
    "vector": {
        "name": "image",
        "vector": [0.1, 0.2, 0.25, 0.35]
    },
    "limit": 2
}'
```
- **搜索相似文本向量**：
```bash
curl -X POST "http://localhost:6333/collections/my_test2/points/search" \
-H "Content-Type: application/json" \
-d '{
    "vector": {
        "name": "text",
        "vector": [0.9, 0.8, 0.6, 0.7, 0.4, 0.5, 0.3, 0.2]
    },
    "limit": 2
}'
```


#### Qdrant - 删除 point
- **按 ID 删除**
```bash
curl -X POST "http://localhost:6333/collections/my_test2/points/delete" \
-H "Content-Type: application/json" \
-d '{
    "points": [1, 2]
}'
```
- **按 filter 删除（比如 payload 条件匹配）**
```bash
curl -X POST "http://localhost:6333/collections/my_test2/points/delete" \
-H "Content-Type: application/json" \
-d '{
    "filter": {
        "must": [
            {
                "key": "category",
                "match": {"value": "cat_updated"}
            }
        ]
    }
}'
```


#### Qdrant - 查看所有的 point
✅ **翻页查看**
- 如果有很多点（超过 `limit`），可以用上次返回的 `next_page_offset` 来继续查询下一页：
```bash
curl -X POST "http://localhost:6333/collections/my_test2/points/scroll" \
-H "Content-Type: application/json" \
-d '{
    "limit": 10,
    "offset": 2
}'
```

- --
✅ **可选过滤条件（比如只看某类）**
- 例如只看 `"category": "cat"` 的数据：
```bash
curl -X POST "http://localhost:6333/collections/my_test2/points/scroll" \
-H "Content-Type: application/json" \
-d '{
    "filter": {
        "must": [
            {
                "key": "category",
                "match": {"value": "cat"}
            }
        ]
    },
    "limit": 10
}'
```

- --
✅ **快速总结**

| 功能 | 接口 | 方法 | 说明 |
| -- | -- | -- | -- |
| 查看所有点 | `/collections/{name}/points/scroll` | `POST` | 分页遍历所有 point |
| 查看单个点 | `/collections/{name}/points/{id}`   | `GET`  | 按 ID 获取一个点   |
| 搜索相似点 | `/collections/{name}/points/search` | `POST` | 基于向量相似度检索    |
