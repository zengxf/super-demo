# ZooKeeper-单机本地部署


## 下载
- https://zookeeper.apache.org/releases.html
  - 点击 `Apache ZooKeeper $version` 链接
- 再点击：https://dlcdn.apache.org/zookeeper/zookeeper-$version/apache-zookeeper-$version-bin.tar.gz
  - 下载后解压


## 初始配置
- 进入 `./conf` 目录
  - 复制 `zoo_sample.cfg` 命名为 `zoo.cfg`


## 启动
- 双击 `./bin/zkServer.cmd`


## 测试
- 参考：https://zookeeper.apache.org/doc/r3.9.2/zookeeperStarted.html
- 双击 `./bin/zkCli.cmd`

```js
[zk: localhost:2181(CONNECTED) 4] ls /
[zookeeper]

[zk: localhost:2181(CONNECTED) 5] create /test
Created /test

[zk: localhost:2181(CONNECTED) 6] set /test ab

[zk: localhost:2181(CONNECTED) 7] get /test
ab

[zk: localhost:2181(CONNECTED) 8]
```