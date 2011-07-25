#!/usr/bin/python

# sshlist v0.2

import gtk
import appindicator
import os
import pynotify

class sshList:
    ver = "0.2"
    list_path = os.getenv("HOME")+"/.sshlist"


    def __init__(self):
        self.checkFile()
        self.buildIndicator()
        self.refreshMenu()
        gtk.main()


    def checkFile(self):
        if not os.path.exists(self.list_path):
            open(self.list_path, 'w').close()


    def buildIndicator(self):
        self.ind = appindicator.Indicator("sshlist",
            "gnome-netstatus-tx",
            appindicator.CATEGORY_APPLICATION_STATUS)
        self.ind.set_label("SSH")
        self.ind.set_status(appindicator.STATUS_ACTIVE)
        self.ind.set_attention_icon("connect_creating")


    def runProgram(self, command):
        cmd = "gnome-terminal -x ssh " + command
        #returns (output, exit value)
        fd=os.popen(cmd, "r")
        output=fd.read()
        exitvalue=fd.close()
        return (output, exitvalue)


    def menuitemResponse(self, widget, command):
        if command == "_about":
            md = gtk.MessageDialog(None, 0, gtk.MESSAGE_INFO,
            gtk.BUTTONS_OK)
            md.set_markup("<b>sshlist v%s</b>" % self.ver)
            md.format_secondary_markup("""A simple sshmenu like replacement for appindicator menu.

            To add items to menu, simple edit the file <i>.sshlist</i> in your home directory (one host per line). The line is directly appended to the ssh command.

            Author: anil.verve@gmail.com
            http://www.gulecha.org
            Updated: phoolish@gmail.com
            """)
            md.run()
            md.destroy()
        elif command == "_settings":
            self.settingsDialogue()
        else:
            self.runProgram(command)


    def settingsDialogue(self):
        settings = gtk.Window(gtk.WINDOW_TOPLEVEL)
        settings.set_title("Settings")
        settings.set_position(gtk.WIN_POS_CENTER)
        settings.set_border_width(5)

        add_ssh = gtk.Button("Add")
        add_ssh.connect_object("clicked", self.addHost, settings)
        save_ssh = gtk.Button("Save")
        save_ssh.connect_object("clicked", self.saveList, settings)
        delete_ssh = gtk.Button("Delete")
        delete_ssh.connect_object("clicked", self.deleteHost, settings)
        close_ssh = gtk.Button("Close")
        close_ssh.connect_object("clicked", gtk.Widget.destroy, settings)

        table = gtk.Table(1, 1, False)

        tree_store = gtk.TreeStore(str, str)

        # read in the ssh hosts list from ~/.sshlist
        hosts = open(self.list_path, "r").read()
        hostlist = hosts.split("\n")

        # create some
        newIter = None
        tempIter = None
        for hostinfo in hostlist:
            # if hostinfo is not a comment
            if not hostinfo.startswith("#") and hostinfo != "":
                hostparts = hostinfo.split(":::")
                title = hostinfo
                command = hostinfo
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
        host_cell.connect('edited', self.hostEdit, (tree_store, 0))
        host_tree_view_column.pack_start(host_cell, True)
        host_tree_view_column.add_attribute(host_cell, 'text', 0)

        command_tree_view_column = gtk.TreeViewColumn('Command')

        self.tree_view.append_column(command_tree_view_column)
        command_cell = gtk.CellRendererText()
        command_cell.set_property('editable', True)
        command_cell.connect('edited', self.hostEdit, (tree_store, 1))
        command_tree_view_column.pack_start(command_cell, True)
        command_tree_view_column.add_attribute(command_cell, 'text', 1)
        table.attach(self.tree_view, 0, 1, 0, 3)
        table.attach(add_ssh, 1, 2, 0, 1)
        table.attach(save_ssh, 1, 2, 1, 2)
        table.attach(delete_ssh, 1, 2, 2, 3)
        table.attach(close_ssh, 1, 2, 3, 4)

        settings.add(table)

        settings.show_all()


    def addHost(self, widget, data = None):
        tree_model = self.tree_view.get_model()
        newIter = tree_model.append(None, ['', ''])
        self.selection.select_iter(newIter)

    def deleteHost(self, widget, data = None):
        dialog = gtk.MessageDialog(
            message_format='Are you sure to delete this?',
            buttons=gtk.BUTTONS_OK_CANCEL)
        response = dialog.run()
        if response == gtk.RESPONSE_OK:
            tree_model, tree_iter = self.selection.get_selected()
            tree_model.remove(tree_iter)
            self.saveList()
        dialog.destroy()

    def saveList(self, widget = None):
            # Overwrite sshlist file
            ssh_file = open(self.list_path, "w")
            ssh_file.write("# Add ssh host info or add a title:::host info")
            ssh_file.write("# Examples\n")
            ssh_file.write("# user@host.com\n")
            ssh_file.write("# title:::user@host.com\n")

            tree_model = self.tree_view.get_model()
            for hostIter in tree_model:
                name, command = hostIter
                ssh_file.write(name + ":::" + command + "\n")

            ssh_file.close()
            self.refreshMenu()
            pynotify.Notification("Updated sshlist", "Menu list was refreshed from ~/.sshlist").show()

    def hostEdit(self, cell, path, new_text, user_data):
            liststore, column = user_data
            liststore[path][column] = new_text
            return

    #delete line
    def refreshMenu(self):
            self.buildMenu()
            self.ind.set_menu(self.menu)

    def buildMenu(self):
        # create a menu
        self.menu = gtk.Menu()

        # read in the ssh hosts list from ~/.sshlist
        hosts = open(self.list_path, "r").read()
        hostlist = hosts.split("\n")

        # create some
        for hostinfo in hostlist:
            # if it isn't a comment create a menu item
            if not hostinfo.startswith("#") and hostinfo != "":
                hostparts = hostinfo.split(":::")
                title = hostinfo
                command = hostinfo
                if len(hostparts) > 1:
                    #second is ssh command
                    command = hostparts.pop()
                    #first section is title
                    title = hostparts.pop()
                menu_items = gtk.MenuItem(title)
                self.menu.append(menu_items)
                # this is where you would connect your menu item up with a function:
                menu_items.connect("activate", self.menuitemResponse, command)
                # show the items
                menu_items.show()

        separator = gtk.SeparatorMenuItem()
        separator.show()
        self.menu.append(separator)

        menu_items = gtk.MenuItem("Settings")
        menu_items.connect("activate", self.menuitemResponse, "_settings")
        menu_items.show()
        self.menu.append(menu_items)

        menu_items = gtk.MenuItem("About")
        menu_items.connect("activate", self.menuitemResponse, "_about")
        menu_items.show()
        self.menu.append(menu_items)


if __name__ == "__main__":
    sshList()
