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
    volatile Completion stack;      // 依赖操作的栈顶 (组装单向链表)
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
    // sign_c_030 异步生成数据
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
    // sign_c_040
    static final class UniApply<T, V> extends UniCompletion<T, V> {
        Function<? super T, ? extends V> fn;
        UniApply( // sign_cm_050
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

        final boolean isLive() { return dep != null; }
    }
```

- `java.util.concurrent.CompletableFuture.UniAccept`
```java
    // sign_c_060
    static final class UniAccept<T> extends UniCompletion<T, Void> {
        Consumer<? super T> fn;
        ... // 构造器类似：UniApply, ref: sign_cm_050
    }
```

- `java.util.concurrent.CompletableFuture.UniRun`
```java
    // sign_c_070
    static final class UniRun<T> extends UniCompletion<T, Void> {
        Runnable fn;
        ... // 构造器类似：UniApply, ref: sign_cm_050
    }
```

### 初始链
#### supplyAsync()
- `java.util.concurrent.CompletableFuture`
```java
    // 调用入口，ref: sign_demo_010
    public static <U> CompletableFuture<U> supplyAsync(Supplier<U> supplier,
                                                       Executor executor) {
        return asyncSupplyStage(screenExecutor(executor), supplier);
    }

    static <U> CompletableFuture<U> asyncSupplyStage(Executor e,
                                                     Supplier<U> f) {
        ...
        CompletableFuture<U> d = new CompletableFuture<U>();
        e.execute(new AsyncSupply<U>(d, f));    // 进行执行数据生成，ref: sign_c_030 | sign_m_110
        return d;
    }
```

- `java.util.concurrent.CompletableFuture.AsyncSupply`
```java
        // sign_m_110 数据生成
        public void run() {
            CompletableFuture<T> d; Supplier<? extends T> f;
            if ((d = dep) != null && (f = fn) != null) {
                dep = null; fn = null;
                if (d.result == null) {
                    try {
                        d.completeValue(f.get());   // 获取数据并填充结果
                    } catch (Throwable ex) {
                        d.completeThrowable(ex);    // 出错时，封装异常填充结果
                    }
                }
                d.postComplete();   // 传递给后面依赖项，ref: sign_m_310
            }
        }
```

#### thenApply()
- `java.util.concurrent.CompletableFuture`
```java
    public <U> CompletableFuture<U> thenApply(
        Function<? super T,? extends U> fn
    ) {
        return uniApplyStage(null, fn);
    }

    // sign_m_210
    private <V> CompletableFuture<V> uniApplyStage(
        Executor e, Function<? super T,? extends V> f
    ) {
        ...
        Object r;
        if ((r = result) != null)
            return uniApplyNow(r, e, f);
        CompletableFuture<V> d = newIncompleteFuture();
        unipush(new UniApply<T,V>(e, d, this, f));  // ref: sign_m_230 | sign_c_040
        return d;
    }

    public <U> CompletableFuture<U> newIncompleteFuture() {
        return new CompletableFuture<U>();
    }

    // sign_m_230
    final void unipush(Completion c) {
        if (c != null) {
            while (!tryPushStack(c)) {
                if (result != null) {
                    NEXT.set(c, null);  // 相当于：c.next = null;
                    break;
                }
            }
            if (result != null)
                c.tryFire(SYNC);        // 有结果就直接触发下级执行
        }
    }

    final boolean tryPushStack(Completion c) {
        Completion h = stack;
        NEXT.set(c, h);                         // 相当于：c.next = stack;
        return STACK.compareAndSet(this, h, c); // 相当于：stack = c;
    }
```

#### thenApplyAsync()
- `java.util.concurrent.CompletableFuture`
```java
    public <U> CompletableFuture<U> thenApplyAsync(
        Function<? super T,? extends U> fn, Executor executor) {
        return uniApplyStage(screenExecutor(executor), fn); // ref: sign_m_210
    }
```

#### thenAccept()
- `java.util.concurrent.CompletableFuture`
```java
    public CompletableFuture<Void> thenAccept(Consumer<? super T> action) {
        return uniAcceptStage(null, action);
    }

    private CompletableFuture<Void> uniAcceptStage(Executor e,
                                                   Consumer<? super T> f) {
        ...
        Object r;
        if ((r = result) != null)
            return uniAcceptNow(r, e, f);
        CompletableFuture<Void> d = newIncompleteFuture();
        unipush(new UniAccept<T>(e, d, this, f));   // ref: sign_m_230 | sign_c_060
        return d;
    }
```

#### thenRun()
- `java.util.concurrent.CompletableFuture`
```java
    public CompletableFuture<Void> thenRun(Runnable action) {
        return uniRunStage(null, action);
    }

    private CompletableFuture<Void> uniRunStage(Executor e, Runnable f) {
        ...
        Object r;
        if ((r = result) != null)
            return uniRunNow(r, e, f);
        CompletableFuture<Void> d = newIncompleteFuture();
        unipush(new UniRun<T>(e, d, this, f));  // ref: sign_m_230 | sign_c_070
        return d;
    }
```

#### 链结构
```js
// dep (new CF)

// (dep.stack)
AsyncSupply-1 -> UniApply-2 -> UniApply-3 -> UniAccept -> UniRun

// (next & src)
UniRun -> UniAccept -> UniApply-3 -> UniApply-2 -> AsyncSupply-1
```

### 调用链
#### postComplete()
- `java.util.concurrent.CompletableFuture`
```java
    // sign_m_310 弹出并尝试触发所有可到达的依赖项
    final void postComplete() {
        CompletableFuture<?> f = this; Completion h;
        while ((h = f.stack) != null ||
               (f != this && (h = (f = this).stack) != null)) {
            CompletableFuture<?> d; Completion t;
            if (STACK.compareAndSet(f, h, t = h.next)) {
                ...
                f = (d = h.tryFire(NESTED)) == null ? this : d; // 触发具体操作逻辑
            }
        }
    }
```

#### UniApply
- `java.util.concurrent.CompletableFuture.UniApply`
```java
        final CompletableFuture<V> tryFire(int mode) {
            CompletableFuture<V> d; CompletableFuture<T> a;
            Object r; Throwable x; Function<? super T,? extends V> f;
            if ((a = src) == null || (r = a.result) == null
                || (d = dep) == null || (f = fn) == null)
                return null;
            tryComplete: 
            if (d.result == null) {
                ... // 源异常处理
                try {
                    if (mode <= 0 && !claim())          // ref: sign_m_325
                        return null;                    // 如果判断为异步执行，则进入此逻辑
                    else {
                        T t = (T) r;                    // 源的结果
                        d.completeValue(f.apply(t));    // 调用 Function 转换并设置结果
                    }
                } ... // catch
            }
            src = null; dep = null; fn = null;
            return d.postFire(a, mode); // 传给下一项
        }
```

- `java.util.concurrent.CompletableFuture.UniCompletion`
```java
        // sign_m_325
        // 如果操作可以运行，则返回 true (相当于没设置线程池，不用异步执行)
        final boolean claim() {
            Executor e = executor;
            if (compareAndSetForkJoinTaskTag(0, 1)) {   // 一般 CAS 成功，进入此逻辑
                if (e == null)
                    return true;    // 没有设置线程池，表示同步执行
                executor = null;    // 置空，防止死循环
                e.execute(this);    // 异步执行
            }
            return false;
        }
```

#### UniAccept
- `java.util.concurrent.CompletableFuture.UniAccept`
```java
        final CompletableFuture<Void> tryFire(int mode) {
            CompletableFuture<Void> d; CompletableFuture<T> a;
            Object r; Throwable x; Consumer<? super T> f;
            if ((a = src) == null || (r = a.result) == null
                || (d = dep) == null || (f = fn) == null)
                return null;
            tryComplete: 
            if (d.result == null) {
                ... // 源异常处理
                try {
                    if (mode <= 0 && !claim())
                        return null;
                    else {
                        T t = (T) r;
                        f.accept(t);        // 调用 Consumer 消费上游结果
                        d.completeNull();
                    }
                } ... // catch
            }
            src = null; dep = null; fn = null;
            return d.postFire(a, mode); // 传给下一项
        }
```

#### UniRun
- `java.util.concurrent.CompletableFuture.UniRun`
```java
        final CompletableFuture<Void> tryFire(int mode) {
            ... // 类似 UniAccept 处理
                            f.run();        // 调用 Runnable 运行
                            d.completeNull();
            ...
        }
```