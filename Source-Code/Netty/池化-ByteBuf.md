## 参考
- [Netty 内存池优化原理](https://lanchestios.github.io/2021/01/13/Netty-内存池优化原理/)
- [Netty-专栏-jemalloc 基本原理](https://learn.lianglianglee.com/专栏/Netty%20核心原理剖析与%20RPC%20实践-完/12%20%20他山之石：高性能内存分配器%20jemalloc%20基本原理.md)
- [Netty-专栏-高性能内存管理设计-上](https://learn.lianglianglee.com/专栏/Netty%20核心原理剖析与%20RPC%20实践-完/13%20%20举一反三：Netty%20高性能内存管理设计（上）.md)
- [Netty-专栏-高性能内存管理设计-下](https://learn.lianglianglee.com/专栏/Netty%20核心原理剖析与%20RPC%20实践-完/14%20%20举一反三：Netty%20高性能内存管理设计（下）.md)
- [ByteBuf 泄漏检测原理](https://github.com/doocs/source-code-hunter/blob/main/docs/Netty/Netty技术细节源码分析/ByteBuf的内存泄漏原因与检测原理.md)
- [Netty 高性能内存管理](https://www.51cto.com/article/608695.html)
- [jemalloc 基本原理](https://blog.csdn.net/weixin_41402069/article/details/125744994)
- [Netty 内存管理源码分析 jemalloc](https://www.jianshu.com/p/550704d5a628)


---
## 单元测试
```java
public class PoolBufTest {
    @Test
    public void test() {
        System.out.println("------ 第一次测试 ------");
        allocAndRelease();

        System.out.println("------ 第二次测试 ------");
        allocAndRelease();
    }

    // 分配和释放
    private void allocAndRelease() {
        ByteBufAllocator allocator = PooledByteBufAllocator.DEFAULT; // 可用 ByteBufAllocator.DEFAULT 获取
        ByteBuf buf = allocator.directBuffer();
        System.out.println("buf-hash: " + System.identityHashCode(buf)); // 第 2 次没有创建新的

        buf.writeInt(10);
        int iv = buf.readInt();
        System.out.println("iv => " + iv);
        buf.release();

        // buf.writeInt(10); // err IllegalReferenceCountException
    }
}
```


---
## ByteBuf
- 测试时默认情况下：
  - 客户端：
    - alloc: `PooledByteBufAllocator(directByDefault: true)`
    - buf: `PooledUnsafeDirectByteBuf`
  - 服务端：
    - alloc: `PooledByteBufAllocator(directByDefault: true)`
    - buf: `PooledUnsafeDirectByteBuf`
- 类结构参考：
  - [基础类介绍-PooledByteBufAllocator](基础类介绍.md#PooledByteBufAllocator)
  - [基础类介绍-PooledUnsafeDirectByteBuf](基础类介绍.md#PooledUnsafeDirectByteBuf)


---
## 内存池原理
- **jemalloc 内存结构**：
  - `Arena -> Chunk (1:n) -> Page (1:n)`

- **类结构**：
  - `PooledByteBufAllocator`
    ```java
        // heap 类型的 arena 数组
        private final PoolArena<byte[]>[] heapArenas;
        // direct memory 类型的 arena 数组
        private final PoolArena<ByteBuffer>[] directArenas;
    ```

  - `PoolArena`
    ```java
    final PooledByteBufAllocator parent; // 所属分配器

    private final PoolSubpage<T>[] smallSubpagePools;
    // private final PoolSubpage<T>[] tinySubpagePools; // 2020 年优化掉了

    // 根据内存使用率分配的 Chunk
    private final PoolChunkList<T> q050;  // 50~100%
    private final PoolChunkList<T> q025;  // 25~75%
    private final PoolChunkList<T> q000;  // 1~50%
    private final PoolChunkList<T> qInit; // 0~25%
    private final PoolChunkList<T> q075;  // 75~100%
    private final PoolChunkList<T> q100;  // 100~100%
    ```

  - `PoolChunkList`
    ```java
    private final PoolArena<T> arena;         // 所属的 Arena
    private final PoolChunkList<T> nextList;  // 与 prevList 组成双向链表
    private PoolChunkList<T> prevList;
    private PoolChunk<T> head;                // PoolChunk 的挂载点
    ```

  - `PoolChunk`
    ```java
    final PoolArena<T> arena; // 所属的 Arena
    final T memory;           // 相当于 byte[] 数组
    private final PoolSubpage<T>[] subpages;  // (使用伙伴算法)管理的内存块
    int freeBytes;            // 剩余的内存大小
    PoolChunkList<T> parent;  // 所属的 PoolChunkList
    PoolChunk<T> prev;        // 与 next 组成双向链表
    PoolChunk<T> next;
    ```

  - `PoolSubpage`
    ```java
    final PoolChunk<T> chunk;     // 所属的 PoolChunk
    private final long[] bitmap;  // 记录每个小内存块的使用状态(即是否已使用)
    PoolSubpage<T> prev;          // 与 next 组成双向链表
    PoolSubpage<T> next;
    final int elemSize;           // 每个小内存块的大小
    private final int runOffset;  // 当前 PoolSubpage 在 PoolChunk 中 memory 的偏移量
    private final int runSize;    // 总内存大小
    private int maxNumElems;      // 最多可以存放多少小内存块： runSize(8K) / elemSize
    private int numAvail;         // 可用于分配的内存块个数
    ```

- **总结说明**：
  - 算法有改进，没有使用`二叉树`，去掉了`tiny`类型
  - `PoolSubpage`只是对`PoolChunk`做使用记录，没有记录具体的内存数据