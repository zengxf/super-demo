# Seata-TM-事务处理


---
## 调用源
- 参考：[AOP-注解处理-处理实现 sign_cb_231](./AOP-注解处理.md#处理实现)


---
## 事务控制
- `io.seata.tm.api.TransactionalTemplate`
```java
// sign_c_110  事务处理模板
public class TransactionalTemplate {
    
    // sign_m_110  事务模板执行
    public Object execute(TransactionalExecutor business) throws Throwable {
        // 1. Get transactionInfo
        TransactionInfo txInfo = business.getTransactionInfo();
        ...
        // 1.1 获取当前事务，如果不是 null，则 tx 角色为参与者: 'GlobalTransactionRole.Participant'.
        GlobalTransaction tx = GlobalTransactionContext.getCurrent(); // ref: sign_m_121

        // 1.2 处理事务传播。
        Propagation propagation = txInfo.getPropagation();
        SuspendedResourcesHolder suspendedResourcesHolder = null;
        try {
            switch (propagation) {
                case NOT_SUPPORTED: // 不支持（当前若有则挂着）
                    if (existingTransaction(tx)) { // 存在事务
                        suspendedResourcesHolder = tx.suspend(false); // 挂起，ref: sign_m_214
                    }
                    return business.execute(); // 执行业务代码，并返回
                case REQUIRES_NEW:  // 需要新的（当前若有则挂着，并创建新的）
                    if (existingTransaction(tx)) {
                        suspendedResourcesHolder = tx.suspend(false); // 挂起，ref: sign_m_214
                    }
                    tx = GlobalTransactionContext.createNew(); // 创建新的事务，ref: sign_m_120
                    break;
                case SUPPORTS:      // 支持（有就用，没有也不创建）
                    if (notExistingTransaction(tx)) {
                        return business.execute(); // 执行业务代码，并返回
                    }
                    // 继续并执行当前事务
                    break;
                case REQUIRED:      // 需要（用当前或创建新的）
                    // 如果当前事务存在，则使用当前事务执行，否则创建新的
                    tx = GlobalTransactionContext.getCurrentOrCreate();// ref: sign_m_122
                    break;
                case NEVER:         // 从不（绝不能有）
                    if (existingTransaction(tx)) { // 存在事务的话，就抛异常
                        throw new TransactionException(...);
                    } else {
                        return business.execute(); // 执行业务代码，并返回
                    }
                case MANDATORY:     // 强制（绝不能没有）
                    if (notExistingTransaction(tx)) { // 不存在事务的话，就抛异常
                        throw new TransactionException(...);
                    }
                    // 继续并执行当前事务
                    break;
                ...
            }

            ...

            try {
                // 2. 如果 tx 角色是‘GlobalTransactionRole.Launcher’，则向 TC 发送 beginTransaction 请求，
                beginTransaction(txInfo, tx); // 开启事务，ref: sign_m_112

                Object rs;
                try {
                    rs = business.execute(); // 执行业务代码
                } catch (Throwable ex) {
                    // 3. 业务异常，根据异常类型回滚或提交事务
                    completeTransactionAfterThrowing(txInfo, tx, ex); // 异常处理，ref: sign_m_114
                    throw ex;
                }

                // 4. 全部完成，提交事务
                commitTransaction(tx, txInfo); // ref: sign_m_113
                return rs;
            }
            ... // finally { }
        } 
        ... // finally { }
    }

    // sign_m_111  判断是否存在事务
    private boolean existingTransaction(GlobalTransaction tx) {
        return tx != null; // 不为空，就表示存在
    }

    // sign_m_112  开启事务
    private void beginTransaction(TransactionInfo txInfo, GlobalTransaction tx) throws ...Exception {
        ... // 不是发起者，直接返回

        try {
            triggerBeforeBegin();   // 钩子(前)处理
            tx.begin(txInfo.getTimeOut(), txInfo.getName()); // 开启事务，ref: sign_m_210
            triggerAfterBegin();    // 钩子(后)处理
        } ... // catch
    }

    // sign_m_113  提交事务
    private void commitTransaction(GlobalTransaction tx, TransactionInfo txInfo) throws ...Exception {
        ... // 不是发起者，直接返回

        ... // 如果超时，则回滚事务并抛出异常

        try {
            triggerBeforeCommit();  // 钩子(前)处理
            tx.commit(); // ref: sign_m_211
            GlobalStatus afterCommitStatus = tx.getLocalStatus();
            ... // 提交后状态校验
            triggerAfterCommit();   // 钩子(后)处理
        } ... // catch
    }

    // sign_m_114  异常处理
    private void completeTransactionAfterThrowing(TransactionInfo txInfo, GlobalTransaction tx, Throwable originalException) throws ...Exception {
        if (txInfo != null && txInfo.rollbackOn(originalException)) { // 此异常要回滚，则回滚
            rollbackTransaction(tx, originalException); // ref: sign_m_115
        } else { // 不要回滚此异常，则提交
            commitTransaction(tx, txInfo); // ref: sign_m_113
        }
    }

    // sign_m_115  回滚事务
    private void rollbackTransaction(GlobalTransaction tx, Throwable originalException) throws ...Exception {
        ... // 不是发起者，直接返回
        try {
            triggerBeforeRollback();    // 钩子(前)处理
            tx.rollback(); // ref: sign_m_212
            triggerAfterRollback();     // 钩子(后)处理
        } ... // catch

        TransactionalExecutor.Code code;
        ...
        throw new TransactionalExecutor.ExecutionException(tx, code, originalException); // 继续抛出异常
    }
}
```

- `io.seata.tm.api.GlobalTransactionContext`
```java
// sign_c_120  事务上下文
public class GlobalTransactionContext {

    // sign_m_120  创建新的事务
    public static GlobalTransaction createNew() {
        return new DefaultGlobalTransaction(); // ref: sign_cm_210
    }

    // sign_m_121  获取当前事务
    public static GlobalTransaction getCurrent() {
        String xid = RootContext.getXID();
        if (xid == null) { // 没有 xid，表示未开启事务，返回 null
            return null;
        }
        // 已存在就是"参与者"角色
        return new DefaultGlobalTransaction(xid, GlobalStatus.Begin, GlobalTransactionRole.Participant); // ref: sign_cm_211
    }

    // sign_m_122  获取当前事务或创建新的
    public static GlobalTransaction getCurrentOrCreate() {
        GlobalTransaction tx = getCurrent(); // ref: sign_m_121
        if (tx == null) {
            return createNew(); // ref: sign_m_120
        }
        return tx;
    }
}
```


---
## 底层逻辑
- `io.seata.tm.api.DefaultGlobalTransaction`
```java
// sign_c_210  默认全局事务
public class DefaultGlobalTransaction implements GlobalTransaction {
    
    private TransactionManager transactionManager;
    private String xid;

    // sign_cm_210
    DefaultGlobalTransaction() {
        // 默认为发起者
        this(null, GlobalStatus.UnKnown, GlobalTransactionRole.Launcher);
    }

    // sign_cm_211
    DefaultGlobalTransaction(String xid, GlobalStatus status, GlobalTransactionRole role) {
        this.transactionManager = TransactionManagerHolder.get();  // 通过 SPI 查找事务管理器
        this.xid = xid;
        this.status = status;
        this.role = role;
    }

    // sign_m_210  开启事务
    @Override
    public void begin(int timeout, String name) throws TransactionException {
        this.createTime = System.currentTimeMillis();
        
        ... // 不是发起者，校验 xid，并直接返回
        ... // 校验 xid

        xid = transactionManager.begin(null, null, name, timeout); // 通过管理器开启事务，ref: sign_m_310
        status = GlobalStatus.Begin;
        RootContext.bind(xid); // 绑定 xid

        ...
    }

    // sign_m_211  提交事务
    @Override
    public void commit() throws TransactionException {
        ... // 不是发起者，并直接返回
        assertXIDNotNull();

        ...
        int retry = COMMIT_RETRY_COUNT <= 0 ? DEFAULT_TM_COMMIT_RETRY_COUNT : COMMIT_RETRY_COUNT;
        try {
            while (retry > 0) {
                try {
                    retry--;
                    status = transactionManager.commit(xid); // 通过管理器提交事务
                    break;
                } ... // catch 
            }
        } finally {
            if (xid.equals(RootContext.getXID())) {
                suspend(true); // ref: sign_m_214
            }
        }
        ...
    }

    // sign_m_212  回滚事务
    @Override
    public void rollback() throws TransactionException {
        ... // 不是发起者，并直接返回
        assertXIDNotNull();

        ...
        int retry = ROLLBACK_RETRY_COUNT <= 0 ? DEFAULT_TM_ROLLBACK_RETRY_COUNT : ROLLBACK_RETRY_COUNT;
        try {
            while (retry > 0) {
                try {
                    retry--;
                    status = transactionManager.rollback(xid);// 通过管理器回滚事务
                    break;
                } ... // catch
            }
        } finally {
            if (xid.equals(RootContext.getXID())) {
                suspend(true); // ref: sign_m_214
            }
        }
        ...
    }

    // sign_m_214  挂起事务 (只是清空 xid)
    @Override
    public SuspendedResourcesHolder suspend(boolean clean) throws TransactionException {
        // In order to associate the following logs with XID, first get and then unbind.
        String xid = RootContext.getXID();
        if (xid != null) {
            ...
            RootContext.unbind();
            return clean ? null : new SuspendedResourcesHolder(xid);
        } ... // else
    }

    // sign_m_215  恢复事务 (只是绑定 xid)
    @Override
    public void resume(SuspendedResourcesHolder suspendedResourcesHolder) throws TransactionException {
        ...
        
        String xid = suspendedResourcesHolder.getXid();
        RootContext.bind(xid);
        ...
    }
}
```


---
## 事务管理器
- `io.seata.tm.DefaultTransactionManager`
  - 参考：[TM-通信客户端-发送请求 sign_m_310](TM-通信客户端.md#发送请求)
```java
// sign_c_310  默认事务管理器
public class DefaultTransactionManager implements TransactionManager {

    // sign_m_310  开启事务，并返回 xid
    @Override
    public String begin(..., String name, int timeout) throws TransactionException {
        GlobalBeginRequest request = new GlobalBeginRequest();
        request.setTransactionName(name);
        request.setTimeout(timeout);

        GlobalBeginResponse response = (GlobalBeginResponse) syncCall(request); // ref: sign_m_320
        ...
        return response.getXid();
    }

    // sign_m_320  请求事务控制器
    private AbstractTransactionResponse syncCall(AbstractTransactionRequest request) throws TransactionException {
        try {
            // 使用 Netty 进行请求 (端口: 8091)，
            // 参考：[TM-通信客户端-发送请求 sign_m_310]
            return (...) TmNettyRemotingClient.getInstance().sendSyncRequest(request); 
        } ... // catch
    }
}
```