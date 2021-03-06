#!/usr/bin/python

#
# FileSequenceWidget, FilesequenceDialog.
# charles vidal charles.vidal@gmail.com 
# 
from PySide import QtCore, QtGui
import os
import random
import re
import imp
import sys
import pyseq as seq  


"""
  Bookmark Manager 
"""
class BookmarkMamanger():

    _instance = None
    
    def __init__(self):
        self.qsettings = QtCore.QSettings("filesequencebrowser", "bookmarks")
    
    def __new__(class_, *args, **kwargs):
        if not isinstance(BookmarkMamanger._instance, BookmarkMamanger):
            BookmarkMamanger._instance = BookmarkMamanger.__new__(class_, *args, **kwargs)
        return BookmarkMamanger._instance
    

    def getBookmarks(self):
        result = []
        for k in self.qsettings.allKeys():
            result.append(  self.qsettings.value( k ) )

        return result

 

    def addBookmark( self , filepath):
        self.qsettings.setValue(str(random.randint(1, 10000)) ,filepath)
         
        

    def deleteBookmark( self, filepath):
        for k in self.qsettings.allKeys():
            if filepath == self.qsettings.value( k ):
                self.qsettings.remove(k)
                return        
         

    @staticmethod
    def getAllBookmarks():
        b = BookmarkMamanger()
        return b.getBookmarks()

    @staticmethod
    def getBookmarkManager():
        return BookmarkMamanger()

"""
 Dialog to manage th bookmark setting.
"""
class dialogBookmark(QtGui.QDialog):
    
    def __init__(self):
        super(dialogBookmark, self).__init__()
        self.initUI()
        
    def initUI(self):      

        layout = QtGui.QVBoxLayout()

        self.deletebtn = QtGui.QPushButton('Delete', self)
 
        self.le = QtGui.QListWidget(self)

        
        layout.addWidget(self.le)
        layout.addWidget(self.deletebtn)
         
        self._buttonBox = QtGui.QDialogButtonBox(QtGui.QDialogButtonBox.Ok)

        self.deletebtn.clicked.connect(self.deleteBookmark)

        self._buttonBox.accepted.connect(self.accept)
        self._buttonBox.rejected.connect(self.reject)
        
        layout.addWidget(self._buttonBox)

        self.refreshListBookmark()
        # Set dialog layout
        self.setLayout(layout)

        self.setWindowTitle('Manage your bookmarks')
        self.exec_()

    def refreshListBookmark(self):
        self.le.clear()
        for v in BookmarkMamanger.getAllBookmarks():
            self.le.addItem(v)
       

    def deleteBookmark(self):
        BookmarkMamanger.getBookmarkManager().deleteBookmark( self.le.currentIndex().data() )        
        self.refreshListBookmark()

"""
  LineEdit to prevent the key return close the dialog , used to enter the path ...
"""
class LineEditWidget(QtGui.QLineEdit):

    def keyPressEvent(self, e):
        if ( e.key() == QtCore.Qt.Key_Return or 
           e.key() == QtCore.Qt.Key_Enter ) :
            return

        return QtGui.QLineEdit.keyPressEvent(self, e)


""""
  ListWidget to catch event Enter or arrow right , or backspace and arrow left.
"""
class ListWidget(QtGui.QListWidget):

    itemSelected = QtCore.Signal()
    gotoparent = QtCore.Signal()
    _actioncontentmenu = []
	
    def keyPressEvent(self, e):
        if ( e.key() == QtCore.Qt.Key_Return or 
           e.key() == QtCore.Qt.Key_Enter  or		
           e.key() == QtCore.Qt.Key_Right) : 
            self.itemSelected.emit()
            return
				
        if ( e.key() == QtCore.Qt.Key_Backspace or 
            e.key() == QtCore.Qt.Key_Left) :
                self.gotoparent.emit()
                return 
			
        return QtGui.QListWidget.keyPressEvent(self, e)

    """
      #param contextMenu : array of dictionnaire action Action, plugin Plugin 
    """
    def setContextMenuAction( self , contextMenu):
        self._actioncontentmenu = contextMenu

    def isSelectedSequence(self ):
        if len( self.currentIndex().data().split("[") ) > 1:
            return True
        else:
            return False

    def getExtension( self ):
        filename, file_extension = os.path.splitext(self.currentIndex().data())
        return file_extension


    #
    # crete menu form _actioncontentmenu 
    # 
    def contextMenuEvent(self, event):
        menu = QtGui.QMenu(self)
        #print self._actioncontentmenu
        for m in  self._actioncontentmenu:
            if type( m ) == QtGui.QAction:
                menu.addAction(m)
            else:
                plugin = m["plugin"]
                #
                # test with dict for the plugin objet
                # if toto in dict(m[[plugin]]):
                if "acceptOnlySequence" in dir( plugin) and self.isSelectedSequence()  == False:
                    continue 

                if self.isSelectedSequence()==True and plugin.acceptSequence() == False:
                    continue

                menu.addAction(m["action"])

        menu.exec_(event.globalPos())



