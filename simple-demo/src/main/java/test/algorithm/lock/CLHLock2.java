package test.algorithm.lock;

import lombok.Data;

import java.util.concurrent.TimeUnit;
import java.util.concurrent.atomic.AtomicReference;
import java.util.concurrent.locks.Condition;
import java.util.concurrent.locks.Lock;

/**
 * 参考：疯狂创客圈
 * <br/>
 * Created by ZXFeng on 2022/6/16.
 */
public class CLHLock2 implements Lock {

    /*** 指向当前节点 */
    private static ThreadLocal<Node> curNodeLocal = new ThreadLocal();
    private String name;
    /*** CLHLock 队列的尾部 */
    private AtomicReference<Node> tail = new AtomicReference<>(null);

    public CLHLock2() {
        this.name = "CLHLock2-def";
        // 设置尾部节点
        tail.getAndSet(Node.EMPTY);
    }

    // 加锁：将节点添加到等待队列的尾部
    @Override
    public void lock() {
        Node curNode = new Node(true, null);
        Node preNode = tail.get();
        // CAS 自旋：将当前节点插入到队列的尾部
        while (!tail.compareAndSet(preNode, curNode)) {
            preNode = tail.get();
        }
        // 设置前驱
        curNode.setPrevNode(preNode);

        // 监听前驱节点的 locked 变量，直到其值为 false
        // 若前继节点的 locked 状态为 true，则表示前一线程还在抢占或者占有锁
        while (curNode.getPrevNode().isLocked()) {
            // 让出 CPU 时间片，提高性能
            Thread.yield();
        }
        // 能执行到这里，说明当前线程获取到了锁
        // 设置在线程本地变量中，用于释放锁
        curNodeLocal.set(curNode);
    }

    @Override
    public void unlock() {
        Node curNode = curNodeLocal.get();
        curNode.setPrevNode(null); // help for GC
        curNodeLocal.set(null);
        curNode.setLocked(false);
    }

    @Data
    static class Node {
        public Node(boolean locked, Node prevNode) {
            this.locked = locked;
            this.prevNode = prevNode;
        }

        // true：当前线程正在抢占锁、或者已经占有锁
        // false：当前线程已经释放锁，下一个线程可以占有锁了
        volatile boolean locked;
        // 前一个节点，需要监听其locked字段
        Node prevNode;
        // 空节点
        public static final Node EMPTY = new Node(false, null);
    }

    @Override
    public void lockInterruptibly() {
        throw new RuntimeException("未实现！");
    }

    @Override
    public boolean tryLock() {
        throw new RuntimeException("未实现！");
    }

    @Override
    public boolean tryLock(long time, TimeUnit unit) {
        throw new RuntimeException("未实现！");
    }

    @Override
    public Condition newCondition() {
        throw new RuntimeException("未实现！");
    }

    @Override
    public String toString() {
        return "CLHLock{" + name + '}';
    }

}