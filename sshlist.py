#!/usr/bin/python

# sshlist v0.2

import gtk
import appindicator
import os
from subprocess import Popen, PIPE
import pynotify
import logging
import configParser

logging.basicConfig(level=logging.DEBUG)

# TODO
# - Change all the spacing, variable and function names to conform to PEP8
# - Finish the run_program (soon to be renamed run_program) method's new 
# implementation, using the subprocess.Popen class, instead of the old
# os.popen
# - Review the rest of the code
# - Use python's configParser module to store the settings
# - add logging

class SSHList:
    version = "0.2"
    listPath = os.path.join(os.getenv("HOME"), ".sshlist")

    def __init__(self):
        self.check_file()
        self.build_indicator()
        self.refresh_menu()
        gtk.main()

    def check_file(self):
        if not os.path.exists(self.listPath):
            open(self.listPath, 'w').close()

    def build_indicator(self):
        self.indicator = appindicator.Indicator("sshlist",
            "gnome-netstatus-tx",
            appindicator.CATEGORY_APPLICATION_STATUS)
        self.indicator.set_label("SSH")
        self.indicator.set_status(appindicator.STATUS_ACTIVE)
        self.indicator.set_attention_icon("connect_creating")

    #def run_program(self, command):
    #    cmd = "gnome-terminal -x ssh " + command
    #    #returns (output, exit value)
    #    fd=os.popen(cmd, "r")
    #    output=fd.read()
    #    exitvalue=fd.close()
    #    return (output, exitvalue)

    def run_program(self, sshHost, sshUser, sshPassword=None, 
                    program='gnome-terminal', progOptions='-x', 
                    sshCommand='ssh', sshOptions='-Y', otherOptions=''):
        sshLogin = '@'.join(sshUser, sshHost)
        otherOpts = otherOptions.split()
        cmdList = [program, progOptions, sshCommand, sshOptions, sshLogin] + \
                  otherOpts
        newProcess = Popen(cmdList, stdin=PIPE, stdout=PIPE, stderr=PIPE)
        stdout, stderr = newProcess.communicate()
        returnCode = newProcess.returncode
        return stdout, returnCode

    def menu_item_response(self, widget, command):
        if command == "_about":
            md = gtk.MessageDialog(None, 0, gtk.MESSAGE_INFO,
            gtk.BUTTONS_OK)
            md.set_markup("<b>sshlist v%s</b>" % self.version)
            md.format_secondary_markup(
            """
            A simple sshmenu like replacement for appindicator menu.
            Author: anil.verve@gmail.com
            http://www.gulecha.org
            Updated: phoolish@gmail.com

            # Instructions

            1. Copy file sshlist.py to /usr/local/bin
            2. Launch sshlist.py
            3. Or better yet, add it to gnome startup programs list so it's run on login.
            """)
            md.run()
            md.destroy()
        elif command == "_settings":
            self.settings_dialogue()
        else:
            self.run_program(command)


    def settings_dialogue(self):
        settings = gtk.Window(gtk.WINDOW_TOPLEVEL)
        settings.set_title("Settings")
        settings.set_position(gtk.WIN_POS_CENTER)
        settings.set_border_width(5)

        add_ssh = gtk.Button("Add")
        add_ssh.connect_object("clicked", self.add_host, settings)
        save_ssh = gtk.Button("Save")
        save_ssh.connect_object("clicked", self.save_list, settings)
        delete_ssh = gtk.Button("Delete")
        delete_ssh.connect_object("clicked", self.delete_host, settings)
        close_ssh = gtk.Button("Close")
        close_ssh.connect_object("clicked", gtk.Widget.destroy, settings)

        table = gtk.Table(1, 1, False)

        tree_store = gtk.TreeStore(str, str)

        # read in the ssh hosts list from ~/.sshlist
        hosts = open(self.listPath, "r").read()
        hostlist = hosts.split("\n")

        # create some
        newIter = None
        tempIter = None
        for hostInfo in hostlist:
            # if hostInfo is not a comment
            if not hostInfo.startswith("#") and hostInfo != "":
                hostparts = hostInfo.split(":::")
                title = hostInfo
                command = hostInfo
                if len(hostparts) > 1:
                    #second is ssh command
                    command = hostparts.pop()
                    #first section is title
                    title = hostparts.pop()
                tempIter = tree_store.append(None, [title, command, ])
            if newIter == None and tempIter != None:
                newIter = tempIter

        self.tree_view = gtk.TreeView(tree_store)

        self.selection = self.tree_view.get_selection()
        self.selection.set_mode(gtk.SELECTION_SINGLE)
        if newIter:
            self.selection.select_iter(newIter)

        host_tree_view_column = gtk.TreeViewColumn('Title')

        self.tree_view.append_column(host_tree_view_column)

        host_cell = gtk.CellRendererText()
        host_cell.set_property('editable', True)
        host_cell.connect('edited', self.host_edit, (tree_store, 0))
        host_tree_view_column.pack_start(host_cell, True)
        host_tree_view_column.add_attribute(host_cell, 'text', 0)

        command_tree_view_column = gtk.TreeViewColumn('Command')

        self.tree_view.append_column(command_tree_view_column)
        command_cell = gtk.CellRendererText()
        command_cell.set_property('editable', True)
        command_cell.connect('edited', self.host_edit, (tree_store, 1))
        command_tree_view_column.pack_start(command_cell, True)
        command_tree_view_column.add_attribute(command_cell, 'text', 1)
        table.attach(self.tree_view, 0, 1, 0, 3)
        table.attach(add_ssh, 1, 2, 0, 1)
        table.attach(save_ssh, 1, 2, 1, 2)
        table.attach(delete_ssh, 1, 2, 2, 3)
        table.attach(close_ssh, 1, 2, 3, 4)

        settings.add(table)

        settings.show_all()


    def add_host(self, widget, data = None):
        treeModel = self.tree_view.get_model()
        newIter = treeModel.append(None, ['', ''])
        self.selection.select_iter(newIter)

    def delete_host(self, widget, data = None):
        dialog = gtk.MessageDialog(
            message_format='Are you sure to delete this?',
            buttons=gtk.BUTTONS_OK_CANCEL)
        response = dialog.run()
        if response == gtk.RESPONSE_OK:
            treeModel, treeIter = self.selection.get_selected()
            treeModel.remove(treeIter)
            self.save_list()
        dialog.destroy()

    def save_list(self, widget = None):
            # Overwrite sshlist file
            sshFile = open(self.listPath, "w")
            sshFile.write("# Add ssh host info or add a title:::host info")
            sshFile.write("# Examples\n")
            sshFile.write("# user@host.com\n")
            sshFile.write("# title:::user@host.com\n")

            treeModel = self.tree_view.get_model()
            for hostIter in treeModel:
                name, command = hostIter
                sshFile.write(name + ":::" + command + "\n")

            sshFile.close()
            self.refresh_menu()
            pynotify.Notification("Updated sshlist", "Menu list was refreshed from ~/.sshlist").show()

    def host_edit(self, cell, path, new_text, user_data):
            listStore, column = user_data
            listStore[path][column] = new_text
            return

    #delete line
    def refresh_menu(self):
            self.build_menu()
            self.indicator.set_menu(self.menu)

    def build_menu(self):
        # create a menu
        self.menu = gtk.Menu()

        # read in the ssh hosts list from ~/.sshlist
        hosts = open(self.listPath, "r").read()
        hostlist = hosts.split("\n")

        # create some
        for hostInfo in hostlist:
            # if it isn't a comment create a menu item
            if not hostInfo.startswith("#") and hostInfo != "":
                #hostparts = hostInfo.split(":::")
                title, command = hostInfo.split(':::')
                #title = hostInfo
                #command = hostInfo
                if len(hostparts) > 1:
                    #second is ssh command
                    command = hostparts.pop()
                    #first section is title
                    title = hostparts.pop()
                menuItems = gtk.MenuItem(title)
                self.menu.append(menuItems)
                # this is where you would connect your menu item up with a function:
                menuItems.connect("activate", self.menu_item_response, command)
                # show the items
                menuItems.show()

        separator = gtk.SeparatorMenuItem()
        separator.show()
        self.menu.append(separator)

        menuItems = gtk.MenuItem("Settings")
        menuItems.connect("activate", self.menu_item_response, "_settings")
        menuItems.show()
        self.menu.append(menuItems)

        menuItems = gtk.MenuItem("About")
        menuItems.connect("activate", self.menu_item_response, "_about")
        menuItems.show()
        self.menu.append(menuItems)

        quit_item = gtk.MenuItem("Quit")
        quit_item.connect("activate", gtk.main_quit, None)
        quit_item.show()
        self.menu.append(quit_item)

if __name__ == "__main__":
    sshList()
