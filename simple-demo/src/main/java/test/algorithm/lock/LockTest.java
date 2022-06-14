package test.algorithm.lock;

import lombok.extern.slf4j.Slf4j;
import util.SleepUtils;

import java.util.concurrent.locks.Lock;

/**
 * <br/>
 * Created by ZXFeng on 2022/6/14.
 */
@Slf4j
public class LockTest {

    public static void main(String[] args) {
        // Lock lock = new CLHLock();
        Lock lock = new MCSLock();

        Runnable run = () -> {
            for (int i = 1; i <= 5; i++) {
                log.info("第 [{}] 次进入加锁！", i);
                lock.lock();
                try {
                    log.info("第 [{}] 次-获得-锁！并睡眠 100 ms.", i);
                    SleepUtils.millisecond(100L);
                } finally {
                    lock.unlock();
                    log.info("第 [{}] 次 释放 锁！", i);
                }
            }
        };

        new Thread(run, "Test-Local-A1").start();
        new Thread(run, "Test-Local-B2").start();
    }

}
