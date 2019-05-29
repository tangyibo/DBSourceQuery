# -*- coding: UTF-8 -*-
from base_reader import ReaderBase
import psycopg2
import psycopg2.extras
psycopg2.extras.register_json(oid=3802, array_oid=3807, globally=True)

class ReaderPostgresql(ReaderBase):

    # 构造函数
    def __init__(self, host, port, dbname, username, password, charset):
        ReaderBase.__init__(self, host, port, dbname, username, password, charset)

    # 建立与PostgreSQL数据库的连接
    def connect(self):
        self._connection = psycopg2.connect(
            host=self.host,
            port=self.port,
            database=self.dbname,
            user=self.username,
            password=self.password
            )

    # 关闭与MySQL的连接
    def close(self):
        self._connection.close()

    # 获取数据库内所有的模式列表
    def get_model_lists(self):
        cursor = self._connection.cursor()
        query_sql = "SELECT DISTINCT nspname FROM pg_namespace"
        try:
            cursor.execute(query_sql)
        except psycopg2.OperationalError as e:
            self.connect()
            cursor = self._connection.cursor()
            cursor.execute(query_sql)
        except Exception as e:
            return False, e.message, [], []

        models = []
        for item in cursor.fetchall():
            models.append(item[0])
        cursor.close()
        return models

    # 获取PostgreSQL中一个数据库内所有的表列表
    def get_table_lists(self,model_name="public"):
        cursor = self._connection.cursor()
        query_sql = "SELECT tablename as table_name,'table' as table_type from pg_catalog.pg_tables where schemaname='%s' \
                    union all \
                    SELECT viewname as table_name,'view' as table_type from pg_catalog.pg_views where schemaname='%s' " \
                    % (model_name, model_name)
        try:
            cursor.execute(query_sql)
        except psycopg2.OperationalError, e:
            self.connect()
            cursor = self._connection.cursor()
            cursor.execute(query_sql)
        except Exception, e:
            return False, e.message, [], []

        tables = []
        for item in cursor.fetchall():
            tables.append({"table_name":item[0],"table_type":str(item[1]).strip()})
        cursor.close()
        return tables

    # 获取mysql的建表语句, 原理：利用PostgreSQL的 select * from  "public"."table_name" limit 0 语句获取
    def get_mysql_create_table_sql(self, model_name, curr_table_name, new_table_name=None, create_if_not_exist=False):
        postgres_cursor = self._connection.cursor(cursor_factory = psycopg2.extras.DictCursor)

        sql = "SELECT * FROM \"%s\".\"%s\" limit 0 " % (model_name,curr_table_name)
        try:
            postgres_cursor.execute(sql)
        except psycopg2.OperationalError as e:
            self.connect()
            mysql_cursor = self._connection.cursor()
            mysql_cursor.execute(sql)
        except Exception, e:
            return False, e.message, []

        table_metadata = []
        columns_names = []
        for column in postgres_cursor.description:
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
            print table_metadata
            postgres_cursor.close()

        try:
            # 获取主键列信息
            primary_key_column = self.__query_table_primary_key(model_name, curr_table_name)
        except Exception as e:
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

            if column['type'] == psycopg2.NUMBER :
                column_type = "BIGINT"
            elif column['type'] == psycopg2.STRING:
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
            elif column['type'] == psycopg2.Timestamp:
                column_type = "DATETIME"
            elif column['type'] == psycopg2.Time:
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

    # 获取表的主键列
    def __query_table_primary_key(self, model_name, table_name):
        cursor = self._connection.cursor()
        sql = "SELECT A.COLUMN_NAME as column_name FROM information_schema.COLUMNS A \
            LEFT JOIN (SELECT pg_attribute.attname FROM pg_index,pg_class,pg_attribute WHERE pg_class.oid = '%s' :: regclass \
            AND pg_index.indrelid = pg_class.oid AND pg_attribute.attrelid = pg_class.oid AND pg_attribute.attnum = ANY (pg_index.indkey) \
            ) B ON A.COLUMN_NAME = b.attname WHERE	A .table_schema = '%s' and A . TABLE_NAME = '%s' and LENGTH (B.attname) > 0" \
              % (table_name, model_name, table_name)

        try:
            cursor.execute(sql)
        except psycopg2.OperationalError, e:
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
