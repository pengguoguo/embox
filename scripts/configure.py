#!/usr/bin/env python
# -*- coding: utf-8 -*-
# Monitor configurator
# date: 19.05.09
# author: sikmir
# requirement: python >= 2.6

import Tkinter
from Tkinter import *
from conf_tab import *
import string, os, traceback
import tkSimpleDialog
import re
import json
import shutil

root, menu, files = ( None, None, None)
frame = { "0" : 0 }
tabs = { "0" : 0 }
build_var = { "0": 0 }
level_var = { "0" : 0 }
common_var = { "0": 0 }
varc, vart, vard = (None, None, None)

def read_config(fileconf):
	""" Read config file """
        global menu, tabs, files
        with open(fileconf, 'r') as conf:
                config = conf.read()
                json_conf = json.loads(config)
                menu = json_conf['Menu']
                files = json_conf['Files']
                for tab in menu:
            		tabs[str(tab)] = json_conf[str(tab)]
        conf.close()

def write_config(fileconf):
	""" Write config file """
	global build_var, common_var, level_var
        with open(fileconf, 'w+') as conf:
		tmp = dict([('Menu', menu), ('Files', files)])
		for i in range( len(menu) ):
			tmp[menu[i]] = tabs[menu[i]]
                #-- Common
                tmp["Common"]["Compiler"] = common_var["Compiler"].get()
                tmp["Common"]["Target"] = common_var["Target"].get()
                tmp["Common"]["Cflags"] = common_var["Cflags"].get()
                tmp["Common"]["Ldflags"] = common_var["Ldflags"].get()
                tmp["Common"]["Arch_num"] = common_var["Arch_num"].get()
                #-- Levels
                tmp["Levels"]["Error"] = level_var["Error"].get()
                tmp["Levels"]["Trace"] = level_var["Trace"].get()
                tmp["Levels"]["Warn"] = level_var["Warn"].get()
                tmp["Levels"]["Debug"] = level_var["Debug"].get()
                tmp["Levels"]["Test_system"] = level_var["Test_system"].get()
                tmp["Levels"]["Leon3"] = level_var["Leon3"].get()
                #-- Build
                tmp["Build"]["Debug"] = build_var["Debug"].get()
                tmp["Build"]["Release"] = build_var["Release"].get()
                tmp["Build"]["Simulation"] = build_var["Simulation"].get()
                tmp["Build"]["Doxygen"] = build_var["Doxygen"].get()
                conf.write(json.dumps(tmp))
        conf.close()

def reload_config():
        """ Reload config """
	read_config(".config.default")
        for item in [ "Compiler", "Ldflags", "Cflags", "Target", "Arch_num" ]:
                common_var[item].set(tabs["Common"][item])
        for i in range( len(tabs[menu[4]].keys()) ):
                name = str(tabs[menu[4]].keys()[i])
                level_var[name].set(tabs[menu[4]][name])
        for i in range( len(tabs[menu[5]].keys()) ):
                name = str(tabs[menu[5]].keys()[i])
                build_var[name].set(tabs[menu[5]][name])
        #-- Drivers
        for item in tabs[menu[1]].keys():
    		for driver, inc, status, desc, mdef in tabs[menu[1]][item]:
            		getattr(vard, driver).set(inc)
        #-- Tests
        for test_name, inc, status, desc, mdef in tabs[menu[2]]:
                getattr(vart, test_name).set(inc)
        #-- Users
        for cmd, inc, status, desc, mdef in tabs[menu[3]]:
                getattr(varc, cmd).set(inc)

def onPress(ar, i, j):
	ar[i][j] = not ar[i][j]

def onPress_dep(item, i, j):
	tabs[menu[1]][item][i][j] = not tabs[menu[1]][item][i][j]
	if item == "common":
		if tabs[menu[1]][item][i][0] == "gaisler":
			for k in range( len(tabs[menu[1]]["gaisler"]) ):
				tabs[menu[1]]["gaisler"][k][1] = not tabs[menu[1]]["gaisler"][k][1]
				getattr(vard, tabs[menu[1]]["gaisler"][k][0]).set(tabs[menu[1]]["gaisler"][k][1])

def getStatus(i):
	if i == 1:
		return "normal"
	if i == 0:
		return "disabled"

def make_conf():
	build_commands()
	build_makefile()
	build_tests()
	write_autoconf()
	write_config(".config")

