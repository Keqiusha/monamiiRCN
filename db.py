import mysql.connector
import logging


class MydbOperator:
    mydb = mysql.connector.connect(
        host="localhost",
        user="root",
        passwd="root",
        database="company_spider_db"
    )

    # tableName = "t_company_info"
    tableName_prefix = "t_company_info_"

    def __init__(self, table_name):
        self.tableName = self.tableName_prefix + table_name

    def is_empty_table(self):
        mycursor = self.mydb.cursor()
        sql = "SELECT COUNT(*) FROM " + self.tableName
        print(sql)
        mycursor.execute(sql)
        return mycursor.fetchone() == (0,)# 修改

    def create_table(self):
        mycursor = self.mydb.cursor()
        sql = "CREATE TABLE IF NOT EXISTS company_spider_db." + self.tableName + "(id bigint(20) NOT NULL AUTO_INCREMENT, job_title varchar(255) NOT NULL DEFAULT '""', company_name varchar(255) NOT NULL DEFAULT '""',company_url varchar(255) NOT NULL DEFAULT '""',location varchar(500) NOT NULL DEFAULT '""',time_created datetime NOT NULL DEFAULT CURRENT_TIMESTAMP , PRIMARY KEY  (id)) ENGINE = InnoDB;"
        mycursor.execute(sql)

    def getByCompanyName(self, company_name):
        mycursor = self.mydb.cursor()
        sql = "SELECT * FROM " + self.tableName + " WHERE " + self.tableName + ".company_name='" + company_name + "'"
        print(sql)
        mycursor.execute(sql)
        return mycursor.fetchone()

    def save_company(self, company_obj):
        mycursor = self.mydb.cursor()
        logging.info("Save company: " + company_obj.company_name)
        sql = "INSERT INTO " + self.tableName + " (job_title, company_name, company_url, location) VALUES (%s, %s, %s, %s)"
        val = (company_obj.job_title, company_obj.company_name, company_obj.company_url, company_obj.location)
        try:
            mycursor.execute(sql, val)
            self.mydb.commit()
        except:
            logging.error("Save company: " + company_obj.company_name + " fail")
            self.mydb.rollback()


    def updateCompany(self, company_obj):
        mycursor = self.mydb.cursor()
        logging.info("Update company: " + company_obj.company_name + "with from_site: " + company_obj.from_site)

        sql = "UPDATE " + self.tableName + " SET company_url=%s, from_site=%s WHERE company_name=%s"
        val = (company_obj.company_url, company_obj.from_site, company_obj.company_name)

        mycursor.execute(sql, val)
        self.mydb.commit()

    def close(self):
        self.mydb.close()
        print("DB connection closed")
