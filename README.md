## xterm_django -- 基于xterm.js、dwebsocket、EPOLL IOLoop的Django Webssh实现


### 简介
- 参考自[xsank/webssh](https://github.com/xsank/webssh)，原项目基于tornado及其WebsocketHandler，并利用IOLoop处理所有IO操作: `paramiko ssh连接Recv`和`websocket返回`的数据
- 本项目利用`dwebsocket`在`Django`中加入websocket连接，原有特性均保留了下来，完善了原有Epoll IO模型的处理逻辑
- IOLoop中会维护每一个Webssh终端的`paramiko ssh shell`对象的Recv文件描述符，及其请求对应的View线程中Websocket连接对象

流程示意如下：

![xterm_dwebsocket_epoll.jpg](https://github.com/peerless1230/static_files/blob/master/xterm_dwebsocket_epoll.jpg)

运行说明:
```
git clone https://github.com/peerless1230/xterm_django
cd xterm_django
python manage.py collectstatic
python manage.py runserver 0.0.0.0:8088
```

### PS
非常感谢原作者[xsank](https://github.com/xsank)。由于原作者已停止维护`Webssh`项目，便重建了一个项目，如有冒昧之处，请与我联系 `peerless1230@gmail.com`
