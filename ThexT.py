#!/usr/bin/python
# -*- coding: UTF-8 -*-
#----------------------------------------------------------------------------------------------
#         Name:   ThexT.py
#         Author:  Wicker25
#         Version: 0.1
#         License: GPL
#         Description: Hex Editor for Gnome
#------------------------------------------------------------------------------------------------

import sys
import time
import gtk
import gtk.glade
import gobject
import pango
import string, re
import binascii
import webbrowser
from os import path, getcwd
import thread
import threading


global GlobalPath
GlobalPath = getcwd()

if path.dirname(sys.argv[0]) != "":
    GlobalPath = path.dirname(sys.argv[0])

sys.path.append(GlobalPath)

gtk.gdk.threads_init()


#Processo per leggere ed analizzare i file--------------------------------------

class ReadFile(threading.Thread):

    def __init__(self, Path):

         #Carica la funzione principale della classe Thread
         threading.Thread.__init__(self)

         #Imposta alcuni valori
         self.CurrentThread = threading.Event()
         self.Path = Path

    def run(self):

            #Funzione per caricare il file o aggiornare la modalità d'evidenziazione

            Appl.HexList.clear()
            Reader = open(self.Path, "rb")
            Appl.BufferBytes = Reader.read()
            Appl.BufferBytes = binascii.b2a_hex(Appl.BufferBytes)
            Reader.close()
            Appl.SAVE_PATH = self.Path

            Appl.SYNTAX_ERROR = []

            gtk.gdk.threads_enter()

            Appl.CDialog = gtk.MessageDialog(Appl.Window, gtk.DIALOG_MODAL, gtk.MESSAGE_INFO, gtk.BUTTONS_OK, "Caricamento in corso.. \n\nAttenzione: Operazione Delicata!!!\nInvitiamo l'utente ad attendere la fine del caricamento prima di iniziare nuove operazioni.")
            Appl.CDialog.show()

            while gtk.events_pending(): pass

            Buffer1 = ""
            Buffer2 = ""

            for t in range(0, len(Appl.BufferBytes)/2):

                Byte = Appl.BufferBytes[t*2:(t+1)*2]

                Buffer1 += Byte+" "

                Buffer2 += unicode(Appl.DeleteReturn(str(binascii.a2b_hex(Byte))))

                if not (t+1) % 16:

                    Appl.HexList.append([string.zfill(hex(t)[2:], 8), Buffer1, Buffer2])

                    Buffer1 = ""
                    Buffer2 = ""

            if Buffer1 != "":

                Buffer1 += "00 "*(16-len(Buffer1))
                Appl.HexList.append([string.zfill(hex(t)[2:], 8), Buffer1, Buffer2])


            Appl.CDialog.destroy()

            gtk.gdk.threads_leave()

            self.stop()

    def stop(self):

            self.CurrentThread.set()


#Processo per scrivere i files eseguibili--------------------------------------


class WriteFile(threading.Thread):

    def __init__(self, Path):

         #Carica la funzione principale della classe Thread
         threading.Thread.__init__(self)

         #Imposta alcuni valori
         self.CurrentThread = threading.Event()
         self.Path = Path

    def run(self):

        #Funzione per salvare il file eseguibile

        Appl.BufferBytes = ""

        ERROR = 0

        try:

            iter = Appl.HexList.get_iter_first ()

            while iter:

                value = Appl.HexList.get_value (iter, 1)
                Appl.BufferBytes += value
	        iter = Appl.HexList.iter_next(iter)

            Appl.BufferBytes = binascii.a2b_hex(Appl.BufferBytes.replace("\n", "").replace(" ", ""))

        except:

            #In caso di un errore

            gtk.gdk.threads_enter()

            EDialog = gtk.MessageDialog(Appl.Window, gtk.DIALOG_MODAL, gtk.MESSAGE_ERROR, gtk.BUTTONS_OK, "Errore nel salvataggio!")
            EDialog.run()
            EDialog.destroy()

            gtk.gdk.threads_leave()

            ERROR = 1

            return

        if not ERROR:

            Writer = open(self.Path, "wb")
            Writer.write(Appl.BufferBytes)
            Writer.close()

            Appl.SAVE_PATH = self.Path

        self.stop()

    def stop(self):

        self.CurrentThread.set()


