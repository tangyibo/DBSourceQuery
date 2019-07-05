# -*- coding: UTF-8 -*-
from base_reader import ReaderBase
import pymysql
from warnings import filterwarnings

filterwarnings("error", category=pymysql.Warning)


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
            connect_timeout=4,
            read_timeout=5
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
            return False, e.message, [], []

        data_mapper = {"BASE TABLE": "table","base table": "table", "VIEW": "view"}
        tables = []
        for item in cursor.fetchall():
            tables.append({"table_name": item[0], "table_type": data_mapper[str(item[1]).strip()]})
        cursor.close()
        return tables

    # 获取mysql的建表语句, 原理：利用MySQL的 show create table 语句获取
    def get_mysql_create_table_sql_v1(self, model_name, curr_table_name, new_table_name=None, create_if_not_exist=False):
        mysql_cursor = self._connection.cursor()

        ######################
        # 生成创建表的SQL语句
        ######################

        show_create_table_sql = "show create table %s " % curr_table_name
        try:
            mysql_cursor.execute(show_create_table_sql)
        except pymysql.OperationalError, e:
            self.connect()
            mysql_cursor = self._connection.cursor()
            mysql_cursor.execute(show_create_table_sql)
        except Exception, e:
            return False, e.message, []

        results = mysql_cursor.fetchone()
        if new_table_name is None:
            create_table_sql = results[1]
        else:
            create_table_sql = results[1].replace(curr_table_name, new_table_name)

        mysql_cursor.close()

        if create_if_not_exist is True:
            create_table_sql = create_table_sql.replace('CREATE TABLE', 'CREATE TABLE IF NOT EXISTS ')

        # remove the current time field
        create_table_sql = create_table_sql.replace('ON UPDATE CURRENT_TIMESTAMP', ' ')

        column_names = self.__query_table_columns(curr_table_name)
        pri_key_columns = self.__query_table_primary_key(curr_table_name)
        return True, create_table_sql, column_names, pri_key_columns

    # 获取mysql的建表语句, 原理：利用MySQL的 select * from  `table_name` limit 0 语句获取
    def get_mysql_create_table_sql(self, model_name, curr_table_name, new_table_name=None, create_if_not_exist=False):
        mysql_cursor = self._connection.cursor()

        sql = "select * from  `%s` limit 0 " % curr_table_name
        try:
            mysql_cursor.execute(sql)
        except pymysql.OperationalError, e:
            self.connect()
            mysql_cursor = self._connection.cursor()
            mysql_cursor.execute(sql)
        except Exception, e:
            return False, e.message, []

        table_metadata = []
        columns_names = []
        for column in mysql_cursor.description:
            columns_names.append(column[0])
            table_metadata.append({
                'name': column[0],
                'type': column[1],
                'display_size': column[2],
                'internal_size': column[3],
                'precision': column[4],
                'scale': column[5],
                'nullable': column[6],
            })

        mysql_cursor.close()

        try:
            # 获取主键列信息
            primary_key_column = self.__query_table_primary_key(curr_table_name)
        except Exception, e:
            return False, e.message, []


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

        for column in table_metadata:
            column_name = column['name']

            if column['type'] == pymysql.NUMBER :
                column_type = "BIGINT"
            elif column['type'] == pymysql.STRING:
                if len(primary_key_column) > 0 and column_name in primary_key_column:
                    column_type = "VARCHAR(255)"
                elif column['internal_size'] < 256:
                    column_type = "VARCHAR(%s)" % (column['internal_size'],)
                elif column['internal_size'] < 65535:
                    column_type = "TEXT"
                elif column['internal_size'] < 166777215:
                    column_type = "MEDIUMTEXT"
                else:
                    column_type = "LONGTEXT"
            elif column['type'] == pymysql.TIMESTAMP:
                column_type = "DATETIME"
            elif column['type'] == pymysql.TIME:
                column_type = "TIMESTAMP"
            else:
                column_type = "LONGTEXT"

            if column['nullable'] == 1:
                nullable = "null"
            else:
                nullable = "not null"

            column_definitions.append("`%s` %s %s" % (column_name, column_type, nullable))

        create_table_sql += ",\n".join(column_definitions)

        if len(primary_key_column) > 0:
            primary_key_column_fields = ",".join(["`%s`" % i for i in primary_key_column])
            create_table_sql += ',\nPRIMARY KEY (%s)' % primary_key_column_fields
        create_table_sql += "\n)ENGINE=InnoDB DEFAULT CHARACTER SET = utf8;"

        return True, create_table_sql, columns_names, primary_key_column


    # 获取表的列信息
    def __query_table_columns(self, table_name):
        cursor = self._connection.cursor()
        sql = "select column_name,data_type from information_schema.COLUMNS where TABLE_SCHEMA='%s' and TABLE_NAME='%s'" % (
            self.dbname, table_name)

        try:
            cursor.execute(sql)
        except pymysql.OperationalError, e:
            self.connect()
            cursor = self._connection.cursor()
            cursor.execute(sql)
        except Exception, e:
            raise Exception(e.message)

        r = cursor.fetchall()
        cursor.close()

        ret = []
        if r:
            for item in r:
                ret.append(item[0])

        return ret

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
            raise Exception(e.message)

        r=cursor.fetchall()
        cursor.close()

        ret = []
        if r:
            for item in r:
                ret.append(item[0])

        return ret
