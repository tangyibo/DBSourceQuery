# -*- coding: UTF-8 -*-
from base_reader import ReaderBase
import pymssql
import re


class ColumnDesc:
    TABLE_CATALOG = 0
    TABLE_SCHEMA = 1
    TABLE_NAME = 2
    COLUMN_NAME = 3
    ORDINAL_POSITION = 4
    COLUMN_DEFAULT = 5
    IS_NULLABLE = 6
    DATA_TYPE = 7
    CHARACTER_MAXIMUM_LENGTH = 8
    CHARACTER_OCTET_LENGTH = 9
    NUMERIC_PRECISION = 10
    NUMERIC_PRECISION_RADIX = 11
    NUMERIC_SCALE = 12
    DATETIME_PRECISION = 13
    CHARACTER_SET_CATALOG = 14
    CHARACTER_SET_SCHEMA = 15
    CHARACTER_SET_NAME = 16
    COLLATION_CATALOG = 17
    COLLATION_SCHEMA = 18
    COLLATION_NAME = 19
    DOMAIN_CATALOG = 20
    DOMAIN_SCHEMA = 21
    DOMAIN_NAME = 22
    IS_IDENTITY = 23


def handle_decimal_type(column_desc):
    precision = column_desc[ColumnDesc.NUMERIC_PRECISION]
    scale = column_desc[ColumnDesc.NUMERIC_SCALE]
    return "DECIMAL(%s, %s)" % (precision, scale)


def handle_char_type(column_desc):
    length = column_desc[ColumnDesc.CHARACTER_MAXIMUM_LENGTH]
    if length <= 255:
        return "CHAR(%s)" % length
    else:
        return "LONGTEXT"


def handle_text_type(column_desc):
    length = column_desc[ColumnDesc.CHARACTER_MAXIMUM_LENGTH]
    if 0 <= length <= 65535:
        return "VARCHAR(%s)" % length
    elif 0 <= length <= 166777215:
        return "MEDIUMTEXT"
    else:
        return "LONGTEXT"


def handle_blob_type(column_desc):
    data_type = column_desc[ColumnDesc.DATA_TYPE].upper()
    length = column_desc[ColumnDesc.CHARACTER_MAXIMUM_LENGTH]
    if data_type == "BINARY" and length <= 255:
        return "BINARY(%s)" % length
    elif data_type == "VARBINARY" and 0 <= length <= 65535:
        return "VARBINARY(%s)" % length
    elif 0 <= length <= 65535:
        return "BLOB"
    elif 0 <= length <= 166777215:
        return "MEDIUMBLOB"
    else:
        return "LONGBLOB"


TYPES_MAP = {
    'INT': 'INT',
    'TINYINT': 'TINYINT',
    'SMALLINT': 'SMALLINT',
    'BIGINT': 'BIGINT',
    'BIT': 'TINYINT(1)',
    'FLOAT': 'FLOAT',
    'REAL': 'FLOAT',
    'NUMERIC': handle_decimal_type,
    'DECIMAL': handle_decimal_type,
    'MONEY': handle_decimal_type,
    'SMALLMONEY': handle_decimal_type,
    'CHAR': handle_char_type,
    'NCHAR': handle_char_type,
    'VARCHAR': handle_text_type,
    'NVARCHAR': handle_text_type,
    'DATE': 'DATE',
    'DATETIME': 'DATETIME',
    'DATETIME2': 'DATETIME',
    'SMALLDATETIME': 'DATETIME',
    'DATETIMEOFFSET': 'DATETIME',
    'TIME': 'TIME',
    'TIMESTAMP': 'TIMESTAMP',
    'ROWVERSION': 'TIMESTAMP',
    'BINARY': handle_blob_type,
    'VARBINARY': handle_blob_type,
    'TEXT': handle_text_type,
    'NTEXT': handle_text_type,
    'IMAGE': handle_blob_type,
    'SQL_VARIANT': handle_blob_type,
    'TABLE': handle_blob_type,
    'HIERARCHYID': handle_blob_type,
    'UNIQUEIDENTIFIER': 'VARCHAR(64)',
    'SYSNAME': 'VARCHAR(160)',
    'XML': 'TEXT'
}


def get_column_type(column_desc):
    source_type = column_desc[ColumnDesc.DATA_TYPE].upper()
    target_type = TYPES_MAP.get(source_type)
    if target_type is None:
        return None
    elif isinstance(target_type, basestring):
        return target_type
    else:
        return target_type(column_desc)