#Principale-----------------------------------------------------------------

class Application(threading.Thread):

    def __init__(self):

        #Impostazioni Generali
        self.title = "ThexT"
        self.version = "0.2"
        self.license = "GPL"
        self.description = "Hex Editor for Gnome"
        self.author = "Wicker25 - wicker25@gmail.com"
        self.site = "http://wicker25.netsons.org/"
        self.icon = gtk.gdk.pixbuf_new_from_file(path.join(GlobalPath, "icon.ico"))
        self.SAVE_PATH = ""
        self.FONT = "Courier New 10"
        self.SPECIAL_COLOR = { "90" : "blue-white", "00" : "red-white", "SyntaxError" : "white-red" }
        self.SYNTAX_ERROR = []

        #Link al mio sito XD
        gtk.about_dialog_set_url_hook(lambda x,y,z: thread.start_new_thread(webbrowser.open,(self.site,)), None)

        #Carica i widgets
        self.Widgets = gtk.glade.XML(path.join(GlobalPath, "gui.glade"),"window1")
        self.Widgets.signal_autoconnect(Application.__dict__)

        #I vari wigets
        self.Window = self.Widgets.get_widget("window1")
        self.Window.set_icon(self.icon)
        self.TreeView = self.Widgets.get_widget("treeview1")
        self.HexList = gtk.ListStore(gobject.TYPE_STRING, gobject.TYPE_STRING, gobject.TYPE_STRING)
        self.TreeView.__init__(self.HexList)

        #Caselle di Testo
        self.ListEntry = []
        for t in range(0, 16):
            self.ListEntry += [self.Widgets.get_widget("entry"+str(t+1))]
            self.ListEntry[t].connect("changed", lambda x: self.on_entry_changed())
        self.ListEntry.append(self.Widgets.get_widget("entry17"))
        self.ListEntry.append(self.Widgets.get_widget("entry18"))

        #Render
        self.Renderer = gtk.CellRendererText()
        self.Renderer.set_property("font", self.FONT)

        #Colonna degli indirizzi
        self.Column = gtk.TreeViewColumn('Indirizzo', self.Renderer, text=0)
        self.TreeView.append_column(self.Column)

        #Colonna del formato esadecimale
        self.Column = gtk.TreeViewColumn('Formato Esadecimale', self.Renderer, text=1)
        self.TreeView.append_column(self.Column)

        #Colonna del formato UNICODE
        self.Column = gtk.TreeViewColumn('Formato Stringa', self.Renderer, text=2)
        self.TreeView.append_column(self.Column)


