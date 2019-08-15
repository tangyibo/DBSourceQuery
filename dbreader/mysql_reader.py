# -*- coding: UTF-8 -*-
from base_reader import ReaderBase
import pymysql
from warnings import filterwarnings

filterwarnings("error", category=pymysql.Warning)
filterwarnings('ignore', category = pymysql.Warning)

class ReaderMysql(ReaderBase):

    # 构造函数
    def __init__(self, host, port, dbname, username, password, charset):
        ReaderBase.__init__(self, host, port, dbname, username, password, charset)

    # 建立与mysql数据库的连接
    def connect(self):
        self._connection = pymysql.connect(
            host=self.host,
            port=self.port,
            db=self.dbname,
            user=self.username,
            password=self.password,
            charset='utf8',
            connect_timeout=20,
            read_timeout=20
            )

    # 关闭与MySQL的连接
    def close(self):
        self._connection.close()

    # 获取数据库内所有的模式列表
    def get_model_lists(self):
        return [self.dbname]

    # 获取MySQL中一个数据库内所有的表列表
    def get_table_lists(self,model_name=None):
        cursor = self._connection.cursor()
        query_sql = "select table_name,table_type from information_schema.tables where table_schema='%s' " % self.dbname
        try:
            cursor.execute(query_sql)
        except pymysql.OperationalError, e:
            self.connect()
            cursor = self._connection.cursor()
            cursor.execute(query_sql)
        except Exception, e:
            return False, str(e.args), [], []

        data_mapper = {"BASE TABLE": "table","base table": "table", "VIEW": "view"}
        tables = []
        for item in cursor.fetchall():
            tables.append({"table_name": item[0], "table_type": data_mapper[str(item[1]).strip()]})
        cursor.close()
        return tables

    # 获取mysql的建表语句, 原理：利用MySQL的 select * from  `table_name` limit 0 语句获取
    def get_mysql_create_table_sql(self, model_name, curr_table_name, new_table_name=None, create_if_not_exist=False):

        try:
            # 获取列元信息
            column_metadata = self.__query_table_columns(curr_table_name)
            # 获取主键列信息
            primary_key_column = self.__query_table_primary_key(curr_table_name)
        except Exception, e:
            return False, str(e.args), []

        ######################
        # 生成创建表的SQL语句
        ######################

        table_name = curr_table_name
        if new_table_name is not None:
            table_name = new_table_name

        if create_if_not_exist:
            create_table_sql = "CREATE TABLE IF NOT EXISTS `%s` (\n" % (table_name,)
        else:
            create_table_sql = "CREATE TABLE `%s` (\n" % (table_name,)

        column_definitions = []

        table_metadata=[]
        for metadata in column_metadata:
            table_metadata.append({
                'name': metadata[0],
                'type': metadata[1],
                'display_size': metadata[2],
                'internal_size': metadata[3],
                'precision': metadata[4],
                'scale': metadata[5],
                'nullable': 1 if metadata[6] == "YES" else 0,
            })

            column_name = metadata[0]
            column_type = metadata[7]

            #if column[0] == 'YES':
            nullable = "null"
            #else:
            #    nullable = "not null"

            column_definitions.append("`%s` %s %s" % (column_name, column_type, nullable))

        create_table_sql += ",\n".join(column_definitions)

        if len(primary_key_column) > 0:
            primary_key_column_fields = ",".join(["`%s`" % i for i in primary_key_column])
            create_table_sql += ',\nPRIMARY KEY (%s)' % primary_key_column_fields
        create_table_sql += "\n)ENGINE=InnoDB DEFAULT CHARACTER SET = utf8;"

        return True, create_table_sql, table_metadata, primary_key_column

    # 测试SQL有效性
    def test_query_sql(self, query_sql):
        cursor = self._connection.cursor()
        sql = 'explain %s' % (query_sql.replace(";", ""),)
        try:
            cursor.execute(sql)
        except Warning, w:
            pass
        except Exception, e:
            raise Exception(str(e.args))

    # 获取表的列信息
    def __query_table_columns(self, table_name):
        cursor = self._connection.cursor()
        sql = "select COLUMN_NAME,DATA_TYPE,CHARACTER_MAXIMUM_LENGTH,CHARACTER_OCTET_LENGTH,NUMERIC_PRECISION,NUMERIC_SCALE,IS_NULLABLE,COLUMN_TYPE from information_schema.COLUMNS where TABLE_SCHEMA='%s' and TABLE_NAME='%s'" % (
            self.dbname, table_name)

        try:
            cursor.execute(sql)
        except pymysql.OperationalError, e:
            self.connect()
            cursor = self._connection.cursor()
            cursor.execute(sql)
        except Exception, e:
            raise Exception(str(e.args))

        r = cursor.fetchall()
        cursor.close()
        return r

    # 获取表的主键列
    def __query_table_primary_key(self, table_name):
        cursor = self._connection.cursor()
        sql = "SELECT column_name FROM INFORMATION_SCHEMA.`KEY_COLUMN_USAGE` WHERE TABLE_SCHEMA='%s' and table_name='%s' AND constraint_name='PRIMARY'" % (
        self.dbname, table_name)

        try:
            cursor.execute(sql)
        except pymysql.OperationalError, e:
            self.connect()
            cursor = self._connection.cursor()
            cursor.execute(sql)
        except Exception, e:
            raise Exception(str(e.args))

        r=cursor.fetchall()
        cursor.close()

        ret = []
        if r:
            for item in r:
                ret.append(item[0])

        return ret
