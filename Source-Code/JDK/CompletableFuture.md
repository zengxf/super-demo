## 使用示例
- https://github.com/zengxf/small-frame-demo/blob/master/jdk-demo/simple-demo/src/main/java/test/new_features/jdk1_8/juc/TestCompletableFuture.java
- 基础方法使用测试：`testThenApply2()`


## JDK 版本
```js
openjdk version "17" 2021-09-14
OpenJDK Runtime Environment (build 17+35-2724)
OpenJDK 64-Bit Server VM (build 17+35-2724, mixed mode, sharing)
```


## 原理
### 类结构
- `java.util.concurrent.CompletableFuture`
```java
public class CompletableFuture<T> implements Future<T>, CompletionStage<T> {
    volatile Object result;         // 结果或封装的异常
    volatile Completion stack;      // 依赖操作的栈顶
}
```

- `java.util.concurrent.CompletableFuture.Completion`
```java
    static abstract class Completion extends ForkJoinTask<Void>
        implements Runnable, AsynchronousCompletionTask
    {
        volatile Completion next;   // 组装单向链表

        // ------ 方法定义 ------

        /** 触发：执行完成操作，返回可能需要传播的依赖项（如果存在）。 */
        abstract CompletableFuture<?> tryFire(int mode);
        abstract boolean isLive();  // 判断是否可触发

        public final void run()                { tryFire(ASYNC); }
        public final boolean exec()            { tryFire(ASYNC); return false; }
        public final Void getRawResult()       { return null; }
        public final void setRawResult(Void v) {}
    }
```

- `java.util.concurrent.CompletableFuture.AsynchronousCompletionTask`
```java
    // 异步任务标识接口（无其他定义）
    public static interface AsynchronousCompletionTask {
    }
```