#-----------------------------------AZIONI DAL MENU'-----------------------------------

    def on_window1_destroy_event(widget, event):

        #Esce dal ciclo principale nel caso sia chiusa la finestra
        gtk.main_quit()

    def on_treeview1_cursor_changed(event):

        try:

            iter = Appl.HexList.get_iter (path = Appl.TreeView.get_cursor()[0][0])
            Hex = Appl.HexList.get_value(iter, 1).split(" ")
            Hex.remove("")
            Hex += ["00"]*(16-len(Hex))
            Ascii = Appl.HexList.get_value(iter, 2)
            Indirizzo = Appl.HexList.get_value(iter, 0)

            for t in range(0, 16):
                Appl.ListEntry[t].set_text(Hex[t])

            Appl.ListEntry[16].set_text(Ascii)
            Appl.ListEntry[17].set_text(Indirizzo)

        except: pass

    def on_entry_changed(self):

        try:

            iter = Appl.HexList.get_iter (path = Appl.TreeView.get_cursor()[0][0])
            new_value = ""
            new_value_ascii = ""

            for t in range(0, 16):

                code = Appl.ListEntry[t].get_text().replace(" ","0")
                code += "0"*(2-len(code))

                Validator =  re.compile('['+string.hexdigits+']+')

                if Validator.match(code[0]) != None and Validator.match(code[1]) != None:

                    new_value += code+" "
                    new_value_ascii += unicode(Appl.DeleteReturn(str(binascii.a2b_hex(code))))

                else:

                    new_value += "00"+" "
                    new_value_ascii += " "

            Appl.ListEntry[16].set_text(new_value_ascii)

            Appl.HexList.set_value(iter, 1, new_value)
            Appl.HexList.set_value(iter, 2, new_value_ascii)

        except: pass

    def on_esci1_activate(event):

        #Esce dal programma
        gtk.main_quit()

    def on_nuovo1_activate(event):

        #Nuovo file

        Appl.SAVE_PATH = ""
        Appl.HexList.clear()

    def on_salva1_activate(event):

        #Funzione per selezionare il file su cui salvare

        if len(Appl.SYNTAX_ERROR) > 0:

            EDialog = gtk.MessageDialog(Appl.Window, gtk.DIALOG_MODAL, gtk.MESSAGE_ERROR, gtk.BUTTONS_OK, "Errore nella sintassi!")
            EDialog.run()
            EDialog.destroy()
            return

        if Appl.SAVE_PATH == "":

            Appl.on_salva_come1_activate()

        else:

            Appl.IniWriteFile(Appl.SAVE_PATH)

    def on_salva_come1_activate(event):

        #Funzione per selezionare il file su cui salvare

        if len(Appl.SYNTAX_ERROR) > 0:

            EDialog = gtk.MessageDialog(Appl.Window, gtk.DIALOG_MODAL, gtk.MESSAGE_ERROR, gtk.BUTTONS_OK, "Errore nella sintassi!")
            EDialog.run()
            EDialog.destroy()
            return

        DialogFile = gtk.FileChooserDialog("Salva File", Appl.Window, gtk.FILE_CHOOSER_ACTION_SAVE,  (gtk.STOCK_CANCEL,gtk.RESPONSE_CANCEL,gtk.STOCK_SAVE,gtk.RESPONSE_OK))


        Resp = DialogFile.run()

        if Resp == gtk.RESPONSE_OK:

            Appl.IniWriteFile(DialogFile.get_filename())
            DialogFile.destroy()
            return

        else:

            DialogFile.destroy()

    def on_apri1_activate(event):

        #Funzione per aprire un nuovo file

        DialogFile = gtk.FileChooserDialog("Apri File", Appl.Window, gtk.FILE_CHOOSER_ACTION_OPEN,  (gtk.STOCK_CANCEL,gtk.RESPONSE_CANCEL,gtk.STOCK_OPEN,gtk.RESPONSE_OK))

        Resp = DialogFile.run()

        if Resp == gtk.RESPONSE_OK:

            Appl.VerifySelectionFile(DialogFile, DialogFile.get_filename())
            return

        else:

            DialogFile.destroy()

    def on_informazioni1_activate(event):

        #Richiama la finestra delle info
        Appl.About()


#-------------------------------------FUNZIONI INTERNE--------------------------------------


    def VerifySelectionFile(self, DialogFile, Path):

        #Verifica se il file esiste

        if path.isfile(Path):

            DialogFile.destroy()
            self.SAVE_PATH = Path

            Appl.IniReadFile(Path)
        else:
            EDialog = gtk.MessageDialog(DialogFile, gtk.DIALOG_MODAL, gtk.MESSAGE_ERROR, gtk.BUTTONS_OK, "Percorso file non valido!")
            EDialog.run()
            EDialog.destroy()

        DialogFile.destroy()

    def IniReadFile(self, Path):

        #Avvia come un nuovo Thread la funzione ReadFile()

        while gtk.events_pending():
            gtk.main_iteration_do()

        Reader = ReadFile(Path)
        Reader.start()

    def IniWriteFile(self, Path):


        #Avvia come un nuovo Thread la funzione ReadFile()

        Writer = WriteFile(Path)
        Writer.start()

    def DeleteReturn(self, string):

        #Rimuove i caratteri non stampabili

        string = ord(string)

        if string < 33: string = 32
        if string > 125: string = 32

        return chr(string)

    def About(self):

        #Finestra delle info

        DlgInfo = gtk.AboutDialog()
        DlgInfo.set_logo(self.icon)
        DlgInfo.set_name(self.title)
        DlgInfo.set_version(self.version)
        DlgInfo.set_comments(self.description)
        DlgInfo.set_license(self.license)
        DlgInfo.set_authors([self.author])
        DlgInfo.set_website(self.site)
        DlgInfo.show_all()
        def close(w, res):
             if res == gtk.RESPONSE_CANCEL:
                     w.hide()
        DlgInfo.connect("response", close)


global Appl
Appl = Application()

gtk.main()


