import argparse
import hashlib
import time
from xmlrpc.client import ServerProxy
from config import serverDB_url
from config import dfs_root_path
from config import local_path
from pathlib import Path

def register_user(name, password):
    hash = hashlib.md5() 
    hash.update(bytes(password, encoding='utf-8'))
    hash_password = hash.hexdigest()

    if proxy.add_user(name, hash_password):
        print('Registered user {} successfully.'.format(name))
    else:
        print('There is already a user {}.'.format(name))
    return

def login_user(name, password):
    result = proxy.get_user(name)
    if result is None:
        print('Username does not exist.')
    else:
        user_id = int(result[0])
        hash_password = result[1]

        hash = hashlib.md5()
        hash.update(bytes(password, encoding='utf-8'))

        if hash_password == hash.hexdigest():
            return App(user_id, name)
        else:
            print('Wrong password.')
    return None

class App(object):
    def __init__(self, user_id, user_name):
        active_server = proxy.get_free_server()
        if active_server is not None:
            self.server_id = active_server[0]
            self.server_address = active_server[1]
        else:
            print('There is no free servers now.')
            exit(1)
        self.server = ServerProxy(self.server_address, allow_none=True)
        self.user_id = user_id
        self.user_name = user_name
        self.cur_path = user_name
        self.local_path = local_path
        self.welcome()
        self.help()

    def welcome(self):
        print('=' * 80)
        print('=', ' ' * 76, '=')
        print('=', format('Welcome to my dfs, dear ' +
              self.user_name + '!', ' ^76'), '=')
        print('=', format('Server address: ' +  repr(self.server_address) + '.', ' ^76'), '=')
        print('=', ' ' * 76, '=')
    
    def pwd(self):
        whole_path = str(Path.home() / dfs_root_path / str(self.cur_path))
        print('=', format('Current path in server: ' + whole_path, ' <76'))

    def cd(self, path):
        cd_path = self.server.cd(self.cur_path, path)
        if cd_path:
            self.cur_path = cd_path
        else: 
            print('=', format('cd failed: There is no directory:' + path, ' <76'))
    
    def ls(self, b):
        result = self.server.ls(self.user_id, self.cur_path, b)
        print('=' * 80)
        print('=', format('All files in path ~/' +
              self.cur_path + ':', ' ^76'), '=')
        print('=', format('File name', ' >20'),format('Is dir', ' >10'), 
            format('Has backup', ' >18'),format('Last modified', ' >25'), '=')
        for file in result:
            last_modified = time.localtime(file[2])
            year_modified = repr(last_modified.tm_year)
            month_modified = repr(last_modified.tm_mon)
            day_modified = repr(last_modified.tm_mday)
            hour_modified = repr(last_modified.tm_hour)
            minute_modified = repr(last_modified.tm_min)
            second_modified = repr(last_modified.tm_sec)
            
            has_backup = 0
            if self.server.check_backup(self.user_id, self.cur_path, file[0]):
                has_backup = 1

            print('=', format(file[0], ' >20'), format(file[1], ' >10'), format(repr(has_backup), ' >18'),
                format(year_modified + '/' + month_modified + '/' + day_modified + '  ' + 
                hour_modified + ':' + minute_modified + ':' + second_modified, ' >25'), '=')
        print('=' * 80)

    def backup(self):
        self.ls(1)

    def recover(self, file_name):
        if not self.server.recover_file(self.user_id, self.cur_path, file_name):
            print('=', format('recover failed: There is no backup for ' + file_name, ' <76'))
        return

    def mkdir(self, dir_name):
        if not self.server.create_dir(self.user_id, self.cur_path, dir_name):
            print('=', format('mkdir failed: There is already a directory ' + dir_name, ' <76'))
        
    def rmdir(self, dir_name):
        if not self.server.remove_dir(self.user_id, self.cur_path, dir_name):
            print('=', format('rmdir failed: There is no directory ' + dir_name + 
            ' or it is not a directory',' <76'))

    def mkfile(self, file_name):
        if not self.server.create_file(self.user_id, self.cur_path, file_name):
            print('=', format('mkfile failed: There is already a file ' + file_name, ' <76'))
    
    def get(self, file_name):
        local_file = str(Path.home() / self.local_path / file_name)
        data = self.server.get_file(self.user_id, self.cur_path, file_name)
        if data is not False:
            print('=', format(
                'Get file ' + file_name + ' in ' + self.local_path + ':', ' <76'))
            print('<<<')
            print(data)
            print('>>>')
            data = data.encode(encoding='utf-8')
            fp = open(local_file, 'wb')
            fp.write(data)
            fp.close()
        else:
            print('=', format(
                'get failed: Cant\'t get file ' + file_name, ' <76'))
    
    def upload(self, file_path):
        file_path = Path.home() / self.local_path / file_path
        names = str(file_path).split('/')
        file_name = names[len(names)-1]

        fp = open(file_path, 'rb')
        data = fp.read()
        fp.close()
        if self.server.upload_file(self.user_id, self.cur_path, file_name, data.decode()):
            print('=', format('Upload ' + str(file_path) + ' to ' +
              self.cur_path + ' successfully.', ' <76'))
            return True
        else:
            print('=', format('Upload ' + str(file_path) + ' to ' +
              self.cur_path + ' failed.', ' <76'))
            return False

    def rm(self, file_name):
        if not self.server.remove_file(self.user_id, self.cur_path, file_name):
            print('=', format('rm failed: There is no file ' + file_name + 
            ' or it is not a file', ' <76'))

    def refresh(self):
        if not self.server.refresh(self.user_id, self.cur_path):
            print('=', format('refresh failed: There is no file ', ' <76'))

    def quit(self):
        proxy.user_quit(self.server_id)
        print('=', format('Quiting the system...', ' <76'))
        print('=', format('Have a nice day!', ' <76'))
        print('=' * 80)
        exit(0)

    def help(self):
        print('=' * 80)
        print('=', format('Command help:',' <76'), '=')
        print('=', format('-  pwd', ' <40'), format('[print current path in server]', ' <35'), '=')
        print('=', format('-  cd <dir_name>', ' <40'), format('[change current path]',' <35'), '=')
        print('=', format('-  ls', ' <40'), format('[list all files in current path]',' <35'), '=')
        print('=', format('-  backup', ' <40'), format('[list all backups in current path]', ' <35'), '=')
        print('=', format('-  recover <file_name>', ' <40'),
              format('[recover a file from backup]', ' <35'), '=')
        print('=', format('-  mkdir <dir_name>', ' <40'),format('[create directory]',' <35'), '=')
        print('=', format('-  rmdir <dir_name>', ' <40'),format('[remove directory]', ' <35'), '=')
        print('=', format('-  mkfile <file_name>', ' <40'),format('[create file]', ' <35'), '=')
        print('=', format('-  get <file_name> <local_path>', ' <40'),format('[get file in local]', ' <35'), '=')
        print('=', format('-      <local_path> default:' + self.local_path, ' <76'), '=')
        print('=', format('-  upload <local_path> <server_path>',' <40'), format('[get file in local]', ' <35'), '=')
        print('=', format('-      <server_path> default:' + self.cur_path, ' <76'), '=')
        print('=', format('-  rm <file_name>', ' <40'),format('[remove file]', ' <35'), '=')
        print('=', format('-  refresh', ' <40'), format('[refresh all files in current path]', ' <35'), '=')
        print('=', format('-  q or quit', ' <40'),format('[quit the system]', ' <35'), '=')
        print('=', format('-  h or help', ' <40'),format('[get command help]', ' <35'), '=')
        print('=' * 80)

    def loop(self):
        while True:
            op = str(input('= ~/' + self.cur_path + ' $ ')).split(' ')
            if op[0] == 'pwd' and len(op) == 1:
                self.pwd()
            elif op[0] == 'cd' and len(op) == 2:
                self.cd(op[1])
            elif op[0] == 'ls' and len(op) == 1:
                self.ls(0)
            elif op[0] == 'backup' and len(op) == 1:
                self.backup()
            elif op[0] == 'recover' and len(op) == 2:
                self.recover(op[1])
            elif op[0] == 'mkdir' and len(op) == 2:
                self.mkdir(op[1])
            elif op[0] == 'rmdir' and len(op) == 2:
                self.rmdir(op[1])
            elif op[0] == 'mkfile' and len(op) == 2:
                self.mkfile(op[1])
            elif op[0] == 'get':
                if len(op) == 3:
                    self.local_path = op[2]
                self.get(op[1])
            elif op[0] == 'upload':
                if len(op) == 3:
                    self.cur_path = op[2]
                self.upload(op[1])
            elif op[0] == 'rm' and len(op) == 2:
                self.rm(op[1])
            elif op[0] == 'refresh' and len(op) == 1:
                self.refresh()
            elif (op[0] == 'help' or op[0] == 'h') and len(op) == 1:
                self.help()
            elif (op[0] == 'quit' or op[0] == 'q') and len(op) == 1:
                self.quit()
            else:
                print('=', format('Wrong command, enter h or help to get command help.', ' <76'))

if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('mode', help='The mode of client, [register] or [login].', type=str)
    parser.add_argument('username', help='User name.', type=str)
    parser.add_argument('password', help='Password.', type=str)
    args = parser.parse_args()

    proxy = ServerProxy(serverDB_url, allow_none=True)

    if args.mode == 'register' or args.mode == 'r':
        register_user(args.username, args.password)
    elif args.mode == 'login' or args.mode == 'l':
        app = login_user(args.username, args.password)
        if app is not None:
            app.loop()
    else:
        print('Invalid mode.')