"""
  generic widget FileSequenceWidget
  display two list :
      one with directory 
      the orther with file or sequence file.

      you can navigate with enter on folder or arrow key.

      This widget emit a signal when you select a file or a sequence file.
"""
class FileSequenceWidget(QtGui.QWidget):
		 
    FOLDER = 0
    FILE = 1 
    SEQUENCE =2 

    fileSelected = QtCore.Signal(str)
    pathChanged = QtCore.Signal(str)

    def getFilenameSelected( self ):
        itemSelected = self.listfile.currentIndex().data()
        return os.path.join( self.path , itemSelected )

    def getDirectorySelected( self ):
        dirSelected = self.directorylist.currentIndex().data()
        return os.path.join( self.path , dirSelected )


    def selectdirectory(self):
        rows =  self.directorylist.selectionModel().selectedRows()
        itemSelected = rows[0].data()
        if  os.path.isdir(os.path.join( self.path , itemSelected)) :
			self.path = os.path.normpath( os.path.join( self.path , itemSelected) ) 
			self.pathEdit.setText( self.path )
        
	
    def selectfile(self, number):
		itemSelected = self.listfile.currentIndex().data()
		self.fileSelected.emit(os.path.join( self.path , itemSelected))

    """
      method testing if the filename is in filters
      @param filename : a filename 
      @param array of filter : .jpg, .png 
      @return boolean  
    """
    def isInFilter(self, filename, filters):
        for filter in filters:
            if filename.lower().endswith(filter.lower()):
                return True
        
        return False

    """
       @return array of filter [ .jpg , .png ]
    """
    def getFilters(self):
        strfilters = self.filtercombo.currentText()
        filters = strfilters.split(";")
        return filters

    """
      add item to the list of 
           folder list if type is FOLDER 
           file in the list view  if type is FILE or SEQUENCE
    """
    def addItem(self, fn,typefile ):
    	item = QtGui.QListWidgetItem()
        item.setText(fn)
        item.setIcon(self.icons[typefile])
        if typefile == FileSequenceWidget.FOLDER:
        	self.directorylist.addItem(item)
        else: 
            extensionfilters = self.getFilters()
            if len(extensionfilters)==0: 
                self.listfile.addItem(item)
            else:
                if self.isInFilter(fn , extensionfilters):
                    self.listfile.addItem(item)
					
	"""
    Slot to go to the directory parent.
    """
    def goToParent( self ):
        self.path = os.path.normpath( os.path.join( self.path , "..") ) 
        self.pathEdit.setText( self.path )
	
    def initInternalVar(self ):
        self._splitSequence = False
        self.iconFile = QtGui.QIcon("icons\\file.png")
        self.iconFolder = QtGui.QIcon("icons\\folder.png")
        self.iconSequence = QtGui.QIcon("icons\\sequence.png")
        self.icons = {} 
        self.icons[FileSequenceWidget.FOLDER] = self.iconFolder
        self.icons[FileSequenceWidget.FILE] = self.iconFile
        self.icons[FileSequenceWidget.SEQUENCE] = self.iconSequence

    def refreshbookmarkcombo(self):
        self.bookmarkCombo.clear()
        self.bookmarkCombo.addItem("")
        for v in BookmarkMamanger.getAllBookmarks():
            self.bookmarkCombo.addItem(v)


    def __init__(self, path, parent=None):
        """
        Create gui.
        """
        super(FileSequenceWidget, self).__init__(parent)
        self.path = path
        self.listseq = {}
        self.initInternalVar()
        label = QtGui.QLabel("Directory")
        pathEdit = LineEditWidget() # QtGui.QLineEdit()
        label.setBuddy(pathEdit)
		
        addBookmark = QtGui.QPushButton("+")
        addBookmark.setMaximumWidth(15)
        addBookmark.setToolTip("Add Path as Bookmark")

        showBookmark = QtGui.QPushButton("b")
        showBookmark.setMaximumWidth(15)
        showBookmark.setToolTip("Show Bookmarks")

        self.bookmarkCombo = QtGui.QComboBox()
        self.refreshbookmarkcombo()

        
        layoutBookmark = QtGui.QHBoxLayout()
        layoutBookmark.addWidget(addBookmark)
        layoutBookmark.addWidget(showBookmark)
        layoutBookmark.addWidget(self.bookmarkCombo)

        frameBookmark = QtGui.QFrame()
        frameBookmark.setLayout(layoutBookmark)

        self.listfile = ListWidget()
        self.directorylist = ListWidget()

        self.pathEdit = pathEdit		

        splitter = QtGui.QSplitter()
        splitter.addWidget(self.directorylist)
        splitter.addWidget(self.listfile)
        
        self.checkboxsplitseq = QtGui.QCheckBox('Split Seq',self) 
        
        if self._splitSequence == True:
            self.checkboxsplitseq.setCheckState(QtCore.Qt.Checked)
        else:
            self.checkboxsplitseq.setCheckState(QtCore.Qt.Unchecked)
			
	    labelfilter = QtGui.QLabel("Filter:")
        self.filtercombo = QtGui.QComboBox()
        labelfilter.setBuddy(self.filtercombo)
		
        layout = QtGui.QGridLayout()
        layout.addWidget(label, 0, 0)
        layout.addWidget(pathEdit, 0, 1)
        layout.addWidget(frameBookmark, 0, 2 )
        layout.addWidget(splitter,1,0,1,3)
        layout.addWidget(self.checkboxsplitseq, 3, 0)
        layout.addWidget(labelfilter,3,1)
        layout.addWidget(self.filtercombo,3,2)

        #
        # Connect Slot ...
        #
        self.pathEdit.textChanged.connect(self.setCurrentDirPath)
        self.listfile.doubleClicked.connect(self.selectfile)
        self.listfile.itemSelected.connect(self.selectfile)
        self.listfile.gotoparent.connect(self.goToParent)
        self.directorylist.doubleClicked.connect(self.selectdirectory)
        self.directorylist.itemSelected.connect(self.selectdirectory)
        self.directorylist.gotoparent.connect(self.goToParent)
        addBookmark.clicked.connect(self.addBookmark)
        showBookmark.clicked.connect(self.showDialogBookmark)
        self.checkboxsplitseq.clicked.connect(self.splitseqchanged)
        self.filtercombo.currentIndexChanged.connect(self.filterchanged)
        self.bookmarkCombo.currentIndexChanged.connect(self.bookmarkchanged)
        self.setLayout(layout)
        self.setWindowTitle("File Sequence browser")
        pathEdit.setText(self.path)
    
    """
       Change directory callback..
    """
    def setCurrentDirPath(self , path ):
        if os.path.isdir( path ) == False:
            self.pathEdit.setStyleSheet("background-color:  rgb(255, 128, 128);")
            return

        self.path = path
        self.pathEdit.setStyleSheet("background-color:  rgb(255, 255, 255);")
        self.directorylist.clear()
        self.listfile.clear()
        self.listseq.clear()

        self.pathChanged.emit( path )

        directory = QtCore.QDir(path)
        files = list(directory.entryList(QtCore.QDir.AllDirs))
        for fn in files:
       	    if fn == ".":
        	    continue
            self.addItem(fn ,FileSequenceWidget.FOLDER)

        if self._splitSequence == False: 
            sequences, others = seq.FileSequence.find(path)
            for s in sequences:
                self.addItem(str(s), FileSequenceWidget.SEQUENCE)
                self.listseq[str(s)] = s
                #print s.padding
                #print s.head

            for o in others:
				self.addItem(o , FileSequenceWidget.FILE)
        else:
            files = [e for e in os.listdir(path) if os.path.isfile(os.path.join(path, e))]
            for fn in files:
				self.addItem(fn ,FileSequenceWidget.FILE)
	
    """
    refresh the filelist
    """
    def refresh( self ):
        self.setCurrentDirPath( self.path)

    """
    slot if the checkbox split seq change.
    """
    def splitseqchanged( self ):
        self._splitSequence = self.checkboxsplitseq.isChecked()
        self.setCurrentDirPath( self.path) 
	
    """
    slot if the commbox selection change
    """
    def filterchanged(self ):
	    self.setCurrentDirPath( self.path)
	
    """
    slot if the commbox bookmark selection change
    """
    def bookmarkchanged(self):
        newpath = self.bookmarkCombo.currentText()
        if newpath != "":
            self.pathEdit.setText( newpath ) 

    """
      add a filter type:
        example : 
        self.addFilter(".jpg;.png;.bmp;.gif;.pic;.exr")
    """
    def addFilter(self, filter):
	    self.filtercombo.addItem(filter)

    # Slot adding bookmark 
    def addBookmark(self):
        BookmarkMamanger.getBookmarkManager().addBookmark(self.path)
        self.refreshbookmarkcombo()

    # Slot show bookmrk dialog
    def showDialogBookmark(self):
        db = dialogBookmark()

    """
        Set Action for the context Menu of DirectoryList
        @param action list of action.
    """
    def setContextMenuActionDirectoryList( self , action):
        self.directorylist.setContextMenuAction( action )
	
    """
        Set Action for the context Menu of DirectoryList
        @param action list of action.
    """
    def setContextMenuActionFileList( self , action):
        self.listfile.setContextMenuAction( action )

    def getSequenseObj( self , filename):
        return self.listseq[filename]

    def isSequence(self, filename):
        return filename in self.listseq 
    
    @property
    def selectedpath( self):
        return self.getDirectorySelected()

    @property
    def selectedfiles( self):
        return self.getFilenameSelected()

