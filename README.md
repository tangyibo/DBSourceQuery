# 数据库信息查询服务

## 一、功能描述

　　通过给定的数据库连接信息获取所有的表列信息、主键信息、及在MySQL中对应的建表语句等
 
## 二、支持的数据库

| 数据库名称 | 数据库英文 | 简写 | 数据库类型 |
| :------:| :------: | :------: | :------: |
| 甲骨文数据库 | oracle | oracle | 关系数据库 |
| MySQL数据库 | mysql | mysql | 关系数据库 |
| 微软SQL Server | SQLServer | mssql | 关系数据库 |
| PostgreSQL | PostgreSQL | postgresql | 关系数据库 |

## 三、安装部署
### 1、安装virtualenv环境
```
  yum install python-virtualenv
  yum install python-psycopg2
```
### 2、配置程序启动需要的虚拟环境
```
  cd DBSourceQuery/
  virtualenv -p `which python` venv
  ./venv/bin/pip install -r requirements.txt
```
### 3、编译生成可执行文件
```
  make
```
### 4、测试运行
```
 cd bin/
 ./dbSourceQuery 或者 ./startup.sh
```

## 四、接口文档

 ### 1、获取数据库中所有的模式(model/schema)
 
 **URI:** http://host:port/query_model_list
 
 **Request Method:** POST
 
 **Request Format:** JOSN格式
 
| 字段名称 | 类型 | 描述 | 取值范围 |
| :------:| :------: | :------: | :------ |
| type | string | 数据库类型 | 可取值：oracle,mysql,mssql,postgresql |
| host | string | IP地址 | 数据库主机的IP地址 |
| port | integer | 端口号 | 整型的端口号 |
| user | string | 帐号 | 登录的帐号名 |
| passwd | string | 密码 | 登录的密码 |
| dbname | string | 库名 | 连接的数据库名称 |
| charset | string | 字符集 | 数据库的字符集|

**Request Example:**

```
 {
    "type":"oracle",
    "host":"172.16.90.252",
    "port":1521,
    "user":"yi_bo",
    "passwd":"yi_bo",
    "dbname":"orcl",
    "charset":"utf-8"
}
```

 **Response Format:** JOSN格式
 
| 字段名称 | 类型 | 描述 | 取值范围 |
| :------:| :------: | :------: | :------ |
| errcode | integer | 错误码 | 0为成功，其他为失败 |
| errmsg | string | 错误信息 | 当errcode=0时，为"ok",否则为错误的详细信息 |
| data | list | 数据列表 | 返回的模式列表 |

**Response Example:**

```
{
    "data":[                       
		"SYS",
		"ODI",
		"TEST",
    ],
    "errcode":0,                  
    "errmsg":"ok"                 
}
```

 ### 2、获取数据库中指定模式下的所有表
 **URI:** http://host:port/query_table_list
 
 **Request Method:** POST
 
 **Request Format:** JOSN格式
 
| 字段名称 | 类型 | 描述 | 取值范围 |
| :------:| :------: | :------: | :------ |
| type | string | 数据库类型 | 可取值：oracle,mysql,mssql,postgresql |
| host | string | IP地址 | 数据库主机的IP地址 |
| port | integer | 端口号 | 整型的端口号 |
| user | string | 帐号 | 登录的帐号名 |
| passwd | string | 密码 | 登录的密码 |
| dbname | string | 库名 | 连接的数据库名称 |
| model | string | 模式名 | 不提供该参数时的情况：当为oracle时为user的值；当为mssql时为dbo；当为postgresql时为public |
| charset | string | 字符集 | 数据库的字符集|

**Request Example:**

```
 {
    "type":"oracle",
    "host":"172.16.90.252",
    "port":1521,
    "user":"yi_bo",
    "passwd":"yi_bo",
    "dbname":"orcl",
    "model":"ODI",
    "charset":"utf-8"
}
```

 **Response Format:** JOSN格式
 
| 字段名称 | 类型 | 描述 | 取值范围 |
| :------:| :------: | :------: | :------ |
| errcode | integer | 错误码 | 0为成功，其他为失败 |
| errmsg | string | 错误信息 | 当errcode=0时，为"ok",否则为错误的详细信息 |
| data | list | 数据列表 | 返回的列表 |
| table_name | string | 表名称 | 表或视图的英文名称 |
| table_type | string | 表类型 | 当表为物理表时标记为table;当表为视图表时标记为view |
| remarks | string | 注释信息 | null;空字符串; 普通字符串|

**Response Example:**

```
{
    "data":[                     
		{
			"table_type": "table",   
			"table_name": "test_world",
			"remarks": "测试用表"
		},
		{
			"table_type": "view",
			"table_name": "v_test",
			"remarks": null
		}
    ],
    "errcode":0,            
    "errmsg":"ok"           
}
```

 ### 3、获取业务数据库中指定表的相关信息
 
 **URI:** http://host:port/query_table_info
 
 **Request Method:** POST
 
 **Request Format:** JOSN格式
 
 | 字段名称 | 类型 | 描述 | 取值范围 |
