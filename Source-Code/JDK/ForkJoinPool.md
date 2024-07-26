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

### 执行
- `java.util.concurrent.ForkJoinPool`
```java
public class ForkJoinPool extends AbstractExecutorService {

    public <T> ForkJoinTask<T> submit(ForkJoinTask<T> task) {
        return externalSubmit(task);
    }

    private <T> ForkJoinTask<T> externalSubmit(ForkJoinTask<T> task) {
        Thread t; ForkJoinWorkerThread wt; WorkQueue q;
        ... // 校验参数

        if (((t = Thread.currentThread()) instanceof ForkJoinWorkerThread) &&
            (q = (wt = (ForkJoinWorkerThread)t).workQueue) != null &&   // 第一次进来，队列为空
            wt.pool == this)
            q.push(task, this);
        else    // 走此逻辑
            externalPush(task);
        return task;
    }

    final void externalPush(ForkJoinTask<?> task) {
        WorkQueue q;
        if ((q = submissionQueue()) == null)        // 查找或创建 WorkQueue
            throw new RejectedExecutionException(); // shutdown or disabled
        else if (q.lockedPush(task))
            signalWork();
    }
}
```