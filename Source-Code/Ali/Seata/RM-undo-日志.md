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
            connectionProxy.appendUndoLog(sqlUndoLog); // 暂存到连接代理，ref: sign_m_120
        }
    }
}
```

- `io.seata.rm.datasource.ConnectionProxy`
```java
public class ConnectionProxy extends AbstractConnectionProxy {
    private final ConnectionContext context = new ConnectionContext();

    // sign_m_120  追加 undo 日志
    public void appendUndoLog(SQLUndoLog sqlUndoLog) {
        context.appendUndoItem(sqlUndoLog); // 暂存到上下文中，ref: sign_m_130
    }
}
```

- `io.seata.rm.datasource.ConnectionContext`
```java
public class ConnectionContext {
    private Savepoint currentSavepoint = DEFAULT_SAVEPOINT;
    private final Map<Savepoint, List<SQLUndoLog>> sqlUndoItemsBuffer = new LinkedHashMap<>(); // sign_f_130

    // sign_m_130  追加 undo
    void appendUndoItem(SQLUndoLog sqlUndoLog) {
        sqlUndoItemsBuffer.computeIfAbsent(currentSavepoint, k -> new ArrayList<>())
            .add(sqlUndoLog); // 追加到默认的保存点里面
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

    // sign_m_210  插入 undo 日志
    @Override   // 调用源，ref: sign_m_220
    protected void insertUndoLogWithNormal(String xid, long branchId, String rollbackCtx, byte[] undoLogContent,
                                           Connection conn) throws SQLException {
        insertUndoLog(xid, branchId, rollbackCtx, undoLogContent, State.Normal, conn); // ref: sign_m_211
    }

    // sign_m_211  保存到 DB
    private void insertUndoLog(String xid, long branchId, String rollbackCtx, byte[] undoLogContent,
                               State state, Connection conn) throws SQLException {
        try (PreparedStatement pst = conn.prepareStatement(INSERT_UNDO_LOG_SQL)) {
            pst.setLong(1, branchId);
            pst.setString(2, xid);
            pst.setString(3, rollbackCtx);
            pst.setBytes(4, undoLogContent);
            pst.setInt(5, state.getValue());
            pst.executeUpdate();
        } ... // catch
    }

}
```

- `io.seata.rm.datasource.undo.AbstractUndoLogManager`
```java
// sign_c_220
public abstract class AbstractUndoLogManager implements UndoLogManager {
    
    // sign_m_220  刷新到 DB
    @Override
    public void flushUndoLogs(ConnectionProxy cp) throws SQLException {
        ConnectionContext connectionContext = cp.getContext();
        ...

        String xid = connectionContext.getXid();
        long branchId = connectionContext.getBranchId();

        BranchUndoLog branchUndoLog = new BranchUndoLog();
        branchUndoLog.setXid(xid);
        branchUndoLog.setBranchId(branchId);
        branchUndoLog.setSqlUndoLogs(connectionContext.getUndoItems()); // 从上下文中获取，数据参考: sign_f_130

        UndoLogParser parser = UndoLogParserFactory.getInstance();
        byte[] undoLogContent = parser.encode(branchUndoLog);

        ... // log
        ... // 压缩

        insertUndoLogWithNormal(xid, branchId, ..., undoLogContent, cp.getTargetConnection()); // ref: sign_m_210
    }
}
```