| :------:| :------: | :------: | :------ |
| type | string | 数据库类型 | 可取值：oracle,mysql,mssql,postgresql |
| host | string | IP地址 | 数据库主机的IP地址 |
| port | integer | 端口号 | 整型的端口号 |
| user | string | 帐号 | 登录的帐号名 |
| passwd | string | 密码 | 登录的密码 |
| dbname | string | 库名 | 连接的数据库名称 |
| model | string | 模式名 | 不提供该参数时的情况：当为oracle时为user的值；当为mssql时为dbo；当为postgresql时为public |
| charset | string | 字符集 | 数据库的字符集|
| src_table | string | 源表名称 | 查询的源业务库表名的实际名称|
| dest_table | string | 新表名称 | 生成的建表SQL中的新表名称|
 
**Request Example:**

```
{
    "type":"oracle",  
    "host":"172.16.90.252",
    "port":1521,
    "user":"yi_bo",
    "passwd":"yi_bo",
    "dbname":"orcl",
    "model":"YI_BO",
    "charset":"utf-8",
    "src_table":"C_SEX",
    "dest_table":"my_test_table"
}
}
```
 
 **Response Format:** JOSN格式
 
| 字段名称 | 类型 | 描述 | 取值范围 |
| :------:| :------: | :------: | :------ |
| errcode | integer | 错误码 | 0为成功，其他为失败 |
| errmsg | string | 错误信息 | 当errcode=0时，为"ok",否则为错误的详细信息 |
| data | Object | 数据列表 | 返回的列表 |
| create_sql | string | 建表的SQL语句 | MySQL数据库语法的建表SQL语句 |
| primary_key | list | 表的主键列 | 表的主键字段列表 |
| columns | list | 表的字段列 | 表的字段列表 |
| name | string | 字段列名称 | 表的字段列表 |
| type | string | 字段列类型 | 表的字段列表 |
| nullable | integer | 是否可为空 | 取值：1-是；0-否 |
| display_size | integer | 显示长度 | 显示长度 |
| precision | integer | Number precision | Number precision |
| scale | integer | Number scale | Number scale  |
| internal_size | integer | 内部字节大小 | 内部字节大小 |
| remarks | string | 注释信息 | null;空字符串; 普通字符串|
| metadata | Object | 表元信息 | 表元信息对象 |
| table_name | string | 表名称 | 表或视图的英文名称 |
| table_type | string | 表类型 | 当表为物理表时标记为table;当表为视图表时标记为view |
| remarks | string | 注释信息 | null;空字符串; 普通字符串|

 **Response Example:**
 
```
{
    "data": {
        "create_sql": "CREATE TABLE IF NOT EXISTS `my_test_table` (\n`id` BIGINT not null,\n`name` TEXT null,\n`value` TEXT null,\nPRIMARY KEY (`id`)\n)ENGINE=InnoDB DEFAULT CHARACTER SET = utf8;",
        "primary_key": [
            "id"
        ],
        "columns": [
            {
                "scale": 0,
				"remarks": "编号",
                "name": "id",
                "nullable": 0,
                "type": "NUMBER",
                "display_size": 12,
                "precision": 11,
                "internal_size": null
            },
            {
                "scale": null,
				"remarks": "键名",
                "name": "name",
                "nullable": 1,
                "type": "NVARCHAR2",
                "display_size": 255,
                "precision": null,
                "internal_size": 1020
            },
            {
                "scale": null,
				"remarks": "键值",
                "name": "value",
                "nullable": 1,
                "type": "NVARCHAR2",
                "display_size": 255,
                "precision": null,
                "internal_size": 1020
            }
        ]
        "metadata": {
            "remarks": "性别代码表",
            "table_type": "table",
            "table_name": "C_SEX"
        }
    },
    "errcode": 0,
    "errmsg": "ok"
}
```

### 4、测试指定数据库中sql有效性
 **URI:** http://host:port/query_sql_test
 
 **Request Method:** POST
 
 **Request Format:** JOSN格式
 
| 字段名称 | 类型 | 描述 | 取值范围 |
| :------:| :------: | :------: | :------ |
| type | string | 数据库类型 | 可取值：oracle,mysql,mssql,postgresql |
| host | string | IP地址 | 数据库主机的IP地址 |
| port | integer | 端口号 | 整型的端口号 |
| user | string | 帐号 | 登录的帐号名 |
| passwd | string | 密码 | 登录的密码 |
| dbname | string | 库名 | 连接的数据库名称 |
| charset | string | 字符集 | 数据库的字符集|
| querysql | string | SQL语句 | 待验证的合法SQL|

**Request Example:**

```
 {
    "type":"oracle",
    "host":"172.16.90.252",
    "port":1521,
    "user":"yi_bo",
    "passwd":"yi_bo",
    "dbname":"orcl",
    "querysql":"select * from test",
    "charset":"utf-8"
}
```

 **Response Format:** JOSN格式
 
| 字段名称 | 类型 | 描述 | 取值范围 |
| :------:| :------: | :------: | :------ |
| errcode | integer | 错误码 | 0为成功，其他为失败 |
| errmsg | string | 错误信息 | 当errcode=0时，为"ok",否则为错误的详细信息 |

**Response Example:**

```
{
    "errcode":0,            
    "errmsg":"ok"           
}
```