def build_commands():
	#-- generate src/conio/shell.inc
	with open(files["shell_inc"], 'w+') as fshell:
		fshell.write("".join(["//Don't edit! ", files["shell_inc"], ": auto-generated by configure.py\n\n"]))
		for test, inc, status, desc, mdef in tabs['Commands']:
			if inc == True:
				if test != "wmem":
					fshell.write("{\"" + test + "\", \"" + desc + "\", " + test + "_shell_handler},\n")
				else:
					fshell.write("{\"" + test + "\", \"" + desc + "\", " + test + "_shell_handler}\n")
	fshell.close()
	#-- generate src/conio/tests.inc
	with open(files["users_inc"], 'w+') as fuser_include:
		fuser_include.write("".join(["//Don't edit! ", files["users_inc"], ": auto-generated by configure.py\n\n"]))
		for cmd, inc, status, desc, mdef in tabs['Commands']:
			if inc == True:
				if cmd != "arp":
					fuser_include.write("#include \"" + cmd + ".h\"\n")
				else:
					fuser_include.write("#include \"" + cmd + "c.h\"\n")
	fuser_include.close()

def repl_compil(m):
	return "CC_PACKET:= " + common_var["Compiler"].get()

def repl_target(m):
	return "TARGET:= " + common_var["Target"].get()

def repl_all(m):
	repl = "all: "
	if build_var["Debug"].get() == 1:
		repl += "debug "
	if build_var["Release"].get() == 1:
		repl += "release "
	if build_var["Simulation"].get() == 1:
		repl += "simulation "
	if build_var["Doxygen"].get() == 1:
		repl += "docs "
	return repl

def repl_cflag(m):
	repl = "CCFLAGS:= " + common_var["Cflags"].get()
	if level_var["Leon3"].get() == 1:
		repl += " -DLEON3"
	if level_var["Test_system"].get() == 1:
		repl += " -D_TEST_SYSTEM_"
	if level_var["Error"].get() == 1:
		repl += " -D_ERROR"
	if level_var["Trace"].get() == 1:
		repl += " -D_TRACE"
	if level_var["Warn"].get() == 1:
		repl += " -D_WARN"
	if level_var["Debug"].get() == 1:
		repl += " -D_DEBUG"
	return repl

def repl_ldflag(m):
        repl = "LDFLAGS:= " + common_var["Ldflags"].get()
        return repl

def build_makefile():
	#-- generate makefile
	with open('makefile', 'r+') as fmk:
		content = fmk.read()
	fmk.close()
	content = re.sub('CC_PACKET:= (\w+(-\w+)?)', repl_compil, content)
	content = re.sub('TARGET:= (\w+)', repl_target, content)
	content = re.sub('CCFLAGS:= ([A-Za-z0-9_\-# ]+)', repl_cflag, content)
	content = re.sub('LDFLAGS:= ([A-Za-z0-9_\-# ]+)', repl_ldflag, content)
	with open('makefile', 'w+') as fmk:
		fmk.write(content)
	fmk.close()
	#-- generate src/makefile
	with open('src/makefile', 'r+') as fmk:
		content = fmk.read()
	fmk.close()
	content = re.sub('all: ([a-z ]+)', repl_all, content)
	with open('src/makefile', 'w+') as fmk:
		fmk.write(content)
	fmk.close()

def build_tests():
	#-- generate src/tests/tests_table.inc
	with open(files["tests_table_inc"], 'w+') as ftest:
		ftest.write("".join(["//Don't edit! ", files["tests_table_inc"], ": auto-generated by configure.py\n\n"]))
		for test, inc, status, desc, mdef in tabs['Tests']:
			if inc == True:
				ftest.write("{\"" + desc + "\", " + test + "},\n")
		ftest.write("{\"empty\", NULL}\n")
	ftest.close()

def repl_flag(pref, flag):
	return pref + "=" + flag

def replacer(mdef, inc, content):
	if inc == True:
                content = re.sub(mdef + '=(\w+)', repl_flag(mdef, "y"), content)
        else:
                content = re.sub(mdef + '=(\w+)', repl_flag(mdef, "n"), content)
        return content

def write_autoconf():
	#-- resr autoconf
        with open(files["autoconf"], 'r+') as faconf:
                content = faconf.read()
        faconf.close()
        #-- Arch
        for ar, value, mdef in tabs['Common']['Arch']:
		content = replacer(mdef, value == common_var["Arch_num"].get(), content)
        #-- Tests
        for test, inc, status, desc, mdef in tabs[menu[2]]:
    		content = replacer(mdef, inc, content)
    	#-- Users
    	for cmd, inc, status, desc, mdef in tabs[menu[3]]:
		content = replacer(mdef, inc, content)
    	#-- Drivers
    	for item in tabs[menu[1]].keys():
                for driver, inc, status, desc, mdef in tabs[menu[1]][item]:
			content = replacer(mdef, inc, content)
	#-- write autoconf
        with open(files["autoconf"], 'w+') as faconf:
                faconf.write(content)
        faconf.close()

