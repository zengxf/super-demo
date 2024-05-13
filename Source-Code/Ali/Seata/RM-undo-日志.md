# Seata-RM-undo-日志


---
## 创建源
- 参考：[RM-事务处理-执行-SQL sign_m_532](./RM-事务处理.md#执行-SQL)


---
## 暂存
- `io.seata.rm.datasource.exec.BaseTransactionalExecutor`
```java
// sign_c_110
public abstract class BaseTransactionalExecutor<T, S extends Statement> implements Executor<T> {

    // sign_m_110  暂存 undo 日志
    protected void prepareUndoLog(TableRecords beforeImage, TableRecords afterImage) throws SQLException {
        ...
        ConnectionProxy connectionProxy = statementProxy.getConnectionProxy();

        TableRecords lockKeyRecords = sqlRecognizer.getSQLType() == SQLType.DELETE ? beforeImage : afterImage;
        String lockKeys = buildLockKey(lockKeyRecords);
        if (null != lockKeys) {
            connectionProxy.appendLockKey(lockKeys);

            SQLUndoLog sqlUndoLog = buildUndoItem(beforeImage, afterImage);
            connectionProxy.appendUndoLog(sqlUndoLog); // 暂存到连接代理
        }
    }
}
```


---
## 持久化
- `io.seata.rm.datasource.undo.mysql.MySQLUndoLogManager`
```java
// sign_c_210
@LoadLevel(name = JdbcConstants.MYSQL)
public class MySQLUndoLogManager extends AbstractUndoLogManager {

    // sign_m_210
    @Override
    protected void insertUndoLogWithNormal(String xid, long branchId, String rollbackCtx, byte[] undoLogContent,
                                           Connection conn) throws SQLException {
        insertUndoLog(xid, branchId, rollbackCtx, undoLogContent, State.Normal, conn);
    }

}
```

- `io.seata.rm.datasource.undo.AbstractUndoLogManager`
```java
// sign_c_220
public abstract class AbstractUndoLogManager implements UndoLogManager {
    
    // sign_m_220  插入到 DB
    @Override
    public void flushUndoLogs(ConnectionProxy cp) throws SQLException {
        ConnectionContext connectionContext = cp.getContext();
        ...

        String xid = connectionContext.getXid();
        long branchId = connectionContext.getBranchId();

        BranchUndoLog branchUndoLog = new BranchUndoLog();
        branchUndoLog.setXid(xid);
        branchUndoLog.setBranchId(branchId);
        branchUndoLog.setSqlUndoLogs(connectionContext.getUndoItems());

        UndoLogParser parser = UndoLogParserFactory.getInstance();
        byte[] undoLogContent = parser.encode(branchUndoLog);

        ... // log
        ... // 压缩

        insertUndoLogWithNormal(xid, branchId, ..., undoLogContent, cp.getTargetConnection()); // ref: sign_m_210
    }
}
```