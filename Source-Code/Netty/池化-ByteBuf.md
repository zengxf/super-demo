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
### 基础类
- 内存分配和回收管理主要由 `PoolChunk` 实现，其内部维护一棵平衡二叉树 `MemoryMap`，所有子节点管理的内存也属于其父节点。
  - 每当申请超过 `8KB` 内存时，就会从 `PoolChunk` 获取。