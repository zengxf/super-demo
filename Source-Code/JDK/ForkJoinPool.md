# JDK-ForkJoinPool


---
## JDK 版本
```js
openjdk version "17.0.12" 2024-07-16
OpenJDK Runtime Environment Temurin-17.0.12+7 (build 17.0.12+7)
OpenJDK 64-Bit Server VM Temurin-17.0.12+7 (build 17.0.12+7, mixed mode, sharing)
```


---
## 测试
```java
@Slf4j
public class MixTest {

    @Test
    public void testFJ() throws Exception {
        ForkJoinPool forkJoinPool = new ForkJoinPool();
        CountTask task = new CountTask(1, 5);
        // System.out.println(task.compute());  // 也可直接用默认的 fj 线程池执行
        Future<Integer> result = forkJoinPool.submit(task);
        System.out.println(result.get());
    }

    public static class CountTask extends RecursiveTask<Integer> {
        private static final int THRESHOLD = 2;     // 阈值
        private final int start;
        private final int end;

        public CountTask(int start, int end) {
            this.start = start;
            this.end = end;
        }

        @Override
        public Integer compute() {
            int sum = 0;

            // 如果任务足够小就计算任务
            boolean canCompute = (end - start) <= THRESHOLD;
            if (canCompute) {
                for (int i = start; i <= end; i++) {
                    sum += i;
                }
            } else {
                // 如果任务大于阈值，就分裂成两个子任务计算
                int middle = (start + end) / 2;
                CountTask leftTask = new CountTask(start, middle);
                CountTask rightTask = new CountTask(middle + 1, end);

                // 执行子任务
                leftTask.fork();
                rightTask.fork();

                // 等待子任务执行完，并得到其结果
                int leftResult = leftTask.join();
                int rightResult = rightTask.join();

                // 合并子任务结果
                sum = leftResult + rightResult;
            }
            return sum;
        }
    }
}
```


---
## 原理
### 类结构
- `java.util.concurrent.ForkJoinPool`
```java
public class ForkJoinPool extends AbstractExecutorService {
    WorkQueue[] queues;                  // main registry
    final ForkJoinWorkerThreadFactory factory;
    final UncaughtExceptionHandler ueh;  // per-worker UEH
    final String workerNamePrefix;       // 创建工作线程的名称前缀
}
```

- `java.util.concurrent.ForkJoinPool.WorkQueue`
```java
    static final class WorkQueue {
        ForkJoinTask<?>[] array;   // 排队的任务；大小为 2 的幂
        final ForkJoinWorkerThread owner; // 拥有线程或共享时为 null
    }
```

- `java.util.concurrent.ForkJoinWorkerThread`
```java
public class ForkJoinWorkerThread extends Thread {
    final ForkJoinPool pool;                // 此线程所在的池
    final ForkJoinPool.WorkQueue workQueue; // 工作窃取机制
}
```

### 初始化
- `java.util.concurrent.ForkJoinPool`
```java
public class ForkJoinPool extends AbstractExecutorService {
    public ForkJoinPool() {
        this(
            Math.min(MAX_CAP, Runtime.getRuntime().availableProcessors()),  // cpus: 20
            defaultForkJoinWorkerThreadFactory, 
            null, false,
            0, MAX_CAP, // 0x7fff ==> 32767
            1, null, 
            DEFAULT_KEEPALIVE, TimeUnit.MILLISECONDS    // def: 60s
        );
    }

    public ForkJoinPool(
        int parallelism, ForkJoinWorkerThreadFactory factory, UncaughtExceptionHandler handler,
        ..., long keepAliveTime, TimeUnit unit
    ) {
        ...
        int p = parallelism;    // = cpus = 20
        this.factory = factory;
        this.ueh = handler;
        this.keepAlive = Math.max(unit.toMillis(keepAliveTime), TIMEOUT_SLOP);  // = 60s
        int size = 1 << (33 - Integer.numberOfLeadingZeros(p - 1));             // = 64
        ...

        this.registrationLock = new ReentrantLock();
        this.queues = new WorkQueue[size];
        String pid = Integer.toString(getAndAddPoolIds(1) + 1);                 // = 1
        this.workerNamePrefix = "ForkJoinPool-" + pid + "-worker-";
    }


    static {
        ...

        defaultForkJoinWorkerThreadFactory = new DefaultForkJoinWorkerThreadFactory();
        ...

        ForkJoinPool tmp = ... new ForkJoinPool((byte) 0);
        common = tmp;   // 通用共公池
    }
}
```

