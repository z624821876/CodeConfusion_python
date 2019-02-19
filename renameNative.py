#! /usr/bin/python
# -*- coding: UTF-8 -*-

# 替换前缀；类名随机字符串；
# python renameNative.py --old_prefix 需要替换的前缀 --new_prefix 新的前缀 --ios_path 项目目录  --proj_path xcodeproj所在目录
# python renameNative.py --old_prefix 'ALA' --new_prefix 'GW' --ios_path /Users/ryan/developer/3dParty/51fanbei2/ALAFanBei  --proj_path /Users/ryan/developer/3dParty/51fanbei2/ALAFanBei

import os,sys
import random
import string
import re
import md5
import time
import json
import shutil
import hashlib 
import time
import argparse
import json

import sys 
reload(sys) 
sys.setdefaultencoding("utf-8")

script_path = os.path.split(os.path.realpath(sys.argv[0]))[0]
add_prefix = ""
old_prefix = "xxx"
new_prefix = "zzz"
ios_src_path = ""
project_file_path = ""

ignore_path_text = [".a", ".framework", '.storyboard', '.xcassets', "ISJFQCommon","ISJJQCommon","Pods","scripts","Other","Macro","Libs","ALAFanBeiTests","ALAFanBeiUITests", "Target_"]
ignore_replace_text = [".a", ".framework", '.xcassets', "Pods", "Lib"]
word_history = []
file_name_history = {}


#单词列表，用以随机名称
with open(os.path.join(script_path, "./word_list.json"), "r") as fileObj:
    word_name_list = json.load(fileObj)


def create_dict_file(input_dict):
    new_dict = {}
    for (key, value) in input_dict.items():
        if 'Controller' in key:
            new_dict[key] = value

    f = open("replace.json", "wb")
    json.dump(new_dict, f)
    f.close()


def random_string():
    global word_name_list

    slice_list = random.sample(word_name_list, 2)
    result = ''
    for item in slice_list:
        result += item.capitalize()
    if result in word_history:
        print('random string repeat:%s' % result)
        return random_string()
    # result = result.upper()
    word_history.append(result)
#    print "random:%s" % (result)
    return result


def get_filename(file_name):
    letter_list = re.findall('[A-Z]+', file_name)[-1]
    if len(letter_list) <= 0:
        new_name = random_string()
#        print "生成新名字 old:%s new:%s" % (file_name, new_name)
        return new_name.encode(encoding='UTF-8')

    letter = letter_list[-1]
    if len(letter) > 0:
        letter = letter[-1]

    l = list(file_name)
    l.reverse()
    result = "".join(l)
    index = result.find(letter) + 1
    end = file_name[-index:]

    new_name = random_string() + end
#    print "生成新名字 old:%s new:%s" % (file_name, new_name)
    return new_name.encode(encoding='UTF-8')


#首字母大写
def isNeedIgnore(file_path):
    global ignore_path_text
    for ignore_text in ignore_path_text:
        if file_path.find(ignore_text) != -1:
            return True
    return False

def replaceStringInFile(full_path, old_text, new_text):
    with open(full_path, "r") as fileObj:
        all_text = fileObj.read()
        fileObj.close()
    all_text = all_text.replace(old_text, new_text)
    with open(full_path, "w") as fileObj:
        fileObj.write(all_text)
        fileObj.close()

def renameFileInXcodeProj(old_file_name, new_file_name):
    global project_file_path
    if os.path.exists(project_file_path):
        replaceStringInFile(project_file_path, old_file_name, new_file_name)

def renameInAllFile(old_text, new_text):
    global ios_src_path
    for parent, folders, files in os.walk(ios_src_path):
        need_ignore = None
        for ignore_folder in ignore_replace_text:
            if parent.find("/" + ignore_folder) != -1:
                need_ignore = ignore_folder
                # print "忽略替换文件:%s" % parent
                break
        if need_ignore:
            continue
        for file in files:
            full_path = os.path.join(parent, file)
            replaceStringInFile(full_path, old_text, new_text)

