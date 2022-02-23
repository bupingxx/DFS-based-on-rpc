import sqlite3
import os
from pathlib import Path
from xmlrpc.server import SimpleXMLRPCServer
from config import serverDB_info
from config import dfs_root_path

def init_table_user():
    conn.execute('''CREATE TABLE USERS
       (USERID INT PRIMARY KEY NOT NULL,
       NAME    TEXT UNIQUE     NOT NULL,
       PASSWORD       TEXT     NOT NULL);''')
    conn.commit()
    return 

def init_table_server():
    conn.execute('''CREATE TABLE SERVERS
       (SERVERID INT PRIMARY KEY NOT NULL,
       FREE              INT     NOT NULL,
       ADDRESS           TEXT    NOT NULL);''')
    conn.commit()
    return 

def init_table_file():
    conn.execute('''CREATE TABLE FILES
       (USERID           TEXT   NOT NULL,
        SERVERID         TEXT   NOT NULL,
        PATH             TEXT   NOT NULL,
        FILENAME         TEXT   NOT NULL,
        ISDIR            TEXT   NOT NULL,
        ISBACKUP         INT    NOT NULL,
        LASTMODIFIED     INT    NOT NULL);''')
    conn.commit()
    return 

def init_db():
    init_table_user()
    init_table_server()
    init_table_file()
    conn.commit()
    return

def add_user(name, password):
    try:
        cursor.execute('SELECT COUNT(*) FROM USERS;')
        result = cursor.fetchone()
        user_id = result[0] + 1
        cursor.execute(
            'INSERT INTO USERS (USERID, NAME, PASSWORD) VALUES (?, ?, ?);', 
            (user_id, name, password))
        conn.commit()

        print("Register user {} {} {}.".format(user_id, name, password))
        user_root_dir = Path.home() / dfs_root_path / name
        if not user_root_dir.exists():
            user_root_dir.mkdir(parents=True)
        return True
    except sqlite3.Error:
        print('Error in add_user')
        return False

def add_server(server_id, address):
    try:
        cursor.execute(
            'INSERT INTO SERVERS (SERVERID, FREE, ADDRESS) VALUES (?, ?, ?);', 
            (server_id, max_conn, address))
        conn.commit()

        print("Register server {} {}.".format(server_id, address))
        return True
    except sqlite3.Error:
        print('Error in add_server')
        return False

def add_file(file_info):
    try:
        [user_id, server_id, path, file_name, isdir, isbackup, last_modified] = file_info
        cursor.execute(
            'INSERT INTO FILES (USERID, SERVERID, PATH, FILENAME, ISDIR, ISBACKUP, LASTMODIFIED) \
            VALUES(?, ?, ?, ?, ?, ?, ?)',                                                       
            (user_id, server_id, path, file_name, isdir, isbackup, last_modified))
        conn.commit()

        print("Add file", file_info)
        return True
    except sqlite3.Error:
        print('Error in add_file')
        return False

def start_server(server_id):
    cursor.execute('UPDATE SERVERS SET FREE = ? WHERE SERVERID = ?;', (max_conn, server_id))
    print('Start server {}.'.format(server_id))


def get_user(user_name):
    try:
        cursor.execute('SELECT USERID, PASSWORD FROM USERS WHERE NAME = ?;', (user_name, ))
        result = cursor.fetchone()
        print('Get user {}.'.format(user_name))
        return result
    except sqlite3.Error:
        print('Error in get_user')
        return None

def get_free_server(): 
    try:
        cursor.execute(
            'SELECT SERVERID, ADDRESS FROM SERVERS WHERE FREE > 0;')
        result = cursor.fetchone()
        if result is not None:
            print(result)
            cursor.execute(
                'UPDATE SERVERS SET FREE = FREE - 1 WHERE SERVERID = ?;', (result[0],))
            conn.commit()
            print('Get free server {}.'.format(result[0]))
        else:
            print('No free server.')
        return result
    except sqlite3.Error:
        print('Error in get_free_server')
        return None

def user_quit(server_id):
    try:
        cursor.execute(
            'UPDATE SERVERS SET FREE = FREE + 1 WHERE SERVERID = ?;', (server_id, ))
        conn.commit()
        print('server {} is free now.'.format(server_id))
    except sqlite3.Error:
        print('Error in user_quit')
        return 

def del_file(user_id, path, file_name, isbackup):
    try:
        cursor.execute(
            'DELETE FROM FILES WHERE USERID = ? AND PATH = ? AND FILENAME = ? AND ISBACKUP = ?;',
            (user_id, path, file_name, isbackup))
        conn.commit()
        print('Del file {} {} {}.'.format(user_id, path, file_name))
        return True
    except sqlite3.Error:
        print('Error in list_file')
        return False

def list_file(user_id, cur_path, b):
    try:
        cursor.execute(
            'SELECT FILENAME, ISDIR, LASTMODIFIED FROM FILES \
            WHERE USERID = ? AND PATH = ? AND ISBACKUP = ?;',
            (user_id, cur_path, b))
        result = cursor.fetchall()
        print('List file {} {}.'.format(user_id, cur_path))
        return result
    except sqlite3.Error:
        print('Error in del_file')
        return False

def check_file_backup(user_id, cur_path, file_name):
    try:
        cursor.execute(
            'SELECT COUNT(*) FROM FILES \
            WHERE USERID = ? AND PATH = ? AND FILENAME = ?;',
            (user_id, cur_path, file_name+'.backup'))

        result = cursor.fetchone()
        print('Check file backup {} {} {}.'.format(user_id, cur_path, file_name))
        return True
    except sqlite3.Error:
        print('Error in del_file')
        return False

def get_file_lastmodified(user_id, cur_path, file_name):
    try:
        cursor.execute(
            'SELECT LASTMODIFIED FROM FILES \
            WHERE USERID = ? AND PATH = ? AND FILENAME = ?;',
            (user_id, cur_path, file_name))

        result = cursor.fetchone()
        print('Get file lastmodified {} {} {}.'.format(
            user_id, cur_path, file_name))
        return result[0]
    except sqlite3.Error:
        print('Error in get_file_lastmodified')
        return False

if __name__ == '__main__':
    need_to_init = 1
    if os.path.exists(os.getcwd() + '/serverDB.db'):
        need_to_init = 0

    conn = sqlite3.connect('serverDB.db')
    print("Open server database successfully.")
    cursor = conn.cursor()
    max_conn = 1
    if need_to_init == 1:
        init_db()
    with SimpleXMLRPCServer(serverDB_info, allow_none=True) as server:
        server.register_function(add_user)
        server.register_function(add_server)
        server.register_function(add_file)
        server.register_function(start_server)
        server.register_function(get_user)
        server.register_function(get_free_server)
        server.register_function(get_file_lastmodified)
        server.register_function(del_file)
        server.register_function(list_file)
        server.register_function(check_file_backup)
        server.register_function(user_quit)
        try:
            server.serve_forever()
        except KeyboardInterrupt:
            conn.close()
            print("Close server database.")