def convert_column_default(col):
    default_value = col[ColumnDesc.COLUMN_DEFAULT]
    if default_value is None:
        return ''
    if default_value.startswith('((') and default_value.endswith('))'):
        default_value = default_value[2:-2]
    elif default_value.startswith('(') and default_value.endswith(')'):
        default_value = default_value[1:-1]

    if '(' in default_value and ')' in default_value:
        default_value = None
    elif default_value.startswith('CREATE'):
        default_value = None
    return ' DEFAULT %s' % default_value if default_value else ''


class ReaderSqlserver(ReaderBase):

    # 构造函数
    def __init__(self, host, port, dbname, username, password, charset):
        ReaderBase.__init__(self, host, port, dbname, username, password, charset)

    # 建立与SQLServer数据库的连接
    def connect(self):
        params = {'server': self.host, 'port': self.port, 'database': self.dbname,
                  'user': self.username, 'password': self.password}
        self._connection = pymssql.connect(login_timeout=20, timeout=20, **params)

    # 关闭与SQLServer的连接
    def close(self):
        pass

    # 获取数据库内所有的模式列表
    def get_model_lists(self):
        cursor = self._connection.cursor()
        sql = "select name from sys.schemas where schema_id<16000"

        try:
            cursor.execute(sql)
        except pymssql.OperationalError, e:
            self.connect()
            cursor = self._connection.cursor()
            cursor.execute(sql)
        except Exception, e:
            raise Exception(str(e.args))

        models = []
        for item in cursor.fetchall():
            models.append(item[0])
        cursor.close()
        return models

    # 获取数据库内所有的表列表
    def get_table_lists(self, model_name="dbo"):
        remarks = self.__query_table_remarks(model_name)

        cursor = self._connection.cursor()
        sql = ''' SELECT [table_name],[table_type] FROM [INFORMATION_SCHEMA].[TABLES] where [table_schema]='%s' ''' % model_name
        try:
            cursor.execute(sql)
        except pymssql.OperationalError, e:
            self.connect()
            cursor = self._connection.cursor()
            cursor.execute(sql)
        except Exception, e:
            raise Exception(str(e.args))

        tables = []
        for item in cursor.fetchall():
            if "VIEW" == str(item[1]).strip().upper():
                tables.append({"table_name": item[0], "table_type": "view",
                               "remarks": remarks[item[0]] if remarks.has_key(item[0]) else ''})
            else:
                tables.append({"table_name": item[0], "table_type": "table",
                               "remarks": remarks[item[0]] if remarks.has_key(item[0]) else ''})
        cursor.close()
        return tables

    # 获取SQLServer的建表语句,原理：利用SQLServer的三个SQL获取表的列、主键信息，然后生成MySQL的建表语句
    def get_mysql_create_table_sql(self, model_name, curr_table_name, new_table_name=None, create_if_not_exist=False):

        # 获取列信息
        columns = self.__query_table_columns(model_name, curr_table_name)
        if len(columns) == 0:
            raise Exception('table name or schema name is invalid!')

        # 获取主键列信息
        primary_key_column = self.__query_table_primary_key(model_name, curr_table_name)

        column_remarks = self.__query_table_column_remarks(curr_table_name, model_name)

        ######################
        # 生成创建表的SQL语句
        ######################

        columns = sorted(columns, key=lambda x: x[ColumnDesc.ORDINAL_POSITION])

        table_name = columns[0][ColumnDesc.TABLE_NAME]
        if new_table_name is not None:
            table_name = new_table_name

        cols = []
        table_metadata = []
        auto_increment_column = None
        for col in columns:
            table_metadata.append({
                'name': col[ColumnDesc.COLUMN_NAME],
                'type': col[ColumnDesc.DATA_TYPE],
                'display_size': col[ColumnDesc.CHARACTER_MAXIMUM_LENGTH],
                'internal_size': col[ColumnDesc.CHARACTER_OCTET_LENGTH],
                'precision': col[ColumnDesc.NUMERIC_PRECISION],
                'scale': col[ColumnDesc.NUMERIC_SCALE],
                'nullable': 1 if col[ColumnDesc.IS_NULLABLE] == "YES" else 0,
                'remarks': column_remarks[col[ColumnDesc.COLUMN_NAME]] if column_remarks.has_key(
                    col[ColumnDesc.COLUMN_NAME]) else ''
            })

            cols.append("`%s` %s %s%s" % (col[ColumnDesc.COLUMN_NAME],
                                          get_column_type(col),
                                          convert_column_default(col),
                                          " NOT NULL" if col[ColumnDesc.COLUMN_NAME] in primary_key_column else ' NULL'))
            auto_increment_column = col[ColumnDesc.COLUMN_NAME] if col[
                ColumnDesc.IS_IDENTITY] else auto_increment_column

        if primary_key_column:
            primary_key_column_fields = ",".join(["`%s`" % i for i in primary_key_column])
            cols.append('PRIMARY KEY (%s)' % primary_key_column_fields)

        if create_if_not_exist:
            create_table_sql = 'CREATE TABLE IF NOT EXISTS `%s` (\n%s) ENGINE=InnoDB DEFAULT CHARSET=utf8' % (
                table_name, ',\n'.join(cols))
        else:
            create_table_sql = 'CREATE TABLE `%s` (\n%s) ENGINE=InnoDB DEFAULT CHARSET=utf8' % (
                table_name, ',\n'.join(cols))

        return True, create_table_sql, table_metadata, primary_key_column

    # 测试SQL有效性
    def test_query_sql(self, query_sql):
        cursor = self._connection.cursor()
        sql = "SELECT top 1 * from ( %s ) tmp" % (query_sql.replace(";", ""),)
        try:
            #cursor.execute("SET NOEXEC ON")
            cursor.execute(sql)
        except Exception, e:
            raise Exception(str(e.args))
        finally:
            #cursor.execute("SET NOEXEC OFF")
            cursor.close()


    # 获取表的列信息
    def __query_table_columns(self, model_name, table_name):
        cursor = self._connection.cursor()
        sql = "select *, COLUMNPROPERTY(object_id(TABLE_NAME), COLUMN_NAME, 'IsIdentity') as IS_IDENTITY \
         from information_schema.COLUMNS where TABLE_NAME='%s' and TABLE_SCHEMA='%s'" % (table_name, model_name)

        try:
            cursor.execute(sql)
        except pymssql.OperationalError, e:
            self.connect()
            cursor = self._connection.cursor()
            cursor.execute(sql)
        except Exception, e:
            raise Exception(str(e.args))

        columns = list(cursor.fetchall())
        cursor.close()
        return columns

    # 获取表的主键列信息
    def __query_table_primary_key(self, model_name, table_name):
        cursor = self._connection.cursor()
        sql = "SELECT COLUMN_NAME FROM INFORMATION_SCHEMA.KEY_COLUMN_USAGE WHERE TABLE_NAME='%s' and CONSTRAINT_SCHEMA='%s' " % (
        table_name, model_name)

        try:
            cursor.execute(sql)
        except pymssql.OperationalError, e:
            self.connect()
            cursor = self._connection.cursor()
            cursor.execute(sql)
        except Exception, e:
            raise Exception(str(e.args))

        r = cursor.fetchall()
        cursor.close()

        ret = []
        if r:
            for item in r:
                ret.append(item[0])

        return ret

    # 获取表的字段注释
    def __query_table_column_remarks(self, table_name, model_name):
        cursor = self._connection.cursor()
        sql = '''
                SELECT a.name AS COLUMN_NAME,CONVERT(nvarchar(50),ISNULL(g.[value], '')) AS REMARKS FROM sys.columns a
				LEFT JOIN sys.extended_properties g ON ( a.object_id = g.major_id AND g.minor_id = a.column_id )
				WHERE object_id = (SELECT object_id FROM sys.tables st INNER JOIN INFORMATION_SCHEMA.TABLES t on st.name=t.TABLE_NAME 
				WHERE	st.name = '%s' and t.TABLE_SCHEMA='%s')
        ''' % (table_name, model_name)

        try:
            cursor.execute(sql)
        except pymssql.OperationalError, e:
            self.connect()
            cursor = self._connection.cursor()
            cursor.execute(sql)
        except Exception, e:
            raise Exception(str(e.args))

        r = cursor.fetchall()
        cursor.close()

        ret = {}
        if r:
            for item in r:
                ret[item[0]] = item[1]

        return ret

    # 获取表的注释
    def __query_table_remarks(self, model_name):
        cursor = self._connection.cursor()
        sql = '''
                SELECT t.TABLE_NAME as TABLE_NAME,	t.TABLE_TYPE as TABLE_TYPE,	CONVERT(nvarchar(50),ISNULL(g.[value], '')) as COMMENTS  
        		FROM INFORMATION_SCHEMA.TABLES t LEFT JOIN sysobjects d on t.TABLE_NAME = d.name 
        		LEFT JOIN sys.extended_properties g on g.major_id=d.id and g.minor_id='0' where t.TABLE_SCHEMA='%s'
        		''' % model_name
        try:
            cursor.execute(sql)
        except pymssql.OperationalError, e:
            self.connect()
            cursor = self._connection.cursor()
            cursor.execute(sql)
        except Exception, e:
            raise Exception(str(e.args))

        r = cursor.fetchall()
        cursor.close()

        ret = {}
        if r:
            for item in r:
                ret[item[0]] = item[2]

        return ret
