PY聊天室

#开发、测试环境：WIN8
#内建账号netease1，netease2，netease3，netease4，密码都是123

#使用说明：
1.服务器默认端口号1234
2.服务器输入'game'可以手动开始21点游戏
3.客户端输入'1'登录，'2'注册，注册成功自动登录
4.登录后进入大厅，输入以'--'开头为特殊指令，否则为发送广播消息。所有指令可通过'--help'查看
 '--all'           发送广播消息，例如：--all hello world
 '--[name]'        发送私聊（对方必须在线），例如：--Bob hello Bob
 '--time'          查看本次在线时间和总计在线时间
 '--user'          查看已在线的用户名
 '--room'          查看已有的房间号
 '--room [num]'    加入房间，例如加入房间1：--room 1
 '--newroom [num]' 创建房间并加入，例如创建房间1：--newroom 1
 '--exitroom'      退出房间
 '--offline'       下线
5.进入某个房间后，信息默认在房间内放松，如需广播请加'--all '前缀
6.21点游戏规则与需求中的描述一致。在开始的15s内，用户可以通过前缀'21game'提交答案，仅接受首次提交的合法表达式，例如:21game 3+6*2

#其他说明
1.存盘信息包括用户名、密码和用户在线时间，存盘文件路径为服务器当前路径，文件名为'data.pkl'
2.同一时间，用户最多只可进入一个房间
3.已创建的房间信息只在内存中，服务器关闭即丢失
4.21点游戏每个整点和半点开始，或者通过服务器指令'game'手动开始。游戏规则如需求中所描述。

#暂不支持：
1.密码修改
2.删除用户
3.删除房间
