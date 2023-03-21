## 版本
- 5.0.14.1

## Ref
- 伪集群搭建 https://www.cnblogs.com/tanghaorong/p/14339880.html

## 准备
- 创建目录：`D:\Data\test\Redis\cluster`
  - 在此目录下再创建目录：
```js
> cd /d D:\Data\test\Redis\cluster
  md node-6391-data
  md node-6392-data
  md node-6393-data 
  md node-6394-data
  md node-6395-data 
  md node-6396-data
```

## 启动
```js
> cd /d D:\MyData\pub-project\super-demo\Redis\cluster

> redis-server node-6391.conf
> redis-server node-6392.conf
> redis-server node-6393.conf
> redis-server node-6394.conf
> redis-server node-6395.conf
> redis-server node-6396.conf
```

## 搭建集群
```js
// 4 个节点创建不了
PS C:\Users\feng> redis-cli --cluster create 127.0.0.1:6391 127.0.0.1:6392 127.0.0.1:6393 127.0.0.1:6394 --cluster-replicas 1
*** ERROR: Invalid configuration for cluster creation.
*** Redis Cluster requires at least 3 master nodes.
*** This is not possible with 4 nodes and 1 replicas per node.
*** At least 6 nodes are required.
// 6 个节点才能创建成功
PS C:\Users\feng> redis-cli --cluster create 127.0.0.1:6391 127.0.0.1:6392 127.0.0.1:6393 127.0.0.1:6394 127.0.0.1:6395 127.0.0.1:6396 --cluster-replicas 1
>>> Performing hash slots allocation on 6 nodes...
Master[0] -> Slots 0 - 5460
Master[1] -> Slots 5461 - 10922
Master[2] -> Slots 10923 - 16383
Adding replica 127.0.0.1:6395 to 127.0.0.1:6391
Adding replica 127.0.0.1:6396 to 127.0.0.1:6392
Adding replica 127.0.0.1:6394 to 127.0.0.1:6393
>>> Trying to optimize slaves allocation for anti-affinity
[WARNING] Some slaves are in the same host as their master
M: 8f2f4893d9c3b4be1e96f34088d0358e20eac312 127.0.0.1:6391
   slots:[0-5460] (5461 slots) master
M: f80ca0aae880e2c1bda65272c78d258aeeca390e 127.0.0.1:6392
   slots:[5461-10922] (5462 slots) master
M: 4466f90e337131ed8c99eaa0b5aad0cab7cc194f 127.0.0.1:6393
   slots:[10923-16383] (5461 slots) master
S: d32b3cc90dace55b85c0dd51d28be136cfd37a7a 127.0.0.1:6394
   replicates f80ca0aae880e2c1bda65272c78d258aeeca390e
S: cbeba26792d985c70be1736f4c5968b3837f8a40 127.0.0.1:6395
   replicates 4466f90e337131ed8c99eaa0b5aad0cab7cc194f
S: 131e34b53729610cbc31048244ac3ad31115f586 127.0.0.1:6396
   replicates 8f2f4893d9c3b4be1e96f34088d0358e20eac312
Can I set the above configuration? (type 'yes' to accept): yes
>>> Nodes configuration updated
>>> Assign a different config epoch to each node
>>> Sending CLUSTER MEET messages to join the cluster
Waiting for the cluster to join
.
>>> Performing Cluster Check (using node 127.0.0.1:6391)
M: 8f2f4893d9c3b4be1e96f34088d0358e20eac312 127.0.0.1:6391
   slots:[0-5460] (5461 slots) master
   1 additional replica(s)
S: d32b3cc90dace55b85c0dd51d28be136cfd37a7a 127.0.0.1:6394
   slots: (0 slots) slave
   replicates f80ca0aae880e2c1bda65272c78d258aeeca390e
S: cbeba26792d985c70be1736f4c5968b3837f8a40 127.0.0.1:6395
   slots: (0 slots) slave
   replicates 4466f90e337131ed8c99eaa0b5aad0cab7cc194f
S: 131e34b53729610cbc31048244ac3ad31115f586 127.0.0.1:6396
   slots: (0 slots) slave
   replicates 8f2f4893d9c3b4be1e96f34088d0358e20eac312
M: f80ca0aae880e2c1bda65272c78d258aeeca390e 127.0.0.1:6392
   slots:[5461-10922] (5462 slots) master
   1 additional replica(s)
M: 4466f90e337131ed8c99eaa0b5aad0cab7cc194f 127.0.0.1:6393
   slots:[10923-16383] (5461 slots) master
   1 additional replica(s)
[OK] All nodes agree about slots configuration.
>>> Check for open slots...
>>> Check slots coverage...
[OK] All 16384 slots covered.
PS C:\Users\feng>
```

## 测试
```js
// 查看集群信息
PS C:\Users\feng> redis-cli --cluster check 127.0.0.1:6391
127.0.0.1:6391 (8f2f4893...) -> 0 keys | 5461 slots | 1 slaves.
127.0.0.1:6392 (f80ca0aa...) -> 0 keys | 5462 slots | 1 slaves.
127.0.0.1:6393 (4466f90e...) -> 0 keys | 5461 slots | 1 slaves.

// 添加主节点
redis-cli --cluster add-node 127.0.0.1:6397 127.0.0.1:6391
// 为 6397 端口增加卡槽
redis-cli --cluster reshard 127.0.0.1:6397
// 添加从节点
redis-cli --cluster add-node 127.0.0.1:6398 127.0.0.1:6391 --cluster-slave --cluster-master-id e3ed175cd38c9ea5b7a0827f2be7b8bfa9385ba2
// 删除从节点
redis-cli --cluster del-node 127.0.0.1:6398 609e99ae01ce067323f8c44207f512b5cd3546e2
// 删除主节点
  // 首先要将它的 slot 卡槽全部提取到别的 master 节点上
  redis-cli --cluster reshard 127.0.0.1:6391
  3000 // 先输入数量
  f80ca0aae880e2c1bda65272c78d258aeeca390e // 接收的节点 ID
  73f19b384906113507b25f256a781ce184777162 // 提取的节点 ID
  done // 完成
// 如果想卡槽分配均匀，可使用如下命令：
redis-cli --cluster rebalance --cluster-threshold 1 127.0.0.1:6391
// 删除 6397 master节点
redis-cli --cluster del-node 127.0.0.1:6397 73f19b384906113507b25f256a781ce184777162

// CRUD 测试：-c 表示集群；-p 是端口
PS C:\Users\feng> redis-cli -c -h 127.0.0.1 -p 6391
127.0.0.1:6391> set testa abc
OK
127.0.0.1:6391> get testa
"abc"
127.0.0.1:6391> set testb ab
-> Redirected to slot [14390] located at 127.0.0.1:6393
OK 
// 会自动跳转
127.0.0.1:6393> get testa
-> Redirected to slot [2133] located at 127.0.0.1:6391
"abc"
127.0.0.1:6391> get testb
-> Redirected to slot [14390] located at 127.0.0.1:6393
"ab"
127.0.0.1:6393> set testc aa
-> Redirected to slot [10263] located at 127.0.0.1:6392
OK
127.0.0.1:6392> get testc
"aa"
127.0.0.1:6392> get testa
-> Redirected to slot [2133] located at 127.0.0.1:6391
"abc"
127.0.0.1:6391>
```