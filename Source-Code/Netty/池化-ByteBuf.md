## 参考
- [Netty 内存池优化原理](https://lanchestios.github.io/2021/01/13/Netty-内存池优化原理/)
- [Netty-专栏-jemalloc 基本原理](https://learn.lianglianglee.com/专栏/Netty%20核心原理剖析与%20RPC%20实践-完/12%20%20他山之石：高性能内存分配器%20jemalloc%20基本原理.md)
- [Netty-专栏-高性能内存管理设计-上](https://learn.lianglianglee.com/专栏/Netty%20核心原理剖析与%20RPC%20实践-完/13%20%20举一反三：Netty%20高性能内存管理设计（上）.md)
- [Netty-专栏-高性能内存管理设计-下](https://learn.lianglianglee.com/专栏/Netty%20核心原理剖析与%20RPC%20实践-完/14%20%20举一反三：Netty%20高性能内存管理设计（下）.md)
- [ByteBuf 泄漏检测原理](https://github.com/doocs/source-code-hunter/blob/main/docs/Netty/Netty技术细节源码分析/ByteBuf的内存泄漏原因与检测原理.md)
- [Netty 高性能内存管理](https://www.51cto.com/article/608695.html)
- [jemalloc 基本原理](https://blog.csdn.net/weixin_41402069/article/details/125744994)


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
### 基础类
- 内存分配和回收管理主要由 `PoolChunk` 实现，其内部维护一棵平衡二叉树 `MemoryMap`，所有子节点管理的内存也属于其父节点。
  - 每当申请超过 `8KB` 内存时，就会从 `PoolChunk` 获取。

### jemalloc-原理
- https://blog.csdn.net/weixin_41402069/article/details/125744994
- **内存分配粒度分为 `Small, Large, Huge` 三类**，并记录很多 meta 数据，
  - 所以在空间占用上要略多于 tcmalloc，
    - 不过在大内存分配的场景，jemalloc 的内存碎片要少于 tcmalloc。
  - jemalloc 内部采用红黑树管理内存块和分页，
    - Huge 对象通过红黑树查找索引数据可以控制在指数级时间。
- **核心目标是**：
  - **高效的内存分配和回收**，提升单线程或者多线程常见下的性能
  - **减少内存碎片**，包括内部碎片和外部碎片
- 碎片
  - 内部碎片
    - 内存是按 Page 进行分配的，即便我们只需要很小的内存，操作系统至少也会分配 4K 大小的 Page，单个 Page 内只有一部分字节都被使用，剩余的字节形成了内部碎片。
  - 外部碎片
    - 与内部碎片相反，外部碎片是在分配较大内存块时产生的。当需要分配大内存块的时候，操作系统只能通过分配连续的 Page 才能满足要求，在程序不断运行的过程中，这些 Page 被频繁的回收并重新分配，Page 之间就会出现小的空闲内存块，这样就形成了外部碎片。