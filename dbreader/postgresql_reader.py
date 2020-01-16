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

    # 关闭与PostgreSQL的连接
    def close(self):
        self._connection.close()

    # 获取数据库内所有的模式列表
    def get_model_lists(self):
        cursor = self._connection.cursor()
        query_sql = "SELECT DISTINCT nspname FROM pg_namespace where nspname not in ('pg_toast','pg_temp_1','pg_toast_temp_1','pg_catalog','information_schema')"
        try:
            cursor.execute(query_sql)
        except psycopg2.OperationalError as e:
            self.connect()
            cursor = self._connection.cursor()
            cursor.execute(query_sql)
        except Exception as e:
            return False, str(e.args), [], []

        models = []
        for item in cursor.fetchall():
            models.append(item[0])
        cursor.close()
        return models

    # 获取PostgreSQL中一个数据库内所有的表列表
    def get_table_lists(self,model_name="public"):
        cursor = self._connection.cursor()
        query_sql = '''
				   SELECT c.relname AS TABLE_NAME, 
                   CASE n.nspname ~ '^pg_' OR n.nspname = 'information_schema' 
                   WHEN true THEN CASE 
                   WHEN n.nspname = 'pg_catalog' OR n.nspname = 'information_schema' THEN CASE c.relkind 
                    WHEN 'r' THEN 'SYSTEM TABLE' 
                    WHEN 'v' THEN 'SYSTEM VIEW' 
                    WHEN 'i' THEN 'SYSTEM INDEX' 
                    ELSE NULL 
                    END 
                   WHEN n.nspname = 'pg_toast' THEN CASE c.relkind 
                    WHEN 'r' THEN 'SYSTEM TOAST TABLE' 
                    WHEN 'i' THEN 'SYSTEM TOAST INDEX' 
                    ELSE NULL 
                    END 
                   ELSE CASE c.relkind 
                    WHEN 'r' THEN 'TEMPORARY TABLE' 
                    WHEN 'i' THEN 'TEMPORARY INDEX' 
                    WHEN 'S' THEN 'TEMPORARY SEQUENCE' 
                    WHEN 'v' THEN 'TEMPORARY VIEW' 
                    ELSE NULL 
                    END 
                   END 
                   WHEN false THEN CASE c.relkind 
                   WHEN 'r' THEN 'TABLE' 
                   WHEN 'i' THEN 'INDEX' 
                   WHEN 'S' THEN 'SEQUENCE' 
                   WHEN 'v' THEN 'VIEW' 
                   WHEN 'c' THEN 'TYPE' 
                   WHEN 'f' THEN 'FOREIGN TABLE' 
                   WHEN 'm' THEN 'MATERIALIZED VIEW' 
                   ELSE NULL 
                   END 
                   ELSE NULL 
                   END 
                   AS TABLE_TYPE, d.description AS REMARKS 
                   FROM pg_catalog.pg_namespace n, pg_catalog.pg_class c 
                   LEFT JOIN pg_catalog.pg_description d ON (c.oid = d.objoid AND d.objsubid = 0) 
                   LEFT JOIN pg_catalog.pg_class dc ON (d.classoid=dc.oid AND dc.relname='pg_class') 
                   LEFT JOIN pg_catalog.pg_namespace dn ON (dn.oid=dc.relnamespace AND dn.nspname='pg_catalog') 
                   WHERE c.relnamespace = n.oid and c.relkind in('r','v') and n.nspname='%s';
                    ''' % model_name
        try:
            cursor.execute(query_sql)
        except psycopg2.OperationalError as e:
            self.connect()
            cursor = self._connection.cursor()
            cursor.execute(query_sql)
        except Exception, e:
            return False, str(e.args), [], []

        tables = []
        for item in cursor.fetchall():
            if "VIEW" == str(item[1]).strip().upper():
                tables.append({"table_name": item[0], "table_type": "view", "remarks": item[2]})
            else:
                tables.append({"table_name": item[0], "table_type": "table", "remarks": item[2]})
        cursor.close()
        return tables

    # 获取PostgreSQL的建表语句, 原理：利用PostgreSQL的 select * from  "public"."table_name" limit 0 语句获取
    def get_mysql_create_table_sql(self, model_name, curr_table_name, new_table_name=None, create_if_not_exist=False):
        postgres_cursor = self._connection.cursor()

        primary_key_column = self.__query_table_primary_key(model_name, curr_table_name)
        column_remarks = self.__query_table_column_remarks(curr_table_name, model_name)
        field_type_mapper=self.__query_table_column_field_type_code()

        sql = "SELECT * FROM \"%s\".\"%s\" limit 0 " % (model_name,curr_table_name)
        try:
            postgres_cursor.execute(sql)
        except psycopg2.OperationalError as e:
            self.connect()
            mysql_cursor = self._connection.cursor()
            mysql_cursor.execute(sql)
        except Exception, e:
            return False, str(e.args), []

        table_metadata = []
        for column in postgres_cursor.description:
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
        postgres_cursor.close()

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

            # display_size无效，需要根据数据类型计算，psycopg2实际上不支持
            column['display_size'] = 1

            if column['type'] == psycopg2.NUMBER:
                if column['scale'] is None:
                    column['scale'] = 0
                if column['precision'] is None:
                    column['precision'] = 0
                if column['precision'] > 65:
                    column['precision'] = 65
                if column['scale'] > 30:
                    column['scale'] = 30
                if column['scale'] > column['precision']:
                    column['scale'] = column['precision']

                if 0 == column['precision']:
                    if column['internal_size'] >= 8:
                        column_type = "BIGINT"
                    else:
                        column_type = "INT"
                else:
                    if column['precision'] > 15:
                        if column['scale'] > 0:
                            column_type = "DECIMAL(%s,%s)" % (column['precision'], column['scale'])
                        else:
                            column_type = "DECIMAL(%s)" % column['precision']
                    else:
                        column_type = "DOUBLE"
            elif column['type'] == psycopg2.STRING:
                if len(primary_key_column) > 0 and column_name in primary_key_column:
                    column_type = "VARCHAR(255)"
                elif column['internal_size'] < 1:
                    column_type = "LONGTEXT"
                elif column['internal_size'] < 256:
                    column_type = "VARCHAR(%s)" % (column['internal_size'] if column['internal_size'] is not None else 64,)
                elif column['internal_size'] < 65535:
                    column_type = "TEXT"
                elif column['internal_size'] < 166777215:
                    column_type = "MEDIUMTEXT"
                else:
                    column_type = "LONGTEXT"
            elif column['type'] == psycopg2.Timestamp:
                column_type = "DATETIME"
            elif column['type'] == psycopg2.Time:
                column_type = "DATETIME"
            elif column['type'] == psycopg2.Date:
                column_type = "DATETIME"
            elif column['type'] == psycopg2.TimeFromTicks:
                column_type = "DATETIME"
            elif column['type'] == psycopg2.TimestampFromTicks:
                column_type = "DATETIME"
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
            metadata['type'] = field_type_mapper[metadata['type']]

        return True, create_table_sql, table_metadata, primary_key_column

    # 测试SQL有效性
    def test_query_sql(self, query_sql):
        cursor = self._connection.cursor()
        sql = "EXPLAIN  %s" % (query_sql.replace(";", ""))
        try:
            cursor.execute(sql)
        except Exception, e:
            raise Exception(str(e.args))
        finally:
            cursor.close()

    # 获取表的主键列
    def __query_table_primary_key(self, model_name, table_name):
        cursor = self._connection.cursor()
        sql = '''
            SELECT NULL AS TABLE_CAT, n.nspname AS TABLE_SCHEM, 
            ct.relname AS TABLE_NAME, a.attname AS COLUMN_NAME, 
            (i.keys).n AS KEY_SEQ, ci.relname AS PK_NAME 
            FROM pg_catalog.pg_class ct 
            JOIN pg_catalog.pg_attribute a ON (ct.oid = a.attrelid) 
            JOIN pg_catalog.pg_namespace n ON (ct.relnamespace = n.oid) 
            JOIN (SELECT i.indexrelid, i.indrelid, i.indisprimary, 
             information_schema._pg_expandarray(i.indkey) AS keys 
             FROM pg_catalog.pg_index i) i 
             ON (a.attnum = (i.keys).x AND a.attrelid = i.indrelid) 
             JOIN pg_catalog.pg_class ci ON (ci.oid = i.indexrelid) 
            WHERE true 
             AND n.nspname ='%s'
             AND ct.relname ='%s'
             AND i.indisprimary ORDER BY table_name, pk_name, key_seq
        ''' % (model_name, table_name)

        try:
            cursor.execute(sql)
        except psycopg2.OperationalError, e:
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
                ret.append(item[3])

        return ret

    # 获取表的字段中文注释
    def __query_table_column_remarks(self, table_name, model_name):
        cursor = self._connection.cursor()
        sql = '''
                SELECT n.nspname,c.relname,a.attname,a.atttypid,a.attnotnull 
                OR (t.typtype = 'd' AND t.typnotnull) AS attnotnull,a.atttypmod,a.attlen,a.attnum,null 
                as attidentity,pg_catalog.pg_get_expr(def.adbin, def.adrelid) AS adsrc,dsc.description,
                t.typbasetype,t.typtype 
                FROM pg_catalog.pg_namespace n 
                JOIN pg_catalog.pg_class c ON (c.relnamespace = n.oid) 
                JOIN pg_catalog.pg_attribute a ON (a.attrelid=c.oid) 
                JOIN pg_catalog.pg_type t ON (a.atttypid = t.oid) 
                LEFT JOIN pg_catalog.pg_attrdef def ON (a.attrelid=def.adrelid AND a.attnum = def.adnum) 
                LEFT JOIN pg_catalog.pg_description dsc ON (c.oid=dsc.objoid AND a.attnum = dsc.objsubid) 
                LEFT JOIN pg_catalog.pg_class dc ON (dc.oid=dsc.classoid AND dc.relname='pg_class') 
                LEFT JOIN pg_catalog.pg_namespace dn ON (dc.relnamespace=dn.oid AND dn.nspname='pg_catalog') 
                WHERE c.relkind in ('r','p','v','f','m') and a.attnum > 0 AND NOT a.attisdropped 
                AND n.nspname LIKE '%s'  AND c.relname LIKE '%s'
                ORDER BY nspname,c.relname,attnum
            ''' % (model_name, table_name)

        try:
            cursor.execute(sql)
        except psycopg2.OperationalError, e:
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
                ret[item[2]] = item[10]

        return ret


    # 获取字段类型码映射关系
    def __query_table_column_field_type_code(self):
        cursor = self._connection.cursor()
        sql = '''
            SELECT n.nspname = ANY(current_schemas(true)), n.nspname, t.oid,t.typname 
            FROM pg_catalog.pg_type t 
            JOIN pg_catalog.pg_namespace n ON t.typnamespace = n.oid where n.nspname='pg_catalog'
            '''
        try:
            cursor.execute(sql)
        except psycopg2.OperationalError, e:
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
                ret[item[2]] = item[3]

        return ret
