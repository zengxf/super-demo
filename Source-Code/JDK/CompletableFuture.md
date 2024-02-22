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

        public final void run()                { tryFire(ASYNC); }  // Runnable
        public final Void getRawResult()       { return null; }     // ForkJoinTask
        public final void setRawResult(Void v) {}                   // ForkJoinTask
        public final boolean exec()            { tryFire(ASYNC); return false; } 
    }
```

- `java.util.concurrent.CompletableFuture.AsynchronousCompletionTask`
```java
    // 异步任务标识接口（无其他定义）
    public static interface AsynchronousCompletionTask {
    }
```

- `java.util.concurrent.CompletableFuture.AsyncSupply`
```java
    // 异步生成数据
    static final class AsyncSupply<T> extends ForkJoinTask<Void>
        implements Runnable, AsynchronousCompletionTask 
    {
        CompletableFuture<T> dep; 
        Supplier<? extends T> fn; // 数据提供者
        AsyncSupply(CompletableFuture<T> dep, Supplier<? extends T> fn) {
            this.dep = dep; this.fn = fn;
        }

        public final Void getRawResult() { return null; }   // ForkJoinTask
        public final void setRawResult(Void v) {}           // ForkJoinTask
        public final boolean exec() { run(); return false; }// ForkJoinTask
    }
```

- `java.util.concurrent.CompletableFuture.UniApply`
```java
    static final class UniApply<T, V> extends UniCompletion<T, V> {
        Function<? super T, ? extends V> fn;
        UniApply(
            Executor executor, CompletableFuture<V> dep,
            CompletableFuture<T> src,
            Function<? super T, ? extends V> fn
        ) {
            super(executor, dep, src); 
            this.fn = fn;
        }
    }
```

- `java.util.concurrent.CompletableFuture.UniCompletion`
```java
    abstract static class UniCompletion<T,V> extends Completion {
        Executor executor;                 // 要使用的执行器（如果没有则为 null）
        CompletableFuture<V> dep;          // 要完成的依赖项
        CompletableFuture<T> src;          // 行动来源

        UniCompletion(
            Executor executor, CompletableFuture<V> dep,
            CompletableFuture<T> src
        ) {
            this.executor = executor; this.dep = dep; this.src = src;
        }
    }
```

- `java.util.concurrent.CompletableFuture.UniAccept`
```java
    static final class UniAccept<T> extends UniCompletion<T, Void> {
        Consumer<? super T> fn;
        ... // 构造器类似：UniApply
    }
```

- `java.util.concurrent.CompletableFuture.UniRun`
```java
    static final class UniRun<T> extends UniCompletion<T, Void> {
        Runnable fn;
        ... // 构造器类似：UniApply
    }
```