#-----------------------------GUI------------------------------
def About():
	view_window = Tkinter.Toplevel(root)
	about_text = "Monitor configurator\nAuthor: Nikolay Korotky\n2009"
	Tkinter.Label(view_window,  text=about_text).pack()
	Tkinter.Button(view_window, text='OK', command=view_window.destroy).pack()
        view_window.focus_set()
        view_window.grab_set()
        view_window.wait_window()

def file_menu():
	file_btn = Tkinter.Menubutton(frame["Menu"], text='File', underline=0)
	file_btn.pack(side=Tkinter.LEFT, padx="2m")
	file_btn.menu = Tkinter.Menu(file_btn)
	file_btn.menu.add_command(label="Save", underline=0, command=make_conf)
	file_btn.menu.add_command(label="Load default", underline=0, command=reload_config)
	file_btn.menu.add('separator')
	file_btn.menu.add_command(label='Exit', underline=0, command=file_btn.quit)
	file_btn['menu'] = file_btn.menu
	return file_btn

def help_menu():
	help_btn = Tkinter.Menubutton(frame["Menu"], text='Help', underline=0,)
	help_btn.pack(side=Tkinter.LEFT, padx="2m")
	help_btn.menu = Tkinter.Menu(help_btn)
	help_btn.menu.add_command(label="About", underline=0, command=About)
	help_btn['menu'] = help_btn.menu
	return help_btn

