import argparse
import os
from xmlrpc.server import SimpleXMLRPCServer
from xmlrpc.client import ServerProxy
from pathlib import Path
from config import serverDB_url
from config import dfs_root_path

def get_backup_path(cur_path):
    paths = cur_path.split('/')
    if len(paths) == 1:
        return paths[0]

    backup_path = paths[0] + '/'
    for i in range(1, len(paths)):
        backup_path += paths[i] + '.backup/'
    return backup_path

def check_file(user_id, cur_dir, file_name):
    lastmodified1 = proxy.get_file_lastmodified(user_id, cur_dir, file_name)
    lastmodified2 = proxy.get_file_lastmodified(user_id, get_backup_path(cur_dir), file_name+'.backup')
    if lastmodified1 > lastmodified2:
        print('It\'s latest.')
        return True
    else:
        print('Check failed.')
        return False

def add_file(user_id, file_path, file_name, isdir, isbackup):
    lastmodified = os.path.getmtime(root_dir / file_path / file_name)
    file_info = [user_id, server_id, file_path, file_name, isdir, isbackup, lastmodified]
    if proxy.add_file(file_info):
        print('add file:', file_info)
        return True
    else:
        return False

def delete_file(user_id, file_path, file_name, isbackup):
    if proxy.del_file(user_id, file_path, file_name, isbackup):
        print('del file:', user_id, file_path, file_name, isbackup)
        return True
    else:
        return False 

def update_file(user_id, file_path, file_name, isdir, isbackup):
    if not delete_file(user_id, file_path, file_name, isbackup):
        return False
    if not add_file(user_id, file_path, file_name, isdir, isbackup):
        return False
    return True

def cd(cur_path, dir_path):
    if dir_path == '..':
        ridx = cur_path.rfind('/')
        if ridx == -1:
            ridx = len(cur_path)

        cur_path = cur_path[0:ridx]
        cd_path = root_dir / cur_path
        if os.path.isdir(cd_path):
            print("cd {}".format(cd_path))
            return (cur_path)
    else:
        cd_path = root_dir / cur_path / dir_path
        if os.path.isdir(cd_path):
            print("cd {}".format(cd_path))
            return (cur_path + '/' + dir_path)
    print("cd failed.")
    return False

def ls(user_id, cur_path, b):
    if b==1:
        cur_path = get_backup_path(cur_path)
    print("ls {}".format(cur_path))
    return proxy.list_file(user_id, cur_path, b)

def refresh(user_id, cur_dir):
    file_list = ls(user_id, cur_dir, 0)
    backup_list = ls(user_id, get_backup_path(cur_dir), 1)
    print('Refresh...')
    print(file_list)
    print(backup_list)
    for file_info in file_list:
        if not update_file(user_id, cur_dir, file_info[0], file_info[1], 0):
            print('refresh {} failed'.format(file_info[0]))
    for file_info in backup_list:
        if not update_file(user_id, cur_dir, file_info[0], file_info[1], 1):
            print('refresh {} failed'.format(file_info[0]))
    return True
    
def create_dir(user_id, cur_dir, dir_name):
    new_dir = root_dir / cur_dir / dir_name
    new_dir_backup = root_dir / get_backup_path(cur_dir) / (dir_name + '.backup')
    print(new_dir_backup) #test
    if not new_dir.exists():
        new_dir_backup.mkdir(parents=True)
        add_file(user_id, get_backup_path(cur_dir), dir_name + '.backup', 1, 1)
        new_dir.mkdir(parents=True)
        add_file(user_id, cur_dir, dir_name, 1, 0)
        print('creat dir {}'.format(new_dir))
        return True
    else:
        return False


def remove_dir(user_id, cur_dir, dir_name):
    del_dir = root_dir / cur_dir / dir_name
    print(del_dir)
    if del_dir.exists() and del_dir.is_dir():
        os.rmdir(del_dir)
        delete_file(user_id, cur_dir, dir_name, 0)
        print('remove dir {}'.format(del_dir))
        return True
    else:
        return False