def dealWithIos():
    print "开始重命名类名"
    global old_prefix, new_prefix, ios_src_path
    for parent, folders, files in os.walk(ios_src_path):
        for file in files:
            old_full_path = os.path.join(parent, file)
            if file.startswith(old_prefix) and not isNeedIgnore(old_full_path):
                if file.endswith('.h') or file.endswith('.m') or file.endswith('.mm') or file.endswith('.xib'):
                    old_file_base_name = os.path.splitext(file)[0]
                    # new_file_name = file.replace(old_prefix, new_prefix)
                    new_file_name = file_name_history.get(old_file_base_name)
                    if not new_file_name:
                        for (key, value) in file_name_history.items():
                            if old_file_base_name.startswith(key):
                                new_file_name = value + old_file_base_name[len(key):]
                                break
                        if not new_file_name:
                            new_file_name = new_prefix + get_filename(old_file_base_name)
                        file_name_history[old_file_base_name] = new_file_name
                    new_file_name = new_file_name + os.path.splitext(file)[-1]

                    print "\t重命名文件: %s -> %s" %(file, new_file_name)

                    new_full_path = os.path.join(parent, new_file_name)
                    print '===new path:%s' % new_full_path
                    os.rename(old_full_path, new_full_path)
                    #在项目工程中改名
                    renameFileInXcodeProj(file, new_file_name)

                    #在可能引用的地方替换
                    new_file_base_name = os.path.splitext(new_file_name)[0]
                    # new_file_base_name = old_file_base_name.replace(old_prefix, new_prefix)
                    renameInAllFile(old_file_base_name, new_file_base_name)

    for parent, folders, files in os.walk(ios_src_path):
        for folder in folders:
            old_full_path = os.path.join(parent, folder)
            if folder.startswith(old_prefix) and not isNeedIgnore(old_full_path):
                new_folder_name = folder.replace(old_prefix, new_prefix)
                print "\t重命名文件夹: %s -> %s" %(folder, new_folder_name)
                new_full_path = os.path.join(parent, new_folder_name)
                os.rename(old_full_path, new_full_path)
                #在项目工程中改名
                renameFileInXcodeProj(folder, new_folder_name)
    print "finish\n"

def addPreFix():
    print "开始添加前缀"
    global add_prefix, ios_src_path
    for parent, folders, files in os.walk(ios_src_path):
        for file in files:
            old_full_path = os.path.join(parent, file)
            if not isNeedIgnore(old_full_path):
                if file.endswith('.h') or file.endswith('.m') or file.endswith('.mm') or file.endswith('.xib'):
                    old_file_base_name = os.path.splitext(file)[0]
                    # new_file_name = add_prefix + file
                    new_file_name = file_name_history.get(old_file_base_name)
                    if new_file_name:
                        new_file_name = add_prefix + new_file_name
                    if not new_file_name:
                        for (key, value) in file_name_history.items():
                            if old_file_base_name.startswith(key):
                                new_file_name = value + old_file_base_name[len(key):]
                                break
                        if not new_file_name:
                            new_file_name = add_prefix + get_filename(old_file_base_name)
                        file_name_history[old_file_base_name] = new_file_name
                    new_file_name = new_file_name + os.path.splitext(file)[-1]

                    print "\t重命名文件: %s` -> %s" %(file, new_file_name)

                    new_full_path = os.path.join(parent, new_file_name)
                    os.rename(old_full_path, new_full_path)
                    #在项目工程中改名
                    renameFileInXcodeProj(file, new_file_name)

                    #在可能引用的地方替换
                    new_file_base_name = os.path.splitext(new_file_name)[0]
                    renameInAllFile(old_file_base_name, new_file_base_name)
                    # renameInAllFile(add_prefix+add_prefix, add_prefix)

    for parent, folders, files in os.walk(ios_src_path):
        for folder in folders:
            old_full_path = os.path.join(parent, folder)
            if not isNeedIgnore(old_full_path):
                new_folder_name = add_prefix + folder
                print "\t重命名文件夹: %s -> %s" %(folder, new_folder_name)
                new_full_path = os.path.join(parent, new_folder_name)
                os.rename(old_full_path, new_full_path)
                #在项目工程中改名
                renameFileInXcodeProj(folder, new_folder_name)
    print "finish\n"


#----------------------------------------------------main------------------------------------------------        
def parse_args():
    global script_path, proj_ios_path
    parser = argparse.ArgumentParser(description='修改类名前缀工具.\n')
    parser.add_argument('--add_prefix', dest='add_prefix', type=str, required=False, default="", help='添加类名前缀')
    parser.add_argument('--old_prefix', dest='old_prefix', type=str, required=False, help='原类名前缀')
    parser.add_argument('--new_prefix', dest='new_prefix', type=str, required=False, help='替换后类名前缀')
    parser.add_argument('--ios_path', dest='ios_path', type=str, required=True, help='OC文件目录')
    parser.add_argument('--proj_path', dest='proj_path', type=str, required=False, default="", help='xx.xcodeproj路径')
    args = parser.parse_args()
    return args

def main():
    global old_prefix, new_prefix, ios_src_path, project_file_path, add_prefix
    app_args = parse_args()

    add_prefix = app_args.add_prefix
    old_prefix = app_args.old_prefix
    new_prefix = app_args.new_prefix
    ios_src_path = app_args.ios_path
    project_file_path = os.path.join(app_args.proj_path, "project.pbxproj")
    if not os.path.exists(ios_src_path):
        print "ios_path not exists: " +  ios_src_path
        exit(0)
    if not os.path.exists(project_file_path):
        print "proj_path not exists: " +  project_file_path

    print "请提前备份文件夹或确认在版本管理软件中"
    raw_input("回车继续执行")
    if add_prefix and add_prefix != "":
        addPreFix()
        exit(0)
    dealWithIos()

    create_dict_file(file_name_history)
 

if __name__ == "__main__":
    main()
    # print get_filename('GWFunerealDeterminationExtension.m')
