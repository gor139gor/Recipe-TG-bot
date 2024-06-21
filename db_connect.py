import mysql.connector


def connect_to_database():
    try:
        connection = mysql.connector.connect(
            host="localhost",
            user="root",
            password="dfdfdf123",
            database="recipe_tgbot"
        )
        print("Connected to the database!")
        return connection
    except mysql.connector.Error as error:
        print("Failed to connect to the database:", error)
        return None


def close_database_connection(connection):
    try:
        if connection.is_connected():
            connection.close()
            print("Connection to the database is closed.")
    except mysql.connector.Error as error:
        print("Failed to close database connection:", error)


def main():
    # Підключення
    connection = connect_to_database()
    if connection is None:
        return

    # Закриття з'єднання
    close_database_connection(connection)


if __name__ == "__main__":
    main()