def create_file(user_id, cur_dir, file_name):
    new_file = root_dir / cur_dir / file_name
    new_file_backup = root_dir / get_backup_path(cur_dir) / (file_name + '.backup')
    if not new_file.exists():
        fp = open(str(new_file_backup), 'wb')
        fp.close()
        add_file(user_id, get_backup_path(cur_dir), file_name + '.backup', 0, 1)
        fp = open(str(new_file), 'wb')
        fp.close()
        add_file(user_id, cur_dir, file_name, 0, 0)
        print('creat file {}'.format(new_file))
        return True
    else:
        return False

def remove_file(user_id, cur_dir, file_name):
    del_file = root_dir / cur_dir / file_name
    print(del_file)
    if del_file.exists() and del_file.is_file():
        os.remove(del_file)
        delete_file(user_id, cur_dir, file_name, 0)
        print('delete file {}'.format(del_file))
        return True
    else:
        return False

def recover_file(user_id, cur_dir, file_name):
    file = root_dir / cur_dir / file_name
    if file.is_dir():
        isdir = 1
    else:
        isdir = 0
    file_path = str(root_dir / cur_dir / file_name)
    file_backup_path = str(root_dir / get_backup_path(cur_dir) / (file_name + '.backup'))
    fp = open(file_backup_path, 'rb')
    data = fp.read()
    fp.close()
    fp = open(file_path, 'wb')
    fp.write(data)
    fp.close()
    if update_file(user_id, cur_dir, file_name, isdir, 0):
        print('recover file {}/{}'.format(cur_dir, file_name))
    return True

def get_file(user_id, cur_dir, file_name):
    file_path = root_dir / cur_dir / file_name
    if not file_path.is_file():
        return False
    if not check_file(user_id, cur_dir, file_name):
        recover_file(user_id, cur_dir, file_name)

    fp = open(str(file_path), 'rb')
    data = fp.read()
    fp.close()
    print('get file {}/{}'.format(cur_dir, file_name))
    return data.decode()


def upload_file(user_id, cur_dir, file_name, file_data):
    file_path = root_dir / cur_dir / file_name
    backup_path = root_dir / get_backup_path(cur_dir) / (file_name + '.backup')
    data = file_data.encode(encoding='utf-8')
    if file_path.exists():
        delete_file(user_id, cur_dir, file_name, 0)
    if backup_path.exists():
        delete_file(user_id, get_backup_path(cur_dir), (file_name + '.backup'), 1)

    fp = open(str(backup_path), 'wb')
    fp.write(data)
    fp.close()
    if not add_file(user_id, get_backup_path(cur_dir), file_name + '.backup', 0, 1):
        return False

    fp = open(str(file_path), 'wb')
    fp.write(data)
    fp.close()
    if not add_file(user_id, cur_dir, file_name, 0, 0):
        return False

    print('upload file {}/{}'.format(cur_dir, file_name))
    return True

def check_backup(user_id, cur_path, name):
    cur_path = get_backup_path(cur_path)
    return proxy.check_file_backup(user_id, cur_path, name)


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('server_id', help='Server ID.', type=int)
    parser.add_argument('port', help='Server port.', type=int)
    args = parser.parse_args()

    server_id = args.server_id
    proxy = ServerProxy(serverDB_url, allow_none=True)
    root_dir = Path.home() / dfs_root_path

    with SimpleXMLRPCServer(('localhost', args.port)) as server:
        server.register_function(cd)
        server.register_function(ls)
        server.register_function(create_dir)
        server.register_function(remove_dir)
        server.register_function(create_file)
        server.register_function(remove_file)
        server.register_function(update_file)
        server.register_function(refresh)
        server.register_function(get_file)
        server.register_function(upload_file)
        server.register_function(recover_file)
        server.register_function(check_backup)

        server_url = 'http://{}:{}'.format(
            server.server_address[0], server.server_address[1])

        print("Registing server {} on port {}, address is {}".format( 
            args.server_id, args.port, server_url))
        
        if(proxy.add_server(server_id, server_url)):
            print("Regist server {} successfully.".format(server_id))
        else:
            proxy.start_server(args.server_id)
            print("Start server {}.".format(args.server_id))

        server.serve_forever()