def main():
	global root, common_var, level_var, build_var, varc, vard, vart
	root = Tkinter.Tk()
	root.title(tabs['Common']['Title'])

	#-- Create the menu frame, and add menus to the menu frame
	frame["Menu"] = Tkinter.Frame(root)
	frame["Menu"].pack(fill=Tkinter.X, side=Tkinter.TOP)
	frame["Menu"].tk_menuBar(file_menu(), help_menu())

	#-- Create the info frame and fill with initial contents
	frame["Info"] = Tkinter.Frame(root)
	frame["Info"].pack(fill=Tkinter.X, side=Tkinter.TOP, pady=1)

	#-- Tabs frame
	frame["Main"] = conf_tab(frame["Info"], LEFT)

	#-- Common frame
	frame["Common"] = Tkinter.Frame(frame["Main"]())
	Label(frame["Common"], text=tabs['Common']['Title'], width=25, background="green").grid(row=0, column=0)
	Label(frame["Common"], text="", width=35, background="green").grid(row=0, column=1)
	Label(frame["Common"], text="Программа предназначенная для началь-", width=35).grid(row=1, column=1)
	Label(frame["Common"], text="ной инициализации и тестирования ап-", width=35).grid(row=2, column=1)
	Label(frame["Common"], text="паратуры. А так же для ее отладки. А", width=35).grid(row=3, column=1)
	Label(frame["Common"], text="так же для отладки системного кода для", width=35).grid(row=4, column=1)
	Label(frame["Common"], text=" дальнейшего переноса кода в Линукс ", width=35).grid(row=5, column=1)
	#-- Arch subframe
	common_var["Arch_num"] = IntVar()
	Label(frame["Common"], text="Arch", width=25, background="lightblue").grid(row=1, column=0)
	for ar, value, mdef in tabs['Common']['Arch']:
		Radiobutton(frame["Common"], text=ar, value=value, variable=common_var["Arch_num"], anchor=W).grid(row=value+2, column=0, sticky=W)
	common_var["Arch_num"].set(tabs["Common"]["Arch_num"])
	#-- Compiler, Ldflags, Cflags, Target subframes
	k = 0
	for item in [ "Compiler", "Ldflags", "Cflags", "Target" ]:
		Label(frame["Common"], text=item, width=25, background="lightblue").grid(row=5 + k, column=0)
		common_var[item] = StringVar()
		Entry(frame["Common"], width=25, textvariable=common_var[item]).grid(row=6 + k, column=0)
		common_var[item].set(tabs["Common"][item])
		k += 2

	#-- Drivers frame
	frame[menu[1]] = Tkinter.Frame(frame["Main"]())
	Label(frame[menu[1]], text=menu[1], width=25, background="lightblue").grid(row=0, column=0)
	Label(frame[menu[1]], text="Description", width=55, background="lightblue").grid(row=0, column=1)
	vard = IntVar()
	row = 1
	for item in tabs[menu[1]].keys():
		if item != "common":
			Label(frame[menu[1]], text=item, width=25, background="lightblue").grid(row=row, column=0)
			row +=1
		tmp = 1
		for driver, inc, status, desc, mdef in tabs[menu[1]][item]:
			setattr(vard, driver, IntVar())
			Checkbutton(frame[menu[1]], text=driver, state=getStatus(status), anchor=W, variable = getattr(vard, driver), \
			    	    command=(lambda tmp=tmp, item=item: onPress_dep(item, tmp-1, 1))).grid(row=row, column=0, sticky=W)
			getattr(vard, driver).set(inc)
			Label(frame[menu[1]], text=desc, state=getStatus(status), width=55, anchor=W).grid(row=row, column=1, sticky=W)
			row += 1
			tmp += 1
		if item != "common":
			Label(frame[menu[1]], text="---------------------------------------", width=25).grid(row=row, column=0)
			row += 1

	#-- Tests frame
	frame[menu[2]] = Tkinter.Frame(frame["Main"]())
	Label(frame[menu[2]], text=menu[2], width=25, background="lightblue").grid(row=0, column=0)
	Label(frame[menu[2]], text="Description", width=35, background="lightblue").grid(row=0, column=1)
	vart = IntVar()
	row = 1
	for test_name, inc, status, desc, mdef in tabs[menu[2]]:
		setattr(vart, test_name, IntVar())
		Checkbutton(frame[menu[2]], text=test_name, state=getStatus(status), anchor=W, variable = getattr(vart, test_name), \
			    command=(lambda row=row: onPress(tabs[menu[2]], row-1, 1))).grid(row=row, column=0, sticky=W)
		getattr(vart, test_name).set(inc)
		Label(frame[menu[2]], text=desc, state=getStatus(status), width=35, anchor=W).grid(row=row, column=1, sticky=W)
		row += 1

	#-- Commands frame
	frame[menu[3]] = Tkinter.Frame(frame["Main"]())
	Label(frame[menu[3]], text=menu[3], width=25, background="lightblue").grid(row=0, column=0)
        Label(frame[menu[3]], text="Description", width=35, background="lightblue").grid(row=0, column=1)
        varc = IntVar()
	row = 1
	for cmd, inc, status, desc, mdef in tabs[menu[3]]:
		setattr(varc, cmd, IntVar())
    		Checkbutton(frame[menu[3]], text=cmd, state=getStatus(status), anchor=W, variable = getattr(varc, cmd), \
    			    command=(lambda row=row: onPress(tabs[menu[3]], row-1, 2))).grid(row=row, column=0, sticky=W)
		getattr(varc, cmd).set(inc)
		Label(frame[menu[3]], text=desc, state=getStatus(status), width=35, anchor=W).grid(row=row, column=1, sticky=W)
		row += 1

	#-- Level frame
	frame[menu[4]] = Tkinter.Frame(frame["Main"]())
	Label(frame[menu[4]], text="Verbous level", width=25, background="lightblue").grid(row=0, column=0)
	Label(frame[menu[4]], text="", width=35).grid(row=0, column=1)
	for i in range( len(tabs[menu[4]].keys()) ):
		name = str(tabs[menu[4]].keys()[i])
		level_var[name] = IntVar()
		Checkbutton(frame[menu[4]], text=tabs[menu[4]].keys()[i], state=NORMAL, anchor=W, \
			    variable = level_var[name]).grid(row=i+1, column=0, sticky=W)
		level_var[name].set(tabs[menu[4]][name])

	#-- Build frame
	frame[menu[5]] = Tkinter.Frame(frame["Main"]())
	Label(frame[menu[5]], text=menu[5], width=25, background="lightblue").grid(row=0, column=0)
	Label(frame[menu[5]], text="", width=35).grid(row=0, column=1)
	for i in range( len(tabs[menu[5]].keys()) ):
		name = str(tabs[menu[5]].keys()[i])
		build_var[name] = IntVar()
		Checkbutton(frame[menu[5]], text=tabs[menu[5]].keys()[i], state=NORMAL, anchor=W, \
			    variable = build_var[name]).grid(row=i+1, column=0, sticky=W)
		build_var[name].set(tabs[menu[5]][name])

	#-- build tabs
	for i in range( len(menu) ):
		frame["Main"].add_screen(frame[str(menu[i])], str(menu[i]))

	root.mainloop()

if __name__=='__main__':
	try:
		if os.path.exists(".config"):
			read_config(".config")
		else:
			read_config(".config.default")
			shutil.copyfile(".config.default", ".config")
		shutil.copyfile(".config", ".config.old")
    		main()
	except:
    		traceback.print_exc()