"""
Modal Dialog to select seauence file..
By default the path in the home users
Example
fsd = FileSequenceDialog(["",".jpg;.png;.bmp;.gif;.pic;.exr",".jpg",".png",".mov;.avi;.mp4;.mpg"]) # for windows
    if fsd.exec_() == QtGui.QDialog.Accepted:
        print fsd.getFilename()

""" 
class FileSequenceDialog(QtGui.QDialog):

    """
       constructor
       @param filters array of extension 
       @param the begin path for the dialog. by default QtCore.QDir.homePath() 
    """
    def __init__(self, filters, path = QtCore.QDir.homePath()):
        super(FileSequenceDialog, self).__init__()
        self.setWindowTitle('Select File Sequence...')
        self.widget = FileSequenceWidget(path)
        
        for f in filters:
             self.widget.addFilter(f)

        layout = QtGui.QVBoxLayout()
        layout.addWidget(self.widget)
        self._buttonBox = QtGui.QDialogButtonBox(QtGui.QDialogButtonBox.Ok| QtGui.QDialogButtonBox.Cancel)

        self._buttonBox.accepted.connect(self.accept)
        self._buttonBox.rejected.connect(self.reject)
		
        self.widget.fileSelected.connect(self.fileSelected)
        layout.addWidget(self._buttonBox)
        # Set dialog layout
        self.setLayout(layout)
        
    def fileSelected(self, fullpathname):
		self.accept()
	
    def getFilename(self):
		return self.widget.getFilenameSelected()

