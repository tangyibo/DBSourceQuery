# -*- coding: UTF-8 -*-
from base_reader import ReaderBase
import cx_Oracle
import os

os.environ['NLS_LANG'] = 'SIMPLIFIED CHINESE_CHINA.UTF8'

TYPES_MAP = {
    cx_Oracle.BFILE: 'BFILE',
    cx_Oracle.NATIVE_FLOAT: 'BINARY_DOUBLE',
    cx_Oracle.BLOB: 'BLOB',
    cx_Oracle.FIXED_CHAR: 'CHAR',
    cx_Oracle.CLOB: 'CLOB',
    cx_Oracle.CURSOR: 'CURSOR',
    cx_Oracle.DATETIME: 'DATE',
    cx_Oracle.INTERVAL: 'INTERVAL DAY TO SECOND',
    cx_Oracle.LONG_STRING: 'LONG',
    cx_Oracle.LONG_BINARY: 'LONG RAW',
    cx_Oracle.FIXED_NCHAR: 'NCHAR',
    cx_Oracle.NCLOB: 'NCLOB',
    cx_Oracle.NUMBER: 'NUMBER',
    cx_Oracle.NCHAR: 'NVARCHAR2',
    cx_Oracle.OBJECT: 'OBJECT',
    cx_Oracle.BINARY: 'RAW',
    cx_Oracle.ROWID: 'ROWID',
    cx_Oracle.TIMESTAMP: 'TIMESTAMP',
    cx_Oracle.NATIVE_FLOAT: 'BINARY_FLOAT',
    cx_Oracle.STRING: 'VARCHAR2'
}

