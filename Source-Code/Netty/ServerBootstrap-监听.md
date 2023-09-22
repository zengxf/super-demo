## 使用示例
- 参考：[简单示例-服务端](简单示例.md#服务端)
- Java 参考：
  - https://github.com/zengxf/small-frame-demo/blob/master/jdk-demo/simple-demo/src/main/java/test/socket/nio/MyNioServer.java


----
## 总结
- 启动顺序：
  - 先注册事件监听
  - 再绑定地址启动服务
- Unsafe:
  - 底层逻辑处理
- 说明：
  - 代码注释中“发送信道激活事件”：实为直接调用钩子函数


----
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
        final ChannelFuture regFuture = initAndRegister(); // sign_m_010 初始化信道并添加到监听器（事件轮循组）
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
                    // sb 设置的是 NioServerSocketChannel
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
  - 参考：[基础类介绍-NioServerSocketChannel](基础类介绍.md#NioServerSocketChannel)
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
                        pipeline.fireChannelActive(); // sign_m_020 发送信道激活事件
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

### 监听
- `io.netty.channel.socket.nio.NioServerSocketChannel`
```java
/*** 服务端-信道 */
public class NioServerSocketChannel extends AbstractNioMessageChannel
                                    implements io.netty.channel.socket.ServerSocketChannel 
{
    public NioServerSocketChannel(ServerSocketChannel channel) { // channel 是 Java NIO 的实例
        super(null, channel, SelectionKey.OP_ACCEPT); // 设置 OP_ACCEPT 类型事件监听
        config = new NioServerSocketChannelConfig(this, javaChannel().socket());
    }
}
```

- `io.netty.channel.nio.AbstractNioMessageChannel`
```java
/*** 抽象 NIO 消息信道 */
public abstract class AbstractNioMessageChannel extends AbstractNioChannel {
    protected AbstractNioMessageChannel(Channel parent, SelectableChannel ch, int readInterestOp) {
        super(parent, ch, readInterestOp); // readInterestOp 要监听的事件类型
    }
}
```

- `io.netty.channel.nio.AbstractNioChannel`
  - **底层操作在此类实现**
```java
/*** 抽象 NIO 信道 */
public abstract class AbstractNioChannel extends AbstractChannel {
    private final SelectableChannel ch; // Java 底层信道
    protected final int readInterestOp; // 要监听的事件类型
    volatile SelectionKey selectionKey; // Java 底层监听的 key 句柄

    /*** 构造器 */
    protected AbstractNioChannel(Channel parent, SelectableChannel ch, int readInterestOp) {
        super(parent);
        this.ch = ch;
        this.readInterestOp = readInterestOp;
        try {
            ch.configureBlocking(false); // 设置为非阻塞
        } ... // 省略 catch 处理
    }

    /*** 获取 Java 底层信道 */
    protected SelectableChannel javaChannel() {
        return ch;
    }

    /*** 获取 Java 底层监听的 key 句柄 */
    protected SelectionKey selectionKey() {
        return selectionKey;
    }

    /*** 注册处理 sign_m_001 */
    @Override
    protected void doRegister() throws Exception {
        ...
        for (;;) {
            try {
                // 向事件轮循里面的选择器进行初步注册，key 的附件为自己
                selectionKey = javaChannel().register(eventLoop().unwrappedSelector(), 0, this);
                return;
            } ... // catch
        }
    }

    /*** sign_m_030 开始读处理 */
    @Override
    protected void doBeginRead() throws Exception {
        new RuntimeException("栈跟踪-设置兴趣事件").printStackTrace();

        ... // 省略 selectionKey 校验 

        final int interestOps = selectionKey.interestOps();
        if ((interestOps & readInterestOp) == 0) {
            selectionKey.interestOps(interestOps | readInterestOp); // 正式注册要监听的事件类型
        }
    }
}
```

#### 注册调用点
- `io.netty.bootstrap.AbstractBootstrap`
```java
    /*** sign_m_010 初始化信道并添加到监听器（事件轮循组） */
    final ChannelFuture initAndRegister() {
        Channel channel = null;
        try {
            channel = channelFactory.newChannel();
            init(channel); // 初始化：信道流水线添加 ServerBootstrapAcceptor 处理器
        } ... // catch

        // config().group() 相当于是设置给引导器的 NioEventLoopGroup
        ChannelFuture regFuture = config().group().register(channel); // 注册处理
        
        ... // 省略 regFuture 异常处理

        return regFuture;
    }
```

- `io.netty.channel.MultithreadEventLoopGroup`
  - 参考：[基础类介绍-NioEventLoopGroup](基础类介绍.md#NioEventLoopGroup)
```java
    /*** 注册（相当于将信道绑定到线程，同时又注册到选择器） */
    @Override
    public ChannelFuture register(Channel channel) {
        /**
         * next(): 通过轮循算法返回下一个事件轮循者（相当于线程）
         */
        return next().register(channel); // 调用事件轮循者进行注册
    }
```

- `io.netty.channel.SingleThreadEventLoop`
  - DefaultChannelPromise 可参考：
    - [基础类介绍-DefaultChannelPromise](基础类介绍.md#DefaultChannelPromise)
    - [异步工具类-DefaultChannelPromise](异步工具类.md#DefaultChannelPromise)
```java
    /*** 注册信道 */
    @Override
    public ChannelFuture register(Channel channel) {
        return register(new DefaultChannelPromise(channel, this));
    }

    /*** 注册信道 */
    @Override
    public ChannelFuture register(final ChannelPromise promise) {
        ObjectUtil.checkNotNull(promise, "promise");
        /**
         * promise.channel().unsafe() 返回的是 NioMessageUnsafe 实例
            */
        promise.channel().unsafe().register(this, promise); // 通过 unsafe 注册
        return promise;
    }
```

- `io.netty.channel.AbstractChannel.AbstractUnsafe`
  - 参考：[基础类介绍-NioMessageUnsafe](基础类介绍.md#NioMessageUnsafe)
```java
    protected abstract class AbstractUnsafe implements Unsafe {
        /*** 注册处理 */
        @Override
        public final void register(EventLoop eventLoop, final ChannelPromise promise) {
            ... // 省略校验等

            AbstractChannel.this.eventLoop = eventLoop;

            if (eventLoop.inEventLoop()) {
                register0(promise);
            } else { // 不是当前线程，则异步调用
                try {
                    eventLoop.execute(new Runnable() {
                        @Override
                        public void run() {
                            register0(promise); // sign_m_201 注册处理
                        }
                    });
                } ... // catch
            }
        }

        // sign_m_201 注册处理
        private void register0(ChannelPromise promise) {
            try {
                ... // 省略校验等

                doRegister(); // 注册处理 sign_m_001: 调用 AbstractNioChannel #doRegister()

                pipeline.invokeHandlerAddedIfNeeded(); // 回调 ChannelHandler #handlerAdded()

                safeSetSuccess(promise); // 设置 promise 为成功
                pipeline.fireChannelRegistered(); // 发射已注册事件
                if (isActive()) { // 调试时：还未激活，不进入此分支
                    if (firstRegistration) {
                        pipeline.fireChannelActive();
                    } else if (config().isAutoRead()) {
                        beginRead();
                    }
                }
            } ... // catch 
        }
    }
```

#### 设置兴趣事件
- **栈跟踪**
```js
java.lang.RuntimeException: 栈跟踪-设置兴趣事件
	at io.netty.channel.nio.AbstractNioChannel.doBeginRead(AbstractNioChannel.java:413)
	at io.netty.channel.nio.AbstractNioMessageChannel.doBeginRead(AbstractNioMessageChannel.java:55)
	at io.netty.channel.AbstractChannel$AbstractUnsafe.beginRead(AbstractChannel.java:834)
	at io.netty.channel.DefaultChannelPipeline$HeadContext.read(DefaultChannelPipeline.java:1362)
	at io.netty.channel.AbstractChannelHandlerContext.invokeRead(AbstractChannelHandlerContext.java:835)
	at io.netty.channel.AbstractChannelHandlerContext.read(AbstractChannelHandlerContext.java:814)
	at io.netty.channel.DefaultChannelPipeline.read(DefaultChannelPipeline.java:1004)
	at io.netty.channel.AbstractChannel.read(AbstractChannel.java:290)
	at io.netty.channel.DefaultChannelPipeline$HeadContext.readIfIsAutoRead(DefaultChannelPipeline.java:1422)
	at io.netty.channel.DefaultChannelPipeline$HeadContext.channelActive(DefaultChannelPipeline.java:1400)
	at io.netty.channel.AbstractChannelHandlerContext.invokeChannelActive(AbstractChannelHandlerContext.java:258) // sign_c_001
	at io.netty.channel.AbstractChannelHandlerContext.invokeChannelActive(AbstractChannelHandlerContext.java:238) // sign_c_0_1
	at io.netty.channel.DefaultChannelPipeline.fireChannelActive(DefaultChannelPipeline.java:895) // sign_m_021 发送信道激活事件
	at io.netty.channel.AbstractChannel$AbstractUnsafe$2.run(AbstractChannel.java:573) // sign_m_020 发送信道激活事件
```

- 在绑定后，发送信道激活事件
  - 自动进行读处理

- `io.netty.channel.DefaultChannelPipeline`
```java
    /*** sign_m_021 发送信道激活事件 */
    @Override
    public final ChannelPipeline fireChannelActive() {
        AbstractChannelHandlerContext.invokeChannelActive(head); // sign_c_0_1 从头节点开始
        return this;
    }

    // 头节点
    final class HeadContext extends AbstractChannelHandlerContext
            implements ChannelOutboundHandler, ChannelInboundHandler 
    {
        /*** sign_c_002 信道激活事件处理 */
        @Override
        public void channelActive(ChannelHandlerContext ctx) {
            ctx.fireChannelActive();

            readIfIsAutoRead();
        }

        private void readIfIsAutoRead() {
            /**
             * io.netty.channel.ChannelConfig #isAutoRead():
             *   默认只在 io.netty.channel.DefaultChannelConfig 实现，
             *   其实现相当于直接返回 true，
             *   所以会进入 read() 方法。
             */
            if (channel.config().isAutoRead()) {
                channel.read(); // sign_c_003
            }
        }

        // sign_c_007
        @Override
        public void read(ChannelHandlerContext ctx) {
            unsafe.beginRead(); // sign_c_008
        }
    }

    // sign_c_004
    @Override
    public final ChannelPipeline read() {
        tail.read(); // sign_c_005
        return this;
    }
```

- `io.netty.channel.AbstractChannelHandlerContext`
```java
    // sign_c_0_1
    static void invokeChannelActive(final AbstractChannelHandlerContext next) {
        EventExecutor executor = next.executor();
        if (executor.inEventLoop()) {
            // next => head
            next.invokeChannelActive(); // sign_c_001
        } ... // else 
    }

    // sign_c_001
    private void invokeChannelActive() {
        if (invokeHandler()) {
            try {
                final ChannelHandler handler = handler();
                final DefaultChannelPipeline.HeadContext headContext = pipeline.head;
                if (handler == headContext) {
                    headContext.channelActive(this); // sign_c_002 从头节点开始
                } ... // else
            } ... // catch
        } ... // else
    }

    // sign_c_005
    @Override
    public ChannelHandlerContext read() {
        final AbstractChannelHandlerContext next = findContextOutbound(MASK_READ);
        EventExecutor executor = next.executor();
        if (executor.inEventLoop()) {
            next.invokeRead(); // sign_c_006
        } ... // else

        return this;
    }

    // sign_c_006
    private void invokeRead() {
        if (invokeHandler()) {
            try {
                final ChannelHandler handler = handler();
                final DefaultChannelPipeline.HeadContext headContext = pipeline.head;
                if (handler == headContext) {
                    headContext.read(this); // sign_c_007
                } ... // else
            } ... // catch 
        } ... // else
    }
```

- `io.netty.channel.AbstractChannel`
```java
    // sign_c_003
    @Override
    public Channel read() {
        pipeline.read(); // sign_c_004
        return this;
    }

    protected abstract class AbstractUnsafe implements Unsafe {
        // sign_c_008
        @Override
        public final void beginRead() {
            ...

            try {
                doBeginRead(); // sign_m_030 开始读
            } ... // catch 
        }
    }
```

#### 监听连接
- 参考：[选择器-监听-原理](选择器-监听.md#原理)