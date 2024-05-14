# Seata-RM-undo-日志及操作


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


---
## 删除
- `io.seata.rm.datasource.undo.AbstractUndoLogManager`
```java
// sign_c_310
public abstract class AbstractUndoLogManager implements UndoLogManager {

    // sign_m_310  删除单条
    @Override  //  调用源：undo 操作完调用
    public void deleteUndoLog(String xid, long branchId, Connection conn) ... {
        try (PreparedStatement deletePST = conn.prepareStatement(DELETE_UNDO_LOG_SQL)) {
            deletePST.setLong(1, branchId);
            deletePST.setString(2, xid);
            deletePST.executeUpdate(); // 执行删除
        } ... // catch
    }

    // sign_m_311  批量删除
    @Override //  调用源：提交成功后异步删除。ref: AsyncWorker #doBranchCommitSafely()
    public void batchDeleteUndoLog(Set<String> xids, Set<Long> branchIds, Connection conn) throws SQLException {
        ...

        int xidSize = xids.size();
        int branchIdSize = branchIds.size();
        String batchDeleteSql = toBatchDeleteUndoLogSql(xidSize, branchIdSize);
        try (PreparedStatement deletePST = conn.prepareStatement(batchDeleteSql)) {
            ... // 填充 deletePST 参数
            deletePST.executeUpdate(); // 执行删除
            ...
        } ... // catch
    }
}
```


---
## undo-操作
- `io.seata.rm.datasource.undo.AbstractUndoLogManager`
```java
// sign_c_410
public abstract class AbstractUndoLogManager implements UndoLogManager {

    // sign_m_410  undo 处理
    @Override
    public void undo(DataSourceProxy dataSourceProxy, String xid, long branchId) throws TransactionException {
        ...

        for (; ; ) {
            try {
                connectionProxy = dataSourceProxy.getConnection();
                conn = connectionProxy.getTargetConnection();

                ...

                // 查找 undo 日志
                selectPST = conn.prepareStatement(buildSelectUndoSql());
                selectPST.setLong(1, branchId);
                selectPST.setString(2, xid);
                rs = selectPST.executeQuery();

                boolean exists = false;
                while (rs.next()) {
                    exists = true;

                    ... // 校验 undo 日志状态

                    String contextString = rs.getString(ClientTableColumnsName.UNDO_LOG_CONTEXT);
                    Map<String, String> context = parseContext(contextString);
                    byte[] rollbackInfo = getRollbackInfo(rs);                  // 获取回滚内容

                    ...
                    BranchUndoLog branchUndoLog = parser.decode(rollbackInfo);  // 解码 undo

                    try {
                        ...

                        List<SQLUndoLog> sqlUndoLogs = branchUndoLog.getSqlUndoLogs();
                        ...

                        for (SQLUndoLog sqlUndoLog : sqlUndoLogs) {
                            TableMeta tableMeta = ...;
                            sqlUndoLog.setTableMeta(tableMeta);
                            AbstractUndoExecutor undoExecutor = UndoExecutorFactory.getUndoExecutor(
                                dataSourceProxy.getDbType(), sqlUndoLog
                            );
                            undoExecutor.executeOn(connectionProxy); // undo 操作，ref: sign_m_420
                        }
                    } ... // finally
                }

                if (exists) {
                    deleteUndoLog(xid, branchId, conn); // 删除 undo 日志，ref: sign_m_310
                    conn.commit();
                    ...
                } 
                ... // else 

                return;
            }
            ... // catch
            ... // finally 
        }
    }
}
```

- `io.seata.rm.datasource.undo.AbstractUndoExecutor`
```java
// sign_c_420
public abstract class AbstractUndoExecutor {

    // sign_m_420  执行 undo
    public void executeOn(ConnectionProxy connectionProxy) throws SQLException {
        Connection conn = connectionProxy.getTargetConnection();
        ...

        PreparedStatement undoPST = null;
        try {
            String undoSQL = buildUndoSQL();    // 具体由子类实现（修改对应修改，删除对应插入，插入对应删除）
            undoPST = conn.prepareStatement(undoSQL);
            TableRecords undoRows = getUndoRows();
            for (Row undoRow : undoRows.getRows()) {
                ...

                undoPrepare(undoPST, undoValues, pkValueList); // 绑定参数

                undoPST.executeUpdate();        // 执行还原 SQL
            }
        } 
        ... // catch finally
    }
}
```