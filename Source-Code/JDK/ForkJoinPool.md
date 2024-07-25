# JDK-ForkJoinPool


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


## 原理
### 类结构
- `java.util.concurrent.ForkJoinPool`
```java
public class ForkJoinPool extends AbstractExecutorService {
    volatile WorkQueue[] workQueues;     // main registry
    final ForkJoinWorkerThreadFactory factory;
    final UncaughtExceptionHandler ueh;  // per-worker UEH
    final String workerNamePrefix;       // 创建工作线程的名称前缀
}
```

- `java.util.concurrent.ForkJoinPool.WorkQueue`
```java
    static final class WorkQueue {
        ForkJoinTask<?>[] array;   // 元素（最初未分配）
        final ForkJoinPool pool;   // 包含池（可能为空）
        final ForkJoinWorkerThread owner; // 拥有线程或共享时为 null
        volatile Thread parker;    // == owner during call to park; else null
        volatile ForkJoinTask<?> currentJoin;  // 在 awaitJoin 中加入的任务
        volatile ForkJoinTask<?> currentSteal; // 主要由 helpStealer 使用
    }
```

- `java.util.concurrent.ForkJoinWorkerThread`
```java
public class ForkJoinWorkerThread extends Thread {
    final ForkJoinPool pool;                // 此线程所在的池
    final ForkJoinPool.WorkQueue workQueue; // 工作窃取机制
}
```