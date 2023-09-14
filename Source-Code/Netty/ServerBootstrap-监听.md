## 使用示例
- 参考：[简单示例-服务端](简单示例.md#服务端)

## 原理
### 启动
- 使用 `bind()` 方法开启服务

- `io.netty.bootstrap.ServerBootstrap`
```java
/*** 服务端-引导类 */
// 继承 AbstractBootstrap
public class ServerBootstrap extends AbstractBootstrap<ServerBootstrap, ServerChannel> {

    // bind() 在父类里

}
```

- `io.netty.bootstrap.AbstractBootstrap`
```java
/*** 抽象-引导类 */
public abstract class AbstractBootstrap<B extends AbstractBootstrap<B, C>, C extends Channel> {
    /*** 绑定地址（启动） */
    public ChannelFuture bind() {
        ... // 省略校验
        return doBind(localAddress);
    }

    // 启动
    private ChannelFuture doBind(final SocketAddress localAddress) {
        final ChannelFuture regFuture = initAndRegister(); // 初始化信道并添加到监听器（事件轮循组）
        final Channel channel = regFuture.channel();
        ... // 省略异常判断处理

        if (regFuture.isDone()) {
            ... // 初始化没这么快，一般不会进入此，因此省略
        } else { // 测试时进入此
            final PendingRegistrationPromise promise = new PendingRegistrationPromise(channel);
            regFuture.addListener(new ChannelFutureListener() { // 添加监听
                @Override
                public void operationComplete(ChannelFuture future) throws Exception {
                    Throwable cause = future.cause();
                    if (cause != null) { // 有异常
                        promise.setFailure(cause); // 设置失败
                    } else {
                        promise.registered(); // 标记下
                        doBind0(regFuture, channel, localAddress, promise); // 绑定处理
                    }
                }
            });
            return promise;
        }
    }

    // 绑定地址
    private static void doBind0(
            final ChannelFuture regFuture, final Channel channel,
            final SocketAddress localAddress, final ChannelPromise promise
    ) { // 此方法在触发 channelRegister() 之前调用
        channel.eventLoop().execute(new Runnable() {
            @Override
            public void run() {
                if (regFuture.isSuccess()) {
                    // sb 设置的是 NioServerSocketChannel（继承 AbstractNioChannel）
                    channel.bind(localAddress, promise) // 进入绑定
                        .addListener(ChannelFutureListener.CLOSE_ON_FAILURE);
                } else {
                    promise.setFailure(regFuture.cause());
                }
            }
        });
    }
}
```

- `io.netty.channel.AbstractChannel`
```java
/*** 抽象-信道类 */
public abstract class AbstractChannel extends DefaultAttributeMap implements Channel {
    /*** 绑定地址 */
    @Override
    public ChannelFuture bind(SocketAddress localAddress, ChannelPromise promise) {
        return pipeline.bind(localAddress, promise); // pipeline 是 DefaultChannelPipeline 的实例
    }
}
```

- `io.netty.channel.DefaultChannelPipeline`
```java
/*** 默认流水线 */
public class DefaultChannelPipeline implements ChannelPipeline {
    /*** 绑定地址 */
    @Override
    public final ChannelFuture bind(SocketAddress localAddress, ChannelPromise promise) {
        /**
         * 从尾节点开始往前传递处理。
         * 链结构：
         *   head <-> ServerBootstrapAcceptor <-> tail
         * 处理顺序：
         *   tail  -> ServerBootstrapAcceptor  -> head
         * 
         * ServerBootstrapAcceptor 
         */
        return tail.bind(localAddress, promise); // 
    }

    /*** 尾节点 */
    final class TailContext extends AbstractChannelHandlerContext implements ChannelInboundHandler {

        // bind(...) 方法在父类里实现

    }
}
```

- `io.netty.channel.AbstractChannelHandlerContext`
```java
/*** 抽象上下文（相当于流水线双向链表的节点） */
abstract class AbstractChannelHandlerContext implements ChannelHandlerContext, ResourceLeakHint {
    @Override
    public ChannelFuture bind(final SocketAddress localAddress, final ChannelPromise promise) {
        ... // 省略校验处理

        /**
         * 查找出站处理器上下文：
         *     查找出来的是 HeadContext，
         *     即：next = head
         */
        final AbstractChannelHandlerContext next = findContextOutbound(MASK_BIND);
        EventExecutor executor = next.executor();
        if (executor.inEventLoop()) {
            next.invokeBind(localAddress, promise); // 调用绑定
        } else {
            ... // 省略异步调用绑定
        }
        return promise;
    }

    // 调用绑定 (this 变为 HeadContext 实例)
    private void invokeBind(SocketAddress localAddress, ChannelPromise promise) {
        if (invokeHandler()) { // 测试时，进入此分支
            try {
                final ChannelHandler handler = handler(); // 返回 head
                final DefaultChannelPipeline.HeadContext headContext = pipeline.head;
                if (handler == headContext) { // 进入此分支
                    headContext.bind(this, localAddress, promise); // 调用头节点的绑定方法(sign001)
                } ... // 省略其他分支处理
            } ... // 省略 catch 处理
        } else {
            bind(localAddress, promise); // 递归调用
        }
    }
}
```

- `io.netty.channel.DefaultChannelPipeline.HeadContext`
```java
    /*** 头节点 */
    final class HeadContext extends AbstractChannelHandlerContext
            implements ChannelOutboundHandler, ChannelInboundHandler {
        /*** 绑定方法(sign001) */
        @Override
        public void bind(
                ChannelHandlerContext ctx, SocketAddress localAddress, ChannelPromise promise
        ) {
            /**
             * unsafe 为 AbstractNioMessageChannel.NioMessageUnsafe 实例
             */
            unsafe.bind(localAddress, promise);
        }
    }
```

- `io.netty.channel.nio.AbstractNioMessageChannel.NioMessageUnsafe`
```java
    // 继承 AbstractNioUnsafe
    private final class NioMessageUnsafe extends AbstractNioUnsafe {

        // bind(...) 在父类 AbstractUnsafe 里实现

    }
```

- `io.netty.channel.nio.AbstractNioChannel.AbstractNioUnsafe`
```java
    // 继承 AbstractUnsafe
    protected abstract class AbstractNioUnsafe extends AbstractUnsafe implements NioUnsafe {
    }
```

- `io.netty.channel.AbstractChannel.AbstractUnsafe`
```java
    protected abstract class AbstractUnsafe implements Unsafe {

        @Override
        public final void bind(final SocketAddress localAddress, final ChannelPromise promise) {
            ... // 省略校验与日志打印

            boolean wasActive = isActive(); // 返回 false
            try {
                /**
                 * doBind(...) 指定的是 NioServerSocketChannel 对象。
                 *     即：回调 NioServerSocketChannel 的绑定方法。
                 */
                doBind(localAddress);
            } ... // 省略 catch 处理

            if (!wasActive && isActive()) { // 相当于之前没启动，后面启动了
                invokeLater(new Runnable() {
                    @Override
                    public void run() {
                        pipeline.fireChannelActive(); // 发送信道激活事件
                    }
                });
            }

            /**
             * 将 promise 设置为成功状态。
             *     这样示例中 bs.bind().sync(); // sign_demo_001
             *     才会返回，否则一直阻塞。
             */
            safeSetSuccess(promise);
        }
    }
```

- `io.netty.channel.socket.nio.NioServerSocketChannel`
```java
/*** NIO 服务端信道 */
public class NioServerSocketChannel extends AbstractNioMessageChannel
                                    implements io.netty.channel.socket.ServerSocketChannel 
{
    // 绑定处理
    @Override
    protected void doBind(SocketAddress localAddress) throws Exception {
        if (PlatformDependent.javaVersion() >= 7) {
            /**
             * javaChannel() 返回的是 java.nio.channels.ServerSocketChannel 实例。 
             *     即：底层使用 Java 的信道绑定地址，
             *          相当于底层开启监听。
             */
            javaChannel().bind(localAddress, config.getBacklog());
        } else {
            javaChannel().socket().bind(localAddress, config.getBacklog());
        }
    }
}
```