"""
Main window for a application browsing the file system.
"""     
class MainWindow(QtGui.QMainWindow):

    def tableviewmode(self ):
        self.widget.setTableViewMode()

    def initToolbar( self ):
    
        """
        self.tableview = QtGui.QAction("&Table View...", self,
            shortcut=QtGui.QKeySequence.Open,
            statusTip="Open an existing file", triggered=self.widget.setTableViewMode)
        
        self.listview = QtGui.QAction("&List View...", self,
            shortcut=QtGui.QKeySequence.Open,
            statusTip="Open an existing file", triggered=self.widget.setListViewMode)
        """
        
        self.fileMenu = self.menuBar().addMenu("&File")
        self.viewMenu = self.menuBar().addMenu("&View")
        
        #self.viewMenu.addAction(self.tableview)
        #self.viewMenu.addAction(self.listview)

        addTabAction = QtGui.QAction("Add Tab ", self)
        addTabAction.triggered.connect(self.addTab)

        self.viewMenu.addAction(addTabAction)

        exitAction = QtGui.QAction('Exit', self)
        exitAction.setShortcut('Ctrl+Q')
        exitAction.triggered.connect(self.close)
        
        self.toolbar = self.addToolBar('Exit')
        self.toolbar.addAction(exitAction)

    

    """
        load and intialise plugins
    """
    def initPlugins(self):

        path = "plugins"
        pluginpath = os.path.join( os.path.dirname( os.path.realpath(__file__) ) , path )
        plugins = []
        # Load plugins
        sys.path.insert(0, pluginpath)
        for f in os.listdir(pluginpath):
            fname, ext = os.path.splitext(f)
            if ext == '.py':
                #print fname
                mod = __import__(fname)
                #print dir(mod)
                #print dir(mod.Plugin())
                plugins.append( mod.Plugin() )
        sys.path.pop(0)
        return plugins    
       
        #fsw.setContextMenuActionFileList([renameFileTabAction])


    """
      slot changing the title of tab for the current tab when user change a path...
    """
    def changecurrenttitletab( self, path ):
        self.tab.setTabText( self.tab.currentIndex(), path )

    def addTab(self , path = QtCore.QDir.homePath()):
        fsw = FileSequenceWidget(path)
        fsw.pathChanged.connect( self.changecurrenttitletab )        
        self.tab.addTab(fsw,path)

        openPathTabAction = QtGui.QAction("Open Path Tab ", self)
        openPathTabAction.triggered.connect(self.openPathTab)
        fsw.setContextMenuActionDirectoryList([openPathTabAction])

