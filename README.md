#业务库信息查询服务

##功能描述
 通过给定的数据库连接信息获取所有的表列信息、主键信息、及在MySQL中对应的建表语句等
 
##接口调用
 ###1 获取业务数据库的中所有的表
 **URI:** http://host:port/query_table_list
 
 **Method:** POST
 
 **Request:** JOSN格式
```
 {
    "type":"oracle",           //数据库类型，可取值：oralce,mysql,mssql
    "host":"172.16.90.252",    //数据库的IP地址
    "port":1521,               //数据库的端口号
    "user":"yi_bo",            //连接帐号
    "passwd":"yi_bo",          //连接的密码
    "dbname":"orcl",           //连接的数据库名
    "charset":"utf-8"          //连接所有的字符集
}
```
 
 **Response:** JOSN格式
```
{
    "data":[                       //响应返回的数据结果
		{
			"table_type": "table",        //表的类型：table-表；view-视图
			"table_name": "test_world"    //表的名称
		},
		{
			"table_type": "view",
			"table_name": "v_test"
		}
    ],
    "errcode":0,                  //错误码，0为成功，其他为失败
    "errmsg":"ok"                 //错误的详细描述信息
}
```

 ###2 获取业务数据库的中指定表的相关信息
 **URI:** http://host:port/query_table_info
 
 **Method:** POST
 
 **Request:** JOSN格式
```
 {
    "type":"oracle",               //数据库类型，可取值：oralce,mysql,mssql
    "host":"172.16.90.252",        //数据库的IP地址
    "port":1521,                   //数据库的端口号
    "user":"yi_bo",                //连接帐号
    "passwd":"yi_bo",              //连接的密码
    "dbname":"orcl",               //连接的数据库名
    "charset":"utf-8",             //连接所有的字符集
    "src_table":"TEST_TABLE",      //要查询的原表名
    "dest_table":"my_test_table",  //新的表名
}
```
 
 **Response:** JOSN格式
```
{
    "data":{                       //响应返回的数据结果
        "create_sql":"CREATE TABLE IF NOT EXISTS `my_test_table` (
                        ID BIGINT not null,
                        NAME VARCHAR(50) null,
                        AGE BIGINT null,
                        PHONE VARCHAR(20) null,
                        EMAIL VARCHAR(255) null,
                        PRIMARY KEY (`ID`)
                     )ENGINE=InnoDB DEFAULT CHARACTER SET = utf8;",
        "primary_key":[
            "ID"
        ],
        "columns":[
            "ID",
            "NAME",
            "AGE",
            "PHONE",
            "EMAIL"
        ]
    },
    "errcode":0,                  //错误码，0为成功，其他为失败
    "errmsg":"ok"                 //错误的详细描述信息
}
```