- `java.util.concurrent.ForkJoinPool.DefaultForkJoinWorkerThreadFactory`
```java
    static final class DefaultForkJoinWorkerThreadFactory implements ForkJoinWorkerThreadFactory {

        
        public final ForkJoinWorkerThread newThread(ForkJoinPool pool) {
            return ... new ForkJoinWorkerThread(null, pool, true, false);
        }
    }
```

### 启动线程
- `java.util.concurrent.ForkJoinPool`
```java
public class ForkJoinPool extends AbstractExecutorService {

    public <T> ForkJoinTask<T> submit(ForkJoinTask<T> task) {
        return externalSubmit(task);
    }

    private <T> ForkJoinTask<T> externalSubmit(ForkJoinTask<T> task) {
        Thread t; ForkJoinWorkerThread wt; WorkQueue q;
        ... // 校验参数

        if (((t = Thread.currentThread()) instanceof ForkJoinWorkerThread) &&   // 第一次进来，不是 FJ 线程
            (q = (wt = (ForkJoinWorkerThread)t).workQueue) != null &&           //            且队列为空
            wt.pool == this)
            q.push(task, this);
        else    // 走此逻辑
            externalPush(task);
        return task;
    }

    final void externalPush(ForkJoinTask<?> task) {
        WorkQueue q;
        if ((q = submissionQueue()) == null)        // 查找或创建 WorkQueue
            throw ...;                  // shutdown or disabled
        else if (q.lockedPush(task))    // 添加到队列
            signalWork();               // 添加成功，则创建或唤醒线程
    }

    final void signalWork() {
        for (long c = ctl; c < 0L;) {
            int sp, i; WorkQueue[] qs; WorkQueue v;
            if ((sp = (int)c & ~UNSIGNALLED) == 0) {  // no idle workers
                ...
                    createWorker();                 // 创建线程
                    break;
            }
            ... // 其他状态校验

            else {
                ...
                Thread vt = v.owner;
                ...
                    LockSupport.unpark(vt);         // 唤醒线程
                    break;
            }
        }
    }

    private boolean createWorker() {
        ForkJoinWorkerThreadFactory fac = factory;
        ForkJoinWorkerThread wt = null;
        try {
            if (fac != null
                && (wt = fac.newThread(this)) != null   // 创建线程
            ) {
                wt.start();     // 启动线程
                return true;
            }
        }
        ... // catch
        return false;
    }

}
```

### 执行
- `java.util.concurrent.ForkJoinWorkerThread`
```java
public class ForkJoinWorkerThread extends Thread {

    public void run() {
        ForkJoinPool p = pool;
        ForkJoinPool.WorkQueue w = workQueue;
        if (p != null && w != null) {   // 初始化失败时跳过
            try {
                p.registerWorker(w);
                onStart();              // (空实现，子类可覆盖)
                p.runWorker(w);         // (这是关键) 执行任务
            } 
            ... // catch ... finally 
        }
    }
}
```

- `java.util.concurrent.ForkJoinPool`
```java
public class ForkJoinPool extends AbstractExecutorService {

    final void runWorker(WorkQueue w) {
        if (mode >= 0 && w != null) {           // skip on failed init
            w.config |= SRC;                    // mark as valid source
            int r = w.stackPred, src = 0;       // use seed from registerWorker
            do {
                r ^= r << 13; r ^= r >>> 17; r ^= r << 5;   // xorshift
            } while ((src = scan(w, src, r)) >= 0 ||        // 扫描并支行任务
                     (src = awaitWork(w)) == 0);
        }
    }
}
```