#        renameFileTabAction = QtGui.QAction("Rename", self)
#        renameFileTabAction.triggered.connect(self.renameFile)


        menucontext = [] 
        for p in self.plugins:
            a = QtGui.QAction(p.getLabel(), self)
            a.triggered.connect(lambda ans=p: self.execplugin(ans))
            dico = {}
            dico['action'] = a;
            dico['plugin'] = p;
            
            menucontext.append(dico)

        fsw.setContextMenuActionFileList( menucontext )
        #fsw.setContextMenuActionFileList( self.plugins )

    def execplugin( self , plugin ):
        plugin.execute( self.tab.currentWidget().selectedfiles,self.tab.currentWidget() )

    def closetab(self,index ):
        self.tab.removeTab( index )

    def openPathTab(self ):
        self.addTab( self.tab.currentWidget() .selectedpath )


    def __init__(self):
        super(MainWindow, self).__init__()

        self.plugins = self.initPlugins()
        # create QTabWidget
        self.tab = QtGui.QTabWidget()
        self.tab.setTabsClosable(True)
        self.tab.tabCloseRequested.connect(self.closetab) 
        self.addTab(QtCore.QDir.homePath())
        self.setCentralWidget(self.tab)
        self.initToolbar()

       


if __name__ == '__main__':

    import sys

    app = QtGui.QApplication(sys.argv)
    window = MainWindow()
    window.show()
	

    #fsd = FileSequenceDialog(["",".jpg;.png;.bmp;.gif;.pic;.exr",".jpg",".png",".mov;.avi;.mp4;.mpg"])
    #if fsd.exec_() == QtGui.QDialog.Accepted:
    #    print fsd.getFilename()
	    
    sys.exit(app.exec_())
