# Git-命令


---
## 查看远程仓库地址
```shell
git remote -v
```


---
## 删除分支
- ref: https://www.freecodecamp.org/chinese/news/git-delete-branch-how-to-remove-a-local-or-remote-branch/
- 删除本地分支 `git branch -d xxxname`
- 强制删除本地分支 `git branch -D xxxname`
- 删除远程分支 `git push origin -d xxxname`


---
## 从 Tag 创建分支
- ref: https://blog.csdn.net/lhcxwjh/article/details/51083249
- 命令格式: `git branch <new-branch-name> <tag-name>`
- 创建分支: `git branch my-2.2.3 2.2.3`
- 切换分支: `git checkout my-2.2.3`


---
## 设置提交用户
```js
git config user.name ZXF
git config user.email zxf@sina.cn
// 查看
git config user.name
git config user.email
```


---
## 取消合并
- ref: https://www.freecodecamp.org/chinese/news/git-undo-merge-how-to-revert-the-last-merge-commit-in-git/
- `git reflog` 更具可读性
```js
PS D:\Work\Code\java-project> git reflog
bec2563a1 (HEAD -> develop) HEAD@{0}: merge fix-by-zxf-0404: Merge made by the 'ort' strategy.  // 这个是合并的记录
8e56854fd (origin/develop) HEAD@{1}: checkout: moving from fix-by-zxf-0404 to develop           // 回滚到这
c00330270 (origin/fix-by-zxf-0404, fix-by-zxf-0404) HEAD@{2}: checkout: moving from uat_new to fix-by-zxf-0404
4fe8a847f (origin/uat_new, uat_new) HEAD@{3}: commit: task#725839
32e650fc1 HEAD@{4}: commit (merge): task#725839

PS D:\Work\Code\java-project> git reset --hard 8e56854fd                                        // 与上对应
HEAD is now at 8e56854fd Merge branch 'xxx' into 'develop'

PS D:\Work\Code\java-project> git status
On branch develop
Your branch is up to date with 'origin/develop'.

nothing to commit, working tree clean
```


---
## 覆盖远程分支
```js
// locdev 本地分支
// remdev 远程分支

git push origin locdev:remdev -f    // 这个才有用 (本地应该是不要在 locdev 分支上使用此命令)

git push origin remdev --force      // 这个命令没用，只是推，不会覆盖
```


---
## 恢复某个文件到上一个提交版本
- ref: https://blog.csdn.net/I_recluse/article/details/88105385
- 但需要重新提交一次
```js
// 1. 首先查看一下该文件的 commit 记录：git log 文件，例如 
git log src/index.java

// 2. 找到需要提交到上一个版本的 commit 号，然后 checkout 该文件的上一版本，输入下面的指令：
// git checkout [commit id] 文件，例如 
git checkout a57fb4b474888f0db4cba18de2180496 src/index.java

// 3. 然后将 checkout 的版本提交到本地
git commit -m "回退到上一版本"

// 4. 最后将改变提交到分支远程：
git push origin 分支名
```


---
## 恢复删除的文件
- ref: https://www.cnblogs.com/yangshifu/p/9680993.html
```shell
git reset HEAD file-or-folder
git checkout file-or-folder
```


---
## GitHub: Clone succeeded, but checkout failed
- **文件名太长**
- ref: https://stackoverflow.com/questions/22041752/github-clone-succeeded-but-checkout-failed
```shell
git config --system core.longpaths true
```


---
## gc 问题
- `git pull` 出现下面问题
```js
See "git help gc" for manual housekeeping.
fatal: bad tree object 957463d7e3bc6725bd571902a09d0b618c307413
fatal: failed to run repack
error: task 'gc' failed
```

- 解决参考：https://stackoverflow.com/questions/9005756/how-to-fix-a-bad-git-tree-object
```shell
// 修复命令：
git fetch --refetch
git gc --aggressive

// 校验是否修复：
git fsck
```


---
## 暂存
- https://www.cnblogs.com/tocy/p/git-stash-reference.html
```shell
# 暂存并备注
git stash save "备注1"

# 查看暂存记录
git stash list

# 重新应用并删除
git stash pop

# 删除第一个
git stash drop stash@{0}
```


---
## ssh
```shell
# 没有就创建 .ssh 目录
cd ~/.ssh

# 生成 key (直接回车就是了)
ssh-keygen -t rsa -b 4096 -C "xx@xx.com"

# 将生成的 id_rsa.pub 内容保存到 Git 网站上去
```


---
## 取消暂存
- 使用 `git add` 将文件添加到暂存区后想要取消（即从暂存区移除）
- **使用 `git restore`**（Git 2.23+ 推荐）
```shell
# 格式
git restore --staged <file>

# 取消指定文件的暂存：
git restore --staged example.txt

# 取消所有文件的暂存：
git restore --staged .
```