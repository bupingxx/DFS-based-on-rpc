### SDFS

___

#### 一、介绍

​	一个基于远程过程调用(RPC) 的，具有client-server架构的分布式文件系统。该系统具有基本的访问、打开、删除文件等功能，同时具有一致性、支持多用户特点。运行环境为Linux。



#### 二、特点

##### 1. 编程语言

​	使用Python语言，利用Python的xmlrpc库实现RPC通信模式。

##### 2. C-S模型

​	文件系统中设计了两个服务器`serverDB`和`server`，以及一个客户端`client`。主要使用了三层的客户-服务器模型，实现的是上传/下载的分布式文件系统，如下图所示：

![image-1](https://github.com/bupingxx/DFS-based-on-rpc/blob/main/img/image-1.png)

##### 3. 透明性

​	本文件系统具有良好的透明性，包括访问、位置和复制的透明性。客户不知道自己对资源访问的方式，也不知道服务器中资源所在的实际位置，同样也不知道服务器如何对数据进行复制备份。

##### 4. 可靠的RPC通信

​	本文件系统实现了可靠的RPC通信，基于XMLRPC框架使用至多一次语义，对于每个RPC请求，服务器都会在控制台输出请求的具体内容，即日志文件；如果请求失败，则会返回错误给客户端。

##### 5. 多用户和安全性

​	服务器`serverDB`维护了服务器的数据库，存储了用户和文件的信息，用户只有在注册后才可以登录连接到空闲的服务器`server`上，由`server`直接处理`client`的RPC请求。对于涉及文件的操作，则由`server`向`serverDB`发送RPC请求来完成。为了加强文件系统的安全性，用户的密码使用`md5`进行加密，再存储到数据库中。

##### 6. 容错、恢复和一致性

​	在文件系统中创建目录和文件时，会自动创建一个用户不可见的副本，副本的后缀名为`.backup`。用户删除文件时，文件的副本不会被立刻删除，便于用户的恢复（相当于垃圾桶功能）。而当用户尝试访问一个没有及时更新的文件时，服务器还可以根据副本进行自动恢复，从而保证所有用户访问的文件都是最新的，即实现了最终一致性。

##### 7. 多功能

​	应用程序具有比较完整的交互界面，在终端中，用户可以输入类似`cd`, `ls`, `mkdir`等常见的`linux`指令。



#### 三、注意

##### 1. 环境

​	Linux 下的Python3.6（或以上）。



##### 2. 参数

​	`config.py`中包含了`serverDB`的ip地址、端口，以及文件系统的根目录，用户的本地目录信息，在服务器和客户端中参数的配置应该保持一致。



##### 3. 数据库

​	服务器的数据库包括`USERS`, `SERVERS`和`FILES`三个表，分别对应存储用户信息、服务器信息和文件信息：

| USERS表  | UserID | Name | Password |
| -------- | ------ | ---- | -------- |
| 数据类型 | INT    | TEXT | TEXT     |

| SERVERS表 | ServerID | Free | Address |
| --------- | -------- | ---- | ------- |
| 数据类型  | INT      | INT  | TEXT    |

| FILES表  | UserID | ServerID | Path | FileName | IsDir | IsBackup | LastModified |
| -------- | ------ | -------- | ---- | -------- | ----- | -------- | ------------ |
| 数据类型 | INT    | INT      | TEXT | TEXT     | INT   | INT      | INT          |



##### 4. 使用方法

​	`makefile`中包含了参考的基本指令，在运行时可以添加`-h`指令来获得帮助，如下所示。

![image-2](https://github.com/bupingxx/DFS-based-on-rpc/blob/main/img/image-2.png)



#### 四、运行效果

![image-3](https://github.com/bupingxx/DFS-based-on-rpc/blob/main/img/image-3.png)



____



![image-4](https://github.com/bupingxx/DFS-based-on-rpc/blob/main/img/image-4.png)


