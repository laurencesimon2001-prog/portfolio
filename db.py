import pymysql
def get_connection():
    return pymysql.connect(
        host="localhost",
        user="lucifer",
        password="7812co2Y",
        database="portfolio_db",
        cursorclass=pymysql.cursors.DictCursor
    )