class ReaderOracle(ReaderBase):

    # 构造函数
    def __init__(self, host, port, dbname, username, password, charset):
        ReaderBase.__init__(self, host, port, dbname, username, password, charset)

    # 建立与oracle数据库的连接
    def connect(self):
        try:
            tns = cx_Oracle.makedsn(self.host, self.port, sid=self.dbname)
            self._connection = cx_Oracle.connect(self.username, self.password, tns, encoding="UTF-8", nencoding="UTF-8")
        except cx_Oracle.OperationalError, e:
            try:
                tns = cx_Oracle.makedsn(self.host, self.port, service_name=self.dbname)
                self._connection = cx_Oracle.connect(self.username, self.password, tns, encoding="UTF-8", nencoding="UTF-8")
            except cx_Oracle.DatabaseError as e:
                raise Exception(e.args[0].message)
        except cx_Oracle.DatabaseError as e:
            raise Exception(e.args[0].message)

    # 关闭与Oracle的连接
    def close(self):
        self._connection.close()

    # 获取数据库内所有的模式列表
    def get_model_lists(self):
        cursor = self._connection.cursor()
        query_sql = "select DISTINCT USERNAME from all_users"
        try:
            cursor.execute(query_sql)
        except cx_Oracle.OperationalError as e:
            self.connect()
            cursor = self._connection.cursor()
            cursor.execute(query_sql)
        except Exception, e:
            raise Exception(e.args[0].message)

        models = []
        for item in cursor.fetchall():
            models.append(item[0])
        cursor.close()
        return models

    # 获取数据库内所有的表列表
    def get_table_lists(self, model_name=None):
        if model_name is None:
            model_name = self.username

        cursor = self._connection.cursor()
        query_sql = '''
                    SELECT "TABLE_NAME","TABLE_TYPE","COMMENTS" from all_tab_comments where "OWNER"='%s' 
                    ''' % model_name.upper()
        try:
            cursor.execute(query_sql)
        except cx_Oracle.OperationalError as e:
            self.connect()
            cursor = self._connection.cursor()
            cursor.execute(query_sql)
        except Exception, e:
            raise Exception(e.args[0].message)

        tables = []
        for item in cursor.fetchall():
            if "VIEW" == str(item[1]).strip().upper():
                tables.append({"table_name": item[0], "table_type": "view", "remarks": item[2]})
            else:
                tables.append({"table_name": item[0], "table_type": "table", "remarks": item[2]})
        cursor.close()
        return tables

    # 获取oracle的建表语句,原理：利用Oracle的 SELECT * FROM table where rownum<1 语句获取列名信息
    def get_mysql_create_table_sql(self, model_name, curr_table_name, new_table_name=None, create_if_not_exist=False):
        oracle_cursor = self._connection.cursor()

        primary_key_column = self.__query_table_primary_key(model_name, curr_table_name)
        column_remarks = self.__query_table_column_remarks(curr_table_name, model_name)

        sql = "SELECT * FROM \"%s\".\"%s\" where rownum<1" % (model_name.upper(), curr_table_name)
        try:
            oracle_cursor.execute(sql)
        except cx_Oracle.OperationalError as e:
            self.connect()
            oracle_cursor = self._connection.cursor()
            oracle_cursor.execute(sql)
        except Exception as e:
            raise e

        table_metadata = []
        # "The description is a list of 7-item tuples where each tuple
        # consists of a column name, column type, display size, internal size,
        # precision, scale and whether null is possible."
        for column in oracle_cursor.description:
            table_metadata.append({
                'name': column[0],
                'type': column[1],
                'display_size': column[2],
                'internal_size': column[3],
                'precision': column[4],
                'scale': column[5],
                'nullable': column[6],
                'remarks': column_remarks[column[0]] if column_remarks.has_key(column[0]) else ''
            })

        oracle_cursor.close()

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
            if column['type'] == cx_Oracle.NUMBER:
                if 0==column['scale'] or 0==column['precision']:
                    column_type = "BIGINT"
                else:
                    if column['precision'] > 4 and column['precision'] <= 64 and column['precision'] > column['scale']:
                        column_type = "DECIMAL(%s, %s)" % (column['precision'], column['scale'])
                    else:
                        column_type = "DECIMAL(65, 4)"
            elif column['type'] == cx_Oracle.STRING:
                if len(primary_key_column) > 0 and column_name in primary_key_column:
                    column_type = "VARCHAR(254)"
                elif column['internal_size'] <= 201:
                    column_type = "VARCHAR(%s)" % (
                    column['internal_size'] if column['internal_size'] is not None else 64,)
                elif column['internal_size'] <= 65535:
                    column_type = "TEXT"
                elif column['internal_size'] < 166777215:
                    column_type = "MEDIUMTEXT"
                else:
                    column_type = "LONGTEXT"
            elif column['type'] == cx_Oracle.DATETIME:
                column_type = "DATETIME"
            elif column['type'] == cx_Oracle.TIMESTAMP:
                column_type = "TIMESTAMP"
            elif column['type'] == cx_Oracle.FIXED_CHAR:
                if column['internal_size'] is None or column['internal_size'] <= 0:
                    column_type = "CHAR(64)"
                elif column['internal_size'] <= 255:
                    column_type = "CHAR(%s)" % (column['internal_size'],)
                else:
                    column_type = "TEXT"
            elif column['type'] == cx_Oracle.CLOB:
                column_type = "LONGBLOB"
            elif column['type'] == cx_Oracle.BLOB:
                column_type = "LONGBLOB"
            else:
                if len(primary_key_column) > 0 and column_name in primary_key_column:
                    column_type = "VARCHAR(255)"
                else:
                    column_type = "LONGTEXT"

            column_definitions.append("`%s` %s %s" % (
                column_name, column_type, " NOT NULL" if column_name in primary_key_column else ' NULL'))

        create_table_sql += ",\n".join(column_definitions)

        if len(primary_key_column) > 0:
            primary_key_column_fields = ",".join(["`%s`" % i for i in primary_key_column])
            create_table_sql += ',\nPRIMARY KEY (%s)' % primary_key_column_fields
        create_table_sql += "\n)ENGINE=InnoDB DEFAULT CHARACTER SET = utf8;"

        for metadata in table_metadata:
            metadata['type']=TYPES_MAP[metadata['type']]

        return True, create_table_sql, table_metadata, primary_key_column

    # 测试SQL有效性
    def test_query_sql(self, query_sql):
        cursor = self._connection.cursor()

        sql = "explain plan for %s" % (query_sql.replace(";", ""),)
        try:
            cursor.execute(sql)
        except Exception, e:
            raise Exception(e.args[0].message)
        finally:
            cursor.close()

    # 获取表的主键列信息
    def __query_table_primary_key(self, model_name, table_name):
        oracle_cursor = self._connection.cursor()

        sql = "SELECT COLUMN_NAME FROM user_cons_columns WHERE 	owner='%s' and 	constraint_name = \
        (SELECT constraint_name FROM user_constraints WHERE table_name = '%s' AND \
        constraint_type = 'P') " % (model_name.upper(), table_name.upper())
        try:
            oracle_cursor.execute(sql)
        except cx_Oracle.OperationalError, e:
            self.connect()
            oracle_cursor = self._connection.cursor()
            oracle_cursor.execute(sql)
        except Exception, e:
            raise Exception(e.args[0].message)

        r = oracle_cursor.fetchall()
        oracle_cursor.close()

        ret = []
        if r:
            for item in r:
                ret.append(item[0])

        return ret

    # 获取表的字段中文注释
    def __query_table_column_remarks(self, table_name, model_name):
        oracle_cursor = self._connection.cursor()
        sql = "select COLUMN_NAME,COMMENTS from all_col_comments where OWNER='%s' and TABLE_NAME='%s'" % (
            model_name, table_name)

        try:
            oracle_cursor.execute(sql)
        except cx_Oracle.OperationalError, e:
            self.connect()
            oracle_cursor = self._connection.cursor()
            oracle_cursor.execute(sql)
        except Exception, e:
            raise Exception(e.args[0].message)

        r = oracle_cursor.fetchall()
        oracle_cursor.close()

        ret = {}
        if r:
            for item in r:
                ret[item[0]] = item[